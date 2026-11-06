"""Minimal Switch agent client: a WebSocket for events, HTTP for calls.

Endpoints (switch-rooms/internals/agent-connection and agent-protocol):
  WS    /agents/{agent_id}/connection/ws
        ?connection_id=&filter=all&rooms=[&start_from=&expected_generation=]
  POST  /agents/{agent_id}/ops/{operation}   body = arguments, header X-Switch-Connection-Id
  POST  /agents/{agent_id}/message           body = {room_id, content}
Every request carries `Authorization: Bearer <agent API key>`. The key is never logged.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
import websockets

from bailiff.events import Event, Malformed, detail, parse_event
from bailiff.redact import redact_bounded

MAX_BACKOFF = 30.0
REFUSED_CLOSE_CODES = range(4400, 4500)

Dial = Callable[[str, dict[str, str]], Awaitable[Any]]


class TakenOver(Exception):
    """Another connection took this connection id. Final: never reconnect."""


class SwitchRefused(Exception):
    """Switch refused the connection (4xxx close or handshake HTTP error). Not retried."""


class ReconnectExhausted(Exception):
    """The socket kept dropping and the reconnect cap was reached."""


class OpError(Exception):
    """A call to Switch returned a non-2xx status."""

    def __init__(self, name: str, status: int, body: str) -> None:
        super().__init__(f"{name} failed with HTTP {status}: {body}")
        self.status = status


async def _default_dial(url: str, headers: dict[str, str]) -> Any:
    # max_size is pinned to 1 MiB so an oversized frame is refused, whatever the library default is.
    return await websockets.connect(url, additional_headers=headers, max_size=2**20)


def _check(name: str, resp: httpx.Response) -> None:
    if not 200 <= resp.status_code < 300:
        raise OpError(name, resp.status_code, resp.text[:200])


def _body(name: str, resp: httpx.Response) -> dict[str, Any]:
    _check(name, resp)
    try:
        data = resp.json()
    except ValueError as exc:
        raise OpError(name, resp.status_code, "response was not JSON") from exc
    return data if isinstance(data, dict) else {"result": data}


class SwitchConnection:
    """One agent's connection to a Switch room. Use as an async context manager."""

    def __init__(
        self,
        base_url: str,
        agent_id: str,
        api_key: str,
        connection_id: str,
        rooms: list[str],
        *,
        max_reconnects: int = 5,
        backoff: float = 1.0,
        timeout: float = 10.0,
        dial: Dial | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
        stable_after: float = 10.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._agent_id = agent_id
        self._api_key = api_key
        self._connection_id = connection_id
        self._rooms = rooms
        self._max_reconnects = max_reconnects
        self._backoff = backoff
        self._dial: Dial = dial or _default_dial
        self._clock = clock
        self._stable_after = stable_after
        self._http = httpx.AsyncClient(base_url=self._base, timeout=timeout, transport=transport)
        self._ws: Any = None
        self.cursor: int | None = None
        self.generation: int | None = None
        self.malformed = 0
        self.redactions = 0

    def _auth(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", **(extra or {})}

    def _ws_url(self) -> str:
        parts = urlsplit(self._base)
        scheme = "wss" if parts.scheme == "https" else "ws"
        query: dict[str, str] = {
            "connection_id": self._connection_id,
            "filter": "all",
            "rooms": ",".join(self._rooms),
        }
        if self.cursor is not None:
            query["start_from"] = str(self.cursor)
        if self.generation is not None:
            query["expected_generation"] = str(self.generation)
        return f"{scheme}://{parts.netloc}{parts.path}/agents/{self._agent_id}/connection/ws?{urlencode(query)}"

    async def _pause(self, failures: int) -> None:
        if failures > self._max_reconnects:
            raise ReconnectExhausted(f"gave up after {self._max_reconnects} reconnect attempts")
        await asyncio.sleep(min(MAX_BACKOFF, self._backoff * 2 ** (failures - 1)))

    async def events(self) -> AsyncIterator[Event]:
        """Yield events. Pings are answered and never yielded.

        Malformed frames are counted and skipped.
        """
        failures = 0
        while True:
            if failures:
                await self._pause(failures)
            try:
                ws = await self._dial(self._ws_url(), self._auth())
            except websockets.InvalidStatus as exc:
                raise SwitchRefused(f"handshake refused: HTTP {exc.response.status_code}") from exc
            except (OSError, websockets.WebSocketException):
                failures += 1
                continue
            self._ws = ws
            connected_at = self._clock()
            try:
                async for raw in ws:
                    frame = parse_event(raw)
                    if isinstance(frame, Malformed):
                        self.malformed += 1
                        continue
                    if frame.type == "ping":
                        await ws.send(json.dumps({"type": "pong", "cursor": self.cursor or 0}))
                        continue
                    info = detail(frame)
                    if frame.type == "evicted" and info.get("code") == "taken_over":
                        raise TakenOver("taken over by another connection; not reconnecting")
                    if frame.type == "connection_state" and isinstance(info.get("generation"), int):
                        self.generation = info["generation"]
                    if frame.cursor is not None and (
                        self.cursor is None or frame.cursor > self.cursor
                    ):
                        self.cursor = frame.cursor
                    yield frame
            except (websockets.ConnectionClosed, OSError):
                pass
            finally:
                self._ws = None
                await ws.close()
            if self._clock() - connected_at >= self._stable_after:
                failures = 0
            code = getattr(ws, "close_code", None)
            if code in REFUSED_CLOSE_CODES:
                raise SwitchRefused(f"Switch closed the connection with code {code}")
            failures += 1

    async def op(self, operation: str, /, **args: Any) -> dict[str, Any]:
        """Call an operation on this agent. Raises OpError on non-2xx."""
        resp = await self._http.post(
            f"/agents/{self._agent_id}/ops/{operation}",
            json=args,
            headers=self._auth({"X-Switch-Connection-Id": self._connection_id}),
        )
        return _body(operation, resp)

    async def post(self, room_id: str, text: str) -> int:
        """Post to a room. Redacts first and returns how many secrets were masked."""
        clean, hits = redact_bounded(text)
        resp = await self._http.post(
            f"/agents/{self._agent_id}/message",
            json={"room_id": room_id, "content": clean},
            headers=self._auth(),
        )
        _check("message", resp)
        self.redactions += hits
        return hits

    async def __aenter__(self) -> SwitchConnection:
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._ws is not None:
            await self._ws.close()
        await self._http.aclose()

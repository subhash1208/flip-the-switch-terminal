default:
    @just --list

check:
    python -m ruff check bailiff tests scripts
    python -m ruff format --check bailiff tests scripts

typecheck:
    python -m mypy bailiff

test:
    python -m pytest -q

demo:
    python -m bailiff.demo --offline

demo-docker:
    docker compose -f deploy/docker-compose.yml build
    python scripts/check_judge_path.py

replay receipt="receipt.json":
    python -m bailiff.replay {{receipt}} --docker

case-demo:
    node sample-app/export-service/case-demo/consumer.js

bob-fails:
    docker compose -f deploy/docker-compose.yml run --rm bob

alice-passes:
    docker compose -f deploy/docker-compose.yml run --rm alice

judge-check:
    python scripts/check_judge_path.py

judge:
    python scripts/judge.py

judge-offline:
    python scripts/judge.py --no-docker

ci: check typecheck test judge-offline

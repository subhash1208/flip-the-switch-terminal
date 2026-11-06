# Case-only import mismatch (real-Mac analogue, not in the judge path)

The real repo renamed `SqlAuthGuard.ts` to `sqlAuthGuard.ts` by case alone, then kept importing `./SqlAuthGuard`.

- macOS APFS (case-insensitive by default): the import resolves and the app boots.
- Linux ext4 (case-sensitive): `Error: Cannot find module './SqlAuthGuard'` with `code: 'MODULE_NOT_FOUND'`.

`case-demo/` flips the spelling so it runs standalone: the file is `SqlAuthGuard.js` and `consumer.js` requires `./sqlAuthGuard`.
It passes on case-insensitive filesystems (APFS, NTFS) and fails on case-sensitive ones (ext4).
It is not required by `test.js`, so the Alice and Bob containers never reach it.
Run it with `just case-demo`.

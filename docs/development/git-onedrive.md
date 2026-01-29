# Git and OneDrive (Windows)

When the repo lives in a **OneDrive-synced folder** on Windows, Git sometimes fails with:

```text
fatal: Unable to create '.../.git/index.lock': Permission denied
```

This is usually due to OneDrive locking or syncing `.git` files while Git is running. Below are **permanent** fixes you can apply once.

## 1. One-time setup (recommended)

Run from the repo root:

```powershell
.\scripts\setup_git_onedrive.ps1
```

This script:

- Removes stale `.git\index.lock` and `.git\config.lock` if present (so Git can run).
- Sets local Git config: `core.fscache false`, `core.longpaths true` (reduces Windows file-handle caching that can conflict with OneDrive).

If you get `Permission denied` when running it (e.g. locking `.git/config`), close other apps using the repo, pause OneDrive briefly, then run it again.

On Linux/macOS (or Git Bash):

```bash
./scripts/setup_git_onedrive.sh
```

## 2. Use the Git-safe wrapper for add/commit/push

If you still hit lock errors, use the wrapper instead of `git` for those commands:

```powershell
.\scripts\git_safe.ps1 add -A
.\scripts\git_safe.ps1 commit -m "Your message"
.\scripts\git_safe.ps1 push
```

`git_safe.ps1` clears `.git\index.lock` before each run and retries once on failure. All other flags work as with `git`.

## 3. OneDrive settings

- **Always keep on this device**: For the repo folder, right‑click → **Always keep on this device**. This avoids “online-only” file behavior that can trigger permission issues.
- **Pause sync while committing**: Temporarily pause OneDrive sync when doing large or batch Git operations, then resume.

## 4. Move the repo outside OneDrive

The most reliable fix is to keep the repo **outside** any OneDrive-synced path (e.g. `C:\dev\smrforge` or `C:\repos\smrforge`). You can still use OneDrive for backups or docs; only the Git working tree should live elsewhere.

## 5. Other causes

- **Stale lock**: Another process or a crashed Git left `.git\index.lock` or `.git\config.lock`. Delete them manually (when no other Git operation is running):

  ```powershell
  Remove-Item -Force .git\index.lock, .git\config.lock -ErrorAction SilentlyContinue
  ```

- **Antivirus / Windows Defender**: Exclude the repo (or `git.exe`) from real‑time scanning if you see repeated permission errors.
- **Ransomware protection**: If the repo is under a protected folder, add an exclusion for the project directory or for `git.exe`.

## Summary

| Step | Action |
|------|--------|
| 1 | Run `.\scripts\setup_git_onedrive.ps1` once |
| 2 | Use `.\scripts\git_safe.ps1` for `add` / `commit` / `push` if lock errors persist |
| 3 | Prefer “Always keep on this device” for the repo folder in OneDrive |
| 4 | Or move the repo outside OneDrive for a permanent fix |

See also: [Testing and coverage](testing-and-coverage.md) for coverage-specific OneDrive workarounds (e.g. `COVERAGE_FILE` in `%TEMP%`).

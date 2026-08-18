# Deploy

Distribution and deployment tooling.

## Layout

- `deploy/config.py` + `deploy/template` - deploy-level configuration
  (repository/branch, python/git/adb executables, OCR server, webui,
  remote access), shared by the webui layer.
- `deploy/git.py` / `deploy/pip.py` - manual-update implementation
  (git pull + pip install), used by the webui update panel
  (`module/webui/updater.py`). There is no background auto-update loop.
- `deploy/set.py` - write `config/deploy.yaml` from the command line
  (`python -m deploy.set Key=Value`).
- `deploy/atomic.py` / `deploy/utils.py` / `deploy/logger.py` - shared
  helpers (atomic file IO, yaml helpers, deploy logging).
- `deploy/docker/` - containerized headless distribution
  (Dockerfile + Dockerfile.cn, python:3.13-slim-bookworm). Untested,
  no in-container self-update.
- `deploy/packaging/` - desktop packaging for the Tauri shell
  (PyInstaller onedir sidecar spec + build notes).

Supported deployment forms: source checkout (git-managed by the user),
the Tauri desktop shell, and Docker. The legacy toolkit installer
(bundled Git/Python/Electron), AidLux, headless dependency lists and the
git-over-CDN pack channel were removed.

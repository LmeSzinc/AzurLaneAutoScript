# Deploy

Distribution and deployment tooling.

## Layout

- `deploy/config.py` + `deploy/template` - deploy-level configuration
  (repository/branch/python paths, OCR server, webui, remote access),
  shared by the webui layer.
- `deploy/git.py` / `deploy/pip.py` - source-distribution updater
  (git pull + pip install), used by `module/webui/updater.py`.
- `deploy/set.py` - write `config/deploy.yaml` from the command line
  (`python -m deploy.set Key=Value`).
- `deploy/atomic.py` / `deploy/utils.py` / `deploy/logger.py` - shared
  helpers (atomic file IO, yaml helpers, deploy logging).
- `deploy/docker/` - containerized headless distribution
  (Dockerfile + Dockerfile.cn, python:3.13-slim-bookworm).
- `deploy/headless/` - Linux headless dependency list
  (opencv-python-headless).
- `deploy/git_over_cdn/` - HTTP pack incremental update client
  (update channel for regions where GitHub is unreachable).
- `deploy/packaging/` - desktop packaging for the Tauri shell
  (PyInstaller onedir sidecar spec + build notes).

The legacy toolkit installer (bundled Git/Python/Electron) and the
AidLux distribution were removed; the installer-time helpers still
needed at runtime were relocated into `module/device/platform/`
(`adb_connect.py`, `DataProcessInfo` in `platform_windows.py`).

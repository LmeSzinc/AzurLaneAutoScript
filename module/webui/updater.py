"""Release-based updater for the desktop app (single channel).

Installed builds update by whole-release replacement: the backend pulls
release metadata from the configured GitHub repository, downloads the two
release assets (NSIS setup exe + PyInstaller sidecar zip), swaps the
sidecar directory and runs the installer silently; the installer replaces
the shell, kills the app and relaunches it, and the new shell spawns the
new backend. The shell's kill-on-close job reaps the old backend tree.

Source checkouts are not special-cased (single UI by design): install
reports an error because there is no sidecar to swap. Developers update
with git manually.
"""

import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile

import requests

from module.base.paths import get_resource_root
from module.logger import logger

GITHUB_API = "https://api.github.com"
DEFAULT_REPO = "Joxos/AzurLaneAutoScript"


class Updater:
    def __init__(self):
        self.state = "idle"  # idle | refreshing | ready | failed | installing
        self.error: str | None = None
        self.releases: list[dict] = []
        self.install: dict | None = None  # {version, stage, progress}
        self._lock = threading.Lock()

    # ---------- configuration ----------

    @property
    def repo(self) -> str:
        return (os.environ.get("ALAS_UPDATE_REPO") or DEFAULT_REPO).strip().strip("/")

    @staticmethod
    def current_version() -> str:
        """Version of the running build, from the bundled version.txt."""
        path = os.path.join(get_resource_root(), "version.txt")
        try:
            with open(path, encoding="utf-8") as f:
                return f.read().strip() or "dev"
        except OSError:
            return "dev"

    @staticmethod
    def is_installed_build() -> bool:
        return bool(getattr(sys, "frozen", False))

    # ---------- release listing ----------

    def refresh(self):
        with self._lock:
            if self.state == "installing":
                return
            self.state = "refreshing"
            self.error = None
        try:
            url = f"{GITHUB_API}/repos/{self.repo}/releases?per_page=30"
            resp = requests.get(
                url, timeout=20, headers={"Accept": "application/vnd.github+json", "User-Agent": "alas"}
            )
            resp.raise_for_status()
            releases = []
            for rel in resp.json():
                releases.append(
                    {
                        "tag": rel["tag_name"],
                        "name": rel.get("name") or rel["tag_name"],
                        "body": (rel.get("body") or "")[:2000],
                        "date": rel.get("published_at") or "",
                        "prerelease": bool(rel.get("prerelease")),
                        "assets": [
                            {
                                "name": a["name"],
                                "size": a.get("size", 0),
                                "url": a["browser_download_url"],
                            }
                            for a in rel.get("assets", [])
                        ],
                    }
                )
            with self._lock:
                self.releases = releases
                self.state = "ready"
        except Exception as e:
            logger.exception("Fetch releases failed")
            with self._lock:
                self.state = "failed"
                self.error = str(e)

    def status(self) -> dict:
        return {
            "current": self.current_version(),
            "repo": self.repo,
            "state": self.state,
            "error": self.error,
            "releases": self.releases,
            "installing": self.install,
        }

    # ---------- install ----------

    def start_install(self, tag: str) -> str | None:
        """Start an install worker; returns an error string if refused."""
        with self._lock:
            if self.state == "installing":
                return "An install is already in progress"
            release = next((r for r in self.releases if r["tag"] == tag), None)
        if release is None:
            return f"Release {tag} not found, refresh the list first"
        threading.Thread(target=self._install_worker, args=(release,), daemon=True).start()
        return None

    def _install_worker(self, release: dict):
        with self._lock:
            self.state = "installing"
            self.install = {"version": release["tag"], "stage": "preparing", "progress": 0}
            self.error = None
        try:
            self._install(release)
        except Exception as e:
            logger.exception("Release install failed")
            with self._lock:
                self.state = "failed"
                self.error = str(e)
                self.install = None

    def _install(self, release: dict):
        if not self.is_installed_build():
            raise RuntimeError("Installing a release requires the installed desktop build")

        sidecar_dir = os.path.dirname(os.path.abspath(sys.executable))
        tmp = os.path.join(os.environ.get("TEMP", "."), "alas-update", release["tag"])
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp, exist_ok=True)

        setup_asset = next(
            (a for a in release["assets"] if a["name"].lower().endswith(".exe") and "setup" in a["name"].lower()), None
        )
        zip_asset = next((a for a in release["assets"] if a["name"].lower().endswith(".zip")), None)
        if setup_asset is None or zip_asset is None:
            raise RuntimeError("Release is missing assets (need the setup exe and the backend zip)")

        def _progress(stage: str, offset: int, scale: int, done: int, total: int):
            frac = 0 if not total else min(done / total, 1.0)
            with self._lock:
                if self.install is not None:
                    self.install["stage"] = stage
                    self.install["progress"] = round((offset + frac * scale) * 100)

        # Backend zip = 60% of the progress bar, shell installer = 40%.
        zip_path = self._download(zip_asset, os.path.join(tmp, zip_asset["name"]), lambda d, t: _progress("downloading backend", 0, 0.6, d, t))
        setup_path = self._download(
            setup_asset, os.path.join(tmp, setup_asset["name"]), lambda d, t: _progress("downloading shell", 0.6, 0.4, d, t)
        )

        # Stop running tasks before swapping files out from under them.
        self._stop_tasks()

        # Swap the sidecar: rename the running dir aside (Windows allows
        # renaming a directory whose exe is running), extract the new one
        # next to it. The old dir is removed on the next startup.
        with self._lock:
            self.install["stage"] = "swapping backend"
        backup = sidecar_dir + ".old"
        shutil.rmtree(backup, ignore_errors=True)
        os.rename(sidecar_dir, backup)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(os.path.dirname(sidecar_dir))
        except Exception:
            shutil.rmtree(sidecar_dir, ignore_errors=True)
            os.rename(backup, sidecar_dir)
            raise

        # Run the NSIS installer silently: it replaces the shell binary,
        # kills this app, and relaunches. This process rarely survives past
        # this point; the job object reaps the backend tree with the shell.
        with self._lock:
            self.install["stage"] = "installing shell"
            self.install["progress"] = 100
        logger.info(f"Running installer {setup_path} /S")
        subprocess.run([setup_path, "/S"], check=True, timeout=900)

    @staticmethod
    def _download(asset: dict, path: str, progress) -> str:
        logger.info(f"Downloading {asset['name']} ({asset.get('size', 0)} bytes)")
        with requests.get(asset["url"], stream=True, timeout=60, headers={"User-Agent": "alas"}) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length") or asset.get("size") or 0)
            done = 0
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        progress(done, total)
        return path

    @staticmethod
    def _stop_tasks():
        from module.webui.process_manager import ProcessManager

        running = []
        for manager in ProcessManager._processes.values():
            if manager.alive:
                running.append(manager)
                manager.stop()
        deadline = time.time() + 30
        while running and time.time() < deadline:
            running = [m for m in running if m.alive]
            time.sleep(0.5)


updater = Updater()

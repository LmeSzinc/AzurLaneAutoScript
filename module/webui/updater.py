"""Release-based updater for the desktop app (single channel).

Installed builds update by whole-release replacement: the backend pulls
release metadata from the configured GitHub repository, downloads the
release's NSIS setup exe and runs it silently. The installer carries the
new sidecar (bundle.resources), kills the running app (the shell's
kill-on-close job reaps this backend tree), overwrites shell and sidecar
files and restarts the app.

Source checkouts are not special-cased (single UI by design): install
reports an error because there is no installed build to replace.
Developers update with git manually.
"""

import os
import shutil
import subprocess
import sys
import threading
import time

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
        """Version of the running build, from the bundled version.txt.

        The file sits next to the sidecar executable (packaging writes it
        into the onedir root), not under the _internal resource dir.
        """
        if getattr(sys, "frozen", False):
            root = os.path.dirname(os.path.abspath(sys.executable))
        else:
            root = get_resource_root()
        path = os.path.join(root, "version.txt")
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

        tmp = os.path.join(os.environ.get("TEMP", "."), "alas-update", release["tag"])
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp, exist_ok=True)

        setup_asset = next(
            (a for a in release["assets"] if a["name"].lower().endswith(".exe") and "setup" in a["name"].lower()), None
        )
        if setup_asset is None:
            raise RuntimeError("Release is missing the setup exe asset")

        def _progress(stage: str, done: int, total: int):
            frac = 0 if not total else min(done / total, 1.0)
            with self._lock:
                if self.install is not None:
                    self.install["stage"] = stage
                    self.install["progress"] = round(frac * 100)

        setup_path = self._download(setup_asset, os.path.join(tmp, setup_asset["name"]), lambda d, t: _progress("downloading installer", d, t))

        # Stop running tasks before the installer replaces files under them.
        self._stop_tasks()

        # Run the NSIS installer silently: it carries the new sidecar
        # (bundle.resources), kills the running app (the job object reaps
        # this backend tree), overwrites the shell and sidecar files and
        # restarts the app. /R makes the installer relaunch the app after
        # a silent install (stock tauri NSIS onInstSuccess hook).
        # CREATE_BREAKAWAY_FROM_JOB: the installer inherits the shell's
        # kill-on-close job through this process; it must survive the job
        # teardown (which fires the moment the installer kills the shell)
        # or the install would be reaped mid-flight and never relaunch.
        with self._lock:
            self.install["stage"] = "installing"
            self.install["progress"] = 100
        logger.info(f"Running installer {setup_path} /S /R")
        creationflags = 0x0100_0000 if os.name == "nt" else 0  # CREATE_BREAKAWAY_FROM_JOB
        subprocess.run([setup_path, "/S", "/R"], check=True, timeout=900, creationflags=creationflags)

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

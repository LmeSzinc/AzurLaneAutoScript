"""Regenerate pip-facing requirement files from the uv project.

`requirements.txt` is consumed by the git+pip developer update channel
(deploy/pip.py) and is the source for the docker variant, so keep the
uv export artifact in sync here:

- requirements.txt                : `uv export` output
- deploy/docker/requirements.txt  : docker variant derived from it
"""

import os
import subprocess
import sys

# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.getcwd())

from deploy.docker.requirements_generator import docker_requirements_generate


def requirements_export():
    print("uv export -> requirements.txt")
    subprocess.run(
        ["uv", "export", "--no-hashes", "--no-dev", "--format", "requirements-txt", "-o", "requirements.txt"],
        check=True,
    )


if __name__ == "__main__":
    requirements_export()
    docker_requirements_generate()

import os
import re
import sys

# Allow `python deploy/docker/requirements_generator.py` from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from deploy.logger import logger

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
logger.info(BASE_FOLDER)

# uv export lines look like `name==version` with optional `; platform marker`
# suffixes; `# via` provenance comments are indented and skipped.
UV_EXPORT_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^ ;#]+)")


def read_uv_export(file):
    out = {}
    with open(file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            res = UV_EXPORT_RE.match(line)
            if res:
                out[res.group(1)] = res.group(2)
    return out


def write_file(file, data):
    lines = []
    for name, version in data.items():
        if version:
            lines.append(f"{name}=={version}")
        else:
            lines.append(str(name))

    with open(file, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines) + "\n")


def docker_requirements_generate(requirements_txt="requirements.txt"):
    """Generate deploy/docker/requirements.txt from the uv export artifact.

    The root requirements.txt is produced by `uv export` (see
    dev_tools/requirements_updater.py) and pins every dependency, so the
    docker image installs a reproducible environment.
    """
    requirements = read_uv_export(requirements_txt)

    logger.info("Generate requirements for Docker image from uv export")
    new = {}
    for name, version in requirements.items():
        # alas-webapp is for windows only
        if name == "alas-webapp":
            continue
        # Docker images have no GUI stack, use the headless opencv build
        if name == "opencv-python":
            name = "opencv-python-headless"
        new[name] = version

    write_file(os.path.join(BASE_FOLDER, "./requirements.txt"), data=new)


if __name__ == "__main__":
    docker_requirements_generate()

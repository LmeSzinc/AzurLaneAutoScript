import os
import re

from deploy.logger import logger

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
logger.info(BASE_FOLDER)

NAME_RE = re.compile(r'^([A-Za-z0-9_.-]+)')


def read_file(file):
    out = {}
    with open(file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if not line.strip():
                continue
            res = [s.strip() for s in line.split('==')]
            if len(res) > 1:
                name, version = res
            else:
                name, version = res[0], None
            out[name] = version

    return out


def write_file(file, data):
    lines = []
    for name, version in data.items():
        if version:
            lines.append(f'{name}=={version}')
        else:
            lines.append(str(name))

    with open(file, 'w', encoding='utf-8', newline='') as f:
        text = '\n'.join(lines)
        text = text.replace('#', '\n#').strip()
        f.write(text)


def headless_requirements_generate(requirements_in='requirements-in.txt'):
    requirements = read_file(requirements_in)

    logger.info(f'Generate requirements for headless environment')
    # Lock by normalized package name (requirements-in entries carry
    # version constraints, e.g. 'opencv-python>=4.12').
    lock = {
        'opencv-python': {
            'name': 'opencv-python-headless',
            'version': None
        },
    }
    new = {}
    logger.info(requirements)
    for name, version in requirements.items():
        if name == 'alas-webapp':
            continue
        match = NAME_RE.match(name)
        lock_name = match.group(1) if match else name
        if lock_name in lock:
            entry = lock[lock_name]
            if isinstance(entry, dict):
                name = entry['name']
                version = entry['version']
            else:
                version = entry
        new[name] = version

    write_file(os.path.join(BASE_FOLDER, f'./requirements.txt'), data=new)


if __name__ == '__main__':
    headless_requirements_generate()

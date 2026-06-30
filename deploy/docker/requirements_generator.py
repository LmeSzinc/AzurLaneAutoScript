import os

from deploy.logger import logger

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
logger.info(BASE_FOLDER)


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


def docker_requirements_generate(requirements_in='requirements-in.txt'):
    requirements = read_file(requirements_in)

    logger.info(f'Generate requirements for Docker image')
    lock = {}
    new = {}
    logger.info(requirements)
    for name, version in requirements.items():
        # alas-webapp is for windows only
        if name == 'alas-webapp':
            continue
        if name == 'opencv-python':
            name = 'opencv-python-headless'
            version = None
        if name in lock:
            version = lock[name] if not isinstance(lock[name], dict) else lock[name]['version']
            name = name if not isinstance(lock[name], dict) else lock[name]['name']
        new[name] = version

    write_file(os.path.join(BASE_FOLDER, f'./requirements.txt'), data=new)


if __name__ == '__main__':
    docker_requirements_generate()

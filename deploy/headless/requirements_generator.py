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


def headless_requirements_generate(requirements_in='requirements-in.txt'):
    requirements = read_file(requirements_in)

    logger.info(f'Generate requirements for headless environment')
    lock = {
        'aiofiles': '23.1.0',
        'inflection': '0.5.1',
        'lz4': '4.3.2',
        'numpy': '1.17.4',
        # 'onepush': '1.2.0',
        'opencv-python': {
            'name': 'opencv-python-headless',
            'version': '4.7.0.72'
        },
        'pillow': '9.5.0',
        'pydantic': '1.10.9',
        'pyyaml': '6.0',
        'retrying': '1.3.4',
        'tqdm': '4.65.0',
        'wrapt': '1.15.0'
    }
    new = {}
    logger.info(requirements)
    for name, version in requirements.items():
        if name == 'alas-webapp':
            continue
        if name in lock:
            version = lock[name] if not isinstance(lock[name], dict) else lock[name]['version']
            name = name if not isinstance(lock[name], dict) else lock[name]['name']
        new[name] = version

    write_file(os.path.join(BASE_FOLDER, f'./requirements.txt'), data=new)


if __name__ == '__main__':
    headless_requirements_generate()

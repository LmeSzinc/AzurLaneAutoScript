import os
from deploy.logger import logger

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
logger.info(BASE_FOLDER)

def read_file(file):
    out = {}
    with open(file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
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
        f.write('\n'.join(lines))


def docker_requirements_generate(requirements_in='requirements-in.txt'):

    if not os.path.exists(requirements_in):
        requirements_in = os.path.join(BASE_FOLDER+"/../../", requirements_in)
        assert os.path.exists(requirements_in)

    requirements = read_file(requirements_in)

    logger.info(f'Generate requirements for Docker image')

    new = {}
    logger.info(requirements)
    for name, version in requirements.items():
        # alas-webapp is for windows only
        if name == 'alas-webapp':
            continue
        if name == 'opencv-python':
            name = 'opencv-python-headless'
            version = None
        # if name == 'numpy':
        #     version = None
        new[name] = version

    write_file(os.path.join(BASE_FOLDER, f'./requirements.txt'), data=new)

if __name__ == '__main__':
    docker_requirements_generate()
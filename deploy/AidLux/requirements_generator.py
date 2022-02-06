import os
import re


def iter_version():
    return [folder for folder in os.listdir('./') if re.match('^[0-9.]+$', folder)]


def read_file(file):
    regex = re.compile('^(.+?)[= ]+([0-9.]+)|^([a-zA-Z0-9.]+)$')
    out = {}
    with open(file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            res = regex.search(line)
            if res:
                name, version, name2 = res.groups()
                if name:
                    out[name] = version
                else:
                    out[name2] = version

    return out


def write_file(file, data):
    lines = []
    for name, version in data.items():
        if version:
            lines.append(f'{name}=={version}')
        else:
            lines.append(str(name))

    with open(file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    """
    Generate requirements.txt for AidLux.
    """
    requirements = read_file('../../requirements-in.txt')
    for aidlux in iter_version():
        print(f'Generate requirements for AidLux {aidlux}')
        pre_installed = read_file(f'./{aidlux}/pre-installed.txt')
        new = {}
        for name, version in requirements.items():
            # alas-webapp is for windows only
            if name == 'alas-webapp':
                continue
            version = pre_installed.get(name, version)
            # Having conflicts with numpy, let pip to decide
            if name == 'numpy':
                version = None
            new[name] = version

        write_file(f'./{aidlux}/requirements.txt', data=new)

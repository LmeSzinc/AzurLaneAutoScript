import re

from module.map.map_grids import SelectedGrids


class Requirement:
    def __init__(self, package, version=None):
        self.package = package
        self.version = version

    def generate(self):
        if self.version:
            return f'{self.package}=={self.version}'
        else:
            return str(self.package)

    def __bool__(self):
        return True

    def __eq__(self, other):
        return self.package == other.package


class RequirementList(SelectedGrids):
    def __init__(self, file):
        super().__init__([])
        self.load_file(file)

    def load_file(self, file):
        regex = re.compile('^(.+?)[= ]+([0-9.]+)|^([a-zA-Z0-9.]+)$')
        out = {}
        with open(file, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                if line.startswith('#'):
                    continue
                res = regex.search(line)
                if res:
                    name, version, name2 = res.groups()
                    if name:
                        out[name] = version
                    else:
                        out[name2] = version

        self.grids = []
        for package, version in out.items():
            self.grids.append(Requirement(package, version))

    def write_file(self, file):
        lines = self.call('generate')
        with open(file, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(lines))

    def insert_version(self, other):
        for other_req in other:
            self_req = self.select(package=other_req.package).first_or_none()
            if self_req:
                self_req.version = other_req.version

    def insert_all(self, other):
        for other_req in other:
            self_req = self.select(package=other_req.package).first_or_none()
            if self_req:
                self_req.version = other_req.version
            else:
                self.grids.append(Requirement(other_req.package, other_req.version))

    def remove_pip_requirements(self):
        self.delete(self.select(package='pip'))
        self.delete(self.select(package='wheel'))
        self.delete(self.select(package='packaging'))
        self.delete(self.select(package='setuptools'))

    def remove_windows_requirements(self):
        self.delete(self.select(package='alas-webapp'))
        self.delete(self.select(package='pywin32'))

    def set_version(self, version_dict):
        for package, version in version_dict.items():
            req = self.select(package=package).first_or_none()
            if req:
                req.version = version

    def write_pip_command(self, file):
        lines = []
        for requirement in self:
            lines.append(f'pip install --no-dependencies {requirement.generate()}')
        with open(file, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(lines))

    def delete(self, grids):
        new = super().delete(grids)
        self.grids = new.grids



if __name__ == '__main__':
    req = RequirementList('../../requirements.txt')
    pre = RequirementList('./pre-installed.txt')
    req.delete(pre)
    req.remove_pip_requirements()
    req.remove_windows_requirements()
    # opencv-python is installed via `pkg` but not shown in `pip list`
    req.delete(req.select(package='opencv-python'))
    # req.set_version({
    #     'numpy': '1.16.6',
    #     'scipy': '1.4.1',
    #     'matplotlib': '3.4.3'
    # })
    print(req.call('generate'))
    # req.write_file('requirements-in.txt')
    req.write_pip_command('pip_command.sh')
import os
import re
from dataclasses import dataclass, fields

from module.base.code_generator import CodeGenerator


@dataclass
class RouteData:
    name: str
    route: str
    plane: str
    floor: str = 'F1'
    position: tuple = None


class RouteExtract:
    def __init__(self, folder):
        self.folder = folder

    def iter_files(self):
        for path, folders, files in os.walk(self.folder):
            path = path.replace('\\', '/')
            for file in files:
                if file.endswith('.py'):
                    yield f'{path}/{file}'

    def extract_route(self, file):
        print(f'Extract {file}')
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        """
        def route_item_enemy(self):
            self.enter_himeko_trial()
            self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))
        """
        regex = re.compile(
            r'def (?P<func>[a-zA-Z0-9_]*?)\(self\):.*?'
            r'self\.map_init\((.*?)\)'
            , re.DOTALL)
        file = file.replace(self.folder, '').replace('.py', '').replace('/', '_').strip('_')
        module = f"{self.folder.strip('./').replace('/', '.')}.{file.replace('_', '.')}"

        for result in regex.findall(content):
            func, data = result

            res = re.search(r'plane=([a-zA-Z_]*)', data)
            if res:
                plane = res.group(1)
            else:
                # Must contain plane
                continue
            res = re.search(r'floor=([\'"a-zA-Z0-9_]*)', data)
            if res:
                floor = res.group(1).strip('"\'')
            else:
                floor = 'F1'
            res = re.search(r'position=\(([0-9.]*)[, ]+([0-9.]*)', data)
            if res:
                position = (float(res.group(1)), float(res.group(2)))
            else:
                position = None

            yield RouteData(
                name=f'{file}__{func}',
                route=f'{module}:{func}',
                plane=plane,
                floor=floor,
                position=position,
            )

    def write(self, file):
        gen = CodeGenerator()
        gen.Import("""
        from tasks.map.route.base import RouteData
        """)
        gen.CommentAutoGenerage('dev_tools.route_extract')

        for f in self.iter_files():
            for row in self.extract_route(f):
                with gen.Object(key=row.name, object_class='RouteData'):
                    for key in fields(row):
                        value = getattr(row, key.name)
                        gen.ObjectAttr(key.name, value)
        gen.write(file)


if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '../'))
    RouteExtract('./route/daily').write('./tasks/map/route/route/daily.py')

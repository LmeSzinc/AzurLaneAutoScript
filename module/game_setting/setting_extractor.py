import os
import re
from dataclasses import dataclass

from tqdm import tqdm

from module.base.decorator import cached_property
from module.device.method.utils import remove_prefix
from module.logger import logger

REGEX_SETTING = re.compile(r'PlayerPrefs.Get(\w{1,10})\((.*)\)')
REGEX_SETTING_KEY = re.compile(r'"(.*?)"')
REGEX_STRING = r'<string name="(?P<name>.*)">(?P<value>.*)</string>'
REGEX_INT = r'<int name="(?P<name>.*)" value="(?P<value>.*)" />'
REGEX_FLOAT = r'<float name="(?P<name>.*)" value="(?P<value>.*)" />'


def _strip_code(string):
    nested = 0
    for word in string:
        if word == '(':
            nested += 1
        if word == ')':
            # End as last )
            if nested == 1:
                yield word
                return
            nested -= 1
        yield word


def strip_code(string):
    return ''.join(list(_strip_code(string)))


@dataclass
class Field:
    formatter: callable
    value: ''
    regex: str

    def __call__(self, *args, **kwargs):
        regex = self.regex
        for arg in args:
            regex = regex.replace('(.*)', arg, 1)
        return Field(self.formatter, self.value, regex)

    @cached_property
    def pattern(self):
        if self.formatter == float:
            pattern = REGEX_FLOAT
        elif self.formatter == int:
            pattern = REGEX_INT
        else:
            pattern = REGEX_STRING
        pattern = pattern.replace(r'(?P<name>.*)', self.regex, 1)
        return pattern

    def find(self, setting):
        res = re.search(self.pattern, setting.data)
        if res is not None:
            self.value = res.groupdict()['value']

    def update(self, setting):
        if '(.*)' in self.pattern:
            res = re.findall(self.pattern, setting.data)
            if res:
                for groups in res:
                    old = self.pattern
                    for group in groups[:-1]:
                        old = old.replace('(.*)', group, 1)
                    new = old.replace(r'(?P<value>.*)', self.value)
                    logger.info('Setting: ' + new)
                    setting.data = re.sub(old, new, setting.data)
                return
            else:
                # Todo
                logger.warning('Setting: ' + self.pattern + 'is not found in game settings, '
                                                            'unable to update setting')
                return

        new = self.pattern.replace(r'(?P<value>.*)', self.value)
        res, num = re.subn(self.pattern, new, setting.data)
        if num > 0:
            logger.info('Setting: ' + new)
            setting.data = res
        else:
            logger.info('Setting: ' + self.pattern + 'is not found in game settings, '
                                                     'set it at the end of file')
            new = '    ' + new + '\n</map>'
            setting.data = re.sub('</map>', new, setting.data)


@dataclass
class LuaSetting:
    raw: str
    # typ: "Int", "String", "Float"
    typ: str
    # "AUTOFIGHT_BATTERY_SAVEMODE, 0"
    # "world_help_progress"
    code: str

    duplicate = False

    @cached_property
    def default(self):
        if ',' in self.code:
            name, default = self.code.split(',', 1)
            default = default.strip(' ",')
            if self.typ == 'Int':
                try:
                    return int(default)
                except ValueError:
                    return 0
            if self.typ == 'String':
                return repr(default)
            if self.typ == 'Float':
                try:
                    return float(default)
                except ValueError:
                    return 0.
        else:
            if self.typ == 'Int':
                return 0
            if self.typ == 'String':
                return repr('')
            if self.typ == 'Float':
                return 0.
        return None

    @cached_property
    def key(self):
        # "autoBotIsAcitve" .. AutoBotCommand.GetAutoBotMark(slot0)
        # "world_help_progress"
        if ',' in self.code:
            code = self.code.rsplit(',', 1)[0].strip(' ')
        else:
            code = self.code.strip(' ')

        res = REGEX_SETTING_KEY.search(code)
        if res:
            return res.group(1).replace('.', '_').replace('%', '_').replace('-', '_').replace(':', '_').strip('_')
        else:
            return ''

    @cached_property
    def formatter(self):
        if self.typ == 'Int':
            return 'int'
        if self.typ == 'String':
            return 'str'
        if self.typ == 'Float':
            return 'float'
        return 'str'

    @cached_property
    def regex(self):
        if ',' in self.code:
            code = self.code.rsplit(',', 1)[0].strip(' ')
        else:
            code = self.code.strip(' ')

        pieces = code.split('..')

        def iter_piece():
            for piece in pieces:
                res = REGEX_SETTING_KEY.search(piece)
                if res:
                    yield res.group(1)
                else:
                    yield '(.*)'

        return repr(''.join(list(iter_piece())))

    @cached_property
    def generated(self):
        if self.key == '':
            return [
                f'# {self.raw}',
                'pass  # Unknown'
            ]
        if self.duplicate:
            return [
                f'# {self.raw}',
                'pass  # Duplicate'
            ]

        return [
            f'# {self.raw}',
            f'{self.key} = Field(formatter={self.formatter}, value={self.default}, regex={self.regex})'
        ]


class SettingExtractor:
    @staticmethod
    def iter_setting_from_file(file):
        with open(file, mode='r', encoding='utf8') as f:
            data = list(f.readlines())

        for row in data:
            row = row.strip()
            res = REGEX_SETTING.search(row)
            if res:
                row = strip_code(res.group(0))
                res = REGEX_SETTING.search(row)
                if res:
                    yield LuaSetting(raw=row, typ=res.group(1), code=res.group(2))

    @staticmethod
    def iter_file_from_folder(folder):
        for path, folders, files in os.walk(folder):
            for file in files:
                file = f'{path}/{file}'
                yield file

    def iter_generated_lines(self, folder):
        dic_settings = set()
        yield 'from module.game_setting.setting_extractor import Field'
        yield ''
        yield '# This file was automatically generated by module/game_setting/setting_extractor.py'
        yield "# Don't modify it manually."
        yield ''
        yield ''
        yield 'class GameSettingsGenerated:'
        files = list(self.iter_file_from_folder(folder))
        for file in tqdm(files):
            settings = list(self.iter_setting_from_file(file))
            if not settings:
                continue
            yield ''
            f = remove_prefix(file, folder).replace("\\", "/")
            yield f'    # {f}'
            for setting in settings:
                if setting.key in dic_settings:
                    setting.duplicate = True
                dic_settings.add(setting.key)
                for line in setting.generated:
                    yield f'    {line}'

    def generate(self, folder, output='./module/game_setting/setting_generated.py'):
        lines = [l + '\n' for l in self.iter_generated_lines(folder)]
        with open(output, mode='w', encoding='utf8') as f:
            f.writelines(lines)


if __name__ == '__main__':
    # Path to AzurLaneLuaScripts\CN
    FOLDER = r''
    ex = SettingExtractor()
    ex.generate(FOLDER)

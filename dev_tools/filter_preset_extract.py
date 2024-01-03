import os
import pandas as pd
import textwrap

from tasks.rogue.keywords import KEYWORDS_ROGUE_PATH
from module.logger import logger

INDENTATION = '    '
PATHS = [
    KEYWORDS_ROGUE_PATH.Preservation,
    KEYWORDS_ROGUE_PATH.Remembrance,
    KEYWORDS_ROGUE_PATH.Nihility,
    KEYWORDS_ROGUE_PATH.Abundance,
    KEYWORDS_ROGUE_PATH.The_Hunt,
    KEYWORDS_ROGUE_PATH.Destruction,
    KEYWORDS_ROGUE_PATH.Elation,
    KEYWORDS_ROGUE_PATH.Propagation,
    KEYWORDS_ROGUE_PATH.Erudition,
]

class PresetFilterGenerator:
    def __init__(self, file_name: str = None):
        if file_name is None:
            file_name = './filter.xlsx'
        if not os.path.exists(file_name):
            logger.warning(f'File {file_name} not found')
            exit()
        self.file = pd.read_excel(file_name, sheet_name=None)
        self.paths = []
        self.path_name = {}
        self.get_paths()
        self.general = ['强力', '输出', '生存', '功能']
        self.replace = {'黄色(强力通用)': '强力', '蓝色(通用输出)': '输出', '绿色(通用生存)': '生存',
                        '红色(通用功能)': '功能'}
        self.content = {}
        self.length = 76

    def get_paths(self):
        for path in PATHS:
            self.paths.append(path.name)
            self.path_name[path.name] = path.cn

    def check_sheet(self, sheet_name: str) -> bool:
        if sheet_name not in self.file:
            logger.warning(f'sheet {sheet_name} not found')
            return False
        else:
            return True

    def to_list(self, sheet: pd.DataFrame, title: str, sort_name: str = '排序') -> list:
        name = '祝福' if title != '奇物' else '奇物'
        sheet_ = sheet[sheet[sort_name] > 0].sort_values(by=sort_name)
        sheet_ = sheet_[name].tolist()

        for key in self.replace.keys():
            if key in sheet_ and self.replace[key] in self.content:
                index = sheet_.index(key)
                sheet_ = sheet_[:index] + self.content[self.replace[key]] + sheet_[index + 1:]

        sheet_ = list(dict.fromkeys(sheet_))

        remove_list = sheet[sheet[sort_name] == -1][name].tolist()
        for item in remove_list:
            if item in sheet_:
                sheet_.remove(item)

        if title == '奇物' and 'XX火漆' in sheet_:
            sheet_[sheet_.index('XX火漆')] = sort_name + '火漆'

        if 'random' in sheet_:
            sheet_.remove('random')

        return sheet_

    def to_str(self, blessing: list, name: str, one_line=False) -> str:
        if one_line:
            ret = ' > '.join(blessing + ['random'])
            return f'{INDENTATION}"{name}": "{ret}",\n'
        ret = f'{INDENTATION}"{name}": \"\"\"\n'

        def list_to_str(l_, ind):
            return textwrap.indent(textwrap.fill(' > '.join(l_), self.length), ind)

        if 'reset' in blessing:
            re_index = blessing.index('reset')
            ret += list_to_str(blessing[: re_index], INDENTATION * 2)
            ret += f'\n{INDENTATION * 2}> reset >\n'
            ret += list_to_str(blessing[re_index + 1:], INDENTATION * 2)

        else:
            ret += list_to_str(blessing, INDENTATION * 2)
        ret = ret.replace(f' >\n{INDENTATION * 2}', f'\n{INDENTATION * 2}> ')
        ret += f'\n{INDENTATION * 2}> random\n{INDENTATION * 2}\"\"\",\n\n'
        return ret

    def generate(self):
        for _ in self.general:
            self.content[_] = self.to_list(self.file[_], _) if self.check_sheet(_) else []

        resonance = {}
        curio = {}
        has_resonance = self.check_sheet('回响')
        has_curio = self.check_sheet('奇物')

        for path in self.paths:
            path_name = self.path_name[path]
            self.content[path] = self.to_list(self.file[path_name], path_name) if self.check_sheet(path_name) else []
            resonance[path] = self.to_list(self.file['回响'][self.file['回响']['命途'] == path_name],
                                           '回响') if has_resonance else []
            curio[path] = self.to_list(self.file['奇物'], '奇物', sort_name=path_name) if has_curio else []
        self.content['回响'] = resonance
        self.content['奇物'] = curio

        preset = 'BLESSING_PRESET = {\n'
        for path in self.paths:
            preset += self.to_str(self.content[path], path)

        preset += '}\nRESONANCE_PRESET = {\n'
        for path in self.paths:
            preset += self.to_str(self.content['回响'][path], path, one_line=True)

        preset += '}\nCURIO_PRESET = {\n'
        for path in self.paths:
            preset += self.to_str(self.content['奇物'][path], path)
        preset += '}'

        with open('./tasks/rogue/blessing/preset.py', 'w', encoding='utf-8') as f:
            f.write(preset)


if __name__ == '__main__':
    PresetFilterGenerator().generate()

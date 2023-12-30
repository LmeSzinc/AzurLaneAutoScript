import codecs
import configparser
import os

from gooey import Gooey, GooeyParser

# from main import AzurLaneAutoScript
# 这是个自定义的模块引入的就是路径
from module.config.dictionary import dic_chi_to_eng, dic_eng_to_chi

def main():
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # print(script_name)
    # Load default value from .ini file.
    config_file = f'./config/{script_name}.ini'
    config = configparser.ConfigParser(interpolation=None)
    config.read_file(codecs.open(config_file, "r", "utf8"))
    # print(config)
    obj = {
        'a': 'setting',
        'b': 'daily',
        'c': 'main',
        'd': 'event',
    }
    saved_config = {}
    # 读取配置文件并获取<Section>
    for opt, option in config.items():
        # 获取<Section>中的键和值
        for key, value in option.items():
            # dic_eng_to_chi是个字典
            key = dic_eng_to_chi.get(key, key)
            if value in dic_eng_to_chi:
                value = dic_eng_to_chi.get(value, value)
            if value == 'None':
                value = ''
            saved_config[key] = value
    print(saved_config)
if __name__ == '__main__':
    main()
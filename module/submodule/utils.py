import os

MOD_DICT = {'maa': 'AlasMaaBridge'}
MOD_CONFIG_DICT = {}


def list_mod():
    out = []
    for item in MOD_DICT.items():
        out.append(item)
    return out


def get_dir_name(name):
    return MOD_DICT[name]


def filepath_mod(name):
    return os.path.join('./submodule', get_dir_name(name))


def mod_template():
    out = []
    for mod_name, dir_name in list_mod():
        for file in os.listdir(os.path.join('./submodule', dir_name, 'config')):
            name, extension = os.path.splitext(file)
            if name == 'template' and extension == '.json':
                out.append(f'{name}-{mod_name}')

    return out


def mod_instance():
    global MOD_CONFIG_DICT
    MOD_CONFIG_DICT.clear()
    out = []
    for mod_name, dir_name in list_mod():
        for file in os.listdir(os.path.join('./submodule', dir_name, 'config')):
            name, extension = os.path.splitext(file)
            if name != 'template' and extension == '.json':
                out.append(name)
                MOD_CONFIG_DICT[name] = mod_name

    return out


def get_config_mod(config_name):
    """
    Args:
        config_name (str):
    """
    if config_name.startswith('template-'):
        return config_name.replace('template-', '')
    try:
        return MOD_CONFIG_DICT[config_name]
    except KeyError:
        return 'alas'

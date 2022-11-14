import os

MOD_DICT = {'maa': 'AlasMaaBridge'}
MOD_CONFIG_DICT = {}


def list_mod():
    return list(MOD_DICT.items())


def get_dir_name(name):
    return MOD_DICT.get(name)


def filepath_mod(name):
    return os.path.join('./submodule', get_dir_name(name))


def mod_template():
    out = []
    for file in os.listdir('./config'):
        name, extension = os.path.splitext(file)
        config_name, mod_name = os.path.splitext(name)
        mod_name = mod_name[1:]
        if config_name == 'template' and extension == '.json' and mod_name != '':
            out.append(f'{config_name}-{mod_name}')

    return out


def mod_instance():
    global MOD_CONFIG_DICT
    MOD_CONFIG_DICT.clear()
    out = []
    for file in os.listdir('./config'):
        name, extension = os.path.splitext(file)
        config_name, mod_name = os.path.splitext(name)
        mod_name = mod_name[1:]
        if config_name != 'template' and extension == '.json' and mod_name != '':
            out.append(config_name)
            MOD_CONFIG_DICT[config_name] = mod_name

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

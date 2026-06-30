import os

MOD_DICT = {
    'maa': 'AlasMaaBridge',
    'fpy': 'AlasFpyBridge',
}
MOD_FUNC_DICT = {
    'MaaCopilot': 'maa',
    'FpyBattle': 'fpy',
    'FpyBenchmark': 'fpy',
    'FpyCall': 'fpy',
}
MOD_CONFIG_DICT = {}


def get_available_func():
    return (
        'Daemon',
        'OpsiDaemon',
        'EventStory',
        'AzurLaneUncensored',
        'Benchmark',
        'GameManager',
    )


def get_available_mod():
    return set(MOD_DICT)


def get_available_mod_func():
    return set(MOD_FUNC_DICT)


def get_func_mod(func):
    return MOD_FUNC_DICT.get(func)


def list_mod_dir():
    return list(MOD_DICT.items())


def get_mod_dir(name):
    return MOD_DICT.get(name)


def get_mod_filepath(name):
    return os.path.join('./submodule', get_mod_dir(name))


def list_mod_template():
    out = []
    for file in os.listdir('./config'):
        name, extension = os.path.splitext(file)
        config_name, mod_name = os.path.splitext(name)
        mod_name = mod_name[1:]
        if config_name == 'template' and extension == '.json' and mod_name != '':
            out.append(f'{config_name}-{mod_name}')

    return out


def list_mod_instance():
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

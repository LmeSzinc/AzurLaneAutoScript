from module.config.utils import *

LANG = 'zh-CN'
TRANSLATE_MODE = False


def set_language(s: str, refresh=False):
    global LANG
    for i, lang in enumerate(LANGUAGES):
        # pywebio.session.info.user_language return `zh-CN` or `zh-cn`, depends on browser
        if lang.lower() == s.lower():
            LANG = LANGUAGES[i]
            break
    else:
        LANG = 'en-US'
    if refresh:
        from pywebio.session import run_js
        run_js('location.reload();')


def t(s):
    """
    Get translation.
    """
    if TRANSLATE_MODE:
        return s
    # print(_t(s, LANG))
    return _t(s, LANG)


def _t(s, lang=None):
    """
    Get translation, ignore TRANSLATE_MODE
    """
    if not lang:
        lang = LANG
    try:
        return dic_lang[lang][s]
    except KeyError:
        print(f"Language key ({s}) not found")
        return s


# temporary dictionary
dic_eng_to_chi = {
    "Gui.Aside.Install": "安装",
    "Gui.Aside.Develop": "开发",
    "Gui.Aside.Performance": "性能",
    "Gui.Aside.Setting": "设置",
    "Gui.Button.ScrollON": "自动滚动 开",
    "Gui.Button.ScrollOFF": "自动滚动 关",
    "Gui.Button.ClearLog": "清空日志",
    "Gui.Toast.DisableTranslateMode": "点击这里关闭翻译模式",
    "Gui.Toast.ConfigSaved": "设置已保存",
    "Gui.Toast.AlasIsRunning": "调度器已在运行中",
    "Gui.MenuAlas.Overview": "总览",
    "Gui.MenuAlas.Log": "运行日志",
    "Gui.MenuDevelop.Translate": "翻译"
}


dic_eng = {
    "Gui.Aside.Install": "Install",
    "Gui.Aside.Develop": "Develop",
    "Gui.Aside.Performance": "Perf.",
    "Gui.Aside.Setting": "Settings",
    "Gui.Button.ScrollON": "Scroll ON",
    "Gui.Button.ScrollOFF": "Scroll OFF",
    "Gui.Button.ClearLog": "Clear Log",
    "Gui.Toast.DisableTranslateMode": "Click here to disable translate mode",
    "Gui.Toast.ConfigSaved": "Config saved",
    "Gui.Toast.AlasIsRunning": "Scheduler is running",
    "Gui.MenuAlas.Overview": "Overview",
    "Gui.MenuAlas.Log": "Logs",
    "Gui.MenuDevelop.Translate": "Translate"
}

dic_tchi = {}
dic_jp = {}

dic_eng_to_eng = {key: key for key in dic_eng_to_chi}
dic_eng_to_eng.update(dic_eng)

dic_eng_to_jp = dic_eng_to_eng.copy()
dic_eng_to_jp.update(dic_jp)

dic_eng_to_tchi = dic_eng_to_chi.copy()
dic_eng_to_tchi.update(dic_tchi)

dic_lang = {
    "zh-CN": dic_eng_to_chi,
    "zh-TW": dic_eng_to_tchi,
    "en-US": dic_eng_to_eng,
    "ja-JP": dic_eng_to_jp,
}


def reload():
    for lang in LANGUAGES:
        for path, v in deep_iter(read_file(filepath_i18n(lang)), depth=3):
            dic_lang[lang]['.'.join(path)] = v

    for key in dic_lang["zh-TW"].keys():
        if dic_lang["zh-TW"][key] == key:
            dic_lang["zh-TW"][key] = dic_lang["zh-CN"][key]

    for key in dic_lang["ja-JP"].keys():
        if dic_lang["ja-JP"][key] == key:
            dic_lang["ja-JP"][key] = dic_lang["en-US"][key]


reload()

"""Shared helpers for the webui API routers."""

import re
from datetime import datetime
from typing import Any

from rich.console import Console

from module.config.deep import deep_get, deep_iter, deep_set
from module.config.utils import alas_instance, filepath_config, write_file
from module.logger import WEB_THEME
from module.webui.process_manager import ProcessManager
from module.webui.setting import State

_update_singleton = None

# Shared render console: creating one Console per renderable made the
# initial full-log dump on SSE connect slow (hundreds of constructions).
# render_log is only called sequentially (single to_thread batches), so a
# shared console is safe.
_render_console: "Console | None" = None


def _get_render_console() -> Console:
    global _render_console
    if _render_console is None:
        _render_console = Console(
            theme=WEB_THEME,
            no_color=False,
            color_system="standard",
            force_terminal=True,
        )
    return _render_console


def _get_updater():
    """Module-level updater singleton so state survives across requests."""
    global _update_singleton
    if _update_singleton is None:
        from module.webui.updater import Updater

        _update_singleton = Updater()
    return _update_singleton


def render_log(renderable) -> str:
    """Render a rich renderable to an ANSI-colored string for the web UI.

    `no_color=False` + explicit `color_system` bypass the NO_COLOR env var so
    output is deterministic; the frontend converts the ANSI SGR codes to
    theme-aware HTML (see webapp-tauri/src/lib/ansi.ts). WEB_THEME restores
    the `web.*` highlight spans (paths/booleans/braces) produced by the func
    stream; rich's Theme merges it over the default styles, so `log.time` and
    `logging.level.*` keep resolving too.
    """
    try:
        console = _get_render_console()
        with console.capture() as capture:
            console.print(renderable)
        return capture.get().rstrip("\n")
    except Exception:
        return str(renderable)


def build_status() -> dict[str, Any]:
    from module.webui import lang

    instances = []
    for name in alas_instance():
        manager = ProcessManager.get_manager(name)
        instances.append(
            {
                "name": name,
                "state": manager.state,
                "alive": manager.alive,
            }
        )
    return {
        "instances": instances,
        "theme": State.theme,
        "language": lang.LANG,
    }


def _parse_value(value: Any, valuetype: str) -> Any:
    """Convert a frontend value to the python type defined by valuetype."""
    if value is None:
        return value
    if valuetype == "int":
        return int(value)
    elif valuetype == "float":
        return float(value)
    elif valuetype == "bool":
        return bool(value)
    elif valuetype == "datetime":
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    elif valuetype == "str":
        return str(value)
    elif valuetype == "list":
        return value if isinstance(value, list) else [value]
    elif valuetype == "dict":
        return value if isinstance(value, dict) else {}
    return value


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def _save_config(modified: dict[str, Any], config_name: str, args_schema: dict[str, Any]) -> dict[str, Any]:
    """Validate and save modified config keys.

    Returns:
        {valid: [...], invalid: [...]}
    """
    valid = []
    invalid = []
    config_updater = State.config_updater
    config = config_updater.read_file(config_name)
    n = datetime.now()
    for p, v in deep_iter(config, depth=3):
        if p[-1].endswith("un") and not isinstance(v, bool):
            if (v - n).days >= 31:
                deep_set(config, p, "")
    for k, v in modified.items():
        valuetype = deep_get(args_schema, k + ".valuetype")
        # Selects carry no valuetype in the schema, but the DOM always
        # sends strings. Infer the type from the option list so numeric
        # options (e.g. Shipyard.ResearchSeries) are stored as ints, not
        # strings - otherwise config_update's option membership check
        # fails on read ('3' not in [1,2,3,...]) and the value silently
        # falls back to the schema default ("config lost").
        if valuetype is None:
            option = deep_get(args_schema, k + ".option")
            if isinstance(option, list) and option:
                if all(isinstance(o, bool) for o in option):
                    valuetype = "bool"
                elif all(isinstance(o, int) for o in option):
                    valuetype = "int"
                elif all(isinstance(o, float) for o in option):
                    valuetype = "float"
        v = _parse_value(v, valuetype)
        validate = deep_get(args_schema, k + ".validate")
        if not len(str(v)):
            default = deep_get(args_schema, k + ".value")
            deep_set(config, k, default)
            valid.append(k)
        elif validate == "datetime":
            # datetime args (e.g. Scheduler.NextRun) validate by parsing;
            # keep the string form so json.dumps stays happy
            try:
                v = datetime.strptime(str(v).replace("T", " "), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                invalid.append(k)
                continue
            deep_set(config, k, v)
            valid.append(k)
            for set_key, set_value in config_updater.save_callback(k, v):
                deep_set(config, set_key, set_value)
                valid.append(set_key)
        elif not validate or re.fullmatch(validate, str(v)):
            deep_set(config, k, v)
            valid.append(k)
            for set_key, set_value in config_updater.save_callback(k, v):
                deep_set(config, set_key, set_value)
                valid.append(set_key)
        else:
            invalid.append(k)

    if valid:
        write_file(filepath_config(config_name), config)
    return {"valid": valid, "invalid": invalid}

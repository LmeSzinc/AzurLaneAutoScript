from fastapi import APIRouter

from module.config.utils import filepath_args, read_file
from module.webui.api.models import SchemaResponse

router = APIRouter(tags=["schema"])


@router.get("/schema/{mod_name}", response_model=SchemaResponse)
def get_schema(mod_name: str = "alas"):
    from module.config.server import to_server

    menu = read_file(filepath_args("menu", mod_name))
    args = read_file(filepath_args("args", mod_name))
    # Resolve server-specific select options, mirroring the legacy
    # AlasGUI.set_group() behavior.
    server = to_server("cn")
    for _task, groups in args.items():
        for _group_name, argv in groups.items():
            for _arg_name, arg_dict in argv.items():
                if arg_dict.get("type") != "select":
                    continue
                options = arg_dict.get("option", [])
                server_options = arg_dict.get(f"option_{server}")
                if isinstance(server_options, list) and server_options:
                    options = server_options
                arg_dict["option"] = options
                if len(options) == 1:
                    only = options[0]
                    if only in arg_dict.get("option_bold", []):
                        arg_dict["type"] = "state"
    return {"menu": menu, "args": args}

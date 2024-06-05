from pywebio.output import clear, put_html, put_scope, put_text, use_scope
from pywebio.session import defer_call, info, run_js

from module.webui.utils import Icon, WebIOTaskHandler, set_localstorage


class Base:
    def __init__(self) -> None:
        self.alive = True
        # Whether window is visible
        self.visible = True
        # Device type
        self.is_mobile = info.user_agent.is_mobile
        # Task handler
        self.task_handler = WebIOTaskHandler()
        defer_call(self.stop)

    def stop(self) -> None:
        self.alive = False
        self.task_handler.stop()


class Frame(Base):
    def __init__(self) -> None:
        super().__init__()
        self.page = "Home"

    def init_aside(self, expand_menu: bool = True, name: str = None) -> None:
        """
        Call this in aside button callback function.
        Args:
            expand_menu: expand menu
            name: button name(label) to be highlight
        """
        self.visible = True
        self.task_handler.remove_pending_task()
        clear("menu")
        if expand_menu:
            self.expand_menu()
        if name:
            self.active_button("aside", name)
            set_localstorage("aside", name)

    def init_menu(self, collapse_menu: bool = True, name: str = None) -> None:
        """
        Call this in menu button callback function.
        Args:
            collapse_menu: collapse menu
            name: button name(label) to be highlight
        """
        self.visible = True
        self.page = name
        self.task_handler.remove_pending_task()
        clear("content")
        if collapse_menu:
            self.collapse_menu()
        if name:
            self.active_button("menu", name)

    @staticmethod
    @use_scope("ROOT", clear=True)
    def _show() -> None:
        put_scope(
            "header",
            [
                put_html(Icon.ALAS).style("--header-icon--"),
                put_text("AlasGG").style("--header-text--"),
                put_scope("header_status"),
                put_scope("header_title"),
            ],
        )
        put_scope(
            "contents",
            [
                put_scope("aside"),
                put_scope("menu"),
                put_scope("content"),
            ],
        )

    @staticmethod
    @use_scope("header_title", clear=True)
    def set_title(text=""):
        put_text(text)

    @staticmethod
    def collapse_menu() -> None:
        run_js(
            f"""
            $("#pywebio-scope-menu").addClass("container-menu-collapsed");
            $(".container-content-collapsed").removeClass("container-content-collapsed");
        """
        )

    @staticmethod
    def expand_menu() -> None:
        run_js(
            f"""
            $(".container-menu-collapsed").removeClass("container-menu-collapsed");
            $("#pywebio-scope-content").addClass("container-content-collapsed");
        """
        )

    @staticmethod
    def active_button(position, value) -> None:
        run_js(
            f"""
            $("button.btn-{position}").removeClass("btn-{position}-active");
            $("div[style*='--{position}-{value}--']>button").addClass("btn-{position}-active");
        """
        )

    @staticmethod
    def pin_set_invalid_mark(keys) -> None:
        if isinstance(keys, str):
            keys = [keys]
        keys = ["_".join(key.split(".")) for key in keys]
        js = "".join(
            [
                f"""$(".form-control[name='{key}']").addClass('is-invalid');"""
                for key in keys
            ]
        )
        if js:
            run_js(js)
        # for key in keys:
        #     pin_update(key, valid_status=False)

    @staticmethod
    def pin_remove_invalid_mark(keys) -> None:
        if isinstance(keys, str):
            keys = [keys]
        keys = ["_".join(key.split(".")) for key in keys]
        js = "".join(
            [
                f"""$(".form-control[name='{key}']").removeClass('is-invalid');"""
                for key in keys
            ]
        )
        if js:
            run_js(js)
        # for key in keys:
        # pin_update(key, valid_status=0)

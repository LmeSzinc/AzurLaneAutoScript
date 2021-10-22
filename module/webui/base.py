from module.webui.lang import t
from module.webui.utils import Icon, TaskHandler
from module.webui.widgets import put_icon_buttons
from pywebio.output import output, put_column, put_html, put_row, put_text
from pywebio.session import defer_call, info, run_js


class Base:
    def __init__(self) -> None:
        self.alive = True
        # Device type
        self.is_mobile = info.user_agent.is_mobile
        # Task handler
        self.task_handler = TaskHandler()
        defer_call(self.stop)

    def stop(self) -> None:
        self.alive = False
        self.task_handler.stop()


class Frame(Base):
    def __init__(self) -> None:
        super().__init__()
        self.aside = output()
        self.menu = output().style("container-menu")
        self.content = output().style("container-content")
        self.title = output().style("title-text-title")
        self.status = output().style("title-status")
        self._status = 0

        self.header = put_row([
            put_html(Icon.ALAS).style("title-icon-alas"),
            put_text("Alas").style("title-text-alas"),
            self.status,
            self.title,
        ]).style("container-title")
        self.asides = put_column([
            self.aside,
            None,
            put_icon_buttons(
                Icon.SETTING,
                buttons=[
                    {"label": t("Gui.Aside.Setting"),
                     "value": "setting", "color": "aside"}],
                onclick=[self.ui_setting],
            ).style("aside-icon-setting"),
        ], size="auto 1fr auto").style("container-aside")

        if self.is_mobile:
            self.contents = put_row([
                self.asides,
                self.menu,
                None,
                self.content,
            ], size="auto auto 1fr").style("container-main")
        else:
            self.contents = put_row([
                self.asides,
                self.menu,
                self.content,
            ], size="auto auto 1fr").style("container-main")

        self.main_area = output(
            put_column([
                self.header,
                self.contents,
            ], size="auto 1fr").style("container-all")
        ).style("container-gui")

    def init_aside(self, expand_menu: bool = True, name: str = None) -> None:
        """
        Call this in aside button callback function.
        Args:
            expand_menu: expand menu
            name: button name(label) to be highlight
        """
        self.task_handler.remove_pending_task()
        self.menu.reset()
        if expand_menu:
            self.expand_menu()
        if name:
            self.active_button('aside', name)

    def init_menu(self,
                  collapse_menu: bool = True,
                  name: str = None
                  ) -> None:
        """
        Call this in menu button callback function.
        Args:
            collapse_menu: collapse menu
            name: button name(label) to be highlight
        """
        self.task_handler.remove_pending_task()
        self.content.reset()
        if collapse_menu:
            self.collapse_menu()
        if name:
            self.active_button('menu', name)

    @staticmethod
    def collapse_menu() -> None:
        run_js(f"""
            $("[style*=container-menu]").addClass("container-menu-collapsed");
            $(".container-content-collapsed").removeClass("container-content-collapsed");
        """)

    @staticmethod
    def expand_menu() -> None:
        run_js(f"""
            $(".container-menu-collapsed").removeClass("container-menu-collapsed");
            $("[style*=container-content]").addClass("container-content-collapsed");
        """)

    @staticmethod
    def active_button(position, value) -> None:
        run_js(f"""
            $("button.btn-{position}").removeClass("btn-{position}-active");
            $("div[style*='--{position}-{value}--']>button").addClass("btn-{position}-active");
        """)

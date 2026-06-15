from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button
from textual.binding import Binding
from rich.text import Text

from screens.base_screen import BaseScreen


LOGO = r"""
  _____          _      _  ___ _   
 / ____|        | |    | |/ (_) |  
| |     ___   __| | ___| ' / _| |_ 
| |    / _ \ / _` |/ _ \  < | | __|
| |___| (_) | (_| |  __/ . \| | |_ 
 \_____\___/ \__,_|\___|_|\_\_|\__|


"""

MENU = [
    ("languages", "📦", "menu.languages", "Установка Python, Node.js, Java и других"),
    ("packages", "📚", "menu.packages", "Поиск и установка библиотек"),
    ("installed", "📋", "menu.installed", "Посмотреть что уже установлено"),
    ("tools", "🔧", "menu.tools", "Диагностика, шаблоны, версии"),
]


class MainMenu(BaseScreen):
    BINDINGS = [
        Binding("escape", "quit", "Выход", show=True),
        Binding("f2", "switch_lang", "RU/EN", show=True),
        Binding("up", "move_up", "", show=False),
        Binding("down", "move_down", "", show=False),
        Binding("enter", "select_item", "", show=False),
    ]

    CSS = """
    MainMenu {
        align: center middle;
    }
    #container {
        width: 64;
        height: auto;
    }
    #logo {
        width: 100%;
        height: 7;
        color: #00d4ff;
        content-align: center top;
        margin-bottom: 0;
    }
    #tagline {
        width: 100%;
        height: 1;
        color: #005577;
        content-align: center middle;
        text-style: italic;
        margin-bottom: 0;
    }
    #version {
        width: 100%;
        height: 1;
        color: #002d4a;
        content-align: center middle;
        margin-bottom: 1;
    }
    .menu-card {
        width: 100%;
        height: 4;
        border: solid #003366;
        background: #0a1628;
        margin-bottom: 1;
        padding: 0 1;
    }
    .menu-card:hover {
        background: #0d1f3c;
        border: solid #005577;
    }
    .menu-card:focus {
        background: #0d1f3c;
        border: solid #00d4ff;
    }
    #exit-btn {
        width: 100%;
        background: #1a0000;
        color: #ff6666;
        height: 3;
        margin-top: 1;
    }
    #hint {
        width: 100%;
        height: 1;
        color: #003d5c;
        content-align: center middle;
        margin-top: 1;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._focus_idx = 0

    def compose(self) -> ComposeResult:
        yield Container(
            Static(LOGO, id="logo"),
            Static(self._("app", "tagline"), id="tagline"),
            Static("[#002d4a]CodeKit v1.0[/]", id="version"),
            *[
                Button(f"{icon}   {self._(*key.split('.'))}", id=sid, classes="menu-card")
                for sid, icon, key, desc in MENU
            ],
            id="container",
        )

    def on_mount(self) -> None:
        logo = self.query_one("#logo")
        tagline = self.query_one("#tagline")
        version = self.query_one("#version")
        cards = list(self.query(".menu-card"))

        logo.styles.opacity = 0.0
        tagline.styles.opacity = 0.0
        version.styles.opacity = 0.0
        for c in cards:
            c.styles.opacity = 0.0

        logo.styles.animate("opacity", 1.0, duration=0.8)
        tagline.styles.animate("opacity", 1.0, duration=0.6)
        version.styles.animate("opacity", 1.0, duration=0.9)

        for i, c in enumerate(cards):
            delay = 0.3 + i * 0.12
            self.set_timer(delay, lambda w=c: w.styles.animate("opacity", 1.0, duration=0.5))

        if cards:
            self.set_timer(1.0, cards[0].focus)

    def action_move_up(self) -> None:
        btns = self.query(".menu-card")
        if self._focus_idx > 0:
            self._focus_idx -= 1
            btns[self._focus_idx].focus()

    def action_move_down(self) -> None:
        btns = self.query(".menu-card")
        if self._focus_idx < len(btns) - 1:
            self._focus_idx += 1
            btns[self._focus_idx].focus()

    def action_select_item(self) -> None:
        btns = self.query(".menu-card")
        if btns and self._focus_idx < len(btns):
            self._open_screen(btns[self._focus_idx].id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self._open_screen(event.button.id)

    def _open_screen(self, screen_id: str) -> None:
        mapping = {
            "languages": ("screens.languages", "LanguagesScreen"),
            "packages": ("screens.packages", "PackagesScreen"),
            "installed": ("screens.installed", "InstalledScreen"),
            "tools": ("screens.tools", "ToolsScreen"),
        }
        if screen_id in mapping:
            mod_path, cls_name = mapping[screen_id]
            import importlib
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            self.app.push_screen(cls())

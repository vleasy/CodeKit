from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.binding import Binding
from rich.text import Text
from utils.config import load_config, load_i18n, save_config


class BaseScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Назад", show=False),
        Binding("f2", "switch_lang", "RU/EN", show=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = load_config()
        self._lang = self._config.get("language", "ru")
        self._i18n = load_i18n(self._lang)

    def _(self, *keys: str) -> str:
        val = self._i18n
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, {})
            else:
                return keys[-1]
        return str(val) if isinstance(val, str) else keys[-1]

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_switch_lang(self) -> None:
        self._config["language"] = "en" if self._lang == "ru" else "ru"
        self._lang = self._config["language"]
        self._i18n = load_i18n(self._lang)
        save_config(self._config)
        self.recompose()

    def make_header(self, _title: str = "") -> Static:
        return Static(
            Text.from_markup(f"[bold #00d4ff]CodeKit[/]"),
            classes="header-box",
        )

    def make_footer(self, text: str = "") -> Static:
        if not text:
            text = self._("common", "hint")
        return Static(f" {text} ", classes="footer-box")

    def animate_fade_in(self, widget, duration: float = 0.6, delay: float = 0.0) -> None:
        widget.styles.opacity = 0.0
        self.set_timer(delay, lambda: widget.styles.animate("opacity", 1.0, duration=duration))

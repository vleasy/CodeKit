from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, RichLog
from rich.text import Text
import threading

from screens.base_screen import BaseScreen
from backends.language_manager import get_languages, install_language, get_manual_info, get_best_installer
from backends.system_detector import detect_language


LANG_ORDER = ["python", "nodejs", "java", "rust", "cpp"]


class LanguagesScreen(BaseScreen):
    CSS = """
    LanguagesScreen {
        background: #0a1628;
    }
    #body {
        height: 100%;
    }
    #sidebar {
        width: 30;
        height: 100%;
        border: solid #005577;
        margin-right: 1;
    }
    .lang-btn {
        width: 100%;
        height: 3;
        background: #0a1628;
        border: none;
        border-bottom: solid #002244;
        content-align: left middle;
        padding: 0 1;
    }
    .lang-btn:hover {
        background: #0d1f3c;
        border-bottom: solid #00aadd;
    }
    .lang-btn:focus {
        background: #1a3a5c;
        border-bottom: solid #00d4ff;
    }
    .lang-btn-active {
        border-left: solid #00d4ff;
    }
    #panel {
        width: 70%;
        height: 100%;
        border: solid #005577;
        padding: 1;
    }
    #info {
        height: auto;
        margin-bottom: 1;
    }
    #actions {
        height: 5;
        margin-bottom: 1;
    }
    #actions Button {
        margin-right: 1;
    }
    #output {
        height: 50%;
        border: solid #003366;
    }
    .btn-primary {
        background: #005577;
        color: #ffffff;
        min-width: 16;
    }
    .btn-warn {
        background: #3e2723;
        color: #ffb347;
        min-width: 16;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._langs = get_languages()
        self._current = "python"

    def compose(self) -> ComposeResult:
        yield self.make_header(self._("lang", "title"))
        with Horizontal(id="body"):
            yield Vertical(id="sidebar")
            with Vertical(id="panel"):
                yield Static("", id="info")
                with Horizontal(id="actions"):
                    yield Button(self._("lang", "install"), id="btn-install", classes="btn-primary")
                    yield Button(self._("lang", "manual"), id="btn-manual", classes="btn-warn")
                yield RichLog(id="output", highlight=True, markup=True)

    def on_mount(self) -> None:
        self._build_list()
        self._show_lang("python")

    def _refresh_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        for btn in sidebar.query(".lang-btn"):
            if hasattr(btn, "data_key") and btn.data_key == self._current:
                btn.classes = "lang-btn lang-btn-active"
            else:
                btn.classes = "lang-btn"

    def _build_list(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.remove_children()
        for idx, key in enumerate(LANG_ORDER):
            if key in self._langs:
                data = self._langs[key]
                det = detect_language(key, data.get("check_command", "")) if data.get("check_command") else None
                icon = data.get("icon", " ")
                name = data.get("name", key)
                status = "●" if det and det.installed else "○"
                style = "#00e676" if det and det.installed else "#005577"
                classes = "lang-btn lang-btn-active" if key == self._current else "lang-btn"
                btn = Button(f"{icon} {name} [{style}]{status}[/]", classes=classes)
                btn.data_key = key
                sidebar.mount(btn)

    def _show_lang(self, key: str) -> None:
        data = self._langs.get(key)
        if not data:
            return
        det = detect_language(key, data.get("check_command", "")) if data.get("check_command") else None
        name = data.get("name", key)
        icon = data.get("icon", " ")
        ver = det.version if det and det.version else "—"
        status = "✓ Установлен" if det and det.installed else "○ Не установлен"
        status_color = "#00e676" if det and det.installed else "#ffb347"
        installer = get_best_installer()

        info = self.query_one("#info")
        info.update(Text.from_markup(
            f"[bold #00d4ff]{icon} {name}[/]\n"
            f"[#005577]Версия:[/] [#a8c8e8]{ver}[/]\n"
            f"[#005577]Статус:[/] [{status_color}]{status}[/]\n"
            f"[#005577]Установщик:[/] [#a8c8e8]{installer}[/]\n"
        ))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn-install":
            self._do_install()
        elif bid == "btn-manual":
            self._do_manual()
        elif hasattr(event.button, "data_key"):
            self._current = event.button.data_key
            self._show_lang(self._current)
            self._refresh_sidebar()

    def _do_install(self) -> None:
        data = self._langs.get(self._current)
        if not data:
            return
        out = self.query_one("#output")
        out.clear()
        out.write(Text.from_markup(f"\n[#00d4ff]Устанавливаю {data.get('name', self._current)}...[/]"))

        def run():
            proc = install_language(self._current)
            if proc:
                for line in iter(proc.stdout.readline, ""):
                    self.call_from_thread(out.write, line.rstrip())
                proc.wait()
                self.call_from_thread(out.write, Text.from_markup(f"\n\n[#00e676]✓ Готово![/]"))
                self.call_from_thread(self._build_list)
            else:
                self.call_from_thread(out.write, Text.from_markup(f"\n\n[#ff5252]Нет подходящего установщика[/]"))
                self.call_from_thread(out.write, Text.from_markup(f"\n[#ffb347]Нажмите «Скачать вручную»[/]"))

        threading.Thread(target=run, daemon=True).start()

    def _do_manual(self) -> None:
        info = get_manual_info(self._current)
        out = self.query_one("#output")
        out.clear()
        out.write(Text.from_markup(
            f"\n[bold #00d4ff]Скачать вручную[/]\n\n"
            f"[#ffb347]Ссылка:[/]\n"
            f"[#a8c8e8]{info.get('url', '—')}[/]\n\n"
            f"[#005577]Сайт:[/] [#a8c8e8]{info.get('website', '—')}[/]\n"
            f"[#005577]Перейдите по ссылке и скачайте установщик.[/]\n"
        ))

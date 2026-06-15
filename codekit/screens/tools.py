import os
import json
import re
import threading
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, RichLog, Tree, Input
from rich.text import Text
from rich.table import Table

from screens.base_screen import BaseScreen
from backends.system_detector import detect_system, detect_language
from backends.language_manager import get_languages
from backends.template_engine import get_template_categories, create_project


TOOLS = [
    ("diag", "🔬", "tools.diag"),
    ("templates", "📁", "tools.templates"),
    ("versions", "🔄", "tools.versions"),
    ("path", "⚙", "tools.path"),
]


class ToolsScreen(BaseScreen):
    CSS = """
    ToolsScreen {
        background: #0a1628;
    }
    #body {
        height: 100%;
    }
    #sidebar {
        width: 24;
        height: 100%;
        border: solid #005577;
        margin-right: 1;
    }
    .tool-btn {
        width: 100%;
        height: 4;
        margin-bottom: 1;
        background: #0a1628;
        border: solid #003366;
    }
    .tool-btn:hover {
        background: #0d1f3c;
        border: solid #005577;
    }
    .tool-btn:focus {
        border: solid #00d4ff;
    }
    .tool-btn-active {
        border-left: solid #00d4ff;
    }
    #content {
        width: 74%;
        height: 100%;
        border: solid #005577;
        padding: 1;
    }
    .tmpl-btn {
        width: 100%;
        margin-bottom: 1;
        background: #0a1628;
        border: solid #003366;
    }
    .tmpl-btn:hover {
        background: #0d1f3c;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._langs = get_languages()
        self._current_tool = "diag"

    def compose(self) -> ComposeResult:
        yield self.make_header(self._("tools", "title"))
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                for sid, icon, key in TOOLS:
                    yield Button(f"{icon} {self._(*key.split('.'))}", id=f"tool-{sid}", classes="tool-btn")
            yield Vertical(id="content")

    def on_mount(self) -> None:
        self._show_tool("diag")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("tool-"):
            self._current_tool = bid[5:]
            self._show_tool(self._current_tool)
            self._refresh_sidebar()
        elif bid == "diag-run":
            self._run_diag()
        elif bid.startswith("tmpl-"):
            self._create_from_template(bid[5:])

    def _show_tool(self, tool: str) -> None:
        content = self.query_one("#content")
        content.remove_children()
        if tool == "diag":
            content.mount(Button("🔍 Запустить проверку", id="diag-run"))
            content.mount(RichLog(id="diag-output", highlight=True, markup=True))
            self._run_diag()
        elif tool == "templates":
            self._show_templates_form(content)
        elif tool == "versions":
            self._show_versions(content)
        elif tool == "path":
            self._show_path(content)

    def _refresh_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        for btn in sidebar.query(".tool-btn"):
            if btn.id == f"tool-{self._current_tool}":
                btn.classes = "tool-btn tool-btn-active"
            else:
                btn.classes = "tool-btn"

    def _run_diag(self) -> None:
        out = self.query_one("#diag-output")
        out.clear()
        sys_info = detect_system()
        t = Table.grid(padding=(0, 1))
        t.add_column(style="#005577", width=14)
        t.add_column(style="#a8c8e8")
        t.add_row("ОС:", f"{sys_info.os}")
        t.add_row("Архитектура:", sys_info.architecture)
        t.add_row("Python:", sys_info.python_version)
        t.add_row("winget:", "✓" if sys_info.has_winget else "—")
        t.add_row("choco:", "✓" if sys_info.has_choco else "—")
        out.write(Text.from_markup("\n[bold #00d4ff]Система[/]\n"))
        out.write(t)
        out.write(Text.from_markup("\n[bold #00d4ff]Языки[/]\n"))
        for key, data in self._langs.items():
            check = data.get("check_command", "")
            det = detect_language(key, check) if check else None
            status = "✓" if det and det.installed else "—"
            c = "#00e676" if det and det.installed else "#005577"
            out.write(Text.from_markup(f"  [{c}]{status}[/] [#a8c8e8]{data.get('name', key)}[/]\n"))

    def _show_templates_form(self, content: Vertical) -> None:
        from backends.template_engine import get_template_categories
        content.mount(Static("\n[bold #00d4ff]Шаблоны проектов[/]\n"))
        cats = get_template_categories()
        for cat, tmpls in cats.items():
            for t in tmpls:
                btn = Button(f"  {t['name']}  [{t['language']}]", id=f"tmpl-{t['key']}", classes="tmpl-btn")
                content.mount(btn)
        content.mount(Input(placeholder="Имя проекта (по умолч. my-project)", id="tmpl-name"))
        content.mount(Static("", id="tmpl-output"))

    def _create_from_template(self, tmpl_key: str) -> None:
        name_input = self.query_one("#tmpl-name")
        project_name = (name_input.value or "my-project").strip() or "my-project"
        out = self.query_one("#tmpl-output")
        try:
            files = create_project(tmpl_key, project_name, str(Path.cwd()))
            out.update(Text.from_markup(f"\n[#00e676]✓ Проект создан![/]\n"))
            for f in files:
                out.update(Text.from_markup(f"  [#a8c8e8]{f}[/]\n"))
        except Exception as e:
            out.update(Text.from_markup(f"\n[#ff5252]Ошибка: {e}[/]"))

    def _show_versions(self, content: Vertical) -> None:
        t = Table.grid(padding=(0, 1))
        t.add_column(style="#005577", width=16)
        t.add_column(style="#a8c8e8")
        for key, data in self._langs.items():
            check = data.get("check_command", "")
            det = detect_language(key, check) if check else None
            ver = det.version if det and det.version else "—"
            t.add_row(data.get("name", key), ver)
        content.mount(Static(f"\n[bold #00d4ff]{self._('tools', 'versions')}[/]\n"))
        content.mount(Static(t))

    def _show_path(self, content: Vertical) -> None:
        path_val = os.environ.get("PATH", "")
        entries = [p for p in path_val.split(";") if p.strip()]
        content.mount(Static(f"\n[bold #00d4ff]{self._('tools', 'path')}[/]\n"))
        t = Table(style="#a8c8e8", border_style="#003366")
        t.add_column("#", style="#005577", width=3)
        t.add_column("Путь", style="#a8c8e8")
        for i, entry in enumerate(entries[:20], 1):
            t.add_row(str(i), entry[:60])
        if len(entries) > 20:
            t.add_row("...", f"и ещё {len(entries) - 20}")
        content.mount(Static(t))

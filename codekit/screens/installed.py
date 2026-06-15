from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, Tree, RichLog
from rich.text import Text
from rich.table import Table

from screens.base_screen import BaseScreen
from backends.language_manager import get_languages, detect_installed_languages
from backends.package_manager import list_installed_packages, get_package_manager


class InstalledScreen(BaseScreen):
    CSS = """
    InstalledScreen {
        background: #0a1628;
    }
    #body {
        height: 100%;
    }
    #tree-panel {
        width: 50%;
        height: 100%;
        border: solid #005577;
        margin-right: 1;
    }
    #detail-panel {
        width: 48%;
        height: 100%;
        border: solid #005577;
        padding: 1;
    }
    #tree-view {
        height: 100%;
    }
    #empty-msg {
        color: #005577;
        content-align: center middle;
        height: 100%;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._detected = detect_installed_languages()

    def compose(self) -> ComposeResult:
        yield self.make_header(self._("inst", "title"))
        with Horizontal(id="body"):
            yield Tree(self._("inst", "title"), id="tree-view")
            with Vertical(id="detail-panel"):
                yield Static(self._("inst", "detail"), id="detail-content")

    def on_mount(self) -> None:
        self._build_tree()

    def _build_tree(self) -> None:
        tree = self.query_one("#tree-view")
        tree.root.expand()
        has_any = False
        for key, data, det in self._detected:
            if data:
                has_any = True
                name = data.get("name", key)
                icon = data.get("icon", " ")
                v = f"({det.version})" if det and det.version else ""
                status = "●" if det and det.installed else "○"
                node = tree.root.add(f"{icon} {name} {status} {v}")
                node.data = {"key": key, "type": "lang"}
                if det and det.installed:
                    pkgs = list_installed_packages(key)
                    for pkg in pkgs[:15]:
                        pn = pkg.get("name", "")
                        pv = pkg.get("version", "")
                        sub = node.add(f"  {pn} ({pv})")
                        sub.data = {"type": "pkg"}
        if not has_any:
            tree.root.add(f"[#005577]{self._('inst', 'empty')}[/]")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        detail = self.query_one("#detail-content")
        node = event.node
        if node.data and node.data.get("type") == "lang":
            key = node.data["key"]
            data = get_languages().get(key, {})
            det = None
            for k, _, d in self._detected:
                if k == key:
                    det = d; break
            t = Table.grid(padding=(0, 1))
            t.add_column(style="#005577", width=16)
            t.add_column(style="#a8c8e8")
            t.add_row("Имя:", data.get("name", key))
            t.add_row("PM:", get_package_manager(key) or "—")
            if det:
                t.add_row("Версия:", det.version or "—")
                t.add_row("Путь:", det.path or "—")
                t.add_row("Статус:", "✓ Установлен" if det.installed else "○ Не установлен")
            detail.update(t)

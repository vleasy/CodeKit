from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, Input
from textual.binding import Binding
from rich.text import Text
from pathlib import Path
import threading

from screens.base_screen import BaseScreen
from backends.language_manager import get_languages, detect_installed_languages
from backends.package_manager import (
    get_popular, search_packages, install_package,
    list_installed_packages, get_package_manager,
    check_manager, uninstall_package,
)
from backends.template_engine import get_template_categories, create_project


LANG_ORDER = ["python", "nodejs", "java", "rust", "cpp"]


class PackagesScreen(BaseScreen):
    BINDINGS = [
        Binding("escape", "go_back", "Назад", show=False),
        Binding("f2", "switch_lang", "RU/EN", show=True),
        Binding("f5", "refresh", "🔄", show=True),
        Binding("f6", "show_templates", "📁", show=True),
    ]

    def action_show_templates(self) -> None:
        self._show_templates()

    CSS = """
    PackagesScreen {
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
        border-left: solid #00d4ff !important;
    }
    #content {
        width: 74%;
        height: 100%;
    }
    #search-input {
        width: 100%;
        height: 3;
        border: solid #005577;
    }
    #search-input:focus {
        border: solid #00d4ff;
    }
    #status-bar {
        height: 1;
        color: #005577;
        content-align: left top;
        margin-bottom: 1;
    }
    #pkg-container {
        height: 100%;
        border: solid #003366;
        overflow-y: auto;
    }
    .pkg-card {
        width: 100%;
        height: 3;
        background: #0a1628;
        border: none;
        border-bottom: solid #002244;
        content-align: left middle;
        padding: 0 1;
    }
    .pkg-card:hover {
        background: #0d1f3c;
        border-bottom: solid #00aadd;
    }
    .pkg-card:focus {
        background: #1a3a5c;
        border-bottom: solid #00d4ff;
    }
    .installed-card {
        width: 100%;
        height: 3;
        background: #0a1628;
        border: none;
        border-bottom: solid #001a33;
        content-align: left middle;
        padding: 0 1;
    }
    .installed-card:hover {
        background: #0d1f3c;
        border-bottom: solid #ffb347;
    }
    .installed-card:focus {
        background: #1a3a5c;
        border-bottom: solid #ffb347;
    }
    .section-title {
        width: 100%;
        height: 1;
        color: #005577;
        padding: 0 1;
        margin-top: 1;
    }
    .pm-warn {
        width: 100%;
        height: 1;
        color: #ffb347;
        padding: 0 1;
    }
    .detail-name {
        width: 100%;
        height: 1;
        color: #00d4ff;
        text-style: bold;
        padding: 0 1;
    }
    .detail-desc {
        width: 100%;
        height: 1;
        color: #a8c8e8;
        padding: 0 1;
        margin-top: 1;
    }
    .detail-label {
        width: 100%;
        height: 1;
        color: #005577;
        padding: 0 1;
    }
    .btn-primary {
        background: #005577;
        color: #ffffff;
        min-width: 16;
        height: 3;
        border: none;
        border-bottom: solid #00d4ff;
    }
    .btn-primary:hover {
        background: #0088aa;
    }
    .btn-danger {
        background: #3e0000;
        color: #ff6666;
        min-width: 16;
        height: 3;
        border: none;
        border-bottom: solid #ff5252;
    }
    .btn-danger:hover {
        background: #5c0000;
    }
    .btn-secondary {
        background: #1a1a2e;
        color: #a8c8e8;
        min-width: 16;
        height: 3;
        border: none;
        border-bottom: solid #003366;
    }
    .btn-secondary:hover {
        background: #2a2a4e;
    }
    .history-btn {
        width: 100%;
        height: 2;
        background: #0a1628;
        border: none;
        border-bottom: solid #001a33;
        content-align: left middle;
        padding: 0 2;
    }
    .history-btn:hover {
        background: #0d1f3c;
    }
    .tmpl-btn {
        width: 100%;
        height: 3;
        margin-bottom: 1;
        background: #0a1628;
        border: solid #003366;
    }
    .tmpl-btn:hover {
        background: #0d1f3c;
        border: solid #00d4ff;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._langs = get_languages()
        self._detected = detect_installed_languages()
        self._current = "python"
        self._show_popular = True
        self._search_history: list[str] = []
        self._detail_pkg: dict | None = None
        self._tmpl_name_input: Input | None = None
        self._tmpl_output: Static | None = None
        self._selected_template: str = ""

    def compose(self) -> ComposeResult:
        yield self.make_header(self._("pkg", "title"))
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                for key in LANG_ORDER:
                    if key in self._langs:
                        data = self._langs[key]
                        icon = data.get("icon", " ")
                        name = data.get("name", key)
                        installed = self._is_installed(key)
                        sc = "#00e676" if installed else "#005577"
                        st = "●" if installed else "○"
                        yield Button(f"{icon} {name} [{sc}]{st}[/]", id=f"lang-{key}", classes="lang-btn")
            with Vertical(id="content"):
                yield Input(placeholder="🔍 Поиск пакетов...", id="search-input")
                yield Static("", id="status-bar")
                yield ScrollableContainer(id="pkg-container")

    def on_mount(self) -> None:
        self._show_packages("python")

    def _is_installed(self, key: str) -> bool:
        for k, _, det in self._detected:
            if k == key and det and det.installed:
                return True
        return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("lang-"):
            self._current = bid[5:]
            self._show_popular = True
            self._show_packages(self._current)
            self._refresh_sidebar()
        elif hasattr(event.button, "pkg_name"):
            self._show_package_detail(event.button.pkg_name)
        elif hasattr(event.button, "installed_name"):
            self._show_installed_detail(event.button.installed_name, event.button.installed_version)
        elif hasattr(event.button, "uninstall_name"):
            self._do_uninstall(event.button.uninstall_name)
        elif hasattr(event.button, "detail_install"):
            self._do_install(event.button.detail_install)
        elif hasattr(event.button, "back_nav"):
            self._show_packages(self._current)
        elif hasattr(event.button, "create_proj"):
            self._create_from_template()
        elif hasattr(event.button, "template_key"):
            self._select_template(event.button.template_key)
        elif hasattr(event.button, "history_query"):
            self.query_one("#search-input").value = event.button.history_query
            self._do_search(event.button.history_query)

    def _refresh_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        for btn in sidebar.query(".lang-btn"):
            if btn.id == f"lang-{self._current}":
                btn.classes = "lang-btn lang-btn-active"
            else:
                btn.classes = "lang-btn"

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.strip()
        if len(q) > 1:
            self._show_popular = False
            self._do_search(q)
        elif len(q) == 0:
            self._show_search_history()
        else:
            self._show_popular = True
            self._show_packages(self._current)

    def _animate_stagger(self, container, start_delay: float = 0.1, gap: float = 0.03) -> None:
        children = list(container.children)
        for i, w in enumerate(children):
            w.styles.opacity = 0.0
            delay = start_delay + i * gap
            self.set_timer(delay, lambda w=w: w.styles.animate("opacity", 1.0, duration=0.35))

    def action_refresh(self) -> None:
        self._show_packages(self._current)

    def _show_search_history(self) -> None:
        if not self._search_history:
            self._show_popular = True
            self._show_packages(self._current)
            return
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        status.update("📜 История поиска:")
        container.mount(Static("[bold #00d4ff]Недавние запросы:[/]", classes="section-title"))
        for q in self._search_history:
            btn = Button(f"  {q}", classes="history-btn")
            btn.history_query = q
            container.mount(btn)
        container.mount(Static("", classes="section-title"))
        back_btn = Button("↩ Назад к популярным", classes="btn-secondary")
        back_btn.back_nav = True
        container.mount(back_btn)
        self._animate_stagger(container)

    def _show_packages(self, key: str) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        data = self._langs.get(key)
        if not data:
            return
        name = data.get("name", key)
        icon = data.get("icon", " ")
        pm = get_package_manager(key) or "—"
        pm_ok = check_manager(key)
        installed_any = self._is_installed(key)
        pm_color = "#00e676" if pm_ok else "#ff5252"
        pm_icon = "✓" if pm_ok else "✗"

        container.mount(Static(
            Text.from_markup(f"[bold #00d4ff]{icon} {name}[/]  [#005577]менеджер: [{pm_color}]{pm_icon} {pm}[/][/]"),
            classes="section-title",
        ))
        if not pm_ok:
            container.mount(Static(
                Text.from_markup(f"[#ffb347]⚠ {pm} не найден в PATH. Некоторые функции недоступны.[/]"),
                classes="pm-warn",
            ))

        installed_pkgs = list_installed_packages(key) if installed_any else []

        if self._show_popular:
            pkgs = get_popular(key)
            if pkgs:
                container.mount(Static("[bold #005577]Популярные пакеты:[/]", classes="section-title"))
                for p in pkgs:
                    pn = p.get("name", "")
                    pd = p.get("desc", "")
                    btn = Button(
                        f"[#a8c8e8]{pn}[/]  [#005577]{pd}[/]    [#00d4ff]→[/]",
                        classes="pkg-card",
                    )
                    btn.pkg_name = pn
                    container.mount(btn)

            if installed_pkgs:
                container.mount(Static("[bold #005577]Установленные:[/]", classes="section-title"))
                for p in installed_pkgs[:15]:
                    pn = p.get("name", "")
                    pv = p.get("version", "")
                    btn = Button(
                        f"[#a8c8e8]{pn}[/] [#005577]{pv}[/]    [#ffb347]✕[/]",
                        classes="installed-card",
                    )
                    btn.installed_name = pn
                    btn.installed_version = pv
                    container.mount(btn)

        cnt = f" | {len(installed_pkgs)} пакетов" if installed_pkgs else ""
        status.update(f"📦 {name} | {pm_icon} {pm}{cnt}")
        self._animate_stagger(container)

    def _show_package_detail(self, pkg_name: str) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        data = self._langs.get(self._current)
        lang_name = data.get("name", self._current) if data else self._current

        container.mount(Static(
            Text.from_markup(f"[bold #00d4ff]📦 {pkg_name}[/]"),
            classes="detail-name",
        ))
        container.mount(Static(
            Text.from_markup(f"[#005577]Язык:[/] [#a8c8e8]{lang_name}[/]"),
            classes="detail-label",
        ))

        pkgs = get_popular(self._current)
        desc = ""
        for p in pkgs:
            if p.get("name") == pkg_name:
                desc = p.get("desc", "")
                break

        if desc:
            container.mount(Static(
                Text.from_markup(f"[#005577]Описание:[/] [#a8c8e8]{desc}[/]"),
                classes="detail-desc",
            ))

        container.mount(Static("", classes="section-title"))

        install_btn = Button(f"⬇ Установить {pkg_name}", classes="btn-primary")
        install_btn.detail_install = pkg_name
        container.mount(install_btn)
        back_btn = Button("↩ Назад", classes="btn-secondary")
        back_btn.back_nav = True
        container.mount(back_btn)

        status.update(f"📦 {pkg_name} — подтвердите установку")
        self._animate_stagger(container)

    def _show_installed_detail(self, pkg_name: str, pkg_version: str) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()

        container.mount(Static(
            Text.from_markup(f"[bold #ffb347]📦 {pkg_name}[/] [#005577]{pkg_version}[/]"),
            classes="detail-name",
        ))
        container.mount(Static(
            Text.from_markup(f"[#005577]Язык:[/] [#a8c8e8]{self._langs.get(self._current, {}).get('name', self._current)}[/]"),
            classes="detail-label",
        ))
        container.mount(Static("", classes="section-title"))
        uninstall_btn = Button(f"✕ Удалить {pkg_name}", classes="btn-danger")
        uninstall_btn.uninstall_name = pkg_name
        container.mount(uninstall_btn)
        back_btn = Button("↩ Назад", classes="btn-secondary")
        back_btn.back_nav = True
        container.mount(back_btn)
        status.update(f"📦 {pkg_name} — управление")
        self._animate_stagger(container)

    def _do_search(self, query: str) -> None:
        if query not in self._search_history:
            self._search_history.insert(0, query)
            self._search_history = self._search_history[:5]

        status = self.query_one("#status-bar")
        container = self.query_one("#pkg-container")
        container.remove_children()
        container.mount(Static(f"[bold #00d4ff]🔍 Поиск: {query}[/]", classes="section-title"))
        status.update(f"🔍 Поиск: {query}...")

        def run():
            results = search_packages(self._current, query)
            self.call_from_thread(self._display_results, results, query)

        threading.Thread(target=run, daemon=True).start()

    def _display_results(self, results: list[dict], query: str) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        container.mount(Static(f"[bold #00d4ff]🔍 Результаты поиска: {query}[/]", classes="section-title"))
        if results:
            status.update(f"🔍 Найдено: {len(results)} пакетов")
            for p in results:
                pn = p.get("name", "")
                pv = p.get("version", "")
                pd = p.get("description", "")
                label = f"[#a8c8e8]{pn}[/]  [#005577]{pv}[/]"
                if pd:
                    label += f"  [#003d5c]{pd[:40]}[/]"
                label += f"    [#00d4ff]→[/]"
                btn = Button(label, classes="pkg-card")
                btn.pkg_name = pn
                container.mount(btn)
        else:
            status.update(f"«{query}» — ничего не найдено")
            container.mount(Static(f"[bold #ffb347]«{query}» — ничего не найдено в реестре[/]", classes="section-title"))
            pkgs = get_popular(self._current)
            filtered = [
                p for p in pkgs
                if query.lower() in p.get("name", "").lower()
                or query.lower() in p.get("desc", "").lower()
            ]
            if filtered:
                container.mount(Static("[bold #005577]Похожие популярные пакеты:[/]", classes="section-title"))
                for p in filtered:
                    pn = p.get("name", "")
                    pd = p.get("desc", "")
                    btn = Button(
                        f"[#a8c8e8]{pn}[/]  [#005577]{pd}[/]    [#00d4ff]→[/]",
                        classes="pkg-card",
                    )
                    btn.pkg_name = pn
                    container.mount(btn)
        self._animate_stagger(container, 0.05, 0.02)

    def _do_install(self, pkg_name: str) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        container.mount(Static(
            Text.from_markup(f"[bold #00d4ff]⬇ Устанавливаю {pkg_name}...[/]"),
            classes="detail-name",
        ))
        status.update(f"⬇ Установка {pkg_name}...")

        def run():
            proc = install_package(self._current, pkg_name)
            if proc:
                for line in iter(proc.stdout.readline, ""):
                    self.call_from_thread(container.mount, Static(f"  [#005577]{line.rstrip()[:80]}[/]"))
                proc.wait()
                self.call_from_thread(status.update, f"✅ {pkg_name} установлен!")
                self.call_from_thread(container.mount, Static(
                    Text.from_markup(f"[bold #00e676]✅ {pkg_name} успешно установлен![/]"),
                ))
                back_btn = Button("↩ Назад к пакетам", classes="btn-secondary")
                back_btn.back_nav = True
                self.call_from_thread(container.mount, back_btn)
            else:
                self.call_from_thread(status.update, f"❌ Не удалось установить {pkg_name}")
                self.call_from_thread(container.mount, Static(
                    Text.from_markup(f"[#ff5252]❌ Не удалось установить {pkg_name}[/]"),
                ))
                back_btn = Button("↩ Назад", classes="btn-secondary")
                back_btn.back_nav = True
                self.call_from_thread(container.mount, back_btn)

        threading.Thread(target=run, daemon=True).start()

    def _do_uninstall(self, pkg_name: str) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        container.mount(Static(
            Text.from_markup(f"[bold #ffb347]✕ Удаляю {pkg_name}...[/]"),
            classes="detail-name",
        ))
        status.update(f"✕ Удаление {pkg_name}...")

        def run():
            proc = uninstall_package(self._current, pkg_name)
            if proc:
                for line in iter(proc.stdout.readline, ""):
                    self.call_from_thread(container.mount, Static(f"  [#005577]{line.rstrip()[:80]}[/]"))
                proc.wait()
                self.call_from_thread(status.update, f"✅ {pkg_name} удалён!")
                self.call_from_thread(container.mount, Static(
                    Text.from_markup(f"[bold #00e676]✅ {pkg_name} удалён![/]"),
                ))
                back_btn = Button("↩ Назад к пакетам", classes="btn-secondary")
                back_btn.back_nav = True
                self.call_from_thread(container.mount, back_btn)
            else:
                self.call_from_thread(status.update, f"❌ Не удалось удалить {pkg_name}")
                self.call_from_thread(container.mount, Static(
                    Text.from_markup(f"[#ff5252]❌ Не удалось удалить {pkg_name}[/]"),
                ))
                back_btn = Button("↩ Назад", classes="btn-secondary")
                back_btn.back_nav = True
                self.call_from_thread(container.mount, back_btn)

        threading.Thread(target=run, daemon=True).start()

    def _show_templates(self) -> None:
        container = self.query_one("#pkg-container")
        status = self.query_one("#status-bar")
        container.remove_children()
        status.update("📁 Шаблоны проектов")
        container.mount(Static("[bold #00d4ff]📁 Создать проект из шаблона[/]", classes="section-title"))
        cats = get_template_categories()
        for cat, tmpls in cats.items():
            for t in tmpls:
                btn = Button(f"  {t['name']}  [{t['language']}]", classes="tmpl-btn")
                btn.template_key = t['key']
                container.mount(btn)
        self._tmpl_name_input = Input(placeholder="Имя проекта (по умолч. my-project)")
        container.mount(self._tmpl_name_input)
        create_btn = Button("📁 Создать проект", classes="btn-primary")
        create_btn.create_proj = True
        container.mount(create_btn)
        self._tmpl_output = Static("")
        container.mount(self._tmpl_output)
        back_btn = Button("↩ Назад", classes="btn-secondary")
        back_btn.back_nav = True
        container.mount(back_btn)
        self._animate_stagger(container)

    def _select_template(self, tmpl_key: str) -> None:
        self._selected_template = tmpl_key
        status = self.query_one("#status-bar")
        status.update(f"📁 Шаблон выбран: {tmpl_key}")

    def _create_from_template(self) -> None:
        if not self._selected_template:
            status = self.query_one("#status-bar")
            status.update("⚠ Сначала выберите шаблон")
            return
        project_name = (self._tmpl_name_input.value or "my-project").strip() or "my-project" if self._tmpl_name_input else "my-project"
        status = self.query_one("#status-bar")
        try:
            files = create_project(self._selected_template, project_name, str(Path.cwd()))
            status.update(f"✅ Проект '{project_name}' создан!")
            if self._tmpl_output:
                self._tmpl_output.update(Text.from_markup(f"\n[#00e676]✅ Проект '{project_name}' создан![/]\n"))
                for f in files:
                    self._tmpl_output.update(Text.from_markup(f"  [#a8c8e8]{f}[/]\n"))
        except Exception as e:
            status.update(f"❌ Ошибка: {e}")
            if self._tmpl_output:
                self._tmpl_output.update(Text.from_markup(f"\n[#ff5252]Ошибка: {e}[/]"))

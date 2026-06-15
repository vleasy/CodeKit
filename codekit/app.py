import os
import sys
from textual.app import App
from screens.main_menu import MainMenu


CSS_BASE = """
Screen {
    background: #0a1628;
}
Static, Button, Label, Input, ListView, RichLog, Tree, DirectoryTree {
    color: #a8c8e8;
}
Button {
    background: #005577;
    color: #ffffff;
    min-width: 20;
    height: 3;
    border: none;
    border-bottom: solid #002244;
    padding: 0 1;
    transition: background 0.15s, border-bottom 0.15s;
}
Button:hover {
    background: #0d1f3c;
    border-bottom: solid #00aadd;
}
Button:focus {
    background: #1a3a5c;
    border-bottom: solid #00d4ff;
}
.header-box {
    height: 3;
    content-align: center middle;
    background: #0d1f3c;
    border: none;
    border-bottom: solid #00d4ff;
    margin-bottom: 1;
    padding: 1 0;
    text-style: bold;
}
.footer-box {
    height: 3;
    content-align: center middle;
    color: #003d5c;
    margin-top: 1;
}
Input {
    border: solid #003366;
    padding: 0 1;
    transition: border 0.15s;
}
Input:focus {
    border: solid #00d4ff;
}
Tree {
    border: solid #003366;
    padding: 0 1;
}
RichLog {
    border: solid #003366;
    padding: 0 1;
    transition: border 0.15s;
}
"""


class CodeKit(App):
    TITLE = "CodeKit"
    CSS = CSS_BASE

    def on_mount(self) -> None:
        if sys.platform == "win32":
            os.system("title CodeKit — Package Manager")
        self.push_screen(MainMenu())


def main():
    CodeKit().run()


if __name__ == "__main__":
    main()

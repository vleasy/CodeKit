import os
import tomllib
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
I18N_DIR = APP_DIR / "i18n"
CONFIG_FILE = APP_DIR / "user_config.toml"

DEFAULT_CONFIG = {
    "language": "ru",
    "install_path": str(Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "CodeKit"),
}


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            return {**DEFAULT_CONFIG, **tomllib.load(f)}
    return dict(DEFAULT_CONFIG)


def save_config(config: dict[str, Any]) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        for k, v in config.items():
            f.write(f'{k} = "{v}"\n')


def load_languages_data() -> dict[str, Any]:
    path = DATA_DIR / "languages.toml"
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def load_templates_data() -> dict[str, Any]:
    path = DATA_DIR / "templates.toml"
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def load_popular_packages() -> dict[str, Any]:
    path = DATA_DIR / "popular_packages.toml"
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def load_i18n(lang: str) -> dict[str, Any]:
    candidates = [
        I18N_DIR / f"{lang}_simple.toml",
        I18N_DIR / f"{lang}.toml",
        I18N_DIR / "ru_simple.toml",
    ]
    for path in candidates:
        if path.exists():
            with open(path, "rb") as f:
                return tomllib.load(f)
    return {}

import os
from pathlib import Path
from typing import Optional

from utils.config import load_languages_data
from utils.installer import (
    check_winget, check_choco, check_scoop, check_brew, check_apt, check_dnf, check_pacman,
    install_via_winget, install_via_choco, install_via_scoop,
    install_via_brew, install_via_apt, install_via_dnf, install_via_pacman,
    open_download_page, check_command_exists,
)
from backends.system_detector import detect_language, get_os_installer


LANG_DATA = load_languages_data()


def get_languages() -> dict:
    return dict(LANG_DATA)


def get_language(lang_key: str) -> Optional[dict]:
    return LANG_DATA.get(lang_key)


def detect_installed_languages() -> list[tuple[str, dict]]:
    results = []
    for key, data in LANG_DATA.items():
        check = data.get("check_command", "")
        if check:
            det = detect_language(key, check)
            results.append((key, data, det))
        else:
            results.append((key, data, None))
    return results


def get_best_installer() -> str:
    if check_winget():
        return "winget"
    if check_choco():
        return "choco"
    if check_scoop():
        return "scoop"
    if check_brew():
        return "brew"
    if check_apt():
        return "apt"
    if check_dnf():
        return "dnf"
    if check_pacman():
        return "pacman"
    return "manual"


def install_language(lang_key: str, installer: str = "auto") -> Optional[object]:
    data = LANG_DATA.get(lang_key)
    if not data:
        return None
    if installer == "auto":
        installer = get_best_installer()
    pid = data.get(f"{installer}_id")
    if not pid:
        return None
    fn_map = {
        "winget": install_via_winget,
        "choco": install_via_choco,
        "scoop": install_via_scoop,
        "brew": install_via_brew,
        "apt": install_via_apt,
        "dnf": install_via_dnf,
        "pacman": install_via_pacman,
    }
    fn = fn_map.get(installer)
    if fn:
        return fn(pid)
    return None


def open_manual_download(lang_key: str) -> Optional[str]:
    data = LANG_DATA.get(lang_key)
    if data and data.get("download_url"):
        open_download_page(data["download_url"])
        return data["download_url"]
    return None


def get_manual_info(lang_key: str) -> dict:
    data = LANG_DATA.get(lang_key, {})
    return {
        "url": data.get("download_url", ""),
        "website": data.get("website", ""),
        "name": data.get("name", lang_key),
    }

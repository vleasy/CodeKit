import os
from pathlib import Path
from typing import Optional

from utils.config import load_languages_data
from utils.installer import (
    check_winget, check_choco, check_scoop,
    install_via_winget, install_via_choco, install_via_scoop,
    open_download_page, check_command_exists,
)
from backends.system_detector import detect_language


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
    return "manual"


def install_language(lang_key: str, installer: str = "auto") -> Optional[object]:
    data = LANG_DATA.get(lang_key)
    if not data:
        return None
    if installer == "auto":
        installer = get_best_installer()
    if installer == "winget":
        pid = data.get("winget_id")
        if pid:
            return install_via_winget(pid)
    elif installer == "choco":
        pid = data.get("choco_id")
        if pid:
            return install_via_choco(pid)
    elif installer == "scoop":
        pid = data.get("scoop_id")
        if pid:
            return install_via_scoop(pid)
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

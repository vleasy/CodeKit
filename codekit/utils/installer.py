import subprocess
import shutil
import webbrowser
from pathlib import Path


def check_winget() -> bool:
    return shutil.which("winget") is not None


def check_choco() -> bool:
    return shutil.which("choco") is not None


def check_scoop() -> bool:
    return shutil.which("scoop") is not None


def install_via_winget(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["winget", "install", "--id", package_id, "--accept-source-agreements", "--accept-package-agreements"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def install_via_choco(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["choco", "install", package_id, "-y"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def install_via_scoop(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["scoop", "install", package_id],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def open_download_page(url: str) -> None:
    webbrowser.open(url)


def check_command_exists(cmd: str) -> bool:
    return shutil.which(cmd.split()[0]) is not None

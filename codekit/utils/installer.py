import subprocess
import shutil
import webbrowser


def check_winget() -> bool:
    return shutil.which("winget") is not None


def check_choco() -> bool:
    return shutil.which("choco") is not None


def check_scoop() -> bool:
    return shutil.which("scoop") is not None


def check_brew() -> bool:
    return shutil.which("brew") is not None


def check_apt() -> bool:
    return shutil.which("apt") is not None


def check_dnf() -> bool:
    return shutil.which("dnf") is not None


def check_pacman() -> bool:
    return shutil.which("pacman") is not None


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


def install_via_brew(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["brew", "install", package_id],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def install_via_apt(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["sudo", "apt", "install", "-y", package_id],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def install_via_dnf(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["sudo", "dnf", "install", "-y", package_id],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def install_via_pacman(package_id: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["sudo", "pacman", "-S", "--noconfirm", package_id],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def open_download_page(url: str) -> None:
    webbrowser.open(url)


def check_command_exists(cmd: str) -> bool:
    return shutil.which(cmd.split()[0]) is not None

import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LanguageDetection:
    name: str
    installed: bool = False
    version: Optional[str] = None
    path: Optional[str] = None


@dataclass
class SystemInfo:
    os: str = platform.system()
    os_version: str = platform.version()
    architecture: str = platform.machine()
    processor: str = platform.processor()
    hostname: str = platform.node()
    python_version: str = platform.python_version()
    has_winget: bool = False
    has_choco: bool = False
    has_scoop: bool = False


def detect_system() -> SystemInfo:
    info = SystemInfo()
    info.has_winget = shutil.which("winget") is not None
    info.has_choco = shutil.which("choco") is not None
    info.has_scoop = shutil.which("scoop") is not None
    return info


def detect_language(lang_key: str, check_cmd: str) -> LanguageDetection:
    detect = LanguageDetection(name=lang_key)
    cmd_parts = check_cmd.split()
    exe = cmd_parts[0]
    exe_path = shutil.which(exe)
    if exe_path:
        detect.installed = True
        detect.path = exe_path
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True, text=True, timeout=10,
            )
            output = result.stdout.strip() or result.stderr.strip()
            if output:
                detect.version = output.splitlines()[0].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
    return detect


def get_disk_info() -> dict[str, str]:
    import shutil as shu
    info = {}
    if platform.system() == "Windows":
        import ctypes
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if bitmask & (1 << i):
                drives.append(f"{chr(65 + i)}:\\")
        for drive in drives:
            try:
                total, used, free = shu.disk_usage(drive)
                info[drive] = {
                    "total": total // (1024**3),
                    "used": used // (1024**3),
                    "free": free // (1024**3),
                }
            except PermissionError:
                pass
    return info

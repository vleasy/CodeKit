import subprocess
import shutil
from typing import Optional


def get_current_version(lang_key: str) -> Optional[str]:
    commands = {
        "python": "python --version",
        "nodejs": "node --version",
        "java": "java -version 2>&1",
        "rust": "rustc --version",
    }
    cmd = commands.get(lang_key)
    if not cmd:
        return None
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output.splitlines()[0].strip() if output else None
    except Exception:
        return None


def switch_version(lang_key: str, version: str) -> Optional[subprocess.Popen]:
    if lang_key == "python" and shutil.which("py"):
        return subprocess.Popen(
            ["py", f"-{version[0]}.{version[2]}", "-m", "pip"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    return None

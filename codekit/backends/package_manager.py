import subprocess
import shutil
from typing import Optional

from utils.config import load_popular_packages


POPULAR = load_popular_packages()


def get_package_manager(lang_key: str) -> Optional[str]:
    managers = {
        "python": "pip",
        "nodejs": "npm",
        "java": "mvn",
        "rust": "cargo",
        "cpp": "vcpkg",
    }
    return managers.get(lang_key)


def check_manager(lang_key: str) -> bool:
    mgr = get_package_manager(lang_key)
    if mgr:
        return shutil.which(mgr) is not None
    return False


def get_popular(lang_key: str) -> list[dict]:
    data = POPULAR.get(lang_key, {})
    return data.get("popular", [])


def search_packages(lang_key: str, query: str) -> list[dict]:
    mgr = get_package_manager(lang_key)
    if mgr == "pip":
        return _search_pip(query)
    elif mgr == "npm":
        return _search_npm(query)
    elif mgr == "cargo":
        return _search_cargo(query)
    return []


def _search_pip(query: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["pip", "search", query],
            capture_output=True, text=True, timeout=30,
        )
        lines = result.stdout.strip().splitlines()[:20]
        packages = []
        for line in lines:
            if "(" in line and ")" in line:
                name = line.split("(")[0].strip()
                version = line.split("(")[1].split(")")[0].strip()
                packages.append({"name": name, "version": version, "manager": "pip"})
        return packages
    except Exception:
        return []


def _search_npm(query: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["npm", "search", query, "--json"],
            capture_output=True, text=True, timeout=30,
        )
        import json
        data = json.loads(result.stdout)
        return [
            {"name": p.get("name", ""), "version": p.get("version", ""), "description": p.get("description", ""), "manager": "npm"}
            for p in data[:20]
        ]
    except Exception:
        return []


def _search_cargo(query: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["cargo", "search", query],
            capture_output=True, text=True, timeout=30,
        )
        lines = result.stdout.strip().splitlines()[:20]
        packages = []
        for line in lines:
            if "=" in line:
                parts = line.split("=")
                name = parts[0].strip()
                version = parts[1].strip().strip('"')
                packages.append({"name": name, "version": version, "manager": "cargo"})
        return packages
    except Exception:
        return []


def install_package(lang_key: str, package_name: str) -> Optional[subprocess.Popen]:
    mgr = get_package_manager(lang_key)
    if mgr == "pip":
        return subprocess.Popen(
            ["pip", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    elif mgr == "npm":
        return subprocess.Popen(
            ["npm", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    elif mgr == "cargo":
        return subprocess.Popen(
            ["cargo", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    return None


def uninstall_package(lang_key: str, package_name: str) -> Optional[subprocess.Popen]:
    mgr = get_package_manager(lang_key)
    if mgr == "pip":
        return subprocess.Popen(
            ["pip", "uninstall", package_name, "-y"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    elif mgr == "npm":
        return subprocess.Popen(
            ["npm", "uninstall", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    elif mgr == "cargo":
        return subprocess.Popen(
            ["cargo", "uninstall", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    return None


def list_installed_packages(lang_key: str) -> list[dict]:
    mgr = get_package_manager(lang_key)
    if mgr == "pip":
        return _list_pip()
    elif mgr == "npm":
        return _list_npm()
    elif mgr == "cargo":
        return _list_cargo()
    return []


def _list_pip() -> list[dict]:
    try:
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True, text=True, timeout=15,
        )
        import json
        return json.loads(result.stdout)
    except Exception:
        return []


def _list_npm() -> list[dict]:
    try:
        result = subprocess.run(
            ["npm", "list", "--json", "--depth=0"],
            capture_output=True, text=True, timeout=15,
        )
        import json
        data = json.loads(result.stdout)
        deps = data.get("dependencies", {})
        return [{"name": k, "version": v.get("version", ""), "manager": "npm"} for k, v in deps.items()]
    except Exception:
        return []


def _list_cargo() -> list[dict]:
    try:
        result = subprocess.run(
            ["cargo", "install", "--list"],
            capture_output=True, text=True, timeout=15,
        )
        lines = result.stdout.strip().splitlines()
        pkgs = []
        for line in lines:
            if " " in line and ":" not in line:
                parts = line.split(" ")
                name = parts[0].strip()
                version = parts[-1].strip("v") if len(parts) > 1 else ""
                pkgs.append({"name": name, "version": version, "manager": "cargo"})
        return pkgs
    except Exception:
        return []

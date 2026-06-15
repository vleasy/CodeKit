import subprocess
import shutil
import time
from typing import Optional

from utils.config import load_popular_packages


POPULAR = load_popular_packages()

_cache: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL_SEARCH = 30
_CACHE_TTL_LIST = 60


def _cache_get(key: str, ttl: int) -> Optional[list[dict]]:
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry[0]) < ttl:
        return entry[1]
    return None


def _cache_set(key: str, data: list[dict]) -> None:
    _cache[key] = (time.monotonic(), data)
    if len(_cache) > 100:
        stale = [k for k, (ts, _) in _cache.items() if (time.monotonic() - ts) > 120]
        for k in stale:
            del _cache[k]


def invalidate_cache() -> None:
    _cache.clear()


def check_pipenv() -> bool:
    return shutil.which("pipenv") is not None


def check_poetry() -> bool:
    return shutil.which("poetry") is not None


def get_available_python_managers() -> list[str]:
    mgrs = ["pip"]
    if check_pipenv():
        mgrs.append("pipenv")
    if check_poetry():
        mgrs.append("poetry")
    return mgrs


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
    cache_key = f"search:{lang_key}:{query}"
    cached = _cache_get(cache_key, _CACHE_TTL_SEARCH)
    if cached is not None:
        return cached
    mgr = get_package_manager(lang_key)
    results = []
    if mgr == "pip":
        results = _search_pip(query)
    elif mgr == "npm":
        results = _search_npm(query)
    elif mgr == "cargo":
        results = _search_cargo(query)
    if results:
        _cache_set(cache_key, results)
    return results


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


def install_package(lang_key: str, package_name: str, manager: str = "") -> Optional[subprocess.Popen]:
    mgr = manager or get_package_manager(lang_key)
    if mgr == "pip":
        return subprocess.Popen(
            ["pip", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "pipenv":
        return subprocess.Popen(
            ["pipenv", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "poetry":
        return subprocess.Popen(
            ["poetry", "add", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "npm":
        return subprocess.Popen(
            ["npm", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "cargo":
        return subprocess.Popen(
            ["cargo", "install", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    return None


def uninstall_package(lang_key: str, package_name: str, manager: str = "") -> Optional[subprocess.Popen]:
    mgr = manager or get_package_manager(lang_key)
    if mgr == "pip":
        return subprocess.Popen(
            ["pip", "uninstall", package_name, "-y"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "pipenv":
        return subprocess.Popen(
            ["pipenv", "uninstall", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "poetry":
        return subprocess.Popen(
            ["poetry", "remove", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "npm":
        return subprocess.Popen(
            ["npm", "uninstall", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    if mgr == "cargo":
        return subprocess.Popen(
            ["cargo", "uninstall", package_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    return None


def list_installed_packages(lang_key: str) -> list[dict]:
    cache_key = f"list:{lang_key}"
    cached = _cache_get(cache_key, _CACHE_TTL_LIST)
    if cached is not None:
        return cached
    mgr = get_package_manager(lang_key)
    results = []
    if mgr == "pip":
        results = _list_pip()
    elif mgr == "npm":
        results = _list_npm()
    elif mgr == "cargo":
        results = _list_cargo()
    if results:
        _cache_set(cache_key, results)
    return results


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

import os
from dataclasses import dataclass

_SEP = os.pathsep


@dataclass
class PathEntry:
    value: str
    source: str = "user"


def get_path_entries() -> list[PathEntry]:
    raw = os.environ.get("PATH", "")
    return [PathEntry(p) for p in raw.split(_SEP) if p.strip()]


def get_env_vars() -> dict[str, str]:
    return dict(sorted(os.environ.items()))


def add_to_path(new_path: str, scope: str = "user") -> None:
    current = os.environ.get("PATH", "")
    if new_path not in current:
        os.environ["PATH"] = new_path + _SEP + current

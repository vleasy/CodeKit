import os
from pathlib import Path
from typing import Any

from utils.config import load_templates_data


TEMPLATES: dict[str, Any] = load_templates_data()


def get_template_categories() -> dict[str, list]:
    cats = {}
    for cat_key, lang_dict in TEMPLATES.items():
        if isinstance(lang_dict, dict):
            for lang_key, tmpl_data in lang_dict.items():
                if isinstance(tmpl_data, dict) and "name" in tmpl_data:
                    cats.setdefault(cat_key, []).append({
                        "key": f"{cat_key}.{lang_key}",
                        "name": tmpl_data.get("name", lang_key),
                        "language": tmpl_data.get("language", ""),
                    })
    return cats


def get_template(template_key: str) -> dict:
    parts = template_key.split(".")
    if len(parts) == 2:
        cat, lang = parts
        outer = TEMPLATES.get(cat, {})
        if isinstance(outer, dict):
            return outer.get(lang, {})
    return {}


def create_project(template_key: str, project_name: str, dest_path: str) -> list[Path]:
    template = get_template(template_key)
    if not template:
        return []
    contents = template.get("contents", {})
    created = []
    base = Path(dest_path) / project_name
    os.makedirs(base, exist_ok=True)
    for _, file_info in contents.items():
        filepath = file_info.get("path", "")
        content = file_info.get("content", "")
        content = content.replace("{{project_name}}", project_name)
        full_path = base / filepath
        os.makedirs(full_path.parent, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(full_path)
    return created

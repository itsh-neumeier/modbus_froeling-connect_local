"""Tests for translation parity across English and German language files."""

from __future__ import annotations

import json
from pathlib import Path

TRANSLATION_DIR = Path("custom_components/froeling_connect_local/translations")


def _flatten_keys(obj: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in obj.items():
        current = f"{prefix}.{key}" if prefix else key
        keys.add(current)
        if isinstance(value, dict):
            keys |= _flatten_keys(value, current)
    return keys


def test_en_de_translation_key_parity() -> None:
    en = json.loads((TRANSLATION_DIR / "en.json").read_text(encoding="utf-8"))
    de = json.loads((TRANSLATION_DIR / "de.json").read_text(encoding="utf-8"))

    assert _flatten_keys(en) == _flatten_keys(de)
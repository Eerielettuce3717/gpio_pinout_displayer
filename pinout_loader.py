from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PINOUTS_JSON = Path(__file__).resolve().parent / "pinouts.json"


@lru_cache(maxsize=1)
def _load_all() -> dict[str, Any]:
    if not PINOUTS_JSON.is_file():
        raise FileNotFoundError(f"missing: {PINOUTS_JSON}")
    data = json.loads(PINOUTS_JSON.read_text(encoding="utf-8"))
    return data.get("boards", {})


def get_pinout_ascii(class_id: str | None, detailed: bool = False) -> list[str] | None:
    if not class_id:
        return None
    board = _load_all().get(class_id)
    if not board:
        return None
    key = "ascii_detailed" if detailed else "ascii"
    lines: list[str] = board[key]
    if lines and lines[0] != board["model_name"]:
        lines = [board["model_name"], *lines]
    elif lines and len(lines) > 1 and lines[1] == board["model_name"]:
        lines = [lines[0], *lines[2:]]
    return lines


def get_model_name(class_id: str | None) -> str | None:
    if not class_id:
        return None
    board = _load_all().get(class_id)
    return board["model_name"] if board else None

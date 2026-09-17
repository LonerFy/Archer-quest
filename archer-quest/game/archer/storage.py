"""Sauvegarde : localStorage dans le navigateur, fichier JSON sur ordinateur."""
import json
import sys
from pathlib import Path

from .config import SAVE_KEY

WEB = sys.platform == "emscripten"
LOCAL_FILE = Path.home() / ".archer-quest.json"


def load_save() -> dict:
    try:
        if WEB:
            import platform  # module injecté par pygbag
            raw = platform.window.localStorage.getItem(SAVE_KEY)
            raw = None if raw is None or str(raw) in ("null", "undefined") else str(raw)
        else:
            raw = LOCAL_FILE.read_text(encoding="utf-8") if LOCAL_FILE.exists() else None
        data = json.loads(raw) if raw else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_save(data: dict) -> None:
    try:
        raw = json.dumps(data)
        if WEB:
            import platform
            platform.window.localStorage.setItem(SAVE_KEY, raw)
        else:
            LOCAL_FILE.write_text(raw, encoding="utf-8")
    except Exception as exc:
        print("Sauvegarde impossible :", exc)

"""
NoteX v1.6 - favorites.py
Favoriler modülü: not ekleme, çıkarma, listeleme, arama
Favoriler dosya yolu: /sdcard/Android/notee/favorites.json
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR       = Path("/sdcard/Android/notee")
FAVORITES_FILE = BASE_DIR / "favorites.json"


def _load() -> list:
    """
    Favorileri yükle.
    Döndürür: [{"name": str, "added_at": str}, ...]
    """
    if not FAVORITES_FILE.exists():
        return []
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(favs: list):
    """Favorileri kaydet."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)


def get_all() -> list:
    """Tüm favorileri döndür."""
    return _load()


def is_favorite(note_name: str) -> bool:
    """Belirtilen not favorilerde mi?"""
    return any(f["name"] == note_name for f in _load())


def add_favorite(note_name: str) -> dict:
    """
    Notu favorilere ekle.
    Döndürür: {"ok": bool, "msg": str}
    """
    if not note_name or not note_name.strip():
        return {"ok": False, "msg": "Not adı boş olamaz."}
    name = note_name.strip()
    favs = _load()
    if any(f["name"] == name for f in favs):
        return {"ok": False, "msg": f"'{name}' zaten favorilerde."}
    favs.append({
        "name"    : name,
        "added_at": datetime.now().isoformat(timespec="seconds"),
    })
    # Alfabetik sırala
    favs.sort(key=lambda x: x["name"].lower())
    _save(favs)
    return {"ok": True, "msg": f"'{name}' favorilere eklendi."}


def remove_favorite(note_name: str) -> dict:
    """
    Notu favorilerden çıkart.
    Döndürür: {"ok": bool, "msg": str}
    """
    name    = note_name.strip()
    favs    = _load()
    new_favs = [f for f in favs if f["name"] != name]
    if len(new_favs) == len(favs):
        return {"ok": False, "msg": f"'{name}' favorilerde bulunamadı."}
    _save(new_favs)
    return {"ok": True, "msg": f"'{name}' favorilerden çıkartıldı."}


def search_favorites(query: str) -> list:
    """
    Favorilerde ada göre ara (büyük/küçük harf duyarsız).
    Döndürür: [{"name": str, "added_at": str}, ...]
    """
    q = query.strip().lower()
    return [f for f in _load() if q in f["name"].lower()]


def count() -> int:
    """Favori sayısını döndür."""
    return len(_load())

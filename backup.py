"""
NoteX v1.4 - backup.py
Manuel yedekleme sistemi.
Yedekler: /sdcard/Android/notee/.notes/<tarih_damgası>/
"""

import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path("/sdcard/Android/notee")
NOTE_DIR   = BASE_DIR / "note"
BACKUP_DIR = BASE_DIR / ".notes"   # Tüm yedekler bu klasörün altında


def ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _stamp() -> str:
    """Yedek klasörü için zaman damgası üret: 20240315_142035"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_notes() -> dict:
    """
    note/ klasöründeki tüm .txt dosyalarını
    .notes/<damga>/ altına kopyalar.

    Döndürür:
        {
          "ok"      : bool,
          "msg"     : str,
          "path"    : str,   # Yedek klasörü yolu
          "count"   : int,   # Yedeklenen dosya sayısı
          "files"   : list,  # Yedeklenen dosya isimleri
        }
    """
    ensure_backup_dir()

    # Yedeklenecek dosyaları bul
    note_files = sorted(NOTE_DIR.glob("*.txt")) if NOTE_DIR.exists() else []
    if not note_files:
        return {"ok": False, "msg": "Yedeklenecek not bulunamadı.",
                "path": "", "count": 0, "files": []}

    stamp      = _stamp()
    target_dir = BACKUP_DIR / stamp
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"ok": False, "msg": f"Yedek klasörü oluşturulamadı: {e}",
                "path": str(target_dir), "count": 0, "files": []}

    backed_up = []
    errors    = []
    for src in note_files:
        dst = target_dir / src.name
        try:
            shutil.copy2(str(src), str(dst))
            backed_up.append(src.name)
        except Exception as e:
            errors.append(f"{src.name}: {e}")

    if errors:
        return {
            "ok"   : False,
            "msg"  : f"{len(backed_up)} not yedeklendi, {len(errors)} hata oluştu.",
            "path" : str(target_dir),
            "count": len(backed_up),
            "files": backed_up,
            "errors": errors,
        }

    return {
        "ok"   : True,
        "msg"  : f"{len(backed_up)} not başarıyla yedeklendi.",
        "path" : str(target_dir),
        "count": len(backed_up),
        "files": backed_up,
        "errors": [],
    }


def list_backups() -> list:
    """
    Mevcut tüm yedekleri listele.
    Döndürür: [{"name": str, "path": str, "count": int, "date": str}, ...]
    Tarih sırasına göre en yeniden eskiye sıralar.
    """
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        files = list(d.glob("*.txt"))
        # Klasör adından tarih parse et
        name = d.name
        try:
            dt = datetime.strptime(name, "%Y%m%d_%H%M%S")
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            date_str = name

        backups.append({
            "name" : name,
            "path" : str(d),
            "count": len(files),
            "date" : date_str,
            "files": [f.name for f in files],
        })
    return backups


def restore_backup(backup_name: str) -> dict:
    """
    Belirtilen yedek klasöründeki dosyaları note/ klasörüne geri yükler.
    Aynı isimde dosya varsa üzerine yazar.

    Döndürür: {"ok": bool, "msg": str, "count": int, "errors": list}
    """
    src_dir = BACKUP_DIR / backup_name
    if not src_dir.exists() or not src_dir.is_dir():
        return {"ok": False, "msg": f"'{backup_name}' yedeği bulunamadı.",
                "count": 0, "errors": []}

    NOTE_DIR.mkdir(parents=True, exist_ok=True)
    files   = list(src_dir.glob("*.txt"))
    if not files:
        return {"ok": False, "msg": "Yedek klasörü boş.",
                "count": 0, "errors": []}

    restored = 0
    errors   = []
    for src in files:
        dst = NOTE_DIR / src.name
        try:
            shutil.copy2(str(src), str(dst))
            restored += 1
        except Exception as e:
            errors.append(f"{src.name}: {e}")

    if errors:
        return {"ok": False,
                "msg": f"{restored} not geri yüklendi, {len(errors)} hata.",
                "count": restored, "errors": errors}

    return {"ok": True,
            "msg": f"{restored} not başarıyla geri yüklendi.",
            "count": restored, "errors": []}

"""
NoteX v1.6 - main.py
"""

import json, hashlib, shutil
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path("/sdcard/Android/notee")
NOTE_DIR   = BASE_DIR / "note"
CFG_FILE   = BASE_DIR / "config.json"
SEC_DIR    = BASE_DIR / ".sec"
SEC_CFG    = BASE_DIR / ".sec_config"
BACKUP_DIR = BASE_DIR / ".notes"
ID_DIR     = BASE_DIR / "id"
ID_FILE    = ID_DIR   / "id.enc"
LIST_DIR   = BASE_DIR / "list"

COLOR_MAP = {
    "cyan":"cyan","green":"green","yellow":"yellow",
    "magenta":"magenta","blue":"blue","red":"red","white":"white",
}

BG_COLOR_MAP = {
    "default":"","dark":"on black","navy":"on navy_blue",
    "dark_green":"on dark_green","dark_red":"on dark_red","dark_purple":"on purple4",
}

FONT_SIZE_MAP  = {"small":0.85,"normal":1.0,"large":1.15}
FONT_STYLE_MAP = {"normal":"","bold":"bold","italic":"italic","bold_italic":"bold italic"}

DEFAULT_CONFIG = {
    "text_color"   : "cyan",
    "app_name"     : "NoteX",
    "version"      : "1.6",
    "author"       : "NoteX Project",
    "lang"         : "tr",
    "font_size"    : "normal",
    "font_style"   : "normal",
    "bg_color"     : "default",
    "share_service": False,
}

CHANGELOG = [
    {"version":"1.6","date":"2024","changes":[
        "4 dil desteği: TR, EN, AZ (Azerbaycanca), ZH (Çince)",
        "NSS v1.0.1: NoteX ID kara liste sistemi",
        "Favoriler özelliği (ekle, çıkart, listele, ara)",
    ]},
    {"version":"1.5","date":"2024","changes":[
        "Note Sharing Service v1.0.0 — LAN P2P not paylaşımı",
        "NoteX ID (şifreli + imzalı)",
        "Not düzenleme (append / replace)",
        "2 yeni şablon: Gelir-Gider, CV (10 şablon)",
    ]},
    {"version":"1.4.5","date":"2024","changes":[
        "Özelleştirme: yazı boyutu, tipi, arka plan",
        "Dışarıdan not düzenleme",
        "3 yeni şablon: Günlük, Rapor, Dilekçe",
        "Güncelleme notları ekranı",
    ]},
    {"version":"1.4","date":"2024","changes":[
        "Yedekleme sistemi","TR/EN dil desteği"]},
    {"version":"1.3","date":"2024","changes":[
        "Şablonlu not kaydetme düzeltmesi","Sıfırlama"]},
    {"version":"1.2","date":"2024","changes":["5 not şablonu","template.py"]},
    {"version":"1.1","date":"2024","changes":["Vault (şifreli klasör)"]},
    {"version":"1.0","date":"2024","changes":["İlk sürüm"]},
]

def ensure_dirs():       NOTE_DIR.mkdir(parents=True,exist_ok=True)
def ensure_sec_dir():    SEC_DIR.mkdir(parents=True,exist_ok=True)
def ensure_backup_dir(): BACKUP_DIR.mkdir(parents=True,exist_ok=True)
def ensure_id_dir():     ID_DIR.mkdir(parents=True,exist_ok=True)
def ensure_list_dir():   LIST_DIR.mkdir(parents=True,exist_ok=True)

def load_config() -> dict:
    ensure_dirs()
    if CFG_FILE.exists():
        try:
            with open(CFG_FILE,"r",encoding="utf-8") as f: cfg=json.load(f)
            for k,v in DEFAULT_CONFIG.items(): cfg.setdefault(k,v)
            return cfg
        except Exception: pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    ensure_dirs()
    with open(CFG_FILE,"w",encoding="utf-8") as f: json.dump(cfg,f,ensure_ascii=False,indent=2)

# ── Vault ─────────────────────────────────────────────────────────────────────
def _hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def load_sec_config() -> dict:
    if SEC_CFG.exists():
        try:
            with open(SEC_CFG,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return {"enabled":False,"password_hash":None}

def save_sec_config(s):
    with open(SEC_CFG,"w",encoding="utf-8") as f: json.dump(s,f,ensure_ascii=False,indent=2)

def is_vault_enabled():
    s=load_sec_config(); return s.get("enabled",False) and bool(s.get("password_hash"))

def activate_vault(pw):
    if is_vault_enabled(): return {"ok":False,"msg":"Şifreli klasör zaten aktif."}
    ensure_sec_dir()
    save_sec_config({"enabled":True,"password_hash":_hash_pw(pw),
                     "created_at":datetime.now().isoformat(timespec="seconds")})
    return {"ok":True,"msg":"Şifreli klasör servisi aktif edildi."}

def deactivate_vault(pw):
    r=verify_vault_password(pw)
    if not r["ok"]: return r
    s=load_sec_config(); s["enabled"]=False; s["password_hash"]=None; save_sec_config(s)
    return {"ok":True,"msg":"Şifreli klasör servisi devre dışı bırakıldı."}

def change_vault_password(old,new):
    r=verify_vault_password(old)
    if not r["ok"]: return r
    s=load_sec_config(); s["password_hash"]=_hash_pw(new); save_sec_config(s)
    return {"ok":True,"msg":"Şifre başarıyla değiştirildi."}

def verify_vault_password(pw):
    if not is_vault_enabled(): return {"ok":False,"msg":"Şifreli klasör servisi aktif değil."}
    s=load_sec_config()
    if _hash_pw(pw)==s.get("password_hash"): return {"ok":True,"msg":"Şifre doğrulandı."}
    return {"ok":False,"msg":"Hatalı şifre!"}

def _sec_path(name):
    safe=name.strip().replace("/","_").replace("\\","_")
    return SEC_DIR/(safe if safe.endswith(".txt") else safe+".txt")

def list_vault_notes():
    if not SEC_DIR.exists(): return []
    return [{"name":p.stem,"size":p.stat().st_size,
             "modified":datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
            for p in sorted(SEC_DIR.glob("*.txt"))]

def move_to_vault(name):
    src=_note_path(name)
    if not src.exists(): return {"ok":False,"msg":f"'{name}' bulunamadı."}
    ensure_sec_dir(); dst=_sec_path(name)
    if dst.exists(): return {"ok":False,"msg":f"Vault'ta '{name}' zaten var."}
    try: shutil.move(str(src),str(dst)); return {"ok":True,"msg":f"'{name}' vault'a taşındı."}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

def move_from_vault(name):
    src=_sec_path(name)
    if not src.exists(): return {"ok":False,"msg":f"Vault'ta '{name}' bulunamadı."}
    ensure_dirs(); dst=_note_path(name)
    if dst.exists(): return {"ok":False,"msg":f"'{name}' notlar klasöründe zaten var."}
    try: shutil.move(str(src),str(dst)); return {"ok":True,"msg":f"'{name}' vault'tan çıkarıldı."}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

def read_vault_note(name):
    p=_sec_path(name)
    if not p.exists(): return {"ok":False,"content":"","msg":f"'{name}' bulunamadı."}
    try: return {"ok":True,"content":p.read_text(encoding="utf-8"),"msg":""}
    except Exception as e: return {"ok":False,"content":"","msg":f"Hata: {e}"}

def delete_vault_note(name):
    p=_sec_path(name)
    if not p.exists(): return {"ok":False,"msg":f"Vault'ta '{name}' bulunamadı."}
    try: p.unlink(); return {"ok":True,"msg":f"'{name}' vault'tan silindi."}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

# ── Normal Not İşlemleri ──────────────────────────────────────────────────────
def _note_path(name):
    safe=name.strip().replace("/","_").replace("\\","_")
    return NOTE_DIR/(safe if safe.endswith(".txt") else safe+".txt")

def create_note(name,content):
    ensure_dirs(); p=_note_path(name)
    if p.exists(): return {"ok":False,"msg":f"'{name}' adında bir not zaten var."}
    try:
        now=datetime.now().isoformat(timespec="seconds")
        p.write_text(f"--- NoteX | {name} ---\nOluşturulma: {now}\n"+"-"*40+f"\n{content}\n",encoding="utf-8")
        return {"ok":True,"msg":f"Not oluşturuldu: {p}"}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

def list_notes():
    ensure_dirs()
    return [{"name":p.stem,"size":p.stat().st_size,
             "modified":datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
            for p in sorted(NOTE_DIR.glob("*.txt"))]

def read_note(name):
    p=_note_path(name)
    if not p.exists(): return {"ok":False,"content":"","msg":f"'{name}' bulunamadı."}
    try: return {"ok":True,"content":p.read_text(encoding="utf-8"),"msg":""}
    except Exception as e: return {"ok":False,"content":"","msg":f"Hata: {e}"}

def delete_note(name):
    p=_note_path(name)
    if not p.exists(): return {"ok":False,"msg":f"'{name}' bulunamadı."}
    try: p.unlink(); return {"ok":True,"msg":f"'{name}' silindi."}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

def find_notes(query):
    q=query.strip().lower()
    return [n for n in list_notes() if q in n["name"].lower()]

def edit_note(name, appended_content: str) -> dict:
    """Mevcut içerik KORUNARAK yeni içerik eklenir."""
    p=_note_path(name)
    if not p.exists(): return {"ok":False,"msg":f"'{name}' bulunamadı."}
    try:
        existing=p.read_text(encoding="utf-8")
        now=datetime.now().isoformat(timespec="seconds")
        sep=f"\n{'─'*40}\n[Düzenleme: {now}]\n{'─'*40}\n"
        p.write_text(existing+sep+appended_content+"\n",encoding="utf-8")
        return {"ok":True,"msg":f"'{name}' güncellendi (önceki içerik korundu)."}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

def replace_note_content(name, new_content: str) -> dict:
    """Notun tüm içeriği değiştirilir."""
    p=_note_path(name)
    if not p.exists(): return {"ok":False,"msg":f"'{name}' bulunamadı."}
    try:
        now=datetime.now().isoformat(timespec="seconds")
        p.write_text(f"--- NoteX | {name} ---\nGüncelleme: {now}\n"+"-"*40+f"\n{new_content}\n",encoding="utf-8")
        return {"ok":True,"msg":f"'{name}' tamamen güncellendi."}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

def rename_note(old,new):
    op=_note_path(old); np=_note_path(new)
    if not op.exists(): return {"ok":False,"msg":f"'{old}' bulunamadı."}
    if np.exists(): return {"ok":False,"msg":f"'{new}' zaten var."}
    try: op.rename(np); return {"ok":True,"msg":f"'{old}' → '{new}'"}
    except Exception as e: return {"ok":False,"msg":f"Hata: {e}"}

# ── Sıfırlama ─────────────────────────────────────────────────────────────────
def reset_all():
    details,errors=[],[]
    for f in [CFG_FILE,SEC_CFG]:
        if f.exists():
            try: f.unlink(); details.append(f"Silindi: {f}")
            except Exception as e: errors.append(str(e))
    for d,label in [(NOTE_DIR,"Not"),(SEC_DIR,"Şifreli not")]:
        if d.exists():
            c=0
            for p in d.glob("*.txt"):
                try: p.unlink(); c+=1
                except Exception as e: errors.append(str(e))
            details.append(f"{label} klasörü temizlendi ({c} dosya).")
    for extra_f in [
        BASE_DIR/"template"/"temp.txt",
        BASE_DIR/"favorites.json",
        BASE_DIR/"share_history.json",
        BASE_DIR/"list"/"blacklist.json",
    ]:
        if extra_f.exists():
            try: extra_f.unlink(); details.append(f"Silindi: {extra_f}")
            except Exception as e: errors.append(str(e))
    if errors:
        return {"ok":False,"msg":"Sıfırlama tamamlandı (bazı hatalar oluştu).","details":details,"errors":errors}
    return {"ok":True,"msg":"NoteX başarıyla sıfırlandı.","details":details,"errors":[]}

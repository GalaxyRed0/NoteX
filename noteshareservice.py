"""
NoteX v1.6 - noteshareservice.py
Note Sharing Service v1.0.1

Değişiklikler v1.0.1:
  - NoteX ID kara liste sistemi (blacklist)
  - Kara listedeki ID'lerden gelen teklifler otomatik reddedilir
  - Kara liste dosya yolu: /sdcard/Android/notee/list/blacklist.json
"""

import os
import json
import socket
import struct
import hashlib
import hmac as _hmac_mod
import random
import string
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

# ─── Sabitler ────────────────────────────────────────────────────────────────
NSS_VERSION  = "1.0.1"
PORT         = 9000
TIMEOUT_S    = 30
SALT         = b"NoteX_NSS_Salt_2024_v1"
HMAC_SECRET  = b"NoteX_HMAC_Secret_2024"

BASE_DIR      = Path("/sdcard/Android/notee")
ID_DIR        = BASE_DIR / "id"
ID_FILE       = ID_DIR / "id.enc"
HISTORY_FILE  = BASE_DIR / "share_history.json"
LIST_DIR      = BASE_DIR / "list"
BLACKLIST_FILE = LIST_DIR / "blacklist.json"

# ─── Protocol ────────────────────────────────────────────────────────────────
MSG_OFFER  = "OFFER"
MSG_ACCEPT = "ACCEPT"
MSG_REJECT = "REJECT"
MSG_DATA   = "DATA"
MSG_ACK    = "ACK"
MSG_ERROR  = "ERROR"

# ══════════════════════════════════════════════════════════════════════════════
# ŞİFRELEME
# ══════════════════════════════════════════════════════════════════════════════

def _derive_key(password: bytes) -> bytes:
    if not CRYPTO_OK:
        raise RuntimeError("cryptography kütüphanesi gerekli: pip install cryptography")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=100_000)
    return base64.urlsafe_b64encode(kdf.derive(password))

def _get_fernet() -> "Fernet":
    return Fernet(_derive_key(HMAC_SECRET))

def encrypt_content(plaintext: str) -> bytes:
    return _get_fernet().encrypt(plaintext.encode("utf-8"))

def decrypt_content(ciphertext: bytes) -> str:
    return _get_fernet().decrypt(ciphertext).decode("utf-8")

# ══════════════════════════════════════════════════════════════════════════════
# KARA LİSTE SİSTEMİ
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_list_dir():
    LIST_DIR.mkdir(parents=True, exist_ok=True)

def load_blacklist() -> list:
    """
    Kara listeyi yükle.
    Döndürür: [{"id": str, "blocked_at": str}, ...]
    """
    if not BLACKLIST_FILE.exists():
        return []
    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def _save_blacklist(bl: list):
    _ensure_list_dir()
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(bl, f, ensure_ascii=False, indent=2)

def is_blacklisted(notex_id: str) -> bool:
    """Verilen NoteX ID kara listede mi?"""
    bl = load_blacklist()
    return any(entry["id"].upper() == notex_id.upper() for entry in bl)

def add_to_blacklist(notex_id: str) -> dict:
    """
    NoteX ID'yi kara listeye ekle.
    Döndürür: {"ok": bool, "msg": str}
    """
    nid = notex_id.strip().upper()
    if not nid:
        return {"ok": False, "msg": "NoteX ID boş olamaz."}
    bl = load_blacklist()
    if any(e["id"] == nid for e in bl):
        return {"ok": False, "msg": f"'{nid}' zaten kara listede."}
    bl.append({"id": nid, "blocked_at": datetime.now().isoformat(timespec="seconds")})
    _save_blacklist(bl)
    return {"ok": True, "msg": f"'{nid}' kara listeye eklendi."}

def remove_from_blacklist(notex_id: str) -> dict:
    """
    NoteX ID'yi kara listeden çıkart.
    Döndürür: {"ok": bool, "msg": str}
    """
    nid = notex_id.strip().upper()
    bl  = load_blacklist()
    new_bl = [e for e in bl if e["id"] != nid]
    if len(new_bl) == len(bl):
        return {"ok": False, "msg": f"'{nid}' kara listede bulunamadı."}
    _save_blacklist(new_bl)
    return {"ok": True, "msg": f"'{nid}' kara listeden çıkartıldı."}

# ══════════════════════════════════════════════════════════════════════════════
# NOTEX ID SİSTEMİ
# ══════════════════════════════════════════════════════════════════════════════

def _generate_raw_id() -> str:
    digits  = "".join(random.choices(string.digits,      k=5))
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    return digits + letters

def _sign_id(raw_id: str) -> str:
    return _hmac_mod.new(HMAC_SECRET, raw_id.encode("utf-8"), hashlib.sha256).hexdigest()

def _verify_id_signature(raw_id: str, signature: str) -> bool:
    return _hmac_mod.compare_digest(_sign_id(raw_id), signature)

def create_notex_id() -> str:
    if not CRYPTO_OK:
        raise RuntimeError("cryptography kütüphanesi gerekli.")
    ID_DIR.mkdir(parents=True, exist_ok=True)
    raw_id    = _generate_raw_id()
    signature = _sign_id(raw_id)
    payload   = json.dumps({
        "id"        : raw_id,
        "sig"       : signature,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    ID_FILE.write_bytes(_get_fernet().encrypt(payload.encode("utf-8")))
    return raw_id

def load_notex_id() -> dict:
    if not CRYPTO_OK:
        return {"ok": False, "id": "", "msg": "cryptography kütüphanesi yüklü değil."}
    if not ID_FILE.exists():
        return {"ok": False, "id": "", "msg": "ID dosyası bulunamadı."}
    try:
        payload = json.loads(_get_fernet().decrypt(ID_FILE.read_bytes()).decode("utf-8"))
    except Exception as e:
        return {"ok": False, "id": "", "msg": f"ID dosyası bozuk veya değiştirilmiş: {e}"}
    raw_id    = payload.get("id", "")
    signature = payload.get("sig", "")
    if not _verify_id_signature(raw_id, signature):
        return {"ok": False, "id": "", "msg": "ID imzası geçersiz! Dosya değiştirilmiş."}
    return {"ok": True, "id": raw_id, "msg": ""}

def get_or_create_id() -> dict:
    if ID_FILE.exists():
        result = load_notex_id()
        result["new"] = False
        return result
    try:
        raw_id = create_notex_id()
        return {"ok": True, "id": raw_id, "msg": "", "new": True}
    except Exception as e:
        return {"ok": False, "id": "", "msg": str(e), "new": False}

def validate_id_file() -> dict:
    if not ID_FILE.exists():
        return {"valid": None, "id": "", "msg": "ID henüz oluşturulmadı."}
    result = load_notex_id()
    return {"valid": result["ok"], "id": result["id"], "msg": result["msg"]}

# ══════════════════════════════════════════════════════════════════════════════
# AĞ
# ══════════════════════════════════════════════════════════════════════════════

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def resolve_peer_ip(target_id: str, timeout: int = 5):
    DISCOVERY_PORT = 9001
    id_r = load_notex_id()
    if not id_r["ok"]:
        return None
    msg = json.dumps({"type": "DISCOVERY", "target_id": target_id,
                      "from_id": id_r["id"]}).encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    found_ip = None
    try:
        sock.sendto(msg, ("<broadcast>", DISCOVERY_PORT))
        data, addr = sock.recvfrom(512)
        resp = json.loads(data.decode("utf-8"))
        if resp.get("type") == "DISCOVERY_RESPONSE" and resp.get("id") == target_id:
            found_ip = addr[0]
    except Exception:
        pass
    finally:
        sock.close()
    return found_ip

# ══════════════════════════════════════════════════════════════════════════════
# TRANSFER GEÇMİŞİ
# ══════════════════════════════════════════════════════════════════════════════

def _load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_history(history: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_history_entry(direction: str, peer_id: str, note_name: str,
                      status: str, size_bytes: int = 0):
    history = _load_history()
    history.insert(0, {
        "direction" : direction,
        "peer_id"   : peer_id,
        "note_name" : note_name,
        "status"    : status,
        "size_bytes": size_bytes,
        "timestamp" : datetime.now().isoformat(timespec="seconds"),
    })
    _save_history(history[:50])

def get_history() -> list:
    return _load_history()

# ══════════════════════════════════════════════════════════════════════════════
# TCP MESAJLAŞMA
# ══════════════════════════════════════════════════════════════════════════════

def _send_msg(sock: socket.socket, msg_type: str, payload: dict):
    data = json.dumps({"type": msg_type, **payload}).encode("utf-8")
    sock.sendall(struct.pack("!I", len(data)) + data)

def _recv_msg(sock: socket.socket) -> dict:
    raw_len = _recv_exact(sock, 4)
    length  = struct.unpack("!I", raw_len)[0]
    return json.loads(_recv_exact(sock, length).decode("utf-8"))

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Bağlantı kesildi.")
        buf += chunk
    return buf

# ══════════════════════════════════════════════════════════════════════════════
# GÖNDERİCİ
# ══════════════════════════════════════════════════════════════════════════════

def send_note(target_ip: str, target_id: str, note_name: str,
              note_content: str, sender_id: str) -> dict:
    if not CRYPTO_OK:
        return {"ok": False, "msg": "cryptography kütüphanesi yüklü değil."}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT_S)
        sock.connect((target_ip, PORT))
        _send_msg(sock, MSG_OFFER, {
            "sender_id" : sender_id,
            "note_name" : note_name,
            "size_bytes": len(note_content.encode("utf-8")),
        })
        resp = _recv_msg(sock)
        if resp.get("type") != MSG_ACCEPT:
            sock.close()
            add_history_entry("sent", target_id, note_name, "rejected")
            return {"ok": False, "msg": f"Reddedildi: {resp.get('reason','Alıcı reddetti.')}"}
        encrypted = encrypt_content(note_content)
        _send_msg(sock, MSG_DATA, {
            "note_name"    : note_name,
            "encrypted_b64": base64.b64encode(encrypted).decode("ascii"),
        })
        ack = _recv_msg(sock)
        sock.close()
        if ack.get("type") == MSG_ACK:
            add_history_entry("sent", target_id, note_name, "success",
                              len(note_content.encode("utf-8")))
            return {"ok": True, "msg": f"'{note_name}' başarıyla gönderildi."}
        add_history_entry("sent", target_id, note_name, "error")
        return {"ok": False, "msg": "Transfer sırasında hata oluştu."}
    except ConnectionRefusedError:
        return {"ok": False, "msg": "Bağlantı reddedildi."}
    except socket.timeout:
        return {"ok": False, "msg": "Bağlantı zaman aşımına uğradı."}
    except Exception as e:
        return {"ok": False, "msg": f"Bağlantı hatası: {e}"}

# ══════════════════════════════════════════════════════════════════════════════
# ALICI SUNUCUSU
# ══════════════════════════════════════════════════════════════════════════════

class NoteReceiver:
    def __init__(self, note_dir: Path, on_offer_callback=None):
        self.note_dir          = note_dir
        self.on_offer_callback = on_offer_callback
        self._running          = False
        self._thread           = None
        self._server_sock      = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server_sock:
            try: self._server_sock.close()
            except Exception: pass

    def _serve(self):
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind(("0.0.0.0", PORT))
            self._server_sock.listen(5)
            self._server_sock.settimeout(1.0)
            while self._running:
                try:
                    conn, addr = self._server_sock.accept()
                    threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception:
            pass

    def _handle(self, conn: socket.socket, addr):
        try:
            conn.settimeout(TIMEOUT_S)
            msg = _recv_msg(conn)
            if msg.get("type") != MSG_OFFER:
                conn.close(); return

            sender_id  = msg.get("sender_id", "?????XX")
            note_name  = msg.get("note_name", "bilinmeyen")
            size_bytes = msg.get("size_bytes", 0)

            # ── Kara liste kontrolü ──────────────────────────────────────────
            if is_blacklisted(sender_id):
                _send_msg(conn, MSG_REJECT, {"reason": "Gönderici kara listede."})
                add_history_entry("received", sender_id, note_name, "blocked")
                conn.close(); return

            # ── Kullanıcı onayı ──────────────────────────────────────────────
            accepted = False
            if self.on_offer_callback:
                accepted = self.on_offer_callback({
                    "sender_id" : sender_id,
                    "note_name" : note_name,
                    "size_bytes": size_bytes,
                    "from_ip"   : addr[0],
                })

            if accepted:
                _send_msg(conn, MSG_ACCEPT, {})
                data_msg = _recv_msg(conn)
                if data_msg.get("type") == MSG_DATA:
                    enc_b64   = data_msg.get("encrypted_b64", "")
                    encrypted = base64.b64decode(enc_b64.encode("ascii"))
                    content   = decrypt_content(encrypted)
                    self.note_dir.mkdir(parents=True, exist_ok=True)
                    safe = note_name.strip().replace("/", "_").replace("\\", "_")
                    dest = self.note_dir / (safe if safe.endswith(".txt") else safe + ".txt")
                    dest.write_text(content, encoding="utf-8")
                    _send_msg(conn, MSG_ACK, {})
                    add_history_entry("received", sender_id, note_name, "success",
                                      len(content.encode()))
            else:
                _send_msg(conn, MSG_REJECT, {"reason": "Kullanıcı reddetti."})
                add_history_entry("received", sender_id, note_name, "rejected")
            conn.close()
        except Exception:
            try: conn.close()
            except Exception: pass

# ══════════════════════════════════════════════════════════════════════════════
# DISCOVERY RESPONDER
# ══════════════════════════════════════════════════════════════════════════════

class DiscoveryResponder:
    def __init__(self, my_id: str):
        self.my_id    = my_id
        self._running = False
        self._thread  = None
        self._sock    = None

    def start(self):
        if self._running: return
        self._running = True
        self._thread  = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            try: self._sock.close()
            except Exception: pass

    def _serve(self):
        DISCOVERY_PORT = 9001
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(("0.0.0.0", DISCOVERY_PORT))
            self._sock.settimeout(1.0)
            while self._running:
                try:
                    data, addr = self._sock.recvfrom(512)
                    msg = json.loads(data.decode("utf-8"))
                    if (msg.get("type") == "DISCOVERY" and
                            msg.get("target_id") == self.my_id and
                            not is_blacklisted(msg.get("from_id", ""))):
                        resp = json.dumps({"type": "DISCOVERY_RESPONSE", "id": self.my_id})
                        self._sock.sendto(resp.encode("utf-8"), addr)
                except socket.timeout:
                    continue
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL SERVİS YÖNETİMİ
# ══════════════════════════════════════════════════════════════════════════════

_receiver   : NoteReceiver       = None
_discoverer : DiscoveryResponder = None
_service_running: bool           = False

def start_service(note_dir: Path, on_offer_callback=None) -> dict:
    global _receiver, _discoverer, _service_running
    if _service_running:
        return {"ok": False, "msg": "Servis zaten çalışıyor."}
    id_result = load_notex_id()
    if not id_result["ok"]:
        return {"ok": False, "msg": f"NoteX ID hatası: {id_result['msg']}"}
    my_id       = id_result["id"]
    _receiver   = NoteReceiver(note_dir, on_offer_callback)
    _discoverer = DiscoveryResponder(my_id)
    _receiver.start()
    _discoverer.start()
    _service_running = True
    return {"ok": True, "msg": f"Servis başlatıldı. ID: {my_id}  IP: {get_local_ip()}:{PORT}"}

def stop_service() -> dict:
    global _receiver, _discoverer, _service_running
    if not _service_running:
        return {"ok": False, "msg": "Servis zaten durdurulmuş."}
    if _receiver:   _receiver.stop()
    if _discoverer: _discoverer.stop()
    _service_running = False
    return {"ok": True, "msg": "Not paylaşma servisi durduruldu."}

def is_service_running() -> bool:
    return _service_running

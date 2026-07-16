"""
NoteX v1.6 - start.py
"""

import sys, os

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)

REQUIRED = {"rich":"rich","questionary":"questionary","prompt_toolkit":"prompt_toolkit"}

def check_deps():
    miss=[]
    for pkg,imp in REQUIRED.items():
        try: __import__(imp)
        except ImportError: miss.append(pkg)
    if miss:
        print("="*50)
        print("NoteX — Missing / Eksik:", ", ".join(miss))
        print("Run: pip install", " ".join(miss))
        print("cryptography için: pip install cryptography")
        print("="*50); sys.exit(1)

check_deps()

import main        as M
import cli         as C
import template    as T
import backup      as B
import favorites   as FAV
import noteshareservice as NSS
from lang import t, get_lang
from rich.console import Console

console = Console()

def _check_id_on_startup(cfg: dict) -> bool:
    if not cfg.get("share_service", False): return True
    check = NSS.validate_id_file()
    if check["valid"] is False:
        lang = get_lang(cfg)
        console.print(f"\n[bold red]⚠  {t('share_id_tampered', lang)}[/]\n")
        cfg["share_service"] = False; M.save_config(cfg); return False
    return True

def dispatch(choice: str, cfg: dict) -> dict:
    lang = get_lang(cfg)
    if   choice == t("menu_create",    lang): C.ui_create_note(cfg)
    elif choice == t("menu_list",      lang): C.ui_list_notes(cfg)
    elif choice == t("menu_delete",    lang): C.ui_delete_note(cfg)
    elif choice == t("menu_find",      lang): C.ui_find_note(cfg)
    elif choice == t("menu_edit",      lang): C.ui_edit_note(cfg)
    elif choice == t("menu_vault",     lang): C.ui_vault(cfg)
    elif choice == t("menu_share",     lang): C.ui_share(cfg)
    elif choice == t("menu_favorites", lang): C.ui_favorites(cfg)
    elif choice == t("menu_settings",  lang): cfg = C.ui_settings(cfg)
    return cfg

def run():
    M.ensure_dirs(); M.ensure_sec_dir(); M.ensure_backup_dir()
    M.ensure_id_dir(); M.ensure_list_dir(); T.ensure_template_dir()
    cfg = M.load_config()
    _check_id_on_startup(cfg)
    console.clear(); C.show_banner(cfg)
    try:
        while True:
            lang = get_lang(cfg)
            try:   choice = C.main_menu(cfg)
            except KeyboardInterrupt: break
            if choice is None or choice == t("menu_quit", lang): break
            console.print(); cfg = dispatch(choice, cfg); console.print()
            try:   input(t("press_enter", lang))
            except (EOFError, KeyboardInterrupt): break
            console.clear(); C.show_banner(cfg)
    except Exception as exc:
        console.print_exception(show_locals=False)
        console.print(f"\n[bold red]Hata:[/] {exc}"); sys.exit(1)
    finally:
        C.show_exit(cfg)

if __name__ == "__main__":
    run()

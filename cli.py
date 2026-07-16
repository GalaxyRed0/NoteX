"""
NoteX v1.6 - cli.py
Yeni: Favoriler UI, 4 dil (TR/EN/AZ/ZH), NSS kara liste yönetimi
"""

import time
import questionary
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from pathlib import Path

import main        as M
import template    as T
import backup      as B
import favorites   as FAV
import noteshareservice as NSS
from lang import t, get_lang

console   = Console()
COLOR_MAP = M.COLOR_MAP

# ─── Yardımcılar ─────────────────────────────────────────────────────────────
def _accent(cfg):  return COLOR_MAP.get(cfg.get("text_color","cyan"),"cyan")
def _lang(cfg):    return get_lang(cfg)
def _fstyle(cfg):  return M.FONT_STYLE_MAP.get(cfg.get("font_style","normal"),"")
def _bg(cfg):      return M.BG_COLOR_MAP.get(cfg.get("bg_color","default"),"")

def _q_style(cfg) -> QStyle:
    acc = cfg.get("text_color","cyan")
    return QStyle([
        ("qmark",f"fg:{acc} bold"),("question","bold"),
        ("answer",f"fg:{acc} bold"),("pointer",f"fg:{acc} bold"),
        ("highlighted",f"fg:{acc} bold"),("selected",f"fg:{acc}"),
        ("separator","fg:#6c6c6c"),("instruction","fg:#6c6c6c italic"),
    ])

def _ask_password(prompt_text, cfg):
    pt_s = PTStyle.from_dict({"prompt":f"fg:{_accent(cfg)} bold"})
    try: return pt_prompt(HTML(f"<b>{prompt_text} </b>"),style=pt_s,is_password=True)
    except (EOFError,KeyboardInterrupt): return ""

def _print_result(r):
    if r["ok"]: console.print(f"[bold green]✓ {r['msg']}[/]")
    else:       console.print(f"[bold red]✗ {r['msg']}[/]")

def _loading_screen(msg, seconds, cfg):
    acc = _accent(cfg)
    with Progress(SpinnerColumn(style=f"bold {acc}"),
                  TextColumn(f"[{acc}]{msg}[/]"),transient=True) as p:
        p.add_task("",total=None); time.sleep(seconds)

def _manual_editor(cfg) -> str:
    acc=_accent(cfg); lang=_lang(cfg)
    pt_s=PTStyle.from_dict({"prompt":f"fg:{acc} bold"})
    kb=KeyBindings(); kw=t("save_keyword",lang)
    console.print(f"[dim]{t('manual_hint',lang)}[/]\n"); lines=[]
    while True:
        try:   line=pt_prompt(HTML("<ansigreen>│</ansigreen> "),style=pt_s,key_bindings=kb)
        except (EOFError,KeyboardInterrupt): break
        if line.strip().upper()==kw: break
        lines.append(line)
    return "\n".join(lines)

def _display_note(name, cfg, vault=False):
    acc=_accent(cfg); fst=_fstyle(cfg)
    r=M.read_vault_note(name) if vault else M.read_note(name)
    if r["ok"]:
        content=f"[{fst}]{r['content']}[/]" if fst else r["content"]
        console.print(Panel(content,title=f"[bold {acc}]{name}{'  🔐' if vault else ''}[/]",
                            border_style=acc,box=box.ROUNDED,padding=(1,2)))
    else:
        console.print(f"[red]{r['msg']}[/]")

# ─── Banner ───────────────────────────────────────────────────────────────────
def show_banner(cfg: dict):
    acc=_accent(cfg); lang=_lang(cfg); bg=_bg(cfg)
    art = f"[bold {acc}{' '+bg if bg else ''}]" + r"""
  _   _       _       __  __
 | \ | | ___ | |_ ___|  \/  |___  ___ 
 |  \| |/ _ \| __/ _ \ |\/| / __|/ __|
 | |\  | (_) | ||  __/ |  | \__ \ (__ 
 |_| \_|\___/ \__\___|_|  |_|___/\___|
""" + "[/]"
    console.print(art)
    vault_s  = f"[bold green]{t('vault_active',lang)}[/]" if M.is_vault_enabled() else f"[dim]{t('vault_passive',lang)}[/]"
    share_s  = f"[bold cyan]📡 ON[/]" if cfg.get("share_service") else "[dim]📡 off[/]"
    fav_s    = f"[dim]⭐{FAV.count()}[/]"
    lang_flags = {"tr":"🇹🇷","en":"🇬🇧","az":"🇦🇿","zh":"🇨🇳"}
    lang_flag = lang_flags.get(lang,"🌐")
    console.print(
        f"  [dim]v{cfg['version']} — {t('app_subtitle',lang)}[/]   "
        f"{t('vault_label',lang)}: {vault_s}   {share_s}   {fav_s}   {lang_flag}\n"
    )

# ─── Ana Menü ─────────────────────────────────────────────────────────────────
def main_menu(cfg: dict) -> str:
    lang=_lang(cfg)
    choices=[t(k,lang) for k in
             ("menu_create","menu_list","menu_delete","menu_find",
              "menu_edit","menu_vault","menu_share","menu_favorites",
              "menu_settings","menu_quit")]
    console.print(Rule(f"[dim]{t('menu_title',lang)}[/]"))
    ch=questionary.select(t("menu_question",lang),choices=choices,
                          style=_q_style(cfg),use_arrow_keys=True).ask()
    return ch or choices[-1]

# ══════════════════════════════════════════════════════════════════════════════
# 📝 YENİ NOT OLUŞTUR
# ══════════════════════════════════════════════════════════════════════════════
def ui_create_note(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('create_title',lang)}[/]",box=box.ROUNDED))
    method=questionary.select(t("create_method_q",lang),
                              choices=[t("create_method_new",lang),t("create_method_ext",lang)],
                              style=_q_style(cfg)).ask()
    if not method: return
    if method==t("create_method_ext",lang): _ui_external_note(cfg); return

    name=questionary.text(t("create_name_q",lang),style=_q_style(cfg),
                          validate=lambda v: True if v.strip() else t("create_name_empty",lang)).ask()
    if not name: return
    use_tmpl=questionary.confirm(t("create_template_q",lang),default=False,style=_q_style(cfg)).ask()
    content=None
    if use_tmpl:
        content=_template_flow(cfg)
        if content is None:
            console.print(f"[dim]{t('no_template_manual',lang)}[/]\n")
            content=_manual_editor(cfg)
    else:
        content=_manual_editor(cfg)
    if not content or not content.strip():
        console.print(f"[yellow]{t('empty_content',lang)}[/]"); return
    _print_result(M.create_note(name.strip(),content))

def _ui_external_note(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('ext_title',lang)}[/]",box=box.ROUNDED))
    path_str=questionary.text(t("ext_path_q",lang),style=_q_style(cfg),
                              validate=lambda v: True if v.strip() else t("ext_path_empty",lang)).ask()
    if not path_str: return
    ext_path=Path(path_str.strip())
    if not ext_path.exists() or not ext_path.is_file():
        console.print(f"[bold red]{t('ext_not_found',lang)} {ext_path}[/]"); return
    try:   original=ext_path.read_text(encoding="utf-8")
    except Exception as e: console.print(f"[bold red]✗ {e}[/]"); return
    console.print(f"\n[dim]{t('ext_loaded',lang)}[/]\n")
    console.print(Panel(original,title=f"[bold {acc}]{ext_path.name}[/]",
                        border_style=acc,box=box.ROUNDED,padding=(1,2)))
    console.print(f"\n[dim]{t('ext_edit_hint',lang)}[/]\n")
    pt_s=PTStyle.from_dict({"prompt":f"fg:{acc} bold"}); kw=t("save_keyword",lang); lines=[]
    while True:
        try:   line=pt_prompt(HTML("<ansigreen>│</ansigreen> "),style=pt_s)
        except (EOFError,KeyboardInterrupt): break
        if line.strip().upper()==kw: break
        lines.append(line)
    if not lines: console.print(f"[dim]{t('ext_no_change',lang)}[/]"); return
    new_content="\n".join(lines)
    try:
        ext_path.write_text(new_content,encoding="utf-8")
        console.print(f"\n[bold green]{t('ext_saved',lang)} {ext_path}[/]")
    except Exception as e: console.print(f"\n[bold red]{t('ext_save_err',lang)} {e}[/]"); return
    if questionary.confirm(t("ext_save_as_note_q",lang),default=False,style=_q_style(cfg)).ask():
        nn=questionary.text(t("ext_note_name_q",lang),style=_q_style(cfg),
                            validate=lambda v: True if v.strip() else t("create_name_empty",lang)).ask()
        if nn: _print_result(M.create_note(nn.strip(),new_content))

# ─── Şablon Akışı ─────────────────────────────────────────────────────────────
def _template_flow(cfg):
    acc=_accent(cfg); lang=_lang(cfg); tmpls=T.get_all_templates()
    console.print()
    table=Table(title=f"[bold {acc}]{t('tmpl_table_title',lang)}[/]",
                box=box.SIMPLE_HEAD,header_style=f"bold {acc}",show_lines=False)
    table.add_column(t("tmpl_col_id",lang),justify="center",style=f"bold {acc}",width=4)
    table.add_column(t("tmpl_col_name",lang),style="bold white",min_width=24)
    table.add_column(t("tmpl_col_desc",lang),style="dim")
    for tmpl in tmpls: table.add_row(str(tmpl["id"]),f"{tmpl['icon']}  {tmpl['name']}",tmpl["description"])
    console.print(table)
    choices=[questionary.Choice(title=f"{tmpl['icon']}  [{tmpl['id']}] {tmpl['name']}",value=tmpl["id"])
             for tmpl in tmpls]
    choices.append(questionary.Choice(title=t("tmpl_cancel",lang),value=0))
    cid=questionary.select(t("tmpl_select_q",lang),choices=choices,style=_q_style(cfg)).ask()
    if cid==0 or cid is None: return None
    tmpl=T.get_template_by_id(cid)
    if not tmpl: console.print(f"[red]{t('tmpl_not_found',lang)}[/]"); return None
    console.print(Panel(f"[bold {acc}]{tmpl['icon']}  {tmpl['name']}[/]\n[dim]{t('tmpl_fill_hint',lang)}[/]",
                        box=box.ROUNDED,border_style=acc))
    pt_s=PTStyle.from_dict({"prompt":f"fg:{acc} bold"}); values={}; today=T.get_today()
    for field in tmpl["fields"]:
        hint=f" [dim]({t('tmpl_date_auto',lang)} {today})[/]" if field=="TARIH" else ""
        console.print(f"  [bold {acc}]▸[/] [white]{field}[/]{hint}")
        try:   val=pt_prompt(HTML("    <ansicyan>↳</ansicyan> "),style=pt_s)
        except (EOFError,KeyboardInterrupt): val=""
        if field=="TARIH" and not val.strip(): val=today
        values[field]=val
    filled=T.fill_template(tmpl,values)
    console.print(Panel(filled,title=f"[bold {acc}]{t('tmpl_preview',lang)} — {tmpl['name']}[/]",
                        border_style=acc,box=box.ROUNDED,padding=(1,2)))
    act=questionary.select(t("tmpl_action_q",lang),
                           choices=[t("tmpl_action_save",lang),t("tmpl_action_edit",lang),t("tmpl_action_cancel",lang)],
                           style=_q_style(cfg)).ask()
    if not act or act==t("tmpl_action_cancel",lang): return None
    if act==t("tmpl_action_save",lang):
        T.save_template_file(filled)
        console.print(f"\n[bold green]✓ {t('content_ready',lang)}[/]"); return filled
    console.print(Panel(filled,title=f"[dim]{t('tmpl_ref_panel',lang)}[/]",border_style="dim",box=box.ROUNDED,padding=(1,1)))
    console.print(f"\n[dim]{t('tmpl_edit_hint',lang)}[/]\n"); kw=t("save_keyword",lang); lines=[]
    while True:
        try:   line=pt_prompt(HTML("<ansigreen>│</ansigreen> "),style=pt_s)
        except (EOFError,KeyboardInterrupt): break
        if line.strip().upper()==kw: break
        lines.append(line)
    edited="\n".join(lines) if lines else filled
    T.save_template_file(edited)
    console.print(f"\n[bold green]✓ {t('content_ready',lang)}[/]"); return edited

# ─── Notları Listele ──────────────────────────────────────────────────────────
def ui_list_notes(cfg):
    acc=_accent(cfg); lang=_lang(cfg); notes=M.list_notes()
    if not notes: console.print(Panel(f"[yellow]{t('list_empty',lang)}[/]",box=box.ROUNDED)); return
    table=Table(title=f"[bold {acc}]{t('list_title',lang)}[/]",
                box=box.SIMPLE_HEAD,show_lines=False,header_style=f"bold {acc}")
    table.add_column(t("list_col_num",lang),justify="right",style="dim",width=4)
    table.add_column(t("list_col_name",lang),style=f"{acc}",min_width=20)
    table.add_column(t("list_col_size",lang),justify="right",style="dim",width=10)
    table.add_column(t("list_col_modified",lang),style="dim",width=18)
    for i,n in enumerate(notes,1):
        star=" ⭐" if FAV.is_favorite(n["name"]) else ""
        sz=f"{n['size']} B" if n['size']<1024 else f"{n['size']//1024} KB"
        table.add_row(str(i),n["name"]+star,sz,n["modified"])
    console.print(table)
    if questionary.confirm(t("list_view_q",lang),default=False,style=_q_style(cfg)).ask():
        ch=questionary.select(t("list_which_q",lang),choices=[n["name"] for n in notes],style=_q_style(cfg)).ask()
        if ch: _display_note(ch,cfg)

# ─── Not Sil ─────────────────────────────────────────────────────────────────
def ui_delete_note(cfg):
    acc=_accent(cfg); lang=_lang(cfg); notes=M.list_notes()
    if not notes: console.print(f"[yellow]{t('delete_none',lang)}[/]"); return
    console.print(Panel(f"[bold {acc}]{t('delete_title',lang)}[/]",box=box.ROUNDED))
    ch=questionary.select(t("delete_which_q",lang),
                          choices=[n["name"] for n in notes]+[t("back",lang)],style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    if questionary.confirm(f"'{ch}' {t('delete_confirm',lang)}",default=False,style=_q_style(cfg)).ask():
        _print_result(M.delete_note(ch))
        # Favoriden de çıkar (sessiz)
        if FAV.is_favorite(ch): FAV.remove_favorite(ch)

# ─── Not Bul ─────────────────────────────────────────────────────────────────
def ui_find_note(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('find_title',lang)}[/]",box=box.ROUNDED))
    query=questionary.text(t("find_q",lang),style=_q_style(cfg),
                           validate=lambda v: True if v.strip() else t("find_empty_q",lang)).ask()
    if not query: return
    results=M.find_notes(query.strip())
    if not results: console.print(f"[yellow]'{query}' {t('find_no_result',lang)}[/]"); return
    table=Table(title=f"[bold {acc}]{t('find_results',lang)} — '{query}'[/]",
                box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
    table.add_column(t("list_col_num",lang),justify="right",style="dim",width=4)
    table.add_column(t("list_col_name",lang),style=f"{acc}")
    table.add_column(t("list_col_modified",lang),style="dim")
    for i,n in enumerate(results,1): table.add_row(str(i),n["name"],n["modified"])
    console.print(table)
    if questionary.confirm(t("find_view_q",lang),default=False,style=_q_style(cfg)).ask():
        ch=questionary.select(t("list_which_q",lang),choices=[n["name"] for n in results],style=_q_style(cfg)).ask()
        if ch: _display_note(ch,cfg)

# ─── Not Düzenleme ────────────────────────────────────────────────────────────
def ui_edit_note(cfg):
    acc=_accent(cfg); lang=_lang(cfg); notes=M.list_notes()
    if not notes: console.print(f"[yellow]{t('edit_none',lang)}[/]"); return
    console.print(Panel(f"[bold {acc}]{t('edit_title',lang)}[/]",box=box.ROUNDED))
    ch=questionary.select(t("edit_which_q",lang),
                          choices=[n["name"] for n in notes]+[t("back",lang)],style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    r=M.read_note(ch)
    if r["ok"]:
        console.print(Panel(r["content"],title=f"[dim]{t('edit_current',lang)}: {ch}[/]",
                            border_style="dim",box=box.ROUNDED,padding=(1,2)))
    mode=questionary.select(t("edit_action_q",lang),
                            choices=[t("edit_append",lang),t("edit_replace",lang),
                                     t("edit_rename",lang),t("edit_back",lang)],
                            style=_q_style(cfg)).ask()
    if not mode or mode==t("edit_back",lang): return
    if mode==t("edit_append",lang):
        console.print(f"\n{t('edit_append_label',lang)}\n")
        console.print(f"[dim]{t('edit_append_hint',lang)}[/]\n")
        nc=_manual_editor(cfg)
        if not nc.strip(): console.print(f"[yellow]{t('edit_empty_warn',lang)}[/]"); return
        _print_result(M.edit_note(ch,nc))
    elif mode==t("edit_replace",lang):
        console.print(f"\n[dim]{t('edit_replace_hint',lang)}[/]\n")
        nc=_manual_editor(cfg)
        if not nc.strip(): console.print(f"[yellow]{t('edit_empty_warn',lang)}[/]"); return
        _print_result(M.replace_note_content(ch,nc))
    elif mode==t("edit_rename",lang):
        nn=questionary.text(t("edit_new_name_q",lang),style=_q_style(cfg),
                            validate=lambda v: True if v.strip() else t("edit_name_empty",lang)).ask()
        if nn:
            res=M.rename_note(ch,nn.strip())
            if res["ok"] and FAV.is_favorite(ch):
                FAV.remove_favorite(ch); FAV.add_favorite(nn.strip())
            _print_result(res)

# ══════════════════════════════════════════════════════════════════════════════
# ⭐ FAVORİLER
# ══════════════════════════════════════════════════════════════════════════════
def ui_favorites(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('fav_title',lang)}[/]",box=box.ROUNDED))
    while True:
        act=questionary.select(
            t("fav_menu_q",lang),
            choices=[t(k,lang) for k in
                     ("fav_add","fav_remove","fav_list","fav_search","fav_back")],
            style=_q_style(cfg)
        ).ask()
        if not act or act==t("fav_back",lang): break
        elif act==t("fav_add",lang):    _fav_add(cfg)
        elif act==t("fav_remove",lang): _fav_remove(cfg)
        elif act==t("fav_list",lang):   _fav_list(cfg)
        elif act==t("fav_search",lang): _fav_search(cfg)
        console.print()

def _fav_add(cfg):
    acc=_accent(cfg); lang=_lang(cfg); notes=M.list_notes()
    if not notes: console.print(f"[yellow]{t('list_empty',lang)}[/]"); return
    # Henüz favoride olmayanları göster
    non_fav=[n["name"] for n in notes if not FAV.is_favorite(n["name"])]
    if not non_fav:
        console.print(f"[dim]{t('fav_already',lang)}[/]"); return
    ch=questionary.select(
        t("fav_which_add_q",lang),
        choices=non_fav+[t("back",lang)],
        style=_q_style(cfg)
    ).ask()
    if not ch or ch==t("back",lang): return
    _print_result(FAV.add_favorite(ch))

def _fav_remove(cfg):
    lang=_lang(cfg); favs=FAV.get_all()
    if not favs: console.print(f"[yellow]{t('fav_empty',lang)}[/]"); return
    ch=questionary.select(
        t("fav_which_remove_q",lang),
        choices=[f["name"] for f in favs]+[t("back",lang)],
        style=_q_style(cfg)
    ).ask()
    if not ch or ch==t("back",lang): return
    _print_result(FAV.remove_favorite(ch))

def _fav_list(cfg):
    acc=_accent(cfg); lang=_lang(cfg); favs=FAV.get_all()
    if not favs:
        console.print(Panel(f"[yellow]{t('fav_empty',lang)}[/]",box=box.ROUNDED)); return
    table=Table(title=f"[bold {acc}]{t('fav_title',lang)}[/]",
                box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
    table.add_column(t("list_col_num",lang),justify="right",style="dim",width=4)
    table.add_column(t("fav_col_name",lang),style=f"{acc}",min_width=22)
    table.add_column(t("fav_col_added",lang),style="dim",width=20)
    for i,f in enumerate(favs,1): table.add_row(str(i),f"⭐ {f['name']}",f["added_at"])
    console.print(table)
    if questionary.confirm(t("fav_view_q",lang),default=False,style=_q_style(cfg)).ask():
        ch=questionary.select(t("list_which_q",lang),
                              choices=[f["name"] for f in favs],style=_q_style(cfg)).ask()
        if ch: _display_note(ch,cfg)

def _fav_search(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    query=questionary.text(t("fav_search_q",lang),style=_q_style(cfg),
                           validate=lambda v: True if v.strip() else t("fav_search_empty",lang)).ask()
    if not query: return
    results=FAV.search_favorites(query.strip())
    if not results: console.print(f"[yellow]{t('fav_search_no_result',lang)}[/]"); return
    table=Table(title=f"[bold {acc}]{t('find_results',lang)} — '{query}'[/]",
                box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
    table.add_column(t("list_col_num",lang),justify="right",style="dim",width=4)
    table.add_column(t("fav_col_name",lang),style=f"{acc}")
    table.add_column(t("fav_col_added",lang),style="dim",width=20)
    for i,f in enumerate(results,1): table.add_row(str(i),f"⭐ {f['name']}",f["added_at"])
    console.print(table)
    if questionary.confirm(t("fav_view_q",lang),default=False,style=_q_style(cfg)).ask():
        ch=questionary.select(t("list_which_q",lang),
                              choices=[f["name"] for f in results],style=_q_style(cfg)).ask()
        if ch: _display_note(ch,cfg)

# ══════════════════════════════════════════════════════════════════════════════
# 🔐 VAULT
# ══════════════════════════════════════════════════════════════════════════════
def ui_vault(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    if not M.is_vault_enabled():
        console.print(Panel(f"[yellow]{t('vault_inactive_msg',lang)}[/]",
                            title=f"[bold {acc}]{t('vault_title',lang)}[/]",
                            box=box.ROUNDED,border_style="yellow")); return
    console.print(Panel(f"[bold {acc}]{t('vault_login_title',lang)}[/]",box=box.ROUNDED))
    pw=_ask_password(t("vault_pw_prompt",lang),cfg)
    if not pw: console.print(f"[yellow]{t('cancelled',lang)}[/]"); return
    res=M.verify_vault_password(pw)
    if not res["ok"]: console.print(f"\n[bold red]✗ {res['msg']}[/]"); return
    console.print(f"\n[bold green]{t('vault_access_ok',lang)}[/]\n"); _vault_menu(cfg)

def _vault_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    while True:
        notes=M.list_vault_notes()
        console.print(Rule(f"[bold {acc}]{t('vault_title',lang)}[/]  [dim]({len(notes)} {t('vault_notes_count',lang)})[/]"))
        act=questionary.select(t("menu_question",lang),
                               choices=[t(k,lang) for k in
                                        ("vault_menu_list","vault_menu_add","vault_menu_remove",
                                         "vault_menu_delete","vault_menu_back")],
                               style=_q_style(cfg)).ask()
        if not act or act==t("vault_menu_back",lang): break
        elif act==t("vault_menu_list",lang):   _vault_list(cfg)
        elif act==t("vault_menu_add",lang):    _vault_add(cfg)
        elif act==t("vault_menu_remove",lang): _vault_remove(cfg)
        elif act==t("vault_menu_delete",lang): _vault_delete(cfg)
        console.print()

def _vault_list(cfg):
    acc=_accent(cfg); lang=_lang(cfg); notes=M.list_vault_notes()
    if not notes: console.print(Panel(f"[yellow]{t('vault_list_empty',lang)}[/]",box=box.ROUNDED)); return
    table=Table(title=f"[bold {acc}]{t('vault_list_title',lang)}[/]",box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
    table.add_column(t("list_col_num",lang),justify="right",style="dim",width=4)
    table.add_column(t("list_col_name",lang),style=f"{acc}",min_width=20)
    table.add_column(t("list_col_size",lang),justify="right",style="dim",width=10)
    table.add_column(t("list_col_modified",lang),style="dim",width=18)
    for i,n in enumerate(notes,1):
        sz=f"{n['size']} B" if n['size']<1024 else f"{n['size']//1024} KB"
        table.add_row(str(i),n["name"],sz,n["modified"])
    console.print(table)
    if questionary.confirm(t("list_view_q",lang),default=False,style=_q_style(cfg)).ask():
        ch=questionary.select(t("list_which_q",lang),choices=[n["name"] for n in notes],style=_q_style(cfg)).ask()
        if ch: _display_note(ch,cfg,vault=True)

def _vault_add(cfg):
    lang=_lang(cfg); notes=M.list_notes()
    if not notes: console.print(f"[yellow]{t('vault_add_none',lang)}[/]"); return
    ch=questionary.select(t("vault_add_which_q",lang),
                          choices=[n["name"] for n in notes]+[t("back",lang)],style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    if questionary.confirm(f"'{ch}' {t('vault_add_confirm',lang)}",default=True,style=_q_style(cfg)).ask():
        _print_result(M.move_to_vault(ch))

def _vault_remove(cfg):
    lang=_lang(cfg); notes=M.list_vault_notes()
    if not notes: console.print(f"[yellow]{t('vault_remove_none',lang)}[/]"); return
    ch=questionary.select(t("vault_remove_which_q",lang),
                          choices=[n["name"] for n in notes]+[t("back",lang)],style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    if questionary.confirm(f"'{ch}' {t('vault_remove_confirm',lang)}",default=True,style=_q_style(cfg)).ask():
        _print_result(M.move_from_vault(ch))

def _vault_delete(cfg):
    lang=_lang(cfg); notes=M.list_vault_notes()
    if not notes: console.print(f"[yellow]{t('vault_delete_none',lang)}[/]"); return
    ch=questionary.select(t("vault_delete_which_q",lang),
                          choices=[n["name"] for n in notes]+[t("back",lang)],style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    if questionary.confirm(f"'{ch}' {t('vault_delete_confirm',lang)}",default=False,style=_q_style(cfg)).ask():
        _print_result(M.delete_vault_note(ch))

# ══════════════════════════════════════════════════════════════════════════════
# 📡 NOT PAYLAŞMA
# ══════════════════════════════════════════════════════════════════════════════
def ui_share(cfg):
    lang=_lang(cfg)
    if not cfg.get("share_service",False):
        console.print(Panel(f"[yellow]{t('share_inactive_warn',lang)}[/]",
                            title=f"[bold cyan]{t('share_title',lang)}[/]",
                            box=box.ROUNDED,border_style="yellow")); return
    id_check=NSS.validate_id_file()
    if id_check["valid"] is False:
        console.print(Panel(f"[bold red]{t('share_id_tampered',lang)}[/]",
                            box=box.ROUNDED,border_style="red"))
        cfg["share_service"]=False; M.save_config(cfg); NSS.stop_service(); return
    if id_check["valid"] is None:
        id_r=NSS.get_or_create_id()
        if not id_r["ok"]:
            console.print(f"[bold red]{t('share_id_error',lang)}: {id_r['msg']}[/]"); return
    _loading_screen(t("share_loading",lang),4,cfg); console.clear()
    if not NSS.is_service_running():
        def _offer_cb(offer): return _incoming_offer_ui(offer,cfg)
        NSS.start_service(M.NOTE_DIR,_offer_cb)
    _share_main_menu(cfg)

def _share_main_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    id_r=NSS.load_notex_id(); my_id=id_r["id"] if id_r["ok"] else "???????"
    while True:
        console.clear()
        console.print(Panel(
            f"[bold cyan]---*Note sharing service*---[/]\n"
            f"[dim]V{NSS.NSS_VERSION} — {t('share_version',lang)}[/]\n"
            f"[bold]{'─'*26}[/]\n"
            f"[bold cyan]NoteX ID: [bold white]{my_id}[/][/]\n"
            f"[bold]{'■'+'-'*9+'■'}[/]",
            box=box.ROUNDED,border_style="cyan"
        ))
        choices=[t(k,lang) for k in
                 ("share_menu_send","share_menu_history","share_menu_about",
                  "share_menu_settings","share_menu_back")]
        act=questionary.select("",choices=choices,style=_q_style(cfg)).ask()
        if not act or act==t("share_menu_back",lang):
            _loading_screen(t("share_loading_back",lang),5,cfg); break
        elif act==t("share_menu_send",lang):    _share_send(cfg,my_id)
        elif act==t("share_menu_history",lang): _share_history(cfg)
        elif act==t("share_menu_about",lang):   _share_about(cfg,my_id)
        elif act==t("share_menu_settings",lang):_share_settings_menu(cfg)

def _share_send(cfg,my_id):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('share_send_title',lang)}[/]",box=box.ROUNDED))
    notes=M.list_notes()
    if not notes: console.print(f"[yellow]{t('share_no_notes',lang)}[/]"); time.sleep(2); return
    target_id=questionary.text(t("share_target_id_q",lang),style=_q_style(cfg),
                               validate=lambda v: True if v.strip() else t("share_target_id_empty",lang)).ask()
    if not target_id: return
    ch=questionary.select(t("share_which_note_q",lang),
                          choices=[n["name"] for n in notes]+[t("back",lang)],style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    console.print(f"\n[dim]{t('share_searching',lang)}[/]")
    target_ip=NSS.resolve_peer_ip(target_id.strip().upper(),timeout=5)
    if not target_ip:
        console.print(f"[bold red]{t('share_not_found',lang)}[/]"); time.sleep(2); return
    note_r=M.read_note(ch)
    if not note_r["ok"]: _print_result(note_r); return
    console.print(f"[dim]{t('share_sending',lang)}[/]")
    _print_result(NSS.send_note(target_ip,target_id.strip().upper(),ch,note_r["content"],my_id))
    time.sleep(2)

def _incoming_offer_ui(offer, cfg) -> bool:
    lang=_lang(cfg)
    console.print(Panel(
        f"[bold cyan]{t('share_offer_title',lang)}[/]\n\n"
        f"  Gönderici : [bold]{offer['sender_id']}[/]\n"
        f"  IP        : [dim]{offer['from_ip']}[/]\n"
        f"  Not Adı   : [bold white]{offer['note_name']}[/]\n"
        f"  Boyut     : {offer['size_bytes']} B",
        box=box.ROUNDED,border_style="cyan"
    ))
    r=questionary.confirm(t("share_offer_accept_q",lang),default=True,style=_q_style(cfg)).ask()
    return bool(r)

def _share_history(cfg):
    acc=_accent(cfg); lang=_lang(cfg); history=NSS.get_history()
    if not history:
        console.print(Panel(f"[yellow]{t('share_history_empty',lang)}[/]",box=box.ROUNDED))
        time.sleep(2); return
    table=Table(title=f"[bold {acc}]{t('share_history_title',lang)}[/]",
                box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
    table.add_column(t("share_col_dir",lang),width=6)
    table.add_column(t("share_col_peer",lang),style=f"{acc}",min_width=9)
    table.add_column(t("share_col_note",lang),min_width=16)
    table.add_column(t("share_col_status",lang),width=10)
    table.add_column(t("share_col_time",lang),style="dim",width=19)
    for h in history:
        dir_icon="📤" if h["direction"]=="sent" else "📥"
        st_col="green" if h["status"]=="success" else("yellow" if h["status"]=="rejected" else "red")
        table.add_row(dir_icon,h["peer_id"],h["note_name"],
                      f"[{st_col}]{h['status']}[/]",h["timestamp"])
    console.print(table); input("\n  [Enter]")

def _share_about(cfg,my_id):
    acc=_accent(cfg); lang=_lang(cfg)
    info=Table(box=box.SIMPLE,show_header=False,padding=(0,2))
    info.add_column("Alan",style=f"bold {acc}"); info.add_column("Değer",style="white")
    info.add_row(t("info_notex_id",lang),my_id)
    info.add_row(t("share_nss_version",lang),f"v{NSS.NSS_VERSION}")
    info.add_row(t("share_notex_ver",lang),M.DEFAULT_CONFIG["version"])
    info.add_row(t("share_local_ip",lang),NSS.get_local_ip())
    info.add_row(t("share_port",lang),str(NSS.PORT))
    console.print(Panel(info,title=f"[bold {acc}]{t('share_about_title',lang)}[/]",
                        box=box.ROUNDED,border_style=acc))
    input("\n  [Enter]")

# ── NSS Ayarları (Kara Liste dahil) ───────────────────────────────────────────
def _share_settings_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('share_settings_menu_title',lang)}[/]",box=box.ROUNDED))
    while True:
        act=questionary.select(
            t("settings_q",lang),
            choices=[
                t("share_bl_add_menu",lang),
                t("share_bl_remove_menu",lang),
                t("share_bl_list_menu",lang),
                t("share_settings_title",lang),   # port / IP bilgisi
                t("settings_back",lang),
            ],
            style=_q_style(cfg)
        ).ask()
        if not act or act==t("settings_back",lang): break
        elif act==t("share_bl_add_menu",lang):    _bl_add(cfg)
        elif act==t("share_bl_remove_menu",lang): _bl_remove(cfg)
        elif act==t("share_bl_list_menu",lang):   _bl_list(cfg)
        elif act==t("share_settings_title",lang): _share_info(cfg)
        console.print()

def _bl_add(cfg):
    lang=_lang(cfg)
    nid=questionary.text(t("share_blocked_q",lang),style=_q_style(cfg),
                         validate=lambda v: True if v.strip() else t("share_blocklist_id_empty",lang)).ask()
    if not nid: return
    _print_result(NSS.add_to_blacklist(nid.strip().upper()))

def _bl_remove(cfg):
    lang=_lang(cfg); bl=NSS.load_blacklist()
    if not bl: console.print(f"[yellow]{t('share_blocklist_empty',lang)}[/]"); return
    choices=[e["id"] for e in bl]+[t("back",lang)]
    ch=questionary.select(t("share_unblock_q",lang),choices=choices,style=_q_style(cfg)).ask()
    if not ch or ch==t("back",lang): return
    _print_result(NSS.remove_from_blacklist(ch))

def _bl_list(cfg):
    acc=_accent(cfg); lang=_lang(cfg); bl=NSS.load_blacklist()
    if not bl:
        console.print(Panel(f"[yellow]{t('share_blocklist_empty',lang)}[/]",box=box.ROUNDED)); return
    table=Table(title=f"[bold {acc}]{t('share_blocklist_title',lang)}[/]",
                box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
    table.add_column(t("list_col_num",lang),justify="right",style="dim",width=4)
    table.add_column(t("share_bl_col_id",lang),style=f"bold {acc}",min_width=10)
    table.add_column(t("share_bl_col_date",lang),style="dim",width=20)
    for i,e in enumerate(bl,1): table.add_row(str(i),e["id"],e["blocked_at"])
    console.print(table)

def _share_info(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    info=Table(box=box.SIMPLE,show_header=False,padding=(0,2))
    info.add_column("Alan",style=f"bold {acc}"); info.add_column("Değer",style="white")
    info.add_row(t("share_port",lang),     str(NSS.PORT))
    info.add_row(t("share_local_ip",lang), NSS.get_local_ip())
    info.add_row(t("share_nss_version",lang),f"v{NSS.NSS_VERSION}")
    info.add_row(t("share_notex_ver",lang),M.DEFAULT_CONFIG["version"])
    console.print(Panel(info,title=f"[bold {acc}]{t('share_settings_title',lang)}[/]",
                        box=box.ROUNDED,border_style=acc))
    input("\n  [Enter]")

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  AYARLAR
# ══════════════════════════════════════════════════════════════════════════════
def ui_settings(cfg) -> dict:
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('settings_title',lang)}[/]",box=box.ROUNDED))
    act=questionary.select(t("settings_q",lang),
                           choices=[t(k,lang) for k in
                                    ("settings_info","settings_color","settings_vault",
                                     "settings_backup","settings_lang","settings_customize",
                                     "settings_changelog","settings_share_svc",
                                     "settings_reset","settings_back")],
                           style=_q_style(cfg)).ask()
    if not act or act==t("settings_back",lang): return cfg
    if   act==t("settings_info",lang):      _show_app_info(cfg)
    elif act==t("settings_color",lang):     cfg=_change_color(cfg)
    elif act==t("settings_vault",lang):     _vault_service_menu(cfg)
    elif act==t("settings_backup",lang):    cfg=_backup_menu(cfg)
    elif act==t("settings_lang",lang):      cfg=_lang_menu(cfg)
    elif act==t("settings_customize",lang): cfg=_customize_menu(cfg)
    elif act==t("settings_changelog",lang): _show_changelog(cfg)
    elif act==t("settings_share_svc",lang): cfg=_share_service_settings(cfg)
    elif act==t("settings_reset",lang):     cfg=_reset_menu(cfg)
    return cfg

def _show_app_info(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    info=Table(box=box.SIMPLE,show_header=False,padding=(0,2))
    info.add_column("Alan",style=f"bold {acc}"); info.add_column("Değer",style="white")
    vault_s=t("info_vault_active",lang) if M.is_vault_enabled() else t("info_vault_passive",lang)
    id_r=NSS.load_notex_id(); my_id=id_r["id"] if id_r["ok"] else "—"
    share_s="Açık ✓" if cfg.get("share_service") else "Kapalı"
    lang_names={"tr":"🇹🇷 Türkçe","en":"🇬🇧 English","az":"🇦🇿 Azərbaycanca","zh":"🇨🇳 中文"}
    rows=[
        ("info_appname",cfg["app_name"]),("info_version",cfg["version"]),
        ("info_notex_id",my_id),("info_notedir",str(M.NOTE_DIR)),
        ("info_secdir",str(M.SEC_DIR)),("info_backupdir",str(M.BACKUP_DIR)),
        ("info_tmplfile",str(T.TEMPLATE_FILE)),("info_color",cfg["text_color"]),
        ("info_font_size",cfg.get("font_size","normal")),
        ("info_font_style",cfg.get("font_style","normal")),
        ("info_bg_color",cfg.get("bg_color","default")),
        ("info_lang",lang_names.get(lang,"?")),
        ("info_notecount",str(len(M.list_notes()))),
        ("info_fav_count",str(FAV.count())),
        ("info_seccount",str(len(M.list_vault_notes()))),
        ("info_vault_status",vault_s),("info_share_status",share_s),
        ("info_tmplcount",str(len(T.get_all_templates()))),
    ]
    for k,v in rows: info.add_row(t(k,lang),v)
    console.print(Panel(info,title=f"[bold {acc}]{t('info_title',lang)}[/]",box=box.ROUNDED,border_style=acc))

def _change_color(cfg):
    lang=_lang(cfg)
    choices=[questionary.Choice(title=[("class:"+c,f"● {c.capitalize()}")],value=c)
             for c in M.COLOR_MAP.keys()]
    ch=questionary.select(t("color_q",lang),choices=choices,style=_q_style(cfg)).ask()
    if ch: cfg["text_color"]=ch; M.save_config(cfg); console.print(f"[bold {ch}]✓ {t('color_set',lang)} '{ch}'[/]")
    return cfg

def _share_service_settings(cfg):
    acc=_accent(cfg); lang=_lang(cfg); enabled=cfg.get("share_service",False)
    status=f"[bold green]{t('svc_share_active',lang)}[/]" if enabled else f"[bold red]{t('svc_share_passive',lang)}[/]"
    console.print(Panel(f"{t('svc_share_status',lang)} {status}",
                        title=f"[bold {acc}]{t('svc_share_title',lang)}[/]",
                        box=box.ROUNDED,border_style=acc))
    choices=([t("svc_share_disable",lang)] if enabled else [t("svc_share_enable",lang)])+[t("svc_share_back",lang)]
    act=questionary.select(t("settings_q",lang),choices=choices,style=_q_style(cfg)).ask()
    if not act or act==t("svc_share_back",lang): return cfg
    if act==t("svc_share_enable",lang):
        id_r=NSS.get_or_create_id()
        if not id_r["ok"]: console.print(f"[bold red]{t('share_id_error',lang)}: {id_r['msg']}[/]"); return cfg
        cfg["share_service"]=True; M.save_config(cfg)
        console.print(f"[bold green]{t('svc_share_enabled_ok',lang)}[/]")
        console.print(f"[dim]NoteX ID: [bold]{id_r['id']}[/][/]")
    elif act==t("svc_share_disable",lang):
        cfg["share_service"]=False; M.save_config(cfg); NSS.stop_service()
        console.print(f"[bold yellow]{t('svc_share_disabled_ok',lang)}[/]")
    return cfg

def _vault_service_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg); enabled=M.is_vault_enabled()
    status=f"[bold green]{t('vsvc_active',lang)}[/]" if enabled else f"[bold red]{t('vsvc_passive',lang)}[/]"
    console.print(Panel(f"{t('vsvc_status',lang)} {status}",
                        title=f"[bold {acc}]{t('vsvc_title',lang)}[/]",box=box.ROUNDED,border_style=acc))
    choices=([] if enabled else [t("vsvc_activate",lang)])+\
            ([t("vsvc_change_pw",lang),t("vsvc_deactivate",lang)] if enabled else [])+[t("vsvc_back",lang)]
    act=questionary.select(t("vsvc_action_q",lang),choices=choices,style=_q_style(cfg)).ask()
    if not act or act==t("vsvc_back",lang): return
    if act==t("vsvc_activate",lang):
        pw1=_ask_password(t("vsvc_new_pw",lang),cfg)
        if not pw1: console.print(f"[yellow]{t('cancelled',lang)}[/]"); return
        pw2=_ask_password(t("vsvc_repeat_pw",lang),cfg)
        if pw1!=pw2: console.print(f"\n[bold red]{t('vsvc_pw_mismatch',lang)}[/]"); return
        if len(pw1)<4: console.print(f"\n[bold red]{t('vsvc_pw_short',lang)}[/]"); return
        console.print(); res=M.activate_vault(pw1); _print_result(res)
        if res["ok"]: console.print(f"\n[dim]{t('vsvc_folder_info',lang)} [bold]{M.SEC_DIR}[/][/]")
    elif act==t("vsvc_change_pw",lang):
        old=_ask_password(t("vsvc_old_pw",lang),cfg)
        n1=_ask_password(t("vsvc_new_pw",lang),cfg); n2=_ask_password(t("vsvc_repeat_pw",lang),cfg)
        if n1!=n2: console.print(f"\n[bold red]{t('vsvc_pw_mismatch',lang)}[/]"); return
        if len(n1)<4: console.print(f"\n[bold red]{t('vsvc_pw_short',lang)}[/]"); return
        console.print(); _print_result(M.change_vault_password(old,n1))
    elif act==t("vsvc_deactivate",lang):
        console.print(Panel(t("vsvc_deact_warn",lang),box=box.ROUNDED,border_style="red"))
        if not questionary.confirm(t("vsvc_deact_confirm",lang),default=False,style=_q_style(cfg)).ask(): return
        pw=_ask_password(t("vault_pw_prompt",lang),cfg); console.print()
        _print_result(M.deactivate_vault(pw))

def _backup_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('bkp_title',lang)}[/]",box=box.ROUNDED))
    while True:
        act=questionary.select(t("bkp_q",lang),
                               choices=[t(k,lang) for k in ("bkp_do","bkp_list","bkp_restore","bkp_back")],
                               style=_q_style(cfg)).ask()
        if not act or act==t("bkp_back",lang): break
        elif act==t("bkp_do",lang):
            console.print(f"\n[dim]{t('bkp_in_progress',lang)}[/]")
            r=B.backup_notes()
            if r["ok"]:
                console.print(f"[bold green]✓ {r['msg']}[/]\n  [dim]📁 {r['path']}[/]")
                for f in r["files"]: console.print(f"  [dim]  ▸ {f}[/]")
            else:
                console.print(f"[bold red]✗ {r['msg']}[/]")
        elif act==t("bkp_list",lang):
            bkps=B.list_backups()
            if not bkps: console.print(Panel(f"[yellow]{t('bkp_no_backups',lang)}[/]",box=box.ROUNDED)); continue
            table=Table(title=f"[bold {acc}]{t('bkp_list_title',lang)}[/]",box=box.SIMPLE_HEAD,header_style=f"bold {acc}")
            table.add_column("#",justify="right",style="dim",width=4)
            table.add_column(t("bkp_col_name",lang),style=f"{acc}",min_width=18)
            table.add_column(t("bkp_col_count",lang),justify="right",style="dim",width=10)
            table.add_column(t("bkp_col_date",lang),style="dim",width=20)
            for i,bk in enumerate(bkps,1): table.add_row(str(i),bk["name"],str(bk["count"]),bk["date"])
            console.print(table)
        elif act==t("bkp_restore",lang):
            bkps=B.list_backups()
            if not bkps: console.print(f"[yellow]{t('bkp_no_backups',lang)}[/]"); continue
            ch=questionary.select(t("bkp_restore_which_q",lang),
                                  choices=[bk["name"] for bk in bkps]+[t("back",lang)],style=_q_style(cfg)).ask()
            if not ch or ch==t("back",lang): continue
            if questionary.confirm(f"'{ch}' {t('bkp_restore_confirm',lang)}",default=False,style=_q_style(cfg)).ask():
                console.print(f"\n[dim]{t('bkp_restoring',lang)}[/]")
                r=B.restore_backup(ch); _print_result(r)
        console.print()
    return cfg

def _lang_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('lang_title',lang)}[/]",box=box.ROUNDED))
    lang_names={"tr":"🇹🇷 Türkçe","en":"🇬🇧 English","az":"🇦🇿 Azərbaycanca","zh":"🇨🇳 中文"}
    console.print(f"  {t('lang_current',lang)} [bold]{lang_names.get(lang,'?')}[/]\n")
    ch=questionary.select(
        t("lang_q",lang),
        choices=[
            questionary.Choice(title=t("lang_tr",lang),value="tr"),
            questionary.Choice(title=t("lang_en",lang),value="en"),
            questionary.Choice(title=t("lang_az",lang),value="az"),
            questionary.Choice(title=t("lang_zh",lang),value="zh"),
            questionary.Choice(title=t("lang_back",lang),value=None),
        ],
        style=_q_style(cfg)
    ).ask()
    if ch is None: return cfg
    if ch==lang: console.print(f"[dim]{t('lang_same',lang)}[/]"); return cfg
    cfg["lang"]=ch; M.save_config(cfg)
    console.print(f"[bold green]✓ {t('lang_set',ch)}[/]"); return cfg

def _customize_menu(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('cust_title',lang)}[/]",box=box.ROUNDED))
    while True:
        act=questionary.select(t("cust_q",lang),
                               choices=[t(k,lang) for k in
                                        ("cust_font_size","cust_font_style","cust_bg_color","cust_back")],
                               style=_q_style(cfg)).ask()
        if not act or act==t("cust_back",lang): break
        elif act==t("cust_font_size",lang):
            ch=questionary.select(t("cust_fs_q",lang),
                                  choices=[questionary.Choice(title=t("cust_fs_small",lang),value="small"),
                                           questionary.Choice(title=t("cust_fs_normal",lang),value="normal"),
                                           questionary.Choice(title=t("cust_fs_large",lang),value="large")],
                                  style=_q_style(cfg)).ask()
            if ch: cfg["font_size"]=ch; M.save_config(cfg); console.print(f"[bold green]{t('cust_fs_set',lang)} {ch}[/]")
        elif act==t("cust_font_style",lang):
            ch=questionary.select(t("cust_fst_q",lang),
                                  choices=[questionary.Choice(title=t("cust_fst_normal",lang),value="normal"),
                                           questionary.Choice(title=t("cust_fst_bold",lang),value="bold"),
                                           questionary.Choice(title=t("cust_fst_italic",lang),value="italic"),
                                           questionary.Choice(title=t("cust_fst_bold_italic",lang),value="bold_italic")],
                                  style=_q_style(cfg)).ask()
            if ch: cfg["font_style"]=ch; M.save_config(cfg); console.print(f"[bold green]{t('cust_fst_set',lang)} {ch}[/]")
        elif act==t("cust_bg_color",lang):
            bg_choices=[("cust_bg_default","default"),("cust_bg_dark","dark"),("cust_bg_navy","navy"),
                        ("cust_bg_dark_green","dark_green"),("cust_bg_dark_red","dark_red"),
                        ("cust_bg_dark_purple","dark_purple")]
            ch=questionary.select(t("cust_bg_q",lang),
                                  choices=[questionary.Choice(title=t(k,lang),value=v) for k,v in bg_choices],
                                  style=_q_style(cfg)).ask()
            if ch is not None: cfg["bg_color"]=ch; M.save_config(cfg); console.print(f"[bold green]{t('cust_bg_set',lang)} {ch}[/]")
        console.print()
    return cfg

def _show_changelog(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    console.print(Panel(f"[bold {acc}]{t('clog_title',lang)}[/]",box=box.ROUNDED))
    for i,entry in enumerate(M.CHANGELOG):
        is_latest=(i==0)
        label=f"[bold {acc}]{entry['version']}[/]"
        if is_latest: label+=f"  [bold green]← {t('clog_latest',lang)}[/]"
        changes="\n".join(f"  [dim]▸[/] {c}" for c in entry["changes"])
        console.print(Panel(changes,title=f"{label}  [dim]{entry['date']}[/]",
                            border_style=acc if is_latest else "dim",box=box.ROUNDED))
        console.print()

def _reset_menu(cfg):
    lang=_lang(cfg)
    console.print(Panel(t("reset_warn",lang),title=f"[bold red]{t('reset_title',lang)}[/]",
                        box=box.ROUNDED,border_style="red"))
    if not questionary.confirm(t("reset_confirm1",lang),default=False,style=_q_style(cfg)).ask():
        console.print(f"[dim]{t('reset_cancelled',lang)}[/]"); return cfg
    if not questionary.confirm(t("reset_confirm2",lang),default=False,style=_q_style(cfg)).ask():
        console.print(f"[dim]{t('reset_cancelled',lang)}[/]"); return cfg
    console.print(f"\n[bold red]{t('reset_in_progress',lang)}[/]")
    r=M.reset_all()
    for d in r.get("details",[]): console.print(f"  [dim]▸ {d}[/]")
    for e in r.get("errors",[]): console.print(f"  [bold red]✗ {e}[/]")
    console.print()
    col="green" if r["ok"] else "yellow"
    console.print(Panel(f"[bold {col}]{'✓' if r['ok'] else '⚠'} {r['msg']}[/]\n[dim]{t('reset_ok_msg',lang) if r['ok'] else ''}[/]",
                        box=box.ROUNDED,border_style=col))
    return M.DEFAULT_CONFIG.copy()

def show_exit(cfg):
    acc=_accent(cfg); lang=_lang(cfg)
    NSS.stop_service()
    console.print(f"\n[bold {acc}]{t('goodbye',lang)}{cfg['version']}[/]\n")

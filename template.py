"""
NoteX v1.5 - template.py  (10 şablon)
"""

from pathlib import Path
from datetime import datetime

BASE_DIR      = Path("/sdcard/Android/notee")
TEMPLATE_DIR  = BASE_DIR / "template"
TEMPLATE_FILE = TEMPLATE_DIR / "temp.txt"

TEMPLATES = [
    {"id":1,"icon":"✉️","name":"Mektup Şablonu","description":"Kişisel veya yarı resmi mektup",
     "fields":["GONDEREN_AD","GONDEREN_ADRES","TARIH","ALICI_AD","ALICI_ADRES","KONU","ICERIK","KAPANIS_IFADESI"],
     "content":"""\
Gönderen : {{GONDEREN_AD}}
Adres    : {{GONDEREN_ADRES}}
Tarih    : {{TARIH}}

Alıcı    : {{ALICI_AD}}
Adres    : {{ALICI_ADRES}}

Konu     : {{KONU}}

Sayın {{ALICI_AD}},

{{ICERIK}}

{{KAPANIS_IFADESI}},
{{GONDEREN_AD}}
"""},
    {"id":2,"icon":"📄","name":"Resmi Belge Şablonu","description":"Kurum içi / dışı resmi yazışma",
     "fields":["BELGE_NO","TARIH","KURUM_ADI","KONU","SAYISAYI","ICERIK","IMZALAYAN_AD","UNVAN"],
     "content":"""\
════════════════════════════════════════
                RESMİ BELGE
════════════════════════════════════════
Belge No : {{BELGE_NO}}
Tarih    : {{TARIH}}
Kurum    : {{KURUM_ADI}}
Sayı     : {{SAYISAYI}}

KONU     : {{KONU}}
────────────────────────────────────────
{{ICERIK}}

────────────────────────────────────────
İmzalayan: {{IMZALAYAN_AD}}
Ünvan    : {{UNVAN}}
════════════════════════════════════════
"""},
    {"id":3,"icon":"⚠️","name":"Şikayetname Şablonu","description":"Resmi şikayet dilekçesi",
     "fields":["SIKAYETCI_AD","SIKAYETCI_ADRES","SIKAYETCI_TC","TARIH","MUHATAP_KURUM",
               "SIKAYET_KONUSU","OLAY_ACIKLAMASI","TALEP","EKLER"],
     "content":"""\
════════════════════════════════════════
              ŞİKAYETNAME
════════════════════════════════════════
Şikayetçi : {{SIKAYETCI_AD}}
Adres     : {{SIKAYETCI_ADRES}}
T.C. No   : {{SIKAYETCI_TC}}
Tarih     : {{TARIH}}
Muhatap   : {{MUHATAP_KURUM}}
Konu      : {{SIKAYET_KONUSU}}
────────────────────────────────────────
{{OLAY_ACIKLAMASI}}
────────────────────────────────────────
TALEP: {{TALEP}}
Ekler: {{EKLER}}

Saygılarımla,
{{SIKAYETCI_AD}}
════════════════════════════════════════
"""},
    {"id":4,"icon":"✅","name":"To-Do List Şablonu","description":"Görev ve yapılacaklar listesi",
     "fields":["LISTE_BASLIGI","TARIH","ONCELIKLI_GOREV","GOREV_1","GOREV_2","GOREV_3","GOREV_4","GOREV_5","NOTLAR"],
     "content":"""\
════════════════════════════════════════
  📋 {{LISTE_BASLIGI}}   Tarih: {{TARIH}}
════════════════════════════════════════
⭐ ÖNCELİKLİ: [ ] {{ONCELIKLI_GOREV}}

  [ ] {{GOREV_1}}
  [ ] {{GOREV_2}}
  [ ] {{GOREV_3}}
  [ ] {{GOREV_4}}
  [ ] {{GOREV_5}}

NOTLAR:
{{NOTLAR}}
════════════════════════════════════════
"""},
    {"id":5,"icon":"🏛️","name":"Resmi Belge 2 Şablonu","description":"Dilekçe (vatandaş → kurum)",
     "fields":["KURUM_ADI","KURUM_BIRIMINE","TARIH","DILEKCE_KONUSU","DILEKCE_METNI",
               "TALEP_CUMLESI","AD_SOYAD","TC_NO","ADRES","TELEFON"],
     "content":"""\
════════════════════════════════════════
               DİLEKÇE
════════════════════════════════════════
Kurum  : {{KURUM_ADI}}   Birim: {{KURUM_BIRIMINE}}
Tarih  : {{TARIH}}       KONU : {{DILEKCE_KONUSU}}
────────────────────────────────────────
Sayın Yetkili,

{{DILEKCE_METNI}}
{{TALEP_CUMLESI}}

Gereğini saygılarımla arz ederim.

Ad Soyad : {{AD_SOYAD}}   T.C.: {{TC_NO}}
Adres    : {{ADRES}}
Telefon  : {{TELEFON}}
════════════════════════════════════════
"""},
    {"id":6,"icon":"📔","name":"Günlük Şablonu","description":"Kişisel günlük / journal",
     "fields":["TARIH","HAVA_DURUMU","RUH_HALI","BUGUN_NELER_OLDU",
               "DUSUNCELER_DUYGULAR","OGRENDIKLERIM","YARIN_HEDEFIM"],
     "content":"""\
╔══════════════════════════════════════╗
  📔  G Ü N L Ü K  —  {{TARIH}}
╚══════════════════════════════════════╝
🌤  Hava  : {{HAVA_DURUMU}}   😊 Ruh hali: {{RUH_HALI}}

📝 BUGÜN:
{{BUGUN_NELER_OLDU}}

💭 DÜŞÜNCELER:
{{DUSUNCELER_DUYGULAR}}

💡 ÖĞRENDİKLERİM:
{{OGRENDIKLERIM}}

🎯 YARIN HEDEFİM:
{{YARIN_HEDEFIM}}
══════════════════════════════════════
"""},
    {"id":7,"icon":"📊","name":"Rapor Şablonu","description":"Genel amaçlı rapor / analiz",
     "fields":["RAPOR_BASLIGI","HAZIRLAYAN","TARIH","BIRIM","OZET","GIRIS","BULGULAR","ANALIZ","SONUC_ONERILER","EKLER"],
     "content":"""\
════════════════════════════════════════════════
  📊  {{RAPOR_BASLIGI}}
  Hazırlayan: {{HAZIRLAYAN}}  |  Birim: {{BIRIM}}  |  Tarih: {{TARIH}}
════════════════════════════════════════════════
1. YÖNETİCİ ÖZETİ
{{OZET}}

2. GİRİŞ
{{GIRIS}}

3. BULGULAR
{{BULGULAR}}

4. ANALİZ
{{ANALIZ}}

5. SONUÇ VE ÖNERİLER
{{SONUC_ONERILER}}

6. EKLER
{{EKLER}}
════════════════════════════════════════════════
"""},
    {"id":8,"icon":"📜","name":"Dilekçe Şablonu","description":"Kapsamlı resmi dilekçe (hukuki)",
     "fields":["MAHKEME_VEYA_KURUM","TARIH","DAVACI_AD","DAVACI_TC","DAVACI_ADRES","DAVACI_TELEFON",
               "DILEKCE_KONUSU","OLAYLAR","HUKUKI_DAYANAK","TALEPLER","BELGELER","AD_SOYAD"],
     "content":"""\
════════════════════════════════════════════════
              📜  D İ L E K Ç E
════════════════════════════════════════════════
                              {{MAHKEME_VEYA_KURUM}}
                              Tarih: {{TARIH}}

{{DAVACI_AD}}  |  TC: {{DAVACI_TC}}
{{DAVACI_ADRES}}  |  Tel: {{DAVACI_TELEFON}}

KONU: {{DILEKCE_KONUSU}}
────────────────────────────────────────────────
OLAYLAR:
{{OLAYLAR}}

HUKUKİ DAYANAK:
{{HUKUKI_DAYANAK}}

TALEPLER:
{{TALEPLER}}

BELGELER:
{{BELGELER}}

Yukarıda arz ettiğim hususların kabulünü saygılarımla arz ederim.
                                        {{AD_SOYAD}}
════════════════════════════════════════════════
"""},
    # ── 9 Gelir-Gider (YENİ) ─────────────────────────────────────────────────
    {"id":9,"icon":"💰","name":"Gelir-Gider Şablonu","description":"Aylık gelir ve gider takip cetveli",
     "fields":["AY_YIL","TOPLAM_GELIR",
               "GELIR_1_AD","GELIR_1_TUTAR",
               "GELIR_2_AD","GELIR_2_TUTAR",
               "GELIR_3_AD","GELIR_3_TUTAR",
               "TOPLAM_GIDER",
               "GIDER_1_AD","GIDER_1_TUTAR",
               "GIDER_2_AD","GIDER_2_TUTAR",
               "GIDER_3_AD","GIDER_3_TUTAR",
               "GIDER_4_AD","GIDER_4_TUTAR",
               "GIDER_5_AD","GIDER_5_TUTAR",
               "TASARRUF","NOTLAR"],
     "content":"""\
╔══════════════════════════════════════════════╗
  💰  GELİR - GİDER CETVELİ
  Dönem: {{AY_YIL}}
╚══════════════════════════════════════════════╝

┌─────────────────────────────────────────────┐
│  GELİRLER                                   │
├─────────────────────────────────────────────┤
│  {{GELIR_1_AD:<28}} {{GELIR_1_TUTAR:>10}} ₺ │
│  {{GELIR_2_AD:<28}} {{GELIR_2_TUTAR:>10}} ₺ │
│  {{GELIR_3_AD:<28}} {{GELIR_3_TUTAR:>10}} ₺ │
├─────────────────────────────────────────────┤
│  TOPLAM GELİR                  {{TOPLAM_GELIR:>9}} ₺ │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  GİDERLER                                   │
├─────────────────────────────────────────────┤
│  {{GIDER_1_AD:<28}} {{GIDER_1_TUTAR:>10}} ₺ │
│  {{GIDER_2_AD:<28}} {{GIDER_2_TUTAR:>10}} ₺ │
│  {{GIDER_3_AD:<28}} {{GIDER_3_TUTAR:>10}} ₺ │
│  {{GIDER_4_AD:<28}} {{GIDER_4_TUTAR:>10}} ₺ │
│  {{GIDER_5_AD:<28}} {{GIDER_5_TUTAR:>10}} ₺ │
├─────────────────────────────────────────────┤
│  TOPLAM GİDER                  {{TOPLAM_GIDER:>9}} ₺ │
└─────────────────────────────────────────────┘

  💵 NET TASARRUF / AÇIK: {{TASARRUF}} ₺

────────────────────────────────────────────────
NOTLAR:
{{NOTLAR}}
════════════════════════════════════════════════
"""},
    # ── 10 CV (YENİ) ──────────────────────────────────────────────────────────
    {"id":10,"icon":"👤","name":"CV Şablonu","description":"Kişisel özgeçmiş / Curriculum Vitae",
     "fields":["AD_SOYAD","DOGUM_TARIHI","TELEFON","EMAIL","ADRES","LINKEDIN",
               "PROFIL_OZETI",
               "EGITIM_1","EGITIM_1_TARIH","EGITIM_1_BOLUM",
               "EGITIM_2","EGITIM_2_TARIH","EGITIM_2_BOLUM",
               "IS_1_SIRKET","IS_1_UNVAN","IS_1_TARIH","IS_1_ACIKLAMA",
               "IS_2_SIRKET","IS_2_UNVAN","IS_2_TARIH","IS_2_ACIKLAMA",
               "BECERILER","DILLER","SERTIFIKALAR","HOBILER","REFERANSLAR"],
     "content":"""\
╔══════════════════════════════════════════════════════╗
  👤  C U R R I C U L U M   V I T A E
╚══════════════════════════════════════════════════════╝

  {{AD_SOYAD}}
  ─────────────────────────────────────────────────────
  📅 {{DOGUM_TARIHI}}     📞 {{TELEFON}}
  📧 {{EMAIL}}
  📍 {{ADRES}}
  🔗 {{LINKEDIN}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PROFİL ÖZETİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{PROFIL_OZETI}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EĞİTİM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎓 {{EGITIM_1}}  ({{EGITIM_1_TARIH}})
     {{EGITIM_1_BOLUM}}

  🎓 {{EGITIM_2}}  ({{EGITIM_2_TARIH}})
     {{EGITIM_2_BOLUM}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  İŞ DENEYİMİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🏢 {{IS_1_SIRKET}}  —  {{IS_1_UNVAN}}  ({{IS_1_TARIH}})
     {{IS_1_ACIKLAMA}}

  🏢 {{IS_2_SIRKET}}  —  {{IS_2_UNVAN}}  ({{IS_2_TARIH}})
     {{IS_2_ACIKLAMA}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BECERİLER & DİLLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Beceriler  : {{BECERILER}}
  Diller     : {{DILLER}}
  Sertifikalar: {{SERTIFIKALAR}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOBİLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {{HOBILER}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REFERANSLAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {{REFERANSLAR}}
══════════════════════════════════════════════════════
"""},
]

def ensure_template_dir():
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

def get_template_by_id(tid: int):
    for t in TEMPLATES:
        if t["id"] == tid: return t
    return None

def get_all_templates() -> list:
    return TEMPLATES

def fill_template(template: dict, values: dict) -> str:
    content = template["content"]
    for field, value in values.items():
        content = content.replace(f"{{{{{field}}}}}", value if value.strip() else f"[{field}]")
    return content

def save_template_file(content: str):
    ensure_template_dir()
    try:
        existing = TEMPLATE_FILE.read_text(encoding="utf-8") if TEMPLATE_FILE.exists() else ""
        sep = f"\n{'='*50}\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n{'='*50}\n"
        TEMPLATE_FILE.write_text(existing + sep + content + "\n", encoding="utf-8")
        return {"ok": True, "msg": f"Şablon kaydedildi: {TEMPLATE_FILE}"}
    except Exception as e:
        return {"ok": False, "msg": f"Kayıt hatası: {e}"}

def get_today() -> str:
    months = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
              "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
    n = datetime.now()
    return f"{n.day} {months[n.month]} {n.year}"

# -*- coding: utf-8 -*-
"""
BOT TELEGRAM AL-MUNTALAQ (المنطلق)
Titik Tolak Dakwah, Tarbiyah & Fiqh Harakah Islamiyah
Karya: As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)
"""

import os
import sys
import json
import time
import re
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Bot Al-Muntalaq Telegram beroperasi 24/7.".encode("utf-8"))

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 0))
    if port:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"Health-check HTTP Server aktif pada port {port} (Sedia untuk Cloud Hosting).")

# Pastikan konsol Windows menyokong emoji dan teks Arab (UTF-8)
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Fail Konfigurasi & Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DATA_PATH = os.path.join(BASE_DIR, "almuntalaq_data.json")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_MUNTALAQ", "")

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if not BOT_TOKEN and cfg.get("bot_token") and cfg.get("bot_token") != "ISI_TOKEN_BOT_ALMUNTALAQ_DI_SINI":
                BOT_TOKEN = cfg.get("bot_token")
    except Exception as e:
        print(f"Ralat membaca config.json: {e}")

# Muat Pangkalan Data Al-Muntalaq
if not os.path.exists(DATA_PATH):
    print(f"Ralat: Fail pangkalan data {DATA_PATH} tidak dijumpai!")
    sys.exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    ALMUNTALAQ_DATA = json.load(f)

CHAPTERS = ALMUNTALAQ_DATA.get("chapters", [])
print(f"Berjaya memuatkan {len(CHAPTERS)} bab Al-Muntalaq.")

# Muat Mutiara Hikmah Al-Muntalaq
QUOTES_PATH = os.path.join(BASE_DIR, "almuntalaq_quotes.json")
HIKMAH_DATA = []
if os.path.exists(QUOTES_PATH):
    try:
        with open(QUOTES_PATH, "r", encoding="utf-8") as f:
            HIKMAH_DATA = json.load(f)
        print(f"Berjaya memuatkan {len(HIKMAH_DATA)} mutiara hikmah Al-Muntalaq.")
    except Exception as e:
        print(f"Ralat membaca almuntalaq_quotes.json: {e}")

# Sesi HTTP
session = requests.Session()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Penyimpanan Sesi Pengguna Sementara
USER_STATE = {} # { chat_id: { 'layer': 'layer1' } }
USER_SEARCH = {} # { chat_id: 'kata_carian' }

def get_user_layer(chat_id):
    if chat_id not in USER_STATE:
        USER_STATE[chat_id] = {'layer': 'layer1'}
    return USER_STATE[chat_id].get('layer', 'layer1')

def set_user_layer(chat_id, layer):
    if chat_id not in USER_STATE:
        USER_STATE[chat_id] = {}
    USER_STATE[chat_id]['layer'] = layer

def send_api(method, payload):
    url = f"{API_BASE}/{method}"
    try:
        res = session.post(url, json=payload, timeout=30)
        data = res.json()
        if not data.get("ok"):
            print(f"Ralat Telegram ({method}): {data.get('description')}")
        return data
    except Exception as e:
        print(f"Ralat API Telegram ({method}): {e}")
        return None

SUP_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

def clean_footnote_tags(text):
    if not text:
        return ""
    # Tukar <sup class="fn-ref" data-fn-id="3" ...>[3]</sup> -> ⁽³⁾
    text = re.sub(
        r'<sup[^>]*data-fn-id=[\'"]?(\d+)[\'"]?[^>]*>.*?</sup>',
        lambda m: f"⁽{m.group(1).translate(SUP_DIGITS)}⁾",
        text,
        flags=re.IGNORECASE
    )
    # Buang sebarang tag <sup> lain jika ada
    text = re.sub(r'</?sup[^>]*>', '', text, flags=re.IGNORECASE)
    return text

def md_to_telegram_html(text):
    if not text:
        return ""
    # Bersihkan tag HTML nota kaki terlebih dahulu sebelum escape entiti
    text = clean_footnote_tags(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*([^\*\n]+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_\n]+?)_(?!_)', r'<i>\1</i>', text)
    text = re.sub(r'^[ \t]*[\*\-][ \t]+', '• ', text, flags=re.MULTILINE)
    return text


def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = send_api("sendMessage", payload)
    if (not res or not res.get("ok")) and parse_mode:
        payload["parse_mode"] = None
        res = send_api("sendMessage", payload)
    return res

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = send_api("editMessageText", payload)
    if res and not res.get("ok"):
        desc = res.get("description", "")
        if "message is not modified" in desc:
            return res
        if parse_mode and "can't parse entities" in desc:
            payload["parse_mode"] = None
            res = send_api("editMessageText", payload)
    return res

def answer_callback_query(callback_query_id, text=""):
    payload = {
        "callback_query_id": callback_query_id,
        "text": text
    }
    return send_api("answerCallbackQuery", payload)

# ================= BAHAGIAN KANDUNGAN IKUT SUBTOPIK =================

def get_chapter_sections(ch_idx):
    """Memecahkan perenggan bab mengikut sub-tajuk (heading2)."""
    ch = CHAPTERS[ch_idx]
    paras = ch.get("paragraphs", [])
    sections = []
    current_title = "Pendahuluan Bab"
    current_paras = []
    
    for p in paras:
        if p.get("type") == "heading2":
            if current_paras:
                sections.append({"title": current_title, "paras": current_paras})
                current_paras = []
            current_title = p.get("text", "Sub-Tajuk")
        else:
            current_paras.append(p)
            
    if current_paras:
        sections.append({"title": current_title, "paras": current_paras})
        
    if not sections:
        sections.append({"title": ch.get("title", "Kandungan"), "paras": paras})
        
    return sections

# ================= MENU GENERATORS =================

def get_main_menu_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🏵️ Senarai Bab (18 Bab)", "callback_data": "menu_chapters"},
                {"text": "⚡ Ringkasan Eksklusif", "callback_data": "menu_summaries"}
            ],
            [
                {"text": "🔍 Carian Topik & Dalil", "callback_data": "menu_search_info"},
                {"text": "💎 Mutiara Hikmah Dakwah", "callback_data": "hikmah_random"}
            ],
            [
                {"text": "🌿 Buka Web PWA Al-Muntalaq 🌐", "url": "https://najsha97-rgb.github.io/al-muntalaq-pwa/"}
            ],
            [
                {"text": "ℹ️ Info Kitab & Syeikh", "callback_data": "menu_about"}
            ]
        ]
    }

def get_chapters_keyboard(mode="full"):
    buttons = []
    # Mukadimah
    prefix = "sumch_" if mode == "summary" else "ch_"
    buttons.append([{"text": "📌 Mukadimah: Duduk Sebentar... Beriman Sejenak", "callback_data": f"{prefix}0"}])
    
    # Bab 1 hingga 17 (2 butang per baris)
    row = []
    for idx in range(1, len(CHAPTERS)):
        ch = CHAPTERS[idx]
        title_clean = ch['title'].replace("'", "")
        title_short = f"🏵️ Bab {idx}: {title_clean}"
        if len(title_short) > 25:
            title_short = title_short[:23] + ".."
        row.append({"text": title_short, "callback_data": f"{prefix}{idx}"})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([{"text": "⬅️ Kembali ke Menu Utama", "callback_data": "menu_main"}])
    return {"inline_keyboard": buttons}

def get_subtopics_keyboard(ch_idx):
    ch = CHAPTERS[ch_idx]
    sections = get_chapter_sections(ch_idx)
    buttons = []
    
    # Butang Ringkasan Bab
    buttons.append([{"text": "⚡ Baca Ringkasan Padat Bab Ini", "callback_data": f"sumch_{ch_idx}"}])
    
    for s_idx, sec in enumerate(sections):
        title_btn = f"🌱 {s_idx+1}. {sec['title']}"
        if len(title_btn) > 36:
            title_btn = title_btn[:34] + ".."
        buttons.append([{"text": title_btn, "callback_data": f"sub_{ch_idx}_{s_idx}_0"}])
        
    buttons.append([
        {"text": "⬅️ Senarai Bab", "callback_data": "menu_chapters"},
        {"text": "🏠 Utama", "callback_data": "menu_main"}
    ])
    return {"inline_keyboard": buttons}

def format_subtopic_text(ch_idx, s_idx, page=0, user_search_query=None):
    ch = CHAPTERS[ch_idx]
    sections = get_chapter_sections(ch_idx)
    if s_idx >= len(sections):
        s_idx = 0
    sec = sections[s_idx]
    
    header = (
        f"🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n"
        f"🌿 <b>AL-MUNTALAQ (الْمُنْطَلَق)</b>\n"
        f"📚 <b>{ch['number']}: {ch['title']}</b>\n"
        f"📑 <b>Sub-Tajuk: {sec['title']}</b>\n"
        f"🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n\n"
    )
    
    paras = sec.get("paras", [])
    if not paras:
        return header + "<i>Tiada teks dalam bahagian ini.</i>", 1
        
    # Render dan Paginasi
    rendered_paras = []
    for p in paras:
        ptype = p.get("type", "text")
        ptext = md_to_telegram_html(p.get("text", ""))
        if ptype == "quran":
            src = f" <i>({md_to_telegram_html(p.get('source',''))})</i>" if p.get('source') else ""
            rendered_paras.append(f"<blockquote>📖 <b>[Ayat Al-Quran]</b>\n<i>« {ptext} »</i>{src}</blockquote>")
        elif ptype == "quote":
            rendered_paras.append(f"<blockquote>❝ <i>{ptext}</i> ❞</blockquote>")
        else:
            if user_search_query and user_search_query.lower() in ptext.lower():
                pattern = re.compile(re.escape(user_search_query), re.IGNORECASE)
                ptext = pattern.sub(lambda m: f"<b><u>{m.group(0)}</u></b>", ptext)
            rendered_paras.append(ptext)
            
    # Himpun mengikut had saiz skrin (~1400 aksara)
    pages_content = []
    cur_page = []
    cur_len = 0
    
    for rp in rendered_paras:
        cur_page.append(rp)
        cur_len += len(rp)
        if cur_len > 1300:
            pages_content.append("\n\n".join(cur_page))
            cur_page = []
            cur_len = 0
            
    if cur_page:
        pages_content.append("\n\n".join(cur_page))
        
    total_pages = len(pages_content)
    page = max(0, min(page, total_pages - 1))
    body = pages_content[page] if pages_content else "<i>Tiada teks.</i>"
    
    page_footer = f"\n\n🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n📄 <i>Halaman {page+1} daripada {total_pages}</i>"
    highlight_note = f"🔍 <i>[Carian Kata Kunci: \"{user_search_query}\"]</i>\n\n" if user_search_query else ""
    return header + highlight_note + body + page_footer, total_pages

def format_summary_text(ch_idx, page=0, user_search_query=None):
    ch = CHAPTERS[ch_idx]
    raw_sum = ch.get("summary", "")
    
    header = (
        f"⚡ ━━━━━━━━━━━━━━━━━━━ 🏵️\n"
        f"💎 <b>RINGKASAN EKSKLUSIF & ANALISIS TARBAWI</b>\n"
        f"📚 <b>{ch['number']}: {ch['title']}</b>\n"
        f"⚡ ━━━━━━━━━━━━━━━━━━━ 🏵️\n\n"
    )
    
    if not raw_sum:
        return header + "<i>Tiada ringkasan bagi bab ini.</i>", 1
        
    # Bahagikan ringkasan jika melebihi had Telegram (~3500 aksara)
    paras = raw_sum.split("\n\n")
    pages = []
    cur_page = []
    cur_len = 0
    
    for p in paras:
        p_clean = md_to_telegram_html(p.strip())
        if user_search_query and user_search_query.lower() in p_clean.lower():
            pattern = re.compile(re.escape(user_search_query), re.IGNORECASE)
            p_clean = pattern.sub(lambda m: f"<b><u>{m.group(0)}</u></b>", p_clean)
        cur_page.append(p_clean)
        cur_len += len(p_clean)
        if cur_len > 2200:
            pages.append("\n\n".join(cur_page))
            cur_page = []
            cur_len = 0
            
    if cur_page:
        pages.append("\n\n".join(cur_page))
        
    total_pages = len(pages)
    page = max(0, min(page, total_pages - 1))
    body = pages[page]
    page_footer = f"\n\n───────────────\n📄 <i>Bahagian {page+1} daripada {total_pages}</i>" if total_pages > 1 else ""
    highlight_note = f"🔍 <i>[Carian Kata Kunci: \"{user_search_query}\"]</i>\n\n" if user_search_query else ""
    return header + highlight_note + body + page_footer, total_pages

# ================= CARIAN PINTAR =================

def search_almuntalaq(keyword):
    kw = keyword.strip().lower()
    if len(kw) < 2:
        return []
        
    results = []
    for ch_idx, ch in enumerate(CHAPTERS):
        # Cari dalam tajuk bab
        if kw in ch['title'].lower():
            results.append({
                "type": "bab",
                "ch_idx": ch_idx,
                "title": f"{ch['number']}: {ch['title']}",
                "snippet": f"Tajuk Bab: {ch['title']}"
            })
            
        # Cari dalam sub-tajuk & perenggan
        sections = get_chapter_sections(ch_idx)
        for s_idx, sec in enumerate(sections):
            if kw in sec['title'].lower():
                results.append({
                    "type": "subtopic",
                    "ch_idx": ch_idx,
                    "s_idx": s_idx,
                    "title": f"{ch['number']} ➔ {sec['title']}",
                    "snippet": f"Sub-Tajuk: {sec['title']}"
                })
                continue
                
            # Cari dalam perenggan
            for p in sec.get("paras", []):
                ptext = clean_footnote_tags(p.get("text", ""))
                if kw in ptext.lower():
                    # Ambil snippet sekeliling perkataan
                    idx_kw = ptext.lower().find(kw)
                    start = max(0, idx_kw - 40)
                    end = min(len(ptext), idx_kw + 100)
                    snippet = ptext[start:end].replace("\n", " ").strip()
                    results.append({
                        "type": "subtopic",
                        "ch_idx": ch_idx,
                        "s_idx": s_idx,
                        "title": f"{ch['number']} ➔ {sec['title']}",
                        "snippet": f"...{snippet}..."
                    })
                    break # satu snippet per sub-tajuk sudah memadai
                    
        # Cari dalam ringkasan
        raw_sum = clean_footnote_tags(ch.get("summary", ""))
        if kw in raw_sum.lower():
            idx_kw = raw_sum.lower().find(kw)
            start = max(0, idx_kw - 40)
            end = min(len(raw_sum), idx_kw + 100)
            snippet = raw_sum[start:end].replace("\n", " ").strip()
            results.append({
                "type": "summary",
                "ch_idx": ch_idx,
                "title": f"⚡ Ringkasan: {ch['number']}",
                "snippet": f"...{snippet}..."
            })
            
        if len(results) >= 15:
            break
            
    return results

# ================= HIKMAH RAWAK =================

def get_random_hikmah_message_and_keyboard():
    if HIKMAH_DATA:
        item = random.choice(HIKMAH_DATA)
        quote_text = md_to_telegram_html(item.get("quote", ""))
        text = (
            f"🟢 ━━━━━━━━━━━━━━━━━━━ ⚜️\n"
            f"💎 <b>MUTIARA HIKMAH DAKWAH</b> ⚜️\n"
            f"🟢 ━━━━━━━━━━━━━━━━━━━ ⚜️\n\n"
            f"👤 <b>{item.get('speaker', 'Tokoh Dakwah')}</b>\n\n"
            f"<blockquote><i>{quote_text}</i></blockquote>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <b>Sumber:</b> {item.get('ch_num', '')} - {item.get('ch_title', '')}\n"
            f"🌿 <i>Kitab Al-Muntalaq — Syeikh Muhammad Ahmad Ar-Rasyid</i>\n"
            f"🌐 https://najsha97-rgb.github.io/al-muntalaq-pwa/"
        )
        ch_idx = item.get("ch_idx", 0)
        kb = {
            "inline_keyboard": [
                [{"text": f"📖 Baca: {item.get('ch_num', 'Bab Ini')}", "callback_data": f"ch_{ch_idx}"}],
                [{"text": "🎲 Mutiara Lain (Rawak)", "callback_data": "hikmah_random"}],
                [{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]
            ]
        }
        return text, kb
    else:
        quotes = []
        for ch in CHAPTERS:
            s = ch.get("summary", "")
            if "💎 Mutiara" in s:
                parts = s.split("💎 Mutiara")
                if len(parts) > 1:
                    sub = parts[1].split("⚔️ Tambahan")[0]
                    lines = [l.strip() for l in sub.split("\n") if l.strip().startswith("•")]
                    for l in lines:
                        quotes.append((ch['number'], ch['title'], l))
                        
        if not quotes:
            return "<i>Mutiara hikmah sedang dikemaskini.</i>", {"inline_keyboard": [[{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]]}
            
        num, title, quote = random.choice(quotes)
        quote_clean = md_to_telegram_html(quote)
        
        text = (
            f"🟢 ━━━━━━━━━━━━━━━━━━━ ⚜️\n"
            f"💎 <b>MUTIARA HIKMAH DAKWAH</b> ⚜️\n"
            f"🟢 ━━━━━━━━━━━━━━━━━━━ ⚜️\n\n"
            f"<blockquote>{quote_clean}</blockquote>\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <i>Sumber: {num} - {title}</i>\n"
            f"🌿 <i>Kitab Al-Muntalaq — Syeikh Muhammad Ahmad Ar-Rasyid</i>\n"
            f"🌐 https://najsha97-rgb.github.io/al-muntalaq-pwa/"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🎲 Mutiara Lain (Rawak)", "callback_data": "hikmah_random"}],
                [{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]
            ]
        }
        return text, kb

# ================= PENGENDALI MESEJ & CALLBACK =================

def handle_message(msg):
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()
    
    if not text:
        return
        
    if text.startswith("/start") or text.startswith("/menu"):
        USER_SEARCH.pop(chat_id, None)
        welcome_text = (
            f"🟢 ━━━━━━━━━━━━━━━━━━━ ⚜️\n"
            f"🌿 <b>AL-MUNTALAQ (الْمُنْطَلَق)</b> 🌿\n"
            f"<i>Titik Tolak Dakwah, Tarbiyah & Fiqh Harakah</i>\n"
            f"🟢 ━━━━━━━━━━━━━━━━━━━ ⚜️\n\n"
            f"<blockquote>📖 <b>Pengarang:</b> As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)\n"
            f"✨ <i>“Sentiasa memperbaharui iman, memurnikan niat, dan menyemarakkan himmah perjuangan.”</i></blockquote>\n\n"
            f"📚 <b>Struktur Ilmiah Kitab:</b>\n"
            f"• 🟢 <code>18 Bab Penuh</code> (Mukadimah + 17 Bab Utama)\n"
            f"• 🌿 <code>92 Sub-Tajuk</code> berstruktur rapi\n"
            f"• 📝 <code>246 Nota Kaki</code> ilmiah\n"
            f"• ⚡ <code>Ringkasan Eksklusif</code> & Dimensi Fiqh Haraki\n"
            f"• 💎 <code>Mutiara Hikmah</code> generasi salaf & pejuang dakwah\n\n"
            f"🌐 <b>Web PWA (Tema Zamrud & Emas):</b>\n"
            f"https://najsha97-rgb.github.io/al-muntalaq-pwa/\n\n"
            f"<i>Sila pilih menu di bawah untuk memulakan bacaan:</i>"
        )
        send_message(chat_id, welcome_text, get_main_menu_keyboard())
        return

    # Carian / Semakan Nota Kaki Terus: /nota 3 atau /fn 3 atau /nota_3 atau /fn_3
    m_fn = re.match(r"^/(?:nota|fn)[_\s]?(\d+)$", text, re.IGNORECASE)
    if m_fn:
        target_id = int(m_fn.group(1))
        found_fn = None
        found_ch = None
        for ch in CHAPTERS:
            for fn in ch.get("footnotes", []):
                if fn.get("id") == target_id:
                    found_fn = fn
                    found_ch = ch
                    break
            if found_fn:
                break
        
        if found_fn:
            fn_reply = (
                f"📝 ━━━━━━━━━━━━━━━━━━━ ⚜️\n"
                f"🌿 <b>NOTA KAKI [{target_id}]</b>\n"
                f"📚 <i>{found_ch['number']}: {found_ch['title']}</i>\n"
                f"📝 ━━━━━━━━━━━━━━━━━━━ ⚜️\n\n"
                f"{md_to_telegram_html(found_fn.get('text', ''))}"
            )
        else:
            fn_reply = f"⚠️ Nota kaki nombor <b>[{target_id}]</b> tidak dijumpai dalam rekod."
            
        send_message(chat_id, fn_reply, {"inline_keyboard": [[{"text": "🏠 Utama", "callback_data": "menu_main"}]]})
        return

    if text.startswith("/cari"):
        query = text[5:].strip()
        USER_SEARCH[chat_id] = query
        if not query:
            send_message(chat_id, "ℹ️ <i>Sila masukkan kata carian. Contoh:</i>\n<code>/cari hawa nafsu</code>\n<code>/cari amal jamaie</code>\n<code>/cari gerhana</code>")
            return
            
        results = search_almuntalaq(query)
        if not results:
            send_message(chat_id, f"🔍 Tiada hasil ditemui untuk kata kunci: <b>\"{md_to_telegram_html(query)}\"</b>.\nCuba perkataan lain.")
            return
            
        buttons = []
        msg_out = f"🔍 <b>Hasil Carian untuk: \"{md_to_telegram_html(query)}\"</b>\n<i>Ditemui {len(results)} topik berkaitan:</i>\n\n"
        
        for idx, r in enumerate(results[:8]):
            msg_out += f"<b>{idx+1}. {r['title']}</b>\n<i>{md_to_telegram_html(r['snippet'])}</i>\n\n"
            if r['type'] == "subtopic":
                buttons.append([{"text": f"📖 Baca: {r['title'][:30]}", "callback_data": f"sub_{r['ch_idx']}_{r['s_idx']}_0"}])
            elif r['type'] == "summary":
                buttons.append([{"text": f"⚡ Buka Ringkasan {r['title'][:25]}", "callback_data": f"sumch_{r['ch_idx']}"}])
            else:
                buttons.append([{"text": f"📖 Buka: {r['title'][:30]}", "callback_data": f"ch_{r['ch_idx']}"}])
                
        buttons.append([{"text": "🏠 Menu Utama", "callback_data": "menu_main"}])
        send_message(chat_id, msg_out, {"inline_keyboard": buttons})
        return

    if text.startswith("/hikmah"):
        h_text, btns = get_random_hikmah_message_and_keyboard()
        send_message(chat_id, h_text, btns)
        return

    # Teks biasa dianggap sebagai carian langsung jika lebih 2 aksara
    if len(text) >= 3 and not text.startswith("/"):
        results = search_almuntalaq(text)
        if results:
            USER_SEARCH[chat_id] = text
            buttons = []
            msg_out = f"🔍 <b>Hasil Carian: \"{md_to_telegram_html(text)}\"</b>\n\n"
            for idx, r in enumerate(results[:6]):
                msg_out += f"<b>{idx+1}. {r['title']}</b>\n<i>{md_to_telegram_html(r['snippet'])}</i>\n\n"
                if r['type'] == "subtopic":
                    buttons.append([{"text": f"📖 {r['title'][:32]}", "callback_data": f"sub_{r['ch_idx']}_{r['s_idx']}_0"}])
                else:
                    buttons.append([{"text": f"⚡ {r['title'][:32]}", "callback_data": f"sumch_{r['ch_idx']}"}])
            buttons.append([{"text": "🏠 Menu Utama", "callback_data": "menu_main"}])
            send_message(chat_id, msg_out, {"inline_keyboard": buttons})
            return

    # Default fallback
    send_message(chat_id, "Sila gunakan arahan /start untuk membuka Menu Utama atau /cari untuk membuat carian.")

def handle_callback(cb):
    cb_id = cb.get("id")
    from_user = cb.get("from", {})
    chat_id = from_user.get("id")
    msg = cb.get("message", {})
    msg_id = msg.get("message_id")
    data = cb.get("data", "")
    
    answer_callback_query(cb_id)
    
    if data == "menu_main":
        USER_SEARCH.pop(chat_id, None)
        welcome_text = (
            f"🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n"
            f"🌿 <b>AL-MUNTALAQ (الْمُنْطَلَق)</b> 🌿\n"
            f"<i>Titik Tolak Dakwah, Tarbiyah & Fiqh Harakah</i>\n"
            f"🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n\n"
            f"<blockquote>📖 <b>Pengarang:</b> As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)\n"
            f"✨ <i>“Sentiasa memperbaharui iman, memurnikan niat, dan menyemarakkan himmah perjuangan.”</i></blockquote>\n\n"
            f"📚 <b>Struktur Ilmiah Kitab:</b>\n"
            f"• 🟢 <code>18 Bab Penuh</code> (Mukadimah + 17 Bab Utama)\n"
            f"• 🌿 <code>92 Sub-Tajuk</code> berstruktur rapi\n"
            f"• 📝 <code>246 Nota Kaki</code> ilmiah\n"
            f"• ⚡ <code>Ringkasan Eksklusif</code> & Dimensi Fiqh Haraki\n"
            f"• 💎 <code>Mutiara Hikmah</code> tokoh dakwah & salaf\n\n"
            f"🌐 <b>Web PWA (Tema Zamrud & Emas):</b>\n"
            f"https://najsha97-rgb.github.io/al-muntalaq-pwa/\n\n"
            f"<i>Sila pilih menu di bawah untuk memulakan bacaan:</i>"
        )
        edit_message(chat_id, msg_id, welcome_text, get_main_menu_keyboard())
        return

    if data == "menu_chapters":
        txt = "🏵️ <b>SENARAI BAB KITAB AL-MUNTALAQ:</b>\nSila pilih bab untuk melihat sub-tajuk dan teks penuh:"
        edit_message(chat_id, msg_id, txt, get_chapters_keyboard(mode="full"))
        return

    if data == "menu_summaries":
        txt = "⚡ <b>RINGKASAN PADAT & FIQH HARAKI AL-MUNTALAQ:</b>\nPilih bab untuk membaca ringkasan berstruktur berserta nukilan emas salafussoleh:"
        edit_message(chat_id, msg_id, txt, get_chapters_keyboard(mode="summary"))
        return

    if data == "menu_search_info":
        txt = (
            f"🔍 ━━━━━━━━━━━━━━━━━━━ 🏵️\n"
            f"🌿 <b>PANDUAN CARIAN PANTAS AL-MUNTALAQ</b>\n"
            f"🔍 ━━━━━━━━━━━━━━━━━━━ 🏵️\n\n"
            f"Anda boleh membuat carian pantas terus dalam ruangan sembang ini dengan menaip:\n\n"
            f"👉 <code>/cari hawa nafsu</code>\n"
            f"👉 <code>/cari gerhana</code>\n"
            f"👉 <code>/cari amal jamaie</code>\n"
            f"👉 <code>/cari tanzim</code>\n"
            f"👉 <code>/cari banna</code>\n\n"
            f"Bot akan mencari secara menyeluruh merangkumi tajuk bab, sub-tajuk, ayat quran dan ringkasan."
        )
        btns = {"inline_keyboard": [[{"text": "⬅️ Kembali ke Menu Utama", "callback_data": "menu_main"}]]}
        edit_message(chat_id, msg_id, txt, btns)
        return

    if data == "hikmah_random":
        h_text, btns = get_random_hikmah_message_and_keyboard()
        edit_message(chat_id, msg_id, h_text, btns)
        return

    if data == "menu_about":
        about_text = (
            f"ℹ️ ━━━━━━━━━━━━━━━━━━━ 🏵️\n"
            f"🌿 <b>MENGENAI KITAB AL-MUNTALAQ (المنطلق)</b> 🌿\n"
            f"ℹ️ ━━━━━━━━━━━━━━━━━━━ 🏵️\n\n"
            f"<blockquote><b>Pengarang:</b> As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)\n"
            f"<b>Genre:</b> Fiqh Dakwah, Tarbiyah & Manhaj Harakah Islamiyah\n"
            f"<b>Struktur:</b> 18 Bab (Mukadimah + 17 Bab), 92 Sub-Tajuk, 246 Nota Kaki</blockquote>\n\n"
            f"Buku <i>al-Muntalaq</i> merupakan siri pertama dalam siri-siri fiqh dakwah dan harakah Islamiyah dimulai dengan <i>al-Muntalaq</i> (mengenali tabiatnya), <i>al-‘Awa’iq</i> (halangan dakwah), <i>al-Raqa’iq</i> (kelembutan jiwa), <i>al-Bawariq</i> (lintasan panduan), dan seterusnya <i>al-Masar</i> (strategi, polisi, dan fiqh perancangan harakah).\n\n"
            f"🌐 <b>Aplikasi Web PWA (Tema Zamrud & Emas):</b>\n"
            f"https://najsha97-rgb.github.io/al-muntalaq-pwa/"
        )
        btns = {
            "inline_keyboard": [
                [{"text": "🟢 Layari Web PWA Al-Muntalaq 🌐", "url": "https://najsha97-rgb.github.io/al-muntalaq-pwa/"}],
                [{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]
            ]
        }
        edit_message(chat_id, msg_id, about_text, btns)
        return

    # Paparan Senarai Subtopik Bab
    if data.startswith("ch_"):
        ch_idx = int(data.split("_")[1])
        ch = CHAPTERS[ch_idx]
        title_ar = f"\n({ch.get('title_ar')})" if ch.get('title_ar') else ""
        txt = (
            f"📚 <b>{ch['number']}: {ch['title']}</b>{title_ar}\n\n"
            f"Sila pilih sub-tajuk untuk dibaca atau klik Ringkasan Padat:"
        )
        edit_message(chat_id, msg_id, txt, get_subtopics_keyboard(ch_idx))
        return

    # Paparan Ringkasan Bab
    if data.startswith("sumch_"):
        parts = data.split("_")
        ch_idx = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
        
        user_search_query = USER_SEARCH.get(chat_id)
        sum_text, total_pages = format_summary_text(ch_idx, page, user_search_query=user_search_query)
        
        nav_buttons = []
        if total_pages > 1:
            row_nav = []
            if page > 0:
                row_nav.append({"text": "⬅️ Bahagian Sebelum", "callback_data": f"sumch_{ch_idx}_{page-1}"})
            if page < total_pages - 1:
                row_nav.append({"text": "➡️ Bahagian Seterusnya", "callback_data": f"sumch_{ch_idx}_{page+1}"})
            if row_nav:
                nav_buttons.append(row_nav)
                
        nav_buttons.append([
            {"text": "📖 Baca Teks Penuh Bab Ini", "callback_data": f"ch_{ch_idx}"},
            {"text": "⬅️ Senarai Bab", "callback_data": "menu_summaries"}
        ])
        nav_buttons.append([{"text": "🏠 Menu Utama", "callback_data": "menu_main"}])
        
        edit_message(chat_id, msg_id, sum_text, {"inline_keyboard": nav_buttons})
        return

    # Paparan Teks Sub-Tajuk
    if data.startswith("sub_"):
        parts = data.split("_")
        ch_idx = int(parts[1])
        s_idx = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0
        
        user_search_query = USER_SEARCH.get(chat_id)
        text_out, total_pages = format_subtopic_text(ch_idx, s_idx, page, user_search_query=user_search_query)
        sections = get_chapter_sections(ch_idx)
        
        nav_buttons = []
        # Paginasi halaman dalam sub-tajuk
        row_p = []
        if page > 0:
            row_p.append({"text": "⬅️ Muka Surat Lalu", "callback_data": f"sub_{ch_idx}_{s_idx}_{page-1}"})
        if page < total_pages - 1:
            row_p.append({"text": "➡️ Muka Surat Seterusnya", "callback_data": f"sub_{ch_idx}_{s_idx}_{page+1}"})
        if row_p:
            nav_buttons.append(row_p)
            
        # Pindah Sub-Tajuk (Sebelum / Selepas)
        row_sub = []
        if s_idx > 0:
            row_sub.append({"text": "⏮ Sub-Tajuk Lalu", "callback_data": f"sub_{ch_idx}_{s_idx-1}_0"})
        if s_idx < len(sections) - 1:
            row_sub.append({"text": "⏭ Sub-Tajuk Seterusnya", "callback_data": f"sub_{ch_idx}_{s_idx+1}_0"})
        if row_sub:
            nav_buttons.append(row_sub)
            
        # Nota Kaki, Intipati Sub-Tajuk & Ringkasan Bab
        ch = CHAPTERS[ch_idx]
        row_extra = [
            {"text": "⚡ Intipati Sub-Tajuk", "callback_data": f"sumsub_{ch_idx}_{s_idx}"},
            {"text": "⚡ Ringkasan Bab", "callback_data": f"sumch_{ch_idx}"}
        ]
        if ch.get("footnotes"):
            row_extra.insert(0, {"text": f"📝 Nota Kaki ({len(ch['footnotes'])})", "callback_data": f"fn_{ch_idx}_{s_idx}_{page}"})
        nav_buttons.append(row_extra)
        
        nav_buttons.append([
            {"text": "📑 Senarai Sub-Tajuk", "callback_data": f"ch_{ch_idx}"},
            {"text": "🏠 Utama", "callback_data": "menu_main"}
        ])
        
        edit_message(chat_id, msg_id, text_out, {"inline_keyboard": nav_buttons})
        return

    # Paparan Intipati Ringkasan Sub-Tajuk
    if data.startswith("sumsub_"):
        parts = data.split("_")
        ch_idx = int(parts[1])
        s_idx = int(parts[2])
        
        ch = CHAPTERS[ch_idx]
        sections = get_chapter_sections(ch_idx)
        sec = sections[s_idx] if s_idx < len(sections) else {"title": "Sub-Tajuk"}
        
        # Cari ringkasan subtopic daripada ch.get("subtopics_data")
        sub_data = ch.get("subtopics_data", [])
        sum_content = None
        
        if s_idx < len(sub_data):
            sum_content = sub_data[s_idx].get("summary")
            
        if not sum_content and len(sub_data) > 0:
            import re
            sec_clean = re.sub(r"^\d+\.\s*", "", sec["title"]).strip().lower()
            for sd in sub_data:
                sd_title = sd.get("title", "").lower()
                if sec_clean in sd_title or sd_title in sec_clean:
                    sum_content = sd.get("summary")
                    break
                    
        if not sum_content:
            sum_content = "* **Intipati & Pemahaman:**\n  Intipati ringkasan bagi sub-tajuk ini sedang dimantapkan."
            
        header = (
            f"🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n"
            f"🌿 <b>AL-MUNTALAQ: INTIPATI SUB-TAJUK</b>\n"
            f"📚 <b>{ch['number']}: {ch['title']}</b>\n"
            f"📑 <b>Sub-Tajuk: {sec['title']}</b>\n"
            f"🟢 ━━━━━━━━━━━━━━━━━━━ 🏵️\n\n"
        )
        
        body = md_to_telegram_html(sum_content)
        msg_out = header + f"<blockquote>{body}</blockquote>"
        
        nav_buttons = [
            [{"text": "📖 Baca Teks Penuh Sub-Tajuk Ini", "callback_data": f"sub_{ch_idx}_{s_idx}_0"}],
            [{"text": "⚡ Ringkasan Penuh Bab", "callback_data": f"sumch_{ch_idx}"}],
            [
                {"text": "📑 Senarai Sub-Tajuk", "callback_data": f"ch_{ch_idx}"},
                {"text": "🏠 Utama", "callback_data": "menu_main"}
            ]
        ]
        edit_message(chat_id, msg_id, msg_out, {"inline_keyboard": nav_buttons})
        return

    # Paparan Nota Kaki Bab
    if data.startswith("fn_"):
        parts = data.split("_")
        ch_idx = int(parts[1])
        s_idx = int(parts[2])
        page = int(parts[3])
        
        ch = CHAPTERS[ch_idx]
        footnotes = ch.get("footnotes", [])
        
        fn_text = (
            f"📝 <b>NOTA KAKI: {ch['number']}</b>\n"
            f"📚 <i>{ch['title']}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for fn in footnotes[:20]: # Papar hingga 20 nota kaki utama
            fn_text += f"<b>[{fn['id']}]</b> {md_to_telegram_html(fn['text'])}\n\n"
            
        btns = [
            [{"text": "⬅️ Kembali ke Bacaan Teks", "callback_data": f"sub_{ch_idx}_{s_idx}_{page}"}],
            [{"text": "🏠 Menu Utama", "callback_data": "menu_main"}]
        ]
        edit_message(chat_id, msg_id, fn_text, {"inline_keyboard": btns})
        return

# ================= GELUNG UTAMA (LONG POLLING) =================

def main():
    print("==================================================================")
    print("             BOT TELEGRAM AL-MUNTALAQ BERMULA                     ")
    print("           Titik Tolak Fiqh & Harakah Islamiyah                  ")
    print("==================================================================")
    
    if not BOT_TOKEN or BOT_TOKEN == "ISI_TOKEN_BOT_ALMUNTALAQ_DI_SINI":
        print("\n[PERINGATAN]: Token Bot Telegram belum diisi!")
        print("Sila masukkan token daripada @BotFather ke dalam fail:")
        print(f"--> {CONFIG_PATH}")
        print("Atau tetapkan environment variable TELEGRAM_BOT_TOKEN_MUNTALAQ.\n")
        
    start_health_server()
    
    # Uji Sambungan Bot jika ada token
    if BOT_TOKEN and BOT_TOKEN != "ISI_TOKEN_BOT_ALMUNTALAQ_DI_SINI":
        res = send_api("getMe", {})
        if res and res.get("ok"):
            bot_info = res["result"]
            print(f"Sambungan Berjaya! Bot Aktif: @{bot_info.get('username')} ({bot_info.get('first_name')})")
        else:
            print("Gagal menyambung ke Telegram. Sila periksa token anda.")

    offset = 0
    print("Menunggu mesej daripada pengguna Telegram (Long Polling aktif)...")
    
    while True:
        try:
            if not BOT_TOKEN or BOT_TOKEN == "ISI_TOKEN_BOT_ALMUNTALAQ_DI_SINI":
                # Semak semula jika pengguna baru simpan token dalam config.json
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        tok = cfg.get("bot_token")
                        if tok and tok != "ISI_TOKEN_BOT_ALMUNTALAQ_DI_SINI":
                            globals()['BOT_TOKEN'] = tok
                            globals()['API_BASE'] = f"https://api.telegram.org/bot{tok}"
                            print(f"\nToken dikesan daripada config.json! Menyambung ke bot...")
                            continue
                time.sleep(3)
                continue
                
            payload = {"offset": offset, "timeout": 25}
            updates_res = send_api("getUpdates", payload)
            
            if updates_res and updates_res.get("ok"):
                updates = updates_res.get("result", [])
                for upd in updates:
                    offset = upd["update_id"] + 1
                    if "message" in upd:
                        handle_message(upd["message"])
                    elif "callback_query" in upd:
                        handle_callback(upd["callback_query"])
            else:
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nBot dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f"Ralat dalam gelung polling: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()

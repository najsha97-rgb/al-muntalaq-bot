# PANDUAN PENGGUNAAN & PELANCARAN BOT TELEGRAM AL-MUNTALAQ (المنطلق)

Bot Telegram ini dibina khas untuk membolehkan para pembaca, aktivis dan pendakwah menelaah keseluruhan kitab agung **Al-Muntalaq (المنطلق)** karya **As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)** secara interaktif melalui Telegram di telefon pintar atau komputer.

---

## 🌟 Ciri-Ciri Utama Bot

1. **Navigasi 18 Bab Lengkap (Mukadimah + 17 Bab):**
   - Mengandungi kesemua **92 sub-tajuk** dalam kitab.
   - Paginasi pintar untuk membaca teks perenggan demi perenggan tanpa teks terpotong.
2. **Sokongan Dwi-Lapisan (Dual Layer):**
   - **Lapisan 1 (Teks Lengkap):** Terjemahan penuh berserta paparan teks ayat Al-Quran, matan hadith, kata-kata salaf dan 246 nota kaki.
   - **Lapisan 2 (Ringkasan Eksklusif):** Ringkasan berstruktur bagi setiap bab berserta **💎 Mutiara Kata-kata Tokoh & Salafussoleh (Nukilan Emas)** dan **⚔️ Fiqh Amal Haraki & Dimensi Tarbawi**.
3. **Carian Pintar (`/cari`):**
   - Taip `/cari hawa nafsu`, `/cari gerhana`, `/cari amal jama'i`, `/cari tanzim`, `/cari banna` untuk mendapatkan topik berkaitan secara serta-merta.
4. **Mutiara Hikmah Dakwah (`/hikmah`):**
   - Memaparkan mutiara kata para sahabat, salafussoleh dan tokoh harakah secara rawak untuk tazkirah harian.
5. **Pautan Terus ke Web PWA:**
   - Butang pautan terus ke [https://al-muntalaq-dakwah.netlify.app/](https://al-muntalaq-dakwah.netlify.app/).

---

## 📋 SOP 3 Langkah Pelancaran Bot Telegram

### Langkah 1: Dapatkan Token Bot Percuma daripada `@BotFather`
1. Buka aplikasi **Telegram** anda.
2. Di ruang carian, cari akaun rasmi: **`@BotFather`** (pastikan ada lencana biru bertanda verified).
3. Tekan butang **Start** atau taip: `/start`
4. Taip arahan: `/newbot`
5. Masukkan **Nama Paparan Bot** (Contoh: `Al-Muntalaq Fiqh Dakwah` atau `Al-Muntalaq Haraki`).
6. Masukkan **Username Bot** yang unik dan mesti berakhir dengan perkataan `bot` (Contoh: `MuntalaqKu_bot`, `AlMuntalaq_Dakwah_bot`, atau `MuntalaqTarbawi_bot`).
7. **@BotFather** akan memberikan **HTTP API Token** panjang seperti contoh berikut:
   ```text
   8123456789:AAFxYz...contohtokenpanjang...
   ```
8. **Salin (Copy)** token tersebut.

---

### Langkah 2: Masukkan Token ke Dalam `config.json`
Buka fail konfigurasi bot:
📂 [`c:\Users\pc\OneDrive\Documents\Bahan_Ilmiah_Dakwah\telegram_bot_almuntalaq\config.json`](file:///c:/Users/pc/OneDrive/Documents/Bahan_Ilmiah_Dakwah/telegram_bot_almuntalaq/config.json)

Gantikan teks `"ISI_TOKEN_BOT_ALMUNTALAQ_DI_SINI"` dengan token yang disalin tadi:
```json
{
  "bot_token": "8123456789:AAFxYz...contohtokenpanjang...",
  "bot_name": "MuntalaqKu_bot",
  "description": "Bot Rasmi Kitab Al-Muntalaq - Titik Tolak Dakwah & Tarbiah Harakah"
}
```
Kemudian tekan **Save (`Ctrl + S`)**.

---

### Langkah 3: Jalankan Bot
Terdapat 2 cara mudah:

#### Cara A: Klik Dua Kali Fail Pintas di Desktop (Paling Mudah)
* Pergi ke folder Desktop: `C:\Users\pc\OneDrive\Desktop\Al-Muntalaq\`
* Klik dua kali pada fail:
  📄 [`START_BOT_ALMUNTALAQ.bat`](file:///C:/Users/pc/OneDrive/Desktop/Al-Muntalaq/START_BOT_ALMUNTALAQ.bat)

#### Cara B: Jalankan Melalui Terminal / Folder Workspace
* Buka folder:
  📂 [`c:\Users\pc\OneDrive\Documents\Bahan_Ilmiah_Dakwah\telegram_bot_almuntalaq`](file:///c:/Users/pc/OneDrive/Documents/Bahan_Ilmiah_Dakwah/telegram_bot_almuntalaq)
* Klik dua kali fail: [`start_bot.bat`](file:///c:/Users/pc/OneDrive/Documents/Bahan_Ilmiah_Dakwah/telegram_bot_almuntalaq/start_bot.bat)

---

## 🎯 Menguji Bot Anda di Telegram
1. Buka Telegram di telefon atau PC anda.
2. Cari username bot yang anda daftarkan tadi (contoh: `@MuntalaqKu_bot`).
3. Tekan butang **Start** atau hantar mesej: `/start`.
4. Bot akan memaparkan Menu Utama dengan butang-butang interaktif sedia digunakan!

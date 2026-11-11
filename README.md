# 💬 Auto Comment TikTok — Powered by Gemini AI

Kirim komentar otomatis ke video TikTok menggunakan multi-akun via Chrome CDP.
Komentar di-generate oleh Google Gemini AI dengan pilihan mood.

## 📁 Struktur File

```
Comment-Tiktok/
├── gemini_comment.py    # Generate komentar via Gemini API
├── tiktok_comment.py    # Kirim komentar ke TikTok via CDP
├── requirements.txt
├── .env.example
└── comment_history.json # Auto-generated: histori komentar yang dikirim
```

## ⚙️ Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Set Gemini API key
set GEMINI_API_KEY=your_key_here   # Windows CMD
$env:GEMINI_API_KEY="your_key"     # PowerShell

# Dapatkan API key gratis di: https://aistudio.google.com/app/apikey
```

## 🚀 Cara Pakai

### Mode Interaktif (direkomendasikan)
```bash
python tiktok_comment.py
```
Akan muncul menu step-by-step untuk pilih URL, mood, dan akun.

### Mode CLI
```bash
# Komentar positif untuk 2 akun, dengan konteks video
python tiktok_comment.py \
  --url "https://tiktok.com/@user/video/123456" \
  --mood positive \
  --accounts akun1 akun2 \
  --context "Video dance viral lagu pop"

# Komentar negatif, tanpa preview (langsung kirim)
python tiktok_comment.py \
  --url "https://tiktok.com/@user/video/123456" \
  --mood negative \
  --no-preview

# Lihat semua opsi
python tiktok_comment.py --help
```

### Test generate komentar saja (tanpa kirim)
```bash
python gemini_comment.py
```

## 😊 Pilihan Mood

| Mood       | Deskripsi                        |
|------------|----------------------------------|
| `positive` | 😊 Pujian & dukungan             |
| `negative` | 😒 Kritik & sinis                |
| `neutral`  | 🤔 Pertanyaan & observasi        |
| `funny`    | 😂 Bercanda & humor              |
| `flirty`   | 😍 Gombal & rayuan               |
| `hype`     | 🔥 Semangat & energik            |

## 📋 Prasyarat

- Python 3.10+
- Chrome berjalan di Windows Host dengan CDP aktif di port 9222-9226
- TikTok sudah login di masing-masing Chrome instance
- Gemini API key (gratis di Google AI Studio)

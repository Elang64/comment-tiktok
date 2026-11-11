"""
ai_comment.py (alias: gemini_comment.py)
─────────────────────────────────────────
Generate komentar TikTok menggunakan AI — support Gemini & Grok.
Provider dipilih via .env: AI_PROVIDER=gemini atau AI_PROVIDER=grok

Mood yang tersedia:
  - positive : komentar positif / pujian
  - negative : komentar negatif / kritik
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Konfigurasi — baca dari .env
# ─────────────────────────────────────────────────────────────

AI_PROVIDER    = os.getenv("AI_PROVIDER", "gemini").lower()   # "gemini" atau "grok"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROK_API_KEY   = os.getenv("GROK_API_KEY", "")

# Model default per provider
GEMINI_MODEL = "gemini-3.8-flash"
GROK_MODEL   = "grok-3-mini"                   # atau "grok-3" untuk yang lebih pintar

# ─────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "positive": """
Kamu adalah pengguna TikTok yang sangat positif dan supportif.
Buat 1 komentar singkat dalam Bahasa Indonesia untuk video TikTok berikut.

Ketentuan:
- Komentar harus positif, mendukung, dan tulus
- Panjang: 1-2 kalimat (maksimal 100 karakter)
- Gunakan bahasa gaul TikTok yang natural (boleh pakai emoji secukupnya)
- JANGAN pakai hashtag
- Output HANYA komentar saja, tanpa penjelasan apapun

Konteks video: {context}
""",

    "negative": """
Kamu adalah pengguna TikTok yang kritis dan suka memberikan kritik pedas.
Buat 1 komentar singkat dalam Bahasa Indonesia untuk video TikTok berikut.

Ketentuan:
- Komentar harus kritis, sinis, atau meremehkan (tapi BUKAN hate speech atau SARA)
- Panjang: 1-2 kalimat (maksimal 100 karakter)
- Gunakan bahasa gaul TikTok yang natural (boleh pakai emoji secukupnya)
- JANGAN pakai hashtag
- Output HANYA komentar saja, tanpa penjelasan apapun

Konteks video: {context}
""",
}

FATAL_CODES = ["400", "401", "403", "404", "429",
               "permission_denied", "unauthenticated",
               "not found", "billing", "not supported",
               "invalid api key", "unauthorized"]


# ─────────────────────────────────────────────────────────────
# Provider: Gemini
# ─────────────────────────────────────────────────────────────

def _init_gemini():
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY belum diset di .env")
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def _generate_gemini(client, prompt: str) -> str:
    from google import genai
    from google.genai import types
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
            max_output_tokens=150,
        ),
    )
    return response.text.strip().strip('"').strip("'")


# ─────────────────────────────────────────────────────────────
# Provider: Grok (xAI) — kompatibel OpenAI SDK
# ─────────────────────────────────────────────────────────────

def _init_grok():
    if not GROK_API_KEY:
        raise ValueError("❌ GROK_API_KEY belum diset di .env")
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "❌ openai package belum terinstall.\n"
            "   Jalankan: pip install openai"
        )
    return OpenAI(
        api_key=GROK_API_KEY,
        base_url="https://api.x.ai/v1",
    )


def _generate_grok(client, prompt: str) -> str:
    response = client.chat.completions.create(
        model=GROK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip().strip('"').strip("'")


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def init_gemini():
    """Inisialisasi AI client sesuai provider yang aktif."""
    if AI_PROVIDER == "grok":
        client = _init_grok()
        print(f"🤖 Provider: Grok ({GROK_MODEL})")
    else:
        client = _init_gemini()
        print(f"🤖 Provider: Gemini ({GEMINI_MODEL})")
    return client


def generate_comment(
    context: str,
    mood: str = "positive",
    client=None,
    count: int = 1,
) -> list[str]:
    """
    Generate komentar TikTok.

    Args:
        context : Deskripsi video
        mood    : 'positive' atau 'negative'
        client  : AI client (dibuat otomatis jika None)
        count   : Jumlah variasi komentar

    Returns:
        List of string komentar

    Raises:
        RuntimeError : error fatal dari API
        ValueError   : mood tidak valid
    """
    if mood not in PROMPT_TEMPLATES:
        raise ValueError(f"Mood '{mood}' tidak valid. Pilihan: {list(PROMPT_TEMPLATES.keys())}")

    if client is None:
        client = init_gemini()

    prompt = PROMPT_TEMPLATES[mood].format(context=context)
    comments = []

    for i in range(count):
        try:
            if AI_PROVIDER == "grok":
                comment = _generate_grok(client, prompt)
            else:
                comment = _generate_gemini(client, prompt)
            comments.append(comment)

        except Exception as e:
            err_str = str(e).lower()
            print(f"[!] Error generate komentar #{i+1}: {e}")

            if any(code in err_str for code in FATAL_CODES):
                hints = ""
                if "not found" in err_str:
                    hints = f"\n   Model tidak ditemukan. Cek nama model di provider {AI_PROVIDER}."
                elif "billing" in err_str or "403" in err_str:
                    hints = "\n   Billing belum aktif atau API key tidak valid."
                elif "429" in err_str:
                    hints = "\n   Rate limit / quota habis. Tunggu sebentar."
                elif "invalid api key" in err_str or "unauthorized" in err_str:
                    hints = "\n   API key salah. Cek kembali isi .env"
                raise RuntimeError(f"AI API fatal error ({AI_PROVIDER}): {e}{hints}")

            comments.append(None)

    return [c for c in comments if c]


def list_moods() -> dict:
    return {
        "positive": "😊 Positif — pujian & dukungan",
        "negative": "😒 Negatif — kritik & sinis",
    }


# Untuk backward compat — GEMINI_MODEL dipakai tiktok_comment.py untuk display
AI_MODEL = GROK_MODEL if AI_PROVIDER == "grok" else GEMINI_MODEL


# ─────────────────────────────────────────────────────────────
# CLI standalone (test generate saja)
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print(f"  🤖 TikTok Comment Generator")
    print(f"     Provider : {AI_PROVIDER.upper()}")
    print(f"     Model    : {AI_MODEL}")
    print("=" * 55)

    try:
        client = init_gemini()
        print("✅ AI API siap\n")
    except (ValueError, ImportError) as e:
        print(e)
        return

    moods = list_moods()
    print("📌 Pilih mood:")
    mood_keys = list(moods.keys())
    for i, (key, desc) in enumerate(moods.items(), 1):
        print(f"  [{i}] {desc}")

    while True:
        try:
            choice = int(input("\nMasukkan nomor [1/2]: "))
            if 1 <= choice <= len(mood_keys):
                selected_mood = mood_keys[choice - 1]
                break
            print("   ⚠️  Masukkan 1 atau 2.")
        except ValueError:
            print("   ⚠️  Masukkan angka.")

    context = input("\nKonteks video: ").strip() or "Video TikTok umum"

    while True:
        try:
            count = int(input("Berapa variasi? [1-5]: ").strip() or "3")
            if 1 <= count <= 5:
                break
        except ValueError:
            count = 3
            break

    print(f"\n⏳ Generating {count} komentar ({selected_mood})...")
    try:
        comments = generate_comment(context, mood=selected_mood, client=client, count=count)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        return

    print(f"\n{'─'*55}")
    for i, c in enumerate(comments, 1):
        print(f"  [{i}] {c}")
    print(f"{'─'*55}")


if __name__ == "__main__":
    main()

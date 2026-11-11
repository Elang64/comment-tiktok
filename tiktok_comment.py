"""
tiktok_comment.py
─────────────────
Kirim komentar otomatis ke video TikTok via Chrome CDP (Playwright).
Komentar di-generate oleh Gemini AI (gemini_comment.py).

Fitur:
  - Pilih mood komentar (positive / negative / neutral / funny / flirty / hype)
  - Pilih akun (atau semua sekaligus)
  - Preview komentar sebelum dikirim
  - Jeda acak antar akun (anti-detect)
  - Simpan hasil ke comment_history.json

Cara pakai:
  python tiktok_comment.py
  python tiktok_comment.py --url "https://tiktok.com/@x/video/..." --mood positive --accounts akun1 akun2
"""

import time
import random
import json
import os
import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright

from gemini_comment import generate_comment, init_gemini, list_moods, AI_MODEL

# ─────────────────────────────────────────────────────────────
# Konfigurasi CDP
# ─────────────────────────────────────────────────────────────

ACCOUNT_PORT_MAP = {
    "akun1": 9222,  # Fatur Ikhsanudin
    "akun2": 9223,  # Ridetes7
    "akun3": 9224,  # Ridonajrul
    "akun4": 9225,  # Usertestpkl
    "akun5": 9226,  # Gptridho
}

DISPLAY_NAMES = {
    "akun1": "Fatur Ikhsanudin",
    "akun2": "Ridetes7",
    "akun3": "Ridonajrul",
    "akun4": "Usertestpkl",
    "akun5": "Gptridho",
}

HOST_IP = "172.18.0.1"

# Delay antar akun (detik)
MIN_DELAY = 5
MAX_DELAY = 12

# File histori
HISTORY_FILE = "comment_history.json"

# ─────────────────────────────────────────────────────────────
# Selector komentar TikTok (coba urut dari paling reliable)
# ─────────────────────────────────────────────────────────────

COMMENT_INPUT_SELECTORS = [
    '[data-e2e="comment-input"]',
    'div[contenteditable="true"][data-e2e*="comment"]',
    'div[contenteditable="true"]',
    'textarea[placeholder*="komentar" i]',
    'textarea[placeholder*="comment" i]',
    'textarea[placeholder*="Add comment" i]',
]

SUBMIT_BUTTON_SELECTORS = [
    '[data-e2e="comment-post"]',
    'div[data-e2e="comment-submit"]',
    'button[data-e2e*="post"]',
    'span[data-e2e*="post"]',
]

# ─────────────────────────────────────────────────────────────
# Histori
# ─────────────────────────────────────────────────────────────

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_history(entry: dict):
    history = load_history()
    history.insert(0, entry)
    history = history[:200]  # batasi 200 entry
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────
# Core: kirim komentar via CDP
# ─────────────────────────────────────────────────────────────

def post_comment(account_name: str, url: str, comment: str) -> dict:
    """
    Kirim satu komentar ke video TikTok menggunakan akun yang terhubung via CDP.

    Returns:
        dict dengan keys: success (bool), account, comment, error (opsional)
    """
    if account_name not in ACCOUNT_PORT_MAP:
        return {
            "success": False,
            "account": account_name,
            "comment": comment,
            "error": f"Akun '{account_name}' tidak ada di mapping",
        }

    port = ACCOUNT_PORT_MAP[account_name]
    cdp_url = f"http://{HOST_IP}:{port}"
    name = DISPLAY_NAMES.get(account_name, account_name)

    print(f"\n{'='*55}")
    print(f"[*] Akun   : {name} ({account_name}) — Port {port}")
    print(f"[*] URL    : {url}")
    print(f"[*] Comment: {comment}")
    print(f"{'='*55}")

    with sync_playwright() as p:
        try:
            # 1. Connect ke Chrome Windows via CDP
            print(f"[*] Connecting ke CDP: {cdp_url} ...")
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # 2. Buka video
            print(f"[*] Navigasi ke video...")
            page.goto(url, timeout=60000)
            print("[*] Tunggu 5 detik agar halaman ter-load...")
            time.sleep(5)

            # 3. Gerak mouse natural
            page.mouse.move(random.randint(200, 600), random.randint(200, 500))
            time.sleep(random.uniform(0.8, 1.5))

            # 4. Scroll sedikit ke bawah (supaya comment section muncul)
            page.evaluate("window.scrollBy(0, 300)")
            time.sleep(1.5)

            # 5. Cari input komentar
            print("[*] Mencari kolom komentar...")
            comment_input = None
            for sel in COMMENT_INPUT_SELECTORS:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0:
                        el.wait_for(state="visible", timeout=5000)
                        comment_input = el
                        print(f"[+] Kolom komentar ditemukan: {sel}")
                        break
                except Exception:
                    continue

            if comment_input is None:
                # Screenshot untuk debug
                debug_path = f"debug_comment_{account_name}_{int(time.time())}.png"
                page.screenshot(path=debug_path)
                return {
                    "success": False,
                    "account": account_name,
                    "comment": comment,
                    "error": f"Kolom komentar tidak ditemukan. Screenshot: {debug_path}",
                }

            # 6. Klik dan ketik komentar (seperti manusia)
            comment_input.click()
            time.sleep(random.uniform(0.5, 1.0))

            # Ketik karakter per karakter dengan jeda acak (anti-detect)
            for char in comment:
                comment_input.type(char, delay=random.randint(50, 150))

            print(f"[+] Komentar diketik: '{comment}'")
            time.sleep(random.uniform(1.0, 2.0))

            # 7. Cari dan klik tombol post
            print("[*] Mencari tombol kirim...")
            submitted = False
            for sel in SUBMIT_BUTTON_SELECTORS:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.wait_for(state="visible", timeout=3000)
                        btn.click(timeout=5000)
                        submitted = True
                        print(f"[+] Tombol kirim diklik: {sel}")
                        break
                except Exception:
                    continue

            # Fallback: tekan Enter
            if not submitted:
                print("[*] Tombol tidak ditemukan, coba tekan Enter...")
                comment_input.press("Enter")
                submitted = True

            time.sleep(random.uniform(2.0, 3.0))

            if submitted:
                print(f"[✅] Komentar berhasil dikirim untuk {name}!")
                return {
                    "success": True,
                    "account": account_name,
                    "comment": comment,
                }
            else:
                return {
                    "success": False,
                    "account": account_name,
                    "comment": comment,
                    "error": "Gagal menemukan tombol kirim",
                }

        except Exception as e:
            print(f"[!] Exception: {e}")
            return {
                "success": False,
                "account": account_name,
                "comment": comment,
                "error": str(e),
            }
        finally:
            # Jangan close browser — CDP hanya lepas koneksi
            pass


# ─────────────────────────────────────────────────────────────
# Orkestrasi multi-akun
# ─────────────────────────────────────────────────────────────

def run_auto_comment(
    url: str,
    accounts: list[str],
    mood: str,
    context: str = "",
    per_account_comment: bool = True,
    preview: bool = True,
) -> dict:
    """
    Jalankan auto comment untuk banyak akun.

    Args:
        url                 : URL video TikTok
        accounts            : List account id yang akan dipakai
        mood                : Mood komentar (positive/negative/dll)
        context             : Deskripsi singkat video untuk Gemini
        per_account_comment : True = generate komentar unik per akun,
                              False = semua akun pakai komentar yang sama
        preview             : True = tampilkan preview dan minta konfirmasi

    Returns:
        dict berisi summary hasil
    """
    print(f"\n{'='*55}")
    print(f"  🤖 Auto Comment TikTok — {AI_MODEL}")
    print(f"{'='*55}")
    print(f"  URL    : {url}")
    print(f"  Mood   : {mood}")
    print(f"  Akun   : {', '.join(accounts)}")
    print(f"{'='*55}\n")

    # Init Gemini
    try:
        gemini_client = init_gemini()
        print(f"✅ Gemini API siap\n")
    except ValueError as e:
        print(e)
        return {"success": False, "error": str(e)}

    if not context:
        context = f"Video TikTok di URL: {url}"

    # Generate komentar
    if per_account_comment:
        # Komentar unik per akun
        print(f"⏳ Generating {len(accounts)} komentar unik (mood: {mood})...")
        try:
            comments_list = generate_comment(
                context, mood=mood, client=gemini_client, count=len(accounts)
            )
        except RuntimeError as e:
            print(f"\n❌ {e}")
            return {"success": False, "error": str(e)}

        # Pad jika kurang, maksimal 3 kali coba
        retry = 0
        while len(comments_list) < len(accounts) and retry < 3:
            retry += 1
            try:
                extra = generate_comment(context, mood=mood, client=gemini_client, count=1)
                comments_list.extend(extra)
            except RuntimeError as e:
                print(f"\n❌ {e}")
                return {"success": False, "error": str(e)}

        if len(comments_list) < len(accounts):
            print(f"⚠️  Hanya berhasil generate {len(comments_list)} komentar dari {len(accounts)} yang diminta.")
            accounts = accounts[:len(comments_list)]

        comments_list = comments_list[:len(accounts)]
    else:
        # Satu komentar sama untuk semua
        print(f"⏳ Generating 1 komentar untuk semua akun (mood: {mood})...")
        try:
            comments_list = generate_comment(context, mood=mood, client=gemini_client, count=1)
        except RuntimeError as e:
            print(f"\n❌ {e}")
            return {"success": False, "error": str(e)}

        if not comments_list:
            print("❌ Gagal generate komentar.")
            return {"success": False, "error": "Gagal generate komentar dari Gemini"}
        comments_list = [comments_list[0]] * len(accounts)

    # Preview
    print(f"\n{'─'*55}")
    print("📋 Preview komentar yang akan dikirim:")
    print(f"{'─'*55}")
    for acc, cmt in zip(accounts, comments_list):
        name = DISPLAY_NAMES.get(acc, acc)
        print(f"  [{acc}] {name}")
        print(f"        💬 \"{cmt}\"")
    print(f"{'─'*55}")

    if preview:
        confirm = input("\n▶️  Lanjutkan kirim komentar? [y/N]: ").strip().lower()
        if confirm != "y":
            print("❌ Dibatalkan.")
            return {"success": False, "error": "Dibatalkan oleh user"}

    # Eksekusi
    task_result = {
        "id": f"comment_{int(time.time())}",
        "url": url,
        "mood": mood,
        "context": context,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": {"success": 0, "failed": 0},
        "details": [],
    }

    print(f"\n🚀 Mulai mengirim komentar...\n")

    for i, (account_id, comment) in enumerate(zip(accounts, comments_list)):
        result = post_comment(account_id, url, comment)
        task_result["details"].append(result)

        if result["success"]:
            task_result["results"]["success"] += 1
        else:
            task_result["results"]["failed"] += 1
            print(f"   ⚠️  Error: {result.get('error', 'Unknown')}")

        # Jeda antar akun (kecuali akun terakhir)
        if i < len(accounts) - 1:
            delay = random.randint(MIN_DELAY, MAX_DELAY)
            print(f"\n⏳ Jeda {delay} detik sebelum akun berikutnya...")
            time.sleep(delay)

    # Ringkasan
    s = task_result["results"]["success"]
    f = task_result["results"]["failed"]
    task_result["status"] = "success" if f == 0 else ("failed" if s == 0 else "partial")

    print(f"\n{'='*55}")
    print(f"🏁 SELESAI")
    print(f"   ✅ Berhasil : {s}")
    print(f"   ❌ Gagal    : {f}")
    print(f"{'='*55}")

    # Simpan histori
    save_history(task_result)
    print(f"💾 Hasil disimpan ke {HISTORY_FILE}")

    return task_result


# ─────────────────────────────────────────────────────────────
# CLI interaktif
# ─────────────────────────────────────────────────────────────

def interactive_mode():
    """Mode interaktif step-by-step."""
    print("=" * 55)
    print("  💬 Auto Comment TikTok — Powered by Gemini AI")
    print("=" * 55)

    # 1. URL
    url = input("\n📎 Masukkan URL video TikTok: ").strip()
    if not url or "tiktok.com" not in url:
        print("❌ URL tidak valid.")
        return

    # 2. Konteks video (opsional)
    print("\n📝 Deskripsi singkat isi video (opsional, tekan Enter untuk skip):")
    print("   Contoh: 'Dance video lagu viral', 'Tutorial masak mie', 'Video kucing lucu'")
    context = input("Konteks: ").strip()

    # 3. Mood
    moods = list_moods()
    print("\n📌 Pilih mood komentar:")
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

    print(f"✅ Mood: {moods[selected_mood]}")

    # 4. Pilih akun
    print("\n👥 Pilih akun:")
    acc_keys = list(ACCOUNT_PORT_MAP.keys())
    print(f"  [0] Semua akun ({len(acc_keys)} akun)")
    for i, acc_id in enumerate(acc_keys, 1):
        name = DISPLAY_NAMES.get(acc_id, acc_id)
        print(f"  [{i}] {acc_id} — {name} (Port {ACCOUNT_PORT_MAP[acc_id]})")

    while True:
        raw = input("\nMasukkan nomor akun (pisah koma, 0=semua): ").strip()
        if raw == "0":
            selected_accounts = acc_keys
            break
        try:
            choices = [int(x.strip()) for x in raw.split(",")]
            selected_accounts = []
            valid = True
            for c in choices:
                if 1 <= c <= len(acc_keys):
                    selected_accounts.append(acc_keys[c - 1])
                else:
                    print(f"   ⚠️  Nomor {c} tidak valid.")
                    valid = False
                    break
            if valid and selected_accounts:
                break
        except ValueError:
            print("   ⚠️  Format tidak valid. Contoh: 1,3,5")

    print(f"✅ Akun dipilih: {', '.join(selected_accounts)}")

    # 5. Mode komentar (unik / sama)
    print("\n🔀 Mode komentar:")
    print("  [1] Komentar unik per akun (lebih natural)")
    print("  [2] Komentar sama untuk semua akun")
    while True:
        try:
            mode_choice = int(input("Pilih [1/2]: ") or "1")
            if mode_choice in (1, 2):
                per_account = mode_choice == 1
                break
        except ValueError:
            pass
        print("   ⚠️  Masukkan 1 atau 2.")

    # 6. Jalankan
    run_auto_comment(
        url=url,
        accounts=selected_accounts,
        mood=selected_mood,
        context=context,
        per_account_comment=per_account,
        preview=True,
    )


def cli_mode():
    """Mode CLI via argumen."""
    parser = argparse.ArgumentParser(
        description="Auto Comment TikTok dengan Gemini AI"
    )
    parser.add_argument("--url", required=True, help="URL video TikTok")
    parser.add_argument(
        "--mood",
        default="positive",
        choices=list(list_moods().keys()),
        help="Mood komentar",
    )
    parser.add_argument(
        "--accounts",
        nargs="+",
        default=list(ACCOUNT_PORT_MAP.keys()),
        help="Akun yang dipakai (misal: akun1 akun2)",
    )
    parser.add_argument("--context", default="", help="Deskripsi singkat video")
    parser.add_argument(
        "--same-comment",
        action="store_true",
        help="Pakai komentar yang sama untuk semua akun",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Langsung kirim tanpa preview konfirmasi",
    )
    args = parser.parse_args()

    run_auto_comment(
        url=args.url,
        accounts=args.accounts,
        mood=args.mood,
        context=args.context,
        per_account_comment=not args.same_comment,
        preview=not args.no_preview,
    )


# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Jika ada argumen CLI, pakai mode CLI
    if len(sys.argv) > 1:
        cli_mode()
    else:
        # Tidak ada argumen → mode interaktif
        interactive_mode()

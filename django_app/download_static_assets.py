"""
download_static_assets.py
=========================
سكريبت تشغله مرة واحدة وقت الـ deploy عشان يحمّل كل الـ assets الخارجية محلياً.

استخدام:
    python download_static_assets.py

بيحمّل:
    - خط Cairo (woff2) من Google Fonts
    - Font Awesome 6.5 (CSS + webfonts)
    - Chart.js

بعد ما يخلص شغّل:
    python manage.py collectstatic
"""

import os
import re
import sys
import urllib.request
import urllib.error

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

DIRS = [
    os.path.join(STATIC_DIR, "fonts", "cairo"),
    os.path.join(STATIC_DIR, "webfonts"),
    os.path.join(STATIC_DIR, "css"),
    os.path.join(STATIC_DIR, "js"),
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def download(url, dest, label=""):
    if os.path.exists(dest):
        print(f"  ✓ موجود بالفعل: {label or os.path.basename(dest)}")
        return True
    print(f"  ↓ تحميل: {label or os.path.basename(dest)} ...", end="", flush=True)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
            f.write(r.read())
        print(" ✓")
        return True
    except Exception as e:
        print(f" ✗ فشل: {e}")
        return False


# ─── 1. Cairo Font ───────────────────────────────────────────────────────────
print("\n[1/3] خط Cairo")

GOOGLE_CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Cairo:wght@300;400;600;700;900&display=swap"
)

try:
    req = urllib.request.Request(GOOGLE_CSS_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        google_css = r.read().decode("utf-8")
except Exception as e:
    print(f"  ✗ فشل تحميل CSS من Google Fonts: {e}")
    google_css = ""

# استخرج كل الـ woff2 URLs
woff2_urls = re.findall(r"url\((https://[^)]+\.woff2[^)]*)\)", google_css)

font_css_lines = []
font_face_blocks = re.findall(r"@font-face\s*\{[^}]+\}", google_css, re.DOTALL)

for block in font_face_blocks:
    url_match = re.search(r"url\((https://[^\)]+\.woff2[^\)]*)\)", block)
    if not url_match:
        continue
    woff2_url = url_match.group(1).strip("'\"")
    filename  = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", woff2_url.split("/")[-1].split("?")[0])
    if not filename.endswith(".woff2"):
        filename += ".woff2"
    dest = os.path.join(STATIC_DIR, "fonts", "cairo", filename)
    ok = download(woff2_url, dest, filename)
    if ok:
        local_block = re.sub(
            r"url\(https://[^\)]+\.woff2[^\)]*\)\s*format\('[^']+'\)",
            f"url('../fonts/cairo/{filename}') format('woff2')",
            block,
        )
        font_css_lines.append(local_block)

# احفظ cairo.css
cairo_css_path = os.path.join(STATIC_DIR, "css", "cairo.css")
if font_css_lines:
    with open(cairo_css_path, "w", encoding="utf-8") as f:
        f.write("\n".join(font_css_lines))
    print(f"  → كتب {cairo_css_path}")
else:
    # Fallback CSS لو Google Fonts مش متاحة
    fallback = """/* Cairo fallback - Google Fonts unavailable at download time */
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
"""
    with open(cairo_css_path, "w", encoding="utf-8") as f:
        f.write(fallback)
    print("  ⚠ استخدم fallback لـ Cairo CSS (Google Fonts غير متاحة)")

# ─── 2. Font Awesome 6.5 ─────────────────────────────────────────────────────
print("\n[2/3] Font Awesome 6.5")

FA_CSS_URL = (
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
)
FA_CSS_DEST = os.path.join(STATIC_DIR, "css", "fontawesome.min.css")

ok = download(FA_CSS_URL, FA_CSS_DEST, "all.min.css")

if ok:
    with open(FA_CSS_DEST, "r", encoding="utf-8") as f:
        fa_css = f.read()

    # استخرج أسماء الـ webfonts
    webfont_files = re.findall(r"url\(\.\./webfonts/([^)]+)\)", fa_css)
    webfont_files = list(dict.fromkeys(  # أزل التكرار
        re.split(r"\?|\s", wf)[0] for wf in webfont_files
    ))

    FA_WEBFONTS_BASE = (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/webfonts/"
    )
    for wf in webfont_files:
        dest = os.path.join(STATIC_DIR, "webfonts", wf)
        download(FA_WEBFONTS_BASE + wf, dest, wf)

    # عدّل الـ CSS عشان يبص على الـ local webfonts
    fa_css_local = fa_css.replace("../webfonts/", "../webfonts/")
    with open(FA_CSS_DEST, "w", encoding="utf-8") as f:
        f.write(fa_css_local)
    print("  → Font Awesome CSS محدّث للـ local webfonts")

# ─── 3. Chart.js ─────────────────────────────────────────────────────────────
print("\n[3/3] Chart.js")

CHARTJS_URL  = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"
CHARTJS_DEST = os.path.join(STATIC_DIR, "js", "chart.umd.min.js")
download(CHARTJS_URL, CHARTJS_DEST, "chart.umd.min.js")

DATALABELS_URL  = "https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"
DATALABELS_DEST = os.path.join(STATIC_DIR, "js", "chartjs-plugin-datalabels.min.js")
download(DATALABELS_URL, DATALABELS_DEST, "chartjs-plugin-datalabels.min.js")

print("\n✅ خلص! دلوقتي شغّل:  python manage.py collectstatic")

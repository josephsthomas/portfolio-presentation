#!/usr/bin/env python3
"""Verify all source-deck text appears in the generated HTML."""
import json, re, html, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
slides = json.loads((ROOT / "extracted/extracted-slides.json").read_text())
raw_html = (ROOT / "site/index.html").read_text()

# Split HTML into per-slide sections keyed by slide number
sections = {}
for m in re.finditer(r'<section[^>]*data-slide="(\d+)"[^>]*>(.*?)</section>', raw_html, re.S):
    num = int(m.group(1))
    plain = html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))
    sections[num] = re.sub(r'\s+', ' ', plain).strip().lower()

def normalise(t):
    return re.sub(r'\s+', ' ', html.unescape(t)).strip().lower()

total, matched, per_slide = 0, 0, []
for slide in slides:
    n = slide["number"]
    html_text = sections.get(n, "")
    missing = []
    for block in slide.get("content", []):
        if block.get("type") != "text":
            continue
        txt = block["content"].strip()
        # Skip page-number tokens (e.g. "02", "5", "86")
        if re.fullmatch(r'\d{1,2}', txt):
            continue
        total += 1
        norm = normalise(txt)
        # Check each sentence/phrase fragment individually (handles line-split text)
        fragments = [f.strip() for f in re.split(r'[·\n]', norm) if f.strip()]
        if all(f in html_text for f in fragments):
            matched += 1
        else:
            missing.append(txt[:80])
    status = "PASS" if not missing else "FAIL"
    per_slide.append((n, status, missing))

print("=" * 60)
print("COPY-VERIFICATION REPORT")
print("=" * 60)
fails = 0
for n, status, missing in per_slide:
    if status == "FAIL":
        fails += 1
        print(f"\n  Slide {n:>2}: {status}")
        for m in missing:
            print(f"           MISSING: {m}")
if fails == 0:
    print("\n  All slides PASS")

pct = matched / total * 100 if total else 100
print(f"\n{'=' * 60}")
print(f"SCORE: {matched}/{total} text blocks matched ({pct:.1f}%)")
print(f"Slides with missing text: {fails}/{len(slides)}")
print("=" * 60)
sys.exit(0 if pct == 100 else 1)

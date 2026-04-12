#!/usr/bin/env python3
"""Optimize images from extracted/assets/ into site/assets-web/ using Pillow."""
import os, sys, pathlib
from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # allow very large images

SRC = pathlib.Path("/home/user/portfolio-presentation/extracted/assets")
DST = pathlib.Path("/home/user/portfolio-presentation/site/assets-web")
HTML = pathlib.Path("/home/user/portfolio-presentation/site/index.html")
DST.mkdir(parents=True, exist_ok=True)

files = sorted(SRC.iterdir())
total_orig = total_opt = 0
ok = skipped = 0

for f in files:
    if not f.is_file():
        continue
    ext = f.suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".tiff", ".tif", ".wmf"):
        print(f"  SKIP (unsupported): {f.name}")
        skipped += 1
        continue
    try:
        orig_size = f.stat().st_size
        img = Image.open(f)
        img.load()  # force full decode so we can close the file
        dims = img.size

        if ext in (".jpg", ".jpeg"):
            out = DST / f.name
            if img.mode == "RGBA":
                img = img.convert("RGB")
            img.save(out, "JPEG", quality=95, optimize=True)
        elif ext == ".png":
            out = DST / f.name
            img.save(out, "PNG", optimize=True)
        else:
            # GIF, TIFF, WMF -> convert to PNG
            stem = f.stem
            out = DST / (stem + ".png")
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            img.save(out, "PNG", optimize=True)

        del img  # free memory immediately

        opt_size = out.stat().st_size
        total_orig += orig_size
        total_opt += opt_size
        saving = (1 - opt_size / orig_size) * 100 if orig_size else 0
        print(f"  OK  {f.name:40s}  {dims[0]}x{dims[1]}  "
              f"{orig_size/1024:.0f}K -> {opt_size/1024:.0f}K  ({saving:+.1f}%)")
        ok += 1
    except Exception as e:
        print(f"  ERR {f.name}: {e}")
        skipped += 1

# Summary
mb = lambda b: f"{b/1024/1024:.1f} MB"
print(f"\n{'='*60}")
print(f"Processed: {ok}  |  Skipped/Error: {skipped}")
print(f"Original total : {mb(total_orig)}")
print(f"Optimized total: {mb(total_opt)}")
saved = total_orig - total_opt
print(f"Savings        : {mb(saved)} ({saved/total_orig*100:.1f}%)" if total_orig else "")

# Update index.html: assets/ -> assets-web/, also fix extensions for converted files
html = HTML.read_text()
# For GIF/TIFF/WMF that became .png, update references
for f in files:
    ext = f.suffix.lower()
    if ext in (".gif", ".tiff", ".tif", ".wmf"):
        old_ref = f"assets/{f.name}"
        new_ref = f"assets-web/{f.stem}.png"
        html = html.replace(old_ref, new_ref)
# General: remaining assets/ refs -> assets-web/
html = html.replace('"assets/', '"assets-web/')
HTML.write_text(html)
print(f"\nUpdated {HTML} — replaced assets/ -> assets-web/ paths")

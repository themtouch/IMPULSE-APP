#!/usr/bin/env python3
"""All 18 SVGs embed the SAME 1402x1122 full-body render (front+back side by
side). Extract it once, downscale, and save a single shared JPEG. The app then
shows front/back via CSS crop of this one image instead of embedding it twice."""
import base64, io, os, re
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SVG  = os.path.join(ROOT, "svg")
OUT  = os.path.join(ROOT, "svg-lite")
os.makedirs(OUT, exist_ok=True)

SCALE, QUALITY = 0.50, 60
RX = re.compile(r"data:image/jpeg;base64,([A-Za-z0-9+/=]+)")

src = open(os.path.join(SVG, "Cuerpo completo front.svg"), encoding="utf-8").read()
raw = base64.b64decode(RX.search(src).group(1))
im = Image.open(io.BytesIO(raw)).convert("RGB")
w, h = im.size
im2 = im.resize((int(w*SCALE), int(h*SCALE)), Image.LANCZOS)
buf = io.BytesIO()
im2.save(buf, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
open(os.path.join(OUT, "body.jpg"), "wb").write(buf.getvalue())
print(f"shared body: {w}x{h} {len(raw)//1024}KB -> {im2.size[0]}x{im2.size[1]} {len(buf.getvalue())//1024}KB")

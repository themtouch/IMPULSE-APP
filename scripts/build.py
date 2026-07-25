#!/usr/bin/env python3
import base64, os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(ROOT, "svg")
STEN = os.path.join(ROOT, "stencils")

def durl_svg(path):
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    return "data:image/svg+xml;base64," + b

# front-body bbox within 1402x1122 source
FOX, FOY, FVW, FVH = 91.5, 31.5, 561.0, 1029.0
BOX, BOY, BVW, BVH = 694.492, 34.5, 605.0, 1025.0
SRCW, SRCH = 1402.0, 1122.0

# ---- shared base: one downscaled JPEG (all SVGs embed the same render) ----
LITE = os.path.join(ROOT, "svg-lite")
def durl_jpg(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
_shared = os.path.join(LITE, "body.jpg")
if os.path.exists(_shared):
    SHARED_BASE = durl_jpg(_shared)
else:  # fallback: extract from the verbatim SVG (still one copy)
    SHARED_BASE = durl_svg(os.path.join(SVG, "Cuerpo completo front.svg"))

import re as _re
def silhouette(name):
    """Extract the full-body silhouette path from a base SVG -> mask data URI."""
    s = open(os.path.join(SVG, name), encoding="utf-8").read()
    vb = _re.search(r'viewBox="([^"]+)"', s).group(1)
    mblock = _re.search(r'<mask[^>]*>(.*?)</mask>', s, _re.S).group(1)
    paths = _re.findall(r'<path\b[^>]*\bd="([^"]+)"', mblock)
    body = "".join(f'<path d="{d}" fill="#fff"/>' for d in paths)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{body}</svg>'
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def crop(ox, oy, vw, vh, mask_uri):
    """CSS to show one figure's bbox from the shared image, clipped to its silhouette."""
    sw = SRCW / vw * 100.0
    sh = SRCH / vh * 100.0
    px = ox / (SRCW - vw) * 100.0
    py = oy / (SRCH - vh) * 100.0
    return (f"background-size:{sw:.4f}% {sh:.4f}%;background-position:{px:.4f}% {py:.4f}%;"
            f"-webkit-mask:url({mask_uri}) 0 0/100% 100% no-repeat;"
            f"mask:url({mask_uri}) 0 0/100% 100% no-repeat;")
FRONT_CROP = crop(FOX, FOY, FVW, FVH, silhouette("Cuerpo completo front.svg"))
BACK_CROP  = crop(BOX, BOY, BVW, BVH, silhouette("Cuerpo completo back.svg"))

# muscle metadata: file, X, Y, W, H (in source space), key, label, group, tier, lagging
FRONT = [
    ("traps & head.svg",   281.215, 31.5,  189, 228, "trapecio",  "Trapecio",    "Espalda",  "C", False),
    ("Shoulders front.svg",210.496, 219.5, 328, 89,  "hombros",   "Hombros",     "Hombros",  "B", False),
    ("Chest front.svg",    266,     232,   219, 106, "pecho",     "Pecho",       "Pecho",    "A", False),
    ("Biceps front.svg",   191.995, 287,   366, 113, "biceps",    "Bíceps",      "Brazos",   "B", False),
    ("Forearms front.svg", 136.328, 364.99,475, 170, "antebrazos","Antebrazos",  "Brazos",   "D", True),
    ("obliques front.svg", 279.5,   316.96,190, 261, "oblicuos",  "Oblicuos",    "Core",     "C", False),
    ("Abs front.svg",      324,     326.5, 101, 216, "abdomen",   "Abdomen",     "Core",     "B", False),
    ("legs front.svg",     246,     470.693,255,283, "cuadriceps","Cuádriceps",  "Piernas",  "A", False),
    ("front calves.svg",   216.5,   714.476,310,346, "pantorrillas","Pantorrillas","Piernas","E", True),
    ("hands front.svg",    92,      516.994,561,113, "manos",     "Manos",       "—",        "—", False),
]
BACK = [
    ("back head.svg",      929.5,   34.5,  127, 162, "cuello",    "Cuello",      "—",        "—", False),
    ("Back.svg",           851.962, 176,   289, 349, "espalda",   "Espalda",     "Espalda",  "A", False),
    ("Arms from back.svg", 695,     99.5,  605, 207, "triceps",   "Tríceps",     "Brazos",   "C", True),
    ("Glutes back.svg",    882,     469.5, 223, 136, "gluteos",   "Glúteos",     "Piernas",  "B", False),
    ("legs from back.svg", 860.5,   533.435,266,264, "isquios",   "Isquiotibiales","Piernas","D", True),
    ("back calves.svg",    820.5,   753.5, 345, 306, "pantorrillasb","Pantorrillas","Piernas","E", True),
]

def layers(items, ox, oy, vw, vh):
    out = []
    meta = []
    for fn, X, Y, W, H, key, label, group, tier, lag in items:
        st = durl_svg(os.path.join(STEN, fn))
        L = (X - ox) / vw * 100.0
        T = (Y - oy) / vh * 100.0
        Wp = W / vw * 100.0
        Hp = H / vh * 100.0
        interactive = tier != "—"
        cls = "m" + (" m--int" if interactive else " m--static")
        style = (f"left:{L:.4f}%;top:{T:.4f}%;width:{Wp:.4f}%;height:{Hp:.4f}%;"
                 f"-webkit-mask:url({st}) center/100% 100% no-repeat;"
                 f"mask:url({st}) center/100% 100% no-repeat;")
        data = f'data-key="{key}" data-label="{label}" data-tier="{tier}" data-group="{group}" data-lag="{int(lag)}"'
        out.append(f'<div class="{cls}" style="{style}" {data}></div>')
        if interactive:
            meta.append({"key":key,"label":label,"tier":tier,"group":group,"lag":lag})
    return "\n".join(out), meta

FRONT_LAYERS, FRONT_META = layers(FRONT, FOX, FOY, FVW, FVH)
BACK_LAYERS,  BACK_META  = layers(BACK, BOX, BOY, BVW, BVH)

def inject(template_name, out_name):
    tpl = open(os.path.join(ROOT, template_name), encoding="utf-8").read()
    fb_path = os.path.join(ROOT, "fallback.json")
    fallback = open(fb_path, encoding="utf-8").read() if os.path.exists(fb_path) else "[]"
    html = (tpl
            .replace("/*FALLBACK_JSON*/", fallback)
            .replace("/*SHARED_BASE*/", SHARED_BASE)
            .replace("/*FRONT_CROP*/", FRONT_CROP)
            .replace("/*BACK_CROP*/", BACK_CROP)
            .replace("/*FRONT_BASE*/", SHARED_BASE)
            .replace("/*BACK_BASE*/", SHARED_BASE)
            .replace("<!--FRONT_LAYERS-->", FRONT_LAYERS)
            .replace("<!--BACK_LAYERS-->", BACK_LAYERS)
            .replace("/*FRONT_ASPECT*/", f"{FVW}/{FVH}")
            .replace("/*BACK_ASPECT*/", f"{BVW}/{BVH}")
            .replace("/*META_JSON*/", json.dumps({"front":FRONT_META,"back":BACK_META}, ensure_ascii=False)))
    out = os.path.join(ROOT, out_name)
    open(out, "w", encoding="utf-8").write(html)
    print("wrote", out_name, os.path.getsize(out), "bytes")

# functional app (app.html). The landing index.html is built separately with the
# verbatim self-cropping base SVGs and is left untouched here.
inject("app-template.html", "app.html")

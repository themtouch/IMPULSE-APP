#!/usr/bin/env python3
import base64, os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(ROOT, "svg")
STEN = os.path.join(ROOT, "stencils")

def durl_svg(path):
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    return "data:image/svg+xml;base64," + b

# ---- base bodies (verbatim, they are the real render) ----
FRONT_BASE = durl_svg(os.path.join(SVG, "Cuerpo completo front.svg"))
BACK_BASE  = durl_svg(os.path.join(SVG, "Cuerpo completo back.svg"))

# front-body bbox within 1402x1122 source
FOX, FOY, FVW, FVH = 91.5, 31.5, 561.0, 1029.0
BOX, BOY, BVW, BVH = 694.492, 34.5, 605.0, 1025.0

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

TEMPLATE = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
html = (TEMPLATE
        .replace("/*FRONT_BASE*/", FRONT_BASE)
        .replace("/*BACK_BASE*/", BACK_BASE)
        .replace("<!--FRONT_LAYERS-->", FRONT_LAYERS)
        .replace("<!--BACK_LAYERS-->", BACK_LAYERS)
        .replace("/*FRONT_ASPECT*/", f"{FVW}/{FVH}")
        .replace("/*BACK_ASPECT*/", f"{BVW}/{BVH}")
        .replace("/*META_JSON*/", json.dumps({"front":FRONT_META,"back":BACK_META}, ensure_ascii=False)))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("wrote index.html", os.path.getsize(os.path.join(ROOT, "index.html")), "bytes")

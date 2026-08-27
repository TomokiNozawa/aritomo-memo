# -*- coding: utf-8 -*-
"""Pixel-coordinate crop on the exif-transposed original."""
import os, sys
from PIL import Image, ImageOps

BASE = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
ROOMS = {"48": "05_4.8帖", "62": "04_6.2帖", "45": "06_4.5帖"}


def load(tag, num):
    d = os.path.join(BASE, ROOMS[tag])
    for f in os.listdir(d):
        if f.endswith("_%s.jpg" % num) or os.path.splitext(f)[0] == num:
            return ImageOps.exif_transpose(Image.open(os.path.join(d, f)))
    raise SystemExit("not found")


for a in sys.argv[1:]:
    tag, num, name, l, t, r, b = a.split(",")[:7]
    md = int(a.split(",")[7]) if len(a.split(",")) > 7 else 1400
    im = load(tag, num)
    c = im.crop((int(l), int(t), int(r), int(b)))
    w, h = c.size
    sc = float(md) / max(w, h)
    c = c.resize((max(1, int(w*sc)), max(1, int(h*sc))), Image.LANCZOS)
    p = os.path.join(OUT, "_v8_4_rooms_%s_%s_%s.png" % (tag, num, name))
    c.save(p)
    print("%s src=%s out=%s" % (os.path.basename(p), im.size, c.size))

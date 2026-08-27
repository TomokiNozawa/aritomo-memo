# -*- coding: utf-8 -*-
import os, sys
from PIL import Image, ImageOps

BASE = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"

ROOMS = {
    "48": "05_4.8帖",
    "62": "04_6.2帖",
    "45": "06_4.5帖",
}

for tag, folder in ROOMS.items():
    d = os.path.join(BASE, folder)
    files = sorted(os.listdir(d))
    for f in files:
        if not f.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        p = os.path.join(d, f)
        im = Image.open(p)
        raw = im.size
        ex = im.getexif()
        ori = ex.get(274, None)
        im2 = ImageOps.exif_transpose(im)
        # short id
        base = os.path.splitext(f)[0]
        if "_260820_" in base:
            num = base.split("_260820_")[-1]
        else:
            num = base
        outp = os.path.join(OUT, "_v8_4_rooms_%s_%s.png" % (tag, num))
        w, h = im2.size
        sc = 1400.0 / max(w, h)
        if sc < 1:
            im2 = im2.resize((int(w*sc), int(h*sc)), Image.LANCZOS)
        im2.save(outp)
        print("%s | raw=%s ori=%s -> %s size=%s" % (f, raw, ori, os.path.basename(outp), im2.size))

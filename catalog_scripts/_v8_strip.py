# -*- coding: utf-8 -*-
"""Crop tall narrow strips around door joints, at native res, upscaled 2x."""
import os, sys
from PIL import Image, ImageOps, ImageEnhance

BASE = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
ROOMS = {"48": "05_4.8帖", "62": "04_6.2帖", "45": "06_4.5帖"}


def load(tag, num):
    d = os.path.join(BASE, ROOMS[tag])
    for f in os.listdir(d):
        if f.endswith("_%s.jpg" % num) or os.path.splitext(f)[0] == num:
            return ImageOps.exif_transpose(Image.open(os.path.join(d, f)))
    raise SystemExit("not found")


def strip(tag, num, name, x, y0, y1, half=110, zoom=2.0, bright=1.6):
    im = load(tag, num)
    W, H = im.size
    c = im.crop((max(0, x-half), y0, min(W, x+half), y1))
    w, h = c.size
    c = c.resize((int(w*zoom), int(h*zoom)), Image.LANCZOS)
    c = ImageEnhance.Brightness(c).enhance(bright)
    c = ImageEnhance.Contrast(c).enhance(1.3)
    p = os.path.join(OUT, "_v8_4_rooms_%s_%s_%s.png" % (tag, num, name))
    c.save(p)
    print("%s src=%dx%d out=%s" % (os.path.basename(p), W, H, c.size))


if __name__ == "__main__":
    for a in sys.argv[1:]:
        f = a.split(",")
        strip(f[0], f[1], f[2], int(f[3]), int(f[4]), int(f[5]),
              int(f[6]) if len(f) > 6 else 110,
              float(f[7]) if len(f) > 7 else 2.0,
              float(f[8]) if len(f) > 8 else 1.6)

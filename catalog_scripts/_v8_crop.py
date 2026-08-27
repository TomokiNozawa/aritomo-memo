# -*- coding: utf-8 -*-
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
    raise SystemExit("not found %s %s" % (tag, num))


def crop(tag, num, name, box_frac, maxdim=1500):
    """box_frac = (l,t,r,b) as fractions of the transposed image."""
    im = load(tag, num)
    W, H = im.size
    l, t, r, b = box_frac
    box = (int(l*W), int(t*H), int(r*W), int(b*H))
    c = im.crop(box)
    w, h = c.size
    sc = float(maxdim) / max(w, h)
    if sc != 1:
        c = c.resize((max(1, int(w*sc)), max(1, int(h*sc))), Image.LANCZOS)
    p = os.path.join(OUT, "_v8_4_rooms_%s_%s_%s.png" % (tag, num, name))
    c.save(p)
    print("%s  src=%dx%d box=%s out=%s" % (os.path.basename(p), W, H, box, c.size))


if __name__ == "__main__":
    import json
    for arg in sys.argv[1:]:
        tag, num, name, l, t, r, b = arg.split(",")
        crop(tag, num, name, (float(l), float(t), float(r), float(b)))

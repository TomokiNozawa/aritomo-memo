# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image, ImageOps

BASE = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等"
ROOMS = {"48": "05_4.8帖", "62": "04_6.2帖", "45": "06_4.5帖"}


def load(tag, num):
    d = os.path.join(BASE, ROOMS[tag])
    for f in os.listdir(d):
        if f.endswith("_%s.jpg" % num):
            return ImageOps.exif_transpose(Image.open(os.path.join(d, f)))


def hscan(tag, num, x0, x1, y0, y1, label, thr=5.0):
    a = np.asarray(load(tag, num).convert("L"), dtype=np.float32)
    band = a[y0:y1, x0:x1].mean(axis=1)
    band = np.convolve(band, np.ones(5)/5.0, mode="same")
    d = np.abs(np.diff(band))
    out, i = [], 1
    while i < len(d)-1:
        if d[i] > thr and d[i] >= d[i-1] and d[i] >= d[i+1]:
            out.append((y0+i, round(float(d[i]), 1)))
            i += 8
        else:
            i += 1
    print("[%s] y-edges (x %d..%d):" % (label, x0, x1), out)


# 4.5 photo 48: closed leaf spans x 1896..2580; sample its middle
hscan("45", "48", 2350, 2450, 60, 400, "45/48 door TOP")
hscan("45", "48", 2350, 2450, 1900, 2249, "45/48 door BOTTOM")
# same for the leading panel (nearer camera-left)
hscan("45", "48", 1980, 2080, 60, 400, "45/48 top @leadpanel")
hscan("45", "48", 1980, 2080, 1900, 2249, "45/48 bottom @leadpanel")

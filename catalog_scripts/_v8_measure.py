# -*- coding: utf-8 -*-
"""Locate vertical joints / horizontal edges by luminance gradient scans."""
import os, sys
import numpy as np
from PIL import Image, ImageOps

BASE = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等"
ROOMS = {"48": "05_4.8帖", "62": "04_6.2帖", "45": "06_4.5帖"}


def load(tag, num):
    d = os.path.join(BASE, ROOMS[tag])
    for f in os.listdir(d):
        if f.endswith("_%s.jpg" % num) or os.path.splitext(f)[0] == num:
            return ImageOps.exif_transpose(Image.open(os.path.join(d, f)))
    raise SystemExit("not found")


def vscan(tag, num, y0, y1, x0, x1, label, thr=6.0):
    im = load(tag, num).convert("L")
    a = np.asarray(im, dtype=np.float32)
    band = a[y0:y1, x0:x1].mean(axis=0)
    band = np.convolve(band, np.ones(5)/5.0, mode="same")
    d = np.abs(np.diff(band))
    peaks = []
    i = 1
    while i < len(d)-1:
        if d[i] > thr and d[i] >= d[i-1] and d[i] >= d[i+1]:
            peaks.append((x0+i, round(float(d[i]), 1)))
            i += 6
        else:
            i += 1
    print("[%s] vertical edges x (y=%d..%d):" % (label, y0, y1))
    print("   ", peaks)


def hscan(tag, num, x0, x1, y0, y1, label, thr=6.0):
    im = load(tag, num).convert("L")
    a = np.asarray(im, dtype=np.float32)
    band = a[y0:y1, x0:x1].mean(axis=1)
    band = np.convolve(band, np.ones(5)/5.0, mode="same")
    d = np.abs(np.diff(band))
    peaks = []
    i = 1
    while i < len(d)-1:
        if d[i] > thr and d[i] >= d[i-1] and d[i] >= d[i+1]:
            peaks.append((y0+i, round(float(d[i]), 1)))
            i += 6
        else:
            i += 1
    print("[%s] horizontal edges y (x=%d..%d):" % (label, x0, x1))
    print("   ", peaks)


if __name__ == "__main__":
    # 4.8 room, photo 61: closed 4-panel closet
    vscan("48", "61", 900, 1100, 1150, 2680, "48/61 joints @midupper", 4.0)
    vscan("48", "61", 1700, 1800, 1150, 2680, "48/61 joints @lower", 4.0)
    hscan("48", "61", 1880, 1960, 60, 400, "48/61 door top @center", 4.0)
    hscan("48", "61", 1880, 1960, 1900, 2200, "48/61 door bottom @center", 4.0)
    print()
    # 4.5 room, photo 48: closed right leaf
    vscan("45", "48", 1100, 1300, 1700, 2760, "45/48 closed-leaf joints", 4.0)

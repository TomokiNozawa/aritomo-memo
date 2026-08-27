# -*- coding: utf-8 -*-
import os, numpy as np
from PIL import Image, ImageOps
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
def up(n):
    return ImageOps.exif_transpose(Image.open(os.path.join(SRC, f"LINE_ALBUM_20260820 内覧_260820_{n}.jpg"))).convert("L")

def vedges(n, y0, y1, x0, x1, top=12):
    a = np.asarray(up(n), dtype=np.float32)[y0:y1, x0:x1]
    prof = a.mean(axis=0)
    g = np.abs(np.gradient(prof))
    # non-max suppression
    idx = np.argsort(g)[::-1]
    picked=[]
    for i in idx:
        if all(abs(i-p)>8 for p in picked):
            picked.append(i)
        if len(picked)>=top: break
    picked.sort()
    print(f"photo {n} rows {y0}-{y1}: vertical edges (x abs) ->")
    for p in picked:
        print(f"   x={x0+p}  grad={g[p]:.1f}  val_left={prof[max(0,p-6)]:.0f} val_right={prof[min(len(prof)-1,p+6)]:.0f}")

def hedges(n, x0, x1, y0, y1, top=12):
    a = np.asarray(up(n), dtype=np.float32)[y0:y1, x0:x1]
    prof = a.mean(axis=1)
    g = np.abs(np.gradient(prof))
    idx = np.argsort(g)[::-1]
    picked=[]
    for i in idx:
        if all(abs(i-p)>8 for p in picked):
            picked.append(i)
        if len(picked)>=top: break
    picked.sort()
    print(f"photo {n} cols {x0}-{x1}: horizontal edges (y abs) ->")
    for p in picked:
        print(f"   y={y0+p}  grad={g[p]:.1f}  val_up={prof[max(0,p-6)]:.0f} val_dn={prof[min(len(prof)-1,p+6)]:.0f}")

if __name__=="__main__":
    print(up("65").size, up("67").size)
    for band in [(1500,1600),(2000,2100),(2500,2600),(2900,3000)]:
        vedges("65", band[0], band[1], 550, 1300, top=8)
    print("---- vertical extent of door (columns 800-1000) ----")
    hedges("65", 800, 1000, 850, 3200, top=8)

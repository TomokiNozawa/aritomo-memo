# -*- coding: utf-8 -*-
"""間取り図_文字なし.jpg の 行/列 を走査して 暗い run (線) の px 区間を吐く (読み取り専用)
usage:
  _plan_scan.py row <y> <x0> <x1> [thr]
  _plan_scan.py col <x> <y0> <y1> [thr]
"""
import os, sys
import numpy as np
from PIL import Image, ImageOps

BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other', '野沢用', 'claude', 'nozaROOM')
SRC = os.path.join(BOX, '間取り図等', '09_その他', '間取り図_文字なし.jpg')

im = ImageOps.exif_transpose(Image.open(SRC)).convert('L')
A = np.asarray(im, dtype=np.int16)

mode = sys.argv[1]
thr = int(sys.argv[5]) if len(sys.argv) > 5 else 150

if mode == 'row':
    y, x0, x1 = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    v = A[y, x0:x1]
    axis = 'x'
    base = x0
else:
    x, y0, y1 = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    v = A[y0:y1, x]
    axis = 'y'
    base = y0

dark = v < thr
runs = []
i = 0
while i < len(dark):
    if dark[i]:
        j = i
        while j < len(dark) and dark[j]:
            j += 1
        runs.append((base + i, base + j - 1, j - i))
        i = j
    else:
        i += 1
print('mode=%s thr=%d  dark runs (%s0,%s1,len):' % (mode, thr, axis, axis))
for a, b, n in runs:
    print('  %4d..%4d  (%d)' % (a, b, n))
# gaps between runs
print('gaps:')
for k in range(len(runs) - 1):
    print('  %4d..%4d  (%d)' % (runs[k][1] + 1, runs[k + 1][0] - 1, runs[k + 1][0] - runs[k][1] - 1))

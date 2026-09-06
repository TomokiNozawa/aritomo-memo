# -*- coding: utf-8 -*-
u"""公式製品画像の平らな面材から 色を画素実測 (中央値 + 標準偏差)。 推定色は使わない。"""
import sys
from PIL import Image
import statistics as st

def sample(f, box, tag):
    im = Image.open(f).convert('RGB').crop(box)
    px = list(im.getdata())
    ch = [[p[i] for p in px] for i in range(3)]
    med = [int(st.median(c)) for c in ch]
    sd = [round(st.pstdev(c), 1) for c in ch]
    print(u'%-34s %s  #%02x%02x%02x  sd=%s  n=%d' % (tag, box, med[0], med[1], med[2], sd, len(px)))

for a in sys.argv[1:]:
    f, x0, y0, x1, y1, tag = a.split(',')
    sample(f, (int(x0), int(y0), int(x1), int(y1)), tag)

def union(specs, tag):
    px = []
    for f, box in specs:
        px += list(Image.open(f).convert('RGB').crop(box).get_flattened_data())
    ch = [[p[i] for p in px] for i in range(3)]
    med = [int(st.median(c)) for c in ch]
    sd = [round(st.pstdev(c), 1) for c in ch]
    print(u'%-30s #%02x%02x%02x sd=%s n=%d' % (tag, med[0], med[1], med[2], sd, len(px)))

# -*- coding: utf-8 -*-
from PIL import Image
import statistics as st
def union(specs, tag):
    px = []
    for f, box in specs:
        px += list(Image.open(f).convert('RGB').crop(box).getdata())
    ch = [[p[i] for p in px] for i in range(3)]
    med = [int(st.median(c)) for c in ch]
    print(u'%-28s #%02x%02x%02x  sd=%s  n=%d' % (tag, med[0], med[1], med[2],
          [round(st.pstdev(c), 1) for c in ch], len(px)))
union([('img/dresser/07.jpg', (80, 225, 480, 265)), ('img/dresser/07.jpg', (450, 310, 600, 560))],
      u'WN 前板 union (studio)')

# -*- coding: utf-8 -*-
from PIL import Image
import statistics as st
def union(specs, tag):
    px = []
    for f, box in specs:
        px += list(Image.open(f).convert('RGB').crop(box).getdata())
    ch = [[p[i] for p in px] for i in range(3)]
    med = [int(st.median(c)) for c in ch]
    print(u'%-30s #%02x%02x%02x  sd=%s  n=%d' % (tag, med[0], med[1], med[2],
          [round(st.pstdev(c), 1) for c in ch], len(px)))
union([('img/chest/12.jpg', (245, 170, 495, 255)), ('img/chest/12.jpg', (245, 360, 495, 540))],
      u'SN 側板 (studio 12.jpg)')
union([('img/chest/02.jpg', (250, 300, 430, 420))], u'SN 前板 (room 02.jpg)')

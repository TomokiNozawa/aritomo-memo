# -*- coding: utf-8 -*-
import sys
from PIL import Image, ImageDraw
f = sys.argv[1]
im = Image.open(f).convert('RGB')
d = ImageDraw.Draw(im)
W, H = im.size
for x in range(0, W, 50):
    d.line([(x, 0), (x, H)], fill=(255, 0, 0)); d.text((x + 2, 2), str(x), fill=(255, 0, 0))
for y in range(0, H, 50):
    d.line([(0, y), (W, y)], fill=(0, 0, 255)); d.text((2, y + 2), str(y), fill=(0, 0, 255))
im.save(sys.argv[2])
print(f, im.size)

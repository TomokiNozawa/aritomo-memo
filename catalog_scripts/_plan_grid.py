# -*- coding: utf-8 -*-
"""間取り図_文字なし.jpg を px グリッド付きで切り出す (読み取り専用)
usage: _plan_grid.py <out.png> <x0> <y0> <x1> <y1> <zoom> <step> [file]
"""
import os, sys
from PIL import Image, ImageOps, ImageDraw, ImageFont

BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other', '野沢用', 'claude', 'nozaROOM')
SRC = os.path.join(BOX, '間取り図等', '09_その他')
SCR = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp', 'claude',
                   'C--Program-Files-Git', '75dc93bd-ffa2-4f4b-9a4a-91a3cabfe85f', 'scratchpad')

out = sys.argv[1]
x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
z = float(sys.argv[6]); step = int(sys.argv[7])
name = sys.argv[8] if len(sys.argv) > 8 else '間取り図_文字なし.jpg'

im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, name))).convert('RGB')
c = im.crop((x0, y0, x1, y1)).resize((int((x1 - x0) * z), int((y1 - y0) * z)), Image.LANCZOS)
d = ImageDraw.Draw(c)
try:
    F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 12)
except Exception:
    F = ImageFont.load_default()
for X in range(((x0 + step - 1) // step) * step, x1, step):
    u = (X - x0) * z
    d.line([(u, 0), (u, c.height)], fill=(255, 0, 0), width=1)
    d.text((u + 2, 2), str(X), fill=(255, 0, 0), font=F)
for Y in range(((y0 + step - 1) // step) * step, y1, step):
    v = (Y - y0) * z
    d.line([(0, v), (c.width, v)], fill=(0, 120, 255), width=1)
    d.text((2, v + 1), str(Y), fill=(0, 120, 255), font=F)
os.makedirs(SCR, exist_ok=True)
c.save(os.path.join(SCR, out), quality=95)
print('saved', os.path.join(SCR, out), c.size, 'orig', im.size)

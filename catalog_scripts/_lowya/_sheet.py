# -*- coding: utf-8 -*-
import glob, os
from PIL import Image, ImageDraw
for sub in ('dresser', 'chest'):
    fs = sorted(glob.glob(os.path.join('img', sub, '*.jpg')))
    C, T = 5, 260
    rows = (len(fs) + C - 1) // C
    sheet = Image.new('RGB', (C * T, rows * (T + 18)), 'white')
    dr = ImageDraw.Draw(sheet)
    for i, f in enumerate(fs):
        im = Image.open(f).convert('RGB'); im.thumbnail((T, T))
        x, y = (i % C) * T, (i // C) * (T + 18)
        sheet.paste(im, (x, y + 18))
        dr.text((x + 4, y + 4), os.path.basename(f), fill='black')
    sheet.save('_sheet_%s.png' % sub)
    print(sub, len(fs), sheet.size)

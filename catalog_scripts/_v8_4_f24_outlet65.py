# -*- coding: utf-8 -*-
exec(open(r"C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_f24_edges.py",encoding="utf-8").read().split('if __name__')[0])
print("=== 65 outlet plate: vertical edges rows 2470-2540, x 1180-1300 ===")
vedges("65", 2470, 2540, 1180, 1300, top=5)
print("=== 65 outlet plate: horizontal edges cols 1215-1255, y 2420-2600 ===")
hedges("65", 1215, 1255, 2420, 2600, top=5)
import PIL.Image, PIL.ExifTags, os
for n in ["65","66","67","68"]:
    p = os.path.join(SRC, f"LINE_ALBUM_20260820 内覧_260820_{n}.jpg")
    ex = PIL.Image.open(p)._getexif() or {}
    d = {PIL.ExifTags.TAGS.get(k,k):v for k,v in ex.items()}
    print(n, "FocalLength", d.get("FocalLength"), "F35", d.get("FocalLengthIn35mmFilm"), "Model", d.get("Model"))

# -*- coding: utf-8 -*-
exec(open(r"C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_f24_edges.py",encoding="utf-8").read().split('if __name__')[0])
print("=== 65: cols 750-1150, y 150-1350 (find ceiling) ===")
hedges("65", 750, 1150, 150, 1350, top=10)
print("=== 65: cols 1200-1400 (east of closet corner), y 150-1400 ===")
hedges("65", 1200, 1400, 150, 1400, top=10)
print("=== 65: cols 600-700 (west sliver), y 150-1400 ===")
hedges("65", 600, 700, 150, 1400, top=10)

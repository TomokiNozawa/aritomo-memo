# -*- coding: utf-8 -*-
exec(open(r"C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_f24_edges.py",encoding="utf-8").read().split('if __name__')[0])
print("=== 65: ceiling/top region, cols 750-1150, y 600-1400 ===")
hedges("65", 750, 1150, 600, 1400, top=10)
print("=== 65: floor region, cols 750-1150, y 2900-3300 ===")
hedges("65", 750, 1150, 2900, 3300, top=10)
print("=== 65: corner column 1186 vertical extent, cols 1170-1200 ===")
hedges("65", 1170, 1200, 600, 3300, top=10)

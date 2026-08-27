# -*- coding: utf-8 -*-
exec(open(r"C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_f24_edges.py",encoding="utf-8").read().split('if __name__')[0])
for band in [(1400,1500),(1900,2000),(2400,2500),(2900,3000)]:
    vedges("67", band[0], band[1], 850, 1600, top=8)
print("=== 67: door vertical extent cols 1050-1250, y 900-3300 ===")
hedges("67", 1050, 1250, 900, 3300, top=10)
print("=== 67: ceiling/floor at closet, cols 1000-1300, y 400-1300 ===")
hedges("67", 1000, 1300, 400, 1300, top=10)
print("=== 67: floor, cols 1000-1300, y 2900-3300 ===")
hedges("67", 1000, 1300, 2900, 3300, top=10)

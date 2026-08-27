# -*- coding: utf-8 -*-
exec(open(r"C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_f24_edges.py",encoding="utf-8").read().split('if __name__')[0])
print(up("66").size)
print("=== 66: outlet plate on north wall: vertical edges, rows 1500-1590, x 1650-1820 ===")
vedges("66", 1500, 1590, 1650, 1820, top=6)
print("=== 66: outlet plate horizontal edges, cols 1710-1750, y 1440-1650 ===")
hedges("66", 1710, 1750, 1440, 1650, top=6)
print("=== 66: closet door edges, rows 1000-1100 / 1500-1600 / 1900-2000, x 850-1650 ===")
for b in [(1000,1100),(1500,1600),(1900,2000)]:
    vedges("66", b[0], b[1], 850, 1650, top=8)

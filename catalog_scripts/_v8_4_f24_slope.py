# -*- coding: utf-8 -*-
exec(open(r"C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_f24_edges.py",encoding="utf-8").read().split('if __name__')[0])
import numpy as np
def edge_y(n, x0, x1, y0, y1):
    a = np.asarray(up(n), dtype=np.float32)[y0:y1, x0:x1]
    prof = a.mean(axis=1); g = np.abs(np.gradient(prof))
    i = int(np.argmax(g)); return y0+i, float(g[i])
print("--- 65 door TOP edge y at successive x windows (search y 1250-1380) ---")
for x0 in range(710, 1110, 50):
    print(x0, x0+50, edge_y("65", x0, x0+50, 1250, 1380))
print("--- 65 door BOTTOM edge y (search y 2950-3060) ---")
for x0 in range(730, 1110, 50):
    print(x0, x0+50, edge_y("65", x0, x0+50, 2950, 3060))
print("--- 65 CEILING line y at closet face (search y 850-1030) ---")
for x0 in range(700, 1180, 60):
    print(x0, x0+60, edge_y("65", x0, x0+60, 850, 1030))

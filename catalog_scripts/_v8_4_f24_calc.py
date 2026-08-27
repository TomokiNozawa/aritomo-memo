# -*- coding: utf-8 -*-
# photo 65 (upright 2250x4000, ultra-wide 2.68mm / 16mm-eq, verified fronto-parallel)
ceil_y, floor_y = 941.0, 3026.0
H = float(240)  # 天井高 (実測メモ 全体注記「天井高 約240」)
scale = H/(floor_y-ceil_y)      # cm per px
def cm(px): return round(px*scale,1)
print("scale cm/px = %.5f  (closet face height %.0f px = %.0f cm)" % (scale, floor_y-ceil_y, H))
items = [("収納 南面 外形幅 (688→1186)", 1186-688),
         ("扉1枚 (戸決り間 708→1112)", 1112-708),
         ("扉1枚 (見え掛り 717→1103)", 1103-717),
         ("扉 高さ (1313→3013)", 3013-1313),
         ("垂れ壁 (941→1313)", 1313-941),
         ("東側 枠/柱 見付け (1126→1186)", 1186-1126),
         ("西側 枠 (694→716)", 716-694)]
for n,p in items: print(f"  {n}: {p:.0f} px = {cm(p)} cm")
print()
print("逆算: 見付け65cm となるために必要な天井高 = %.0f cm" % ((1186-688)/ (1186-688) * 65/ ( (1186-688)/(floor_y-ceil_y) )))
print("逆算: 扉1枚38cm となるために必要な天井高 = %.0f cm" % (38/((1112-708)/(floor_y-ceil_y))))

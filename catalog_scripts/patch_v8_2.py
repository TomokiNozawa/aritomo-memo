# -*- coding: utf-8 -*-
"""v8.2: ニトリ アザン3 の4色を「同一部位・同一条件」で採り直す。冪等。

v8.1 は 室内カット写真の『足元側 側板』(= 影側) から採っていたため、
albedo ではなく陰影込みの見え方になっていた。3D は Lambert で更に暗くなるので
二重に暗くなり、「ホワイトウォッシュ」が茶色く見えていた (WW #beb5a6)。

v8.2 は 4色とも **ヘッドボードの平らな面材** から採り直す。
サンプル領域は下記のとおりで、いずれも標準偏差が小さい = 木口・影・背景・小物が
混ざっていない平らな面だけを拾えていることの機械的な裏付け。

  WW   08_公式商品画像_WW_ヘッドボード背面.jpg   rect(216,384,660,696)   #ebe6e0  sd=(3.8,3.8,3.9)
  GY   13_公式商品画像_GY_ヘッドボード背面.jpg   rect(420,522,792,594)   #a19080  sd=(6.5,7.0,7.2)
  LBR3 14_公式商品画像_LBR3_ヘッドボード背面.jpg rect(420,522,792,594)   #b79162  sd=(5.0,4.9,5.0)
  MBR2 15_公式商品画像_MBR2_ヘッドボード.jpg     rect(144,792,720,1056)  #926645  sd=(11.5,9.9,8.7)

(MBR2 のみ画像の画角が違う = 背面ではなく正面の接写なので、同じく平らな前板から採った)

CATALOG_SEED v2.8 -> v2.9 / ROOM_DATA 不変 / アザン3以外の34商品はバイト単位で不変。
"""
import io
import re
import json
import hashlib
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'

# 旧値 (影側から採った値) -> 新値 (平らな面材から採り直した値)
NEW = {
    'ホワイトウォッシュ': ('#beb5a6', '#ebe6e0'),
    'グレーウォッシュ':   ('#988372', '#a19080'),
    'ライトブラウン':     ('#ae8452', '#b79162'),
    'ミドルブラウン':     ('#7b5437', '#926645'),
}


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


src = io.open(P, encoding='utf-8').read()
rd_before = sha(RD_PAT, src)
items_before = json.loads(re.search(CS_PAT, src, re.S).group(1))['items']

if '#ebe6e0' in src:
    print('適用0件 / skip 1件 (既に採り直し済み)')
    sys.exit(0)

m = re.search(CS_PAT, src, re.S)
cs = json.loads(m.group(1))
hit = 0
for it in cs['items']:
    if 'アザン' not in (it.get('name') or ''):
        continue
    hit += 1
    changed = []
    for c in it.get('colors') or []:
        for key, (old, new) in NEW.items():
            if key in (c.get('name') or ''):
                assert c.get('hex') == old, '%s の旧値が想定と違う: %s' % (key, c.get('hex'))
                c['hex'] = new
                changed.append('%s %s→%s' % (key, old, new))
    assert len(changed) == 4, '4色そろっていない: %s' % changed
    it['color'] = NEW['ホワイトウォッシュ'][1]          # 既定 = WW
    it['specNote'] = (it.get('specNote') or '') + (
        ' ★v8.2 カラーの16進を採り直した: v8.1 は室内カット写真の『足元側 側板』(影側) から'
        '採っていたため albedo ではなく陰影込みの値になり、3D の Lambert で二重に暗くなって'
        '「ホワイトウォッシュ」が茶色く見えていた (旧 WW #beb5a6)。'
        'v8.2 は4色とも【ヘッドボードの平らな面材】から採り直し '
        '(WW #ebe6e0 sd3.8 / GY #a19080 sd6.5 / LBR3 #b79162 sd5.0 / MBR2 #926645 sd11.5、'
        'いずれも標準偏差が小さく木口・影・背景・小物が混ざっていないことの裏付け)。'
        'サンプル画像と領域は Box の README に記録。'
    )
    print('  ' + ' / '.join(changed))
assert hit == 1, 'アザン3 が %d 件 (1件のはず)' % hit

cs['version'] = '2.9'
cs['updatedAt'] = '2026-08-24'
src = (src[:m.start()]
       + 'var CATALOG_SEED = ' + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n'
       + src[m.end():])

assert sha(RD_PAT, src) == rd_before, 'ROOM_DATA が変化した'
items_after = json.loads(re.search(CS_PAT, src, re.S).group(1))['items']
assert len(items_after) == len(items_before) == 35, 'アイテム数が変わった'
J = (lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True))
changed_names = [a.get('name') for a, b in zip(items_after, items_before) if J(a) != J(b)]
assert len(changed_names) == 1 and 'アザン' in changed_names[0], \
    '意図しない商品が変わった: %s' % changed_names

io.open(P, 'w', encoding='utf-8', newline='').write(src)
print('適用1件 (アザン3 の4色を平らな面材から採り直し / 既定 WW も更新)')
print('ROOM_DATA sha256 %s (不変) / 変更は「%s」のみ' % (rd_before[:12], changed_names[0]))

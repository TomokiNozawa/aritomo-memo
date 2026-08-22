# -*- coding: utf-8 -*-
u"""現在の room.html から **v6.7 パッチだけを巻き戻した** 比較用ファイルを作る。
   (並行セッションの v6.6 等 他の変更は そのまま残るので、 before/after の差が
    v6.7 の1件だけになる)  出力: catalog_scripts/_before_v6_1.html
"""
import importlib.util, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location('p67', os.path.join(HERE, 'patch_washdoor_v6_7.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

text = p.read_text()

# JS パッチを逆方向 (new → old) に当てる
for name, marker, old, new in p.JS_PATCHES:
    n = text.count(new)
    assert n == 1, u'逆パッチ失敗 %s: %d 件' % (name, n)
    text = text.replace(new, old, 1)

# ROOM_DATA を v6.1 相当へ戻す (walls の分割を戻し version/notes を戻す)
i, line = p.data_line(text, p.RD_PREFIX)
rd, semi = p.parse_json_line(line, p.RD_PREFIX)
walls = rd['walls']
i2 = [k for k, w in enumerate(walls) if w.get('id') == 'W-LDK-N2']
i3 = [k for k, w in enumerate(walls) if w.get('id') == 'W-LDK-N3']
assert len(i2) == 1 and len(i3) == 1
old_n2 = {u'id': u'W-LDK-N2', u'name': u'LDK北壁②（キッチン）', u'room': u'ldk', u'dir': u'N',
          u'horiz': True, u'c': 208.5, u'from': 364.0, u'to': 790.0, u'length': 426.0,
          u'height': 240, u'outSign': -1, u'where': u'x364.0〜790.0 (y208.5)', u'seq': 2,
          u'of': 2, u'minor': False, u'feature': u'キッチン / タイル壁 / ダクト / コンロ'}
del walls[i3[0]]
walls[i2[0]] = old_n2
[w for w in walls if w['id'] == 'W-LDK-N1'][0]['of'] = 2
rd['meta']['version'] = '6.1'
rd['meta']['notes'] = [n for n in rd['meta']['notes'] if u'★v6.2 (2026-08-22)' not in n]
lines = text.split('\n')
lines[i] = p.dump_json_line(rd, p.RD_PREFIX, semi)
text = '\n'.join(lines)

out = os.path.join(HERE, '_before_v6_1.html')
io.open(out, 'w', encoding='utf-8', newline='').write(text)
print(u'書き出し: %s' % out)
print(u'  OPEN_MATCH_TOL 残存 = %d 件 (0 が正)' % text.count('OPEN_MATCH_TOL'))
print(u'  ROOM_DATA version   = %s' % rd['meta']['version'])

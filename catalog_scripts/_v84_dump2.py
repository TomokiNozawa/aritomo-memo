# -*- coding: utf-8 -*-
import io, json
src = io.open(r'C:\Users\t2262\aritomo-memo\room.html', encoding='utf-8').read()
for ln in src.split('\n'):
    if ln.startswith('var ROOM_DATA = '):
        rd = json.loads(ln[len('var ROOM_DATA = '):].rstrip().rstrip(';')); break
print('== ROOMS ==')
for r in rd['rooms']:
    print(r.get('id'), r.get('name'), r.get('poly') or r.get('rect'))
print()
print('== WALLS (those crossing y 180..400 or x 400..800) ==')
for w in rd['walls']:
    print(json.dumps(w, ensure_ascii=False))

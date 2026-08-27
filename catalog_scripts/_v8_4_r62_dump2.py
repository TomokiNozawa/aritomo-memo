# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8')
src = io.open(r'C:\Users\t2262\aritomo-memo\room.html', encoding='utf-8').read()
for ln in src.split('\n'):
    if ln.startswith('var ROOM_DATA = '):
        rd = json.loads(ln[len('var ROOM_DATA = '):].rstrip().rstrip(';')); break
print('=== rooms ===')
for r in rd['rooms']:
    print(r.get('id'), r.get('key'), r.get('name'), r.get('poly'))
print()
for sec in ['openings','fixtures','outlets','lights','walls']:
    print('===',sec,'(west6_2 / wic) ===')
    for o in rd[sec]:
        if o.get('room') in ('west6_2','wic','east62'):
            print(json.dumps(o, ensure_ascii=False)[:700])
    print()

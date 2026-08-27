# -*- coding: utf-8 -*-
import io, json
src = io.open(r'C:\Users\t2262\aritomo-memo\room.html', encoding='utf-8').read()
for ln in src.split('\n'):
    if ln.startswith('var ROOM_DATA = '):
        rd = json.loads(ln[len('var ROOM_DATA = '):].rstrip().rstrip(';')); break
print('== FIXTURES ==')
for f in rd['fixtures']:
    print(f.get('id'), '|', f.get('name'), '| rect=',f.get('rect'), '| h=',f.get('h'),'bottomH=',f.get('bottomH'))
    if f.get('label'): print('     label:', f['label'])
print()
print('== OPENINGS ==')
for o in rd['openings']:
    print(json.dumps(o, ensure_ascii=False))

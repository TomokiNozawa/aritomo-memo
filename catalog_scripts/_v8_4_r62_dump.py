# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8')
src = io.open(r'C:\Users\t2262\aritomo-memo\room.html', encoding='utf-8').read()
rd=None
for ln in src.split('\n'):
    if ln.startswith('var ROOM_DATA = '):
        rd = json.loads(ln[len('var ROOM_DATA = '):].rstrip().rstrip(';')); break
print('top keys:', list(rd.keys()))
def scan(o, path=''):
    if isinstance(o, dict):
        s = json.dumps(o, ensure_ascii=False)
        yield path, o
        for k,v in o.items():
            yield from scan(v, path+'/'+str(k))
    elif isinstance(o, list):
        for i,v in enumerate(o):
            yield from scan(v, path+'/%d'%i)

hits=[]
for path,o in scan(rd):
    s=json.dumps(o, ensure_ascii=False)
    if any(w in s for w in ['通気','換気','給気','空気','vent','エアコン','AC-']) and len(s)<600:
        hits.append((path,s))
seen=set()
for p,s in hits:
    if s in seen: continue
    seen.add(s)
    print(p, s)

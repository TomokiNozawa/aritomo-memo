# -*- coding: utf-8 -*-
import io, json, sys
src = io.open(r'C:\Users\t2262\aritomo-memo\room.html', encoding='utf-8').read()
rd=None
for ln in src.split('\n'):
    if ln.startswith('var ROOM_DATA = '):
        rd = json.loads(ln[len('var ROOM_DATA = '):].rstrip().rstrip(';')); break
print('keys', list(rd.keys()))
def out(s):
    sys.stdout.write(s+'\n')
for k,v in rd.items():
    if isinstance(v,list):
        out('--- %s (%d) ---'%(k,len(v)))

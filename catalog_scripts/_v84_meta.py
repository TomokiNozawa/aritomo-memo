# -*- coding: utf-8 -*-
import io,json
src=io.open(r'C:\Users\t2262\aritomo-memo\room.html',encoding='utf-8').read()
for ln in src.split('\n'):
    if ln.startswith('var ROOM_DATA = '):
        rd=json.loads(ln[len('var ROOM_DATA = '):].rstrip().rstrip(';')); break
print(json.dumps(rd['meta'],ensure_ascii=False,indent=1))

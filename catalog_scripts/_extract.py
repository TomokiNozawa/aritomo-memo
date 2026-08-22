# -*- coding: utf-8 -*-
"""room.html から ROOM_DATA / CATALOG_SEED を抽出して JSON で吐く (読み取り専用)"""
import io, json, os, re, hashlib, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'room.html')
OUT = os.path.join(ROOT, 'catalog_scripts', '_out')
os.makedirs(OUT, exist_ok=True)

src = io.open(HTML, encoding='utf-8').read()
lines = src.split('\n')

def grab(varname):
    for i, l in enumerate(lines):
        if l.startswith('var %s = {' % varname):
            body = l[len('var %s = ' % varname):]
            body = body.rstrip()
            if body.endswith(';'):
                body = body[:-1]
            return i, body
    raise SystemExit('not found: ' + varname)

i_rd, rd_txt = grab('ROOM_DATA')
i_cs, cs_txt = grab('CATALOG_SEED')

print('ROOM_DATA line   =', i_rd + 1, 'len', len(rd_txt))
print('CATALOG_SEED line=', i_cs + 1, 'len', len(cs_txt))
print('CATALOG_SEED sha256 =', hashlib.sha256(cs_txt.encode('utf-8')).hexdigest())
print('ROOM_DATA    sha256 =', hashlib.sha256(rd_txt.encode('utf-8')).hexdigest())

rd = json.loads(rd_txt)
io.open(os.path.join(OUT, 'room_data.json'), 'w', encoding='utf-8').write(
    json.dumps(rd, ensure_ascii=False, indent=1))
print('version =', rd['meta']['version'])
print('top keys =', list(rd.keys()))
for k, v in rd.items():
    if isinstance(v, list):
        print('  %-12s len=%d' % (k, len(v)))

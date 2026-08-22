# -*- coding: utf-8 -*-
"""全 openings が 対応部屋のポリゴン辺に乗っているかを機械検証する (読み取り専用)"""
import io, json, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = json.load(io.open(os.path.join(ROOT, 'catalog_scripts', '_out', 'room_data.json'), encoding='utf-8'))

rooms = {r['id']: r for r in rd['rooms']}

print('=== ROOMS ===')
for r in rd['rooms']:
    print('%-12s %-14s poly=%s' % (r['id'], r.get('name', ''), r['poly']))

print()
print('=== OPENINGS ===')
for o in rd['openings']:
    print(json.dumps(o, ensure_ascii=False))

print()
print('=== WALLS (id, room, from, to) ===')
for w in rd['walls']:
    print('%-16s %-12s %s -> %s  %s' % (w.get('id'), w.get('room'), w.get('from'), w.get('to'), w.get('name', '')))

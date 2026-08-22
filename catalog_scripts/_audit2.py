# -*- coding: utf-8 -*-
"""buildWalls() の開口マッチングを Python で忠実に再現し、
   全開口 × 全部屋エッジ について 許容差を変えたときの マッチ状況を機械監査する。"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = json.load(io.open(os.path.join(ROOT, 'catalog_scripts', '_out', 'room_data.json'), encoding='utf-8'))

def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def opening_range(o):
    horiz = abs(o['wallFrom'][1] - o['wallTo'][1]) < 0.01
    c = o['wallFrom'][1] if horiz else o['wallFrom'][0]
    if horiz:
        a = min(o['wallFrom'][0], o['wallTo'][0]); b = max(o['wallFrom'][0], o['wallTo'][0])
    else:
        a = min(o['wallFrom'][1], o['wallTo'][1]); b = max(o['wallFrom'][1], o['wallTo'][1])
    return dict(horiz=horiz, c=c, a=a, b=b)

def edges():
    for room in rd['rooms']:
        poly = room['poly']; n = len(poly)
        for i in range(n):
            p1 = poly[i]; p2 = poly[(i + 1) % n]
            horiz = abs(p1[1] - p2[1]) < 0.01
            c = p1[1] if horiz else p1[0]
            if horiz:
                a = min(p1[0], p2[0]); b = max(p1[0], p2[0])
            else:
                a = min(p1[1], p2[1]); b = max(p1[1], p2[1])
            if b - a < 0.5: continue
            probe = [(a + b) / 2, c - 2] if horiz else [c - 2, (a + b) / 2]
            in_neg = point_in_poly(probe, poly)
            out_sign = 1 if in_neg else -1
            d = ('S' if in_neg else 'N') if horiz else ('E' if in_neg else 'W')
            yield dict(room=room['key'], rid=room.get('id'), horiz=horiz, c=c, a=a, b=b,
                       dir=d, outSign=out_sign, isBal=room['key'].startswith('balcony'))

EDGES = list(edges())

def matches(o, tol):
    r = opening_range(o)
    out = []
    for e in EDGES:
        if e['horiz'] != r['horiz']: continue
        if abs(r['c'] - e['c']) > tol: continue
        if min(r['b'], e['b']) - max(r['a'], e['a']) <= 2: continue
        out.append((e, abs(r['c'] - e['c'])))
    return out

def near_edges(o, tol):
    """許容差を無視して 「重なりのある平行エッジ」 を全部拾う (=本来くり抜くべき候補)"""
    r = opening_range(o)
    out = []
    for e in EDGES:
        if e['horiz'] != r['horiz']: continue
        if min(r['b'], e['b']) - max(r['a'], e['a']) <= 2: continue
        d = abs(r['c'] - e['c'])
        if d <= 30: out.append((e, d))
    return sorted(out, key=lambda x: x[1])

print('=== 開口ごと: 現行 tol=12 でくり抜かれるエッジ / 30cm以内の全候補エッジ ===')
bad = []
for o in rd['openings']:
    r = opening_range(o)
    m12 = matches(o, 18)
    ne = near_edges(o, 18)
    tag = 'horiz(y=%.1f)' % r['c'] if r['horiz'] else 'vert(x=%.1f)' % r['c']
    print('\n%-7s %-9s %s  range %.1f..%.1f  room=%s' % (o['id'], o['type'], tag, r['a'], r['b'], o['room']))
    own = [e for e, d in m12 if e['room'] == o['room']]
    print('   tol12 matched: ' + (', '.join('%s.%s c=%.1f (%.1f..%.1f) d=%.1f' % (e['room'], e['dir'], e['c'], e['a'], e['b'], d) for e, d in m12) or '(なし)'))
    others = [(e, d) for e, d in ne if not any(e is e2 for e2, _ in m12)]
    if others:
        print('   ★ tol12 で 外れた 近傍エッジ: ' + ', '.join('%s.%s c=%.1f (%.1f..%.1f) Δ=%.2f' % (e['room'], e['dir'], e['c'], e['a'], e['b'], d) for e, d in others))
    if not own:
        print('   ⚠ 自室のエッジに一致しない → パネル未描画')
        bad.append((o['id'], 'panel-missing'))
    if others:
        bad.append((o['id'], 'blocked-by:' + ','.join('%s.%s(Δ%.2f)' % (e['room'], e['dir'], d) for e, d in others)))

print('\n=== 問題サマリ ===')
for b in bad: print(' ', b)

print('\n=== 許容差を変えたときの マッチ数の変化 ===')
for tol in (12, 14, 16, 17, 18, 20, 24):
    tot = sum(len(matches(o, tol)) for o in rd['openings'])
    print('  tol=%-3s 総マッチ数=%d' % (tol, tot))

print('\n=== tol を 12→18 に上げたとき 新規に追加されるマッチ ===')
for o in rd['openings']:
    m12 = matches(o, 12); m18 = matches(o, 18)
    new = [(e, d) for e, d in m18 if not any(e is e2 for e2, _ in m12)]
    for e, d in new:
        print('  %-7s + %s.%s c=%.1f (%.1f..%.1f) Δ=%.2f' % (o['id'], e['room'], e['dir'], e['c'], e['a'], e['b'], d))

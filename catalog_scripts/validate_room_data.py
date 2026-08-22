# -*- coding: utf-8 -*-
u"""nozaROOM ROOM_DATA 常設バリデータ (読み取り専用) — ★v7.1 新設

room.html に埋め込まれた ROOM_DATA を読み、以下を ERROR / WARN で機械検出する。
「同じ実体に別IDが付いている」 二重登録を 二度と作らないための 恒久チェック。

  ── 重複検出 (★v7.1 の主目的) ──────────────────────────────
  D1 完全包含        : 3D AABB が 他要素を丸ごと含む                    → ERROR
  D2 bbox 80%重複    : 重なり体積 >= min(体積) * 0.8                    → ERROR
  D3 中心が内部      : 一方の中心が 他方の AABB 内にある                → WARN
  D4 同 type + 同名 かつ 近接 (中心間 60cm 以内)                        → ERROR
  D5 同 type + 同名 (離れている = 別実体か要確認)                       → WARN
     ※ 末尾の連番だけが違う名前 (ダウンライト12/13・高所小窓1/2 等) は
       「意図した連番シリーズ」 として D4/D5 の対象外にする。
  D6 実体のある fixture 同士が 少しでも貫通している                     → WARN
  ── 残骸検出 ────────────────────────────────────────
  R1 3D 非描画 fixture (FIX_STYLE に type が無い)                       → WARN
  R2 ROOM_DATA で未使用の FIX_STYLE type (JS 側の残骸)                  → WARN
  R3 ラベルの座標記述と rect の食い違い (過去改訂の置き去り)            → WARN
  R4 点要素 (コンセント/照明/エアコン) が 所属室のポリゴン外            → WARN
  ── 構造整合 ────────────────────────────────────────
  S1 ID の重複 / 欠番 / 採番規約違反                                    → ERROR
  S2 walls が 部屋ポリゴン+開口 から 再生成した結果と一致するか         → ERROR
  S3 開口が どの部屋ポリゴンの辺にも載っていない                        → ERROR

D1〜D3 には 「設計上わざと重なっている」 組み合わせの 許容リスト (ALLOW) がある。
新しく重なりが出たら 必ずここで検出されるので、 意図的なものだけ ALLOW に追記すること。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/validate_room_data.py
  終了コード: ERROR が 1 件でもあれば 1
"""
import io
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wallgen  # noqa: E402

ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, 'room.html')
OPEN_MATCH_TOL = 18.0        # room.html の同名定数と一致させること

ERRORS, WARNS = [], []


def err(t):
    ERRORS.append(t)
    print(u'  [ERROR] ' + t)


def warn(t):
    WARNS.append(t)
    print(u'  [WARN ] ' + t)


# ── 意図的な重なりの許容リスト ────────────────────────────────
#   (A, B, 理由)。 A/B は id。 順不同で照合する。
# ── リタイア済み ID (削除された要素。 二度と別の実体に再利用しない) ──
RETIRED_IDS = {
    'F-16': u'ペット小部屋 (petbase) — 実物は存在せず ただの白壁だった / v7.2 で削除',
    'OP-02': u'ペット小部屋の開口 62x66 — 旧 F-16 が同じものを描画していた二重定義 / v7.1 で削除',
}

ALLOW = [
    ('F-01', 'F-02', u'シンクはキッチンカウンターの天板に落とし込み'),
    ('F-01', 'F-03', u'コンロはキッチンカウンターの天板に落とし込み'),
    # ★v7.2 旧 F-17 (petbase) 削除にともなう繰り上げ (F-18→F-17 … F-53→F-53) に追従済み
    ('F-27', 'C-11', u'洗面台の側面に付くコンセント'),
    ('F-27', 'C-12', u'三面鏡裏収納の内部コンセント (ラベルに明記)'),
    ('F-12', 'C-20', u'クローゼット部分の上壁のコンセント'),
    ('F-12', 'D-04', u'クローゼットの扉は収納 fixture の面に付く'),
    ('F-34', 'C-07', u'シューズBOX 上・LDK側の壁面コンセント'),
    ('F-42', 'C-16', u'6.2帖 西壁 = PS(33帯) の面に付くコンセント'),
    ('F-21', 'C-05', u'タイルTV壁の面に付く集約コンセント'),
    ('F-32', 'F-35', u'姿見は玄関土間の西壁に付く (土間は非描画のデータ枠)'),
    ('F-32', 'OP-01', u'玄関⇔廊下の開口は土間の東端 (土間は非描画のデータ枠)'),
    ('F-48', 'F-49', u'ハンガーパイプは棚板の下面に吊る (高さで分離)'),
    ('F-15', 'F-17', u'吊戸棚はカウンターの真上 (高さで分離)'),
    ('F-15', 'F-20', u'モニターはカウンターの上方 (高さで分離)'),
    ('F-15', 'C-06', u'★v7.3 C-06 はニッチ一体カウンターの台下 (h65 < 天板下端71)'),
    ('D-10', 'L-16', u'玄関ダウンライトは玄関ドアの内側直近'),
]
ALLOW_SET = set()
for a, b, _ in ALLOW:
    ALLOW_SET.add((a, b))
    ALLOW_SET.add((b, a))
ALLOW_WHY = dict()
for a, b, w in ALLOW:
    ALLOW_WHY[(a, b)] = w
    ALLOW_WHY[(b, a)] = w


def load():
    src = io.open(TARGET, encoding='utf-8').read()
    rd = None
    for ln in src.split('\n'):
        if ln.startswith('var ROOM_DATA = '):
            b = ln[len('var ROOM_DATA = '):].rstrip()
            if b.endswith(';'):
                b = b[:-1]
            rd = json.loads(b)
            break
    assert rd, 'ROOM_DATA not found'
    m = re.search(r'const FIX_STYLE = \{(.*?)\n\};', src, re.S)
    assert m, 'FIX_STYLE not found'
    fix_types = set(re.findall(r'^\s*([a-z_]+):\s*\{', m.group(1), re.M))
    return rd, src, fix_types


def bbox_fix(f, ch):
    if f.get('poly'):
        xs = [p[0] for p in f['poly']]
        ys = [p[1] for p in f['poly']]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    else:
        r = f['rect']
        x0, y0, x1, y1 = r[0], r[1], r[0] + r[2], r[1] + r[3]
    b = float(f.get('bottomH') or 0)
    t = float(f.get('h') or ch)
    return (x0, x1, y0, y1, b, max(t, b + 0.1))


def bbox_open(o):
    a, b = o['wallFrom'], o['wallTo']
    x0, x1 = min(a[0], b[0]), max(a[0], b[0])
    y0, y1 = min(a[1], b[1]), max(a[1], b[1])
    if x1 - x0 < 1:
        x0, x1 = x0 - 5, x1 + 5
    if y1 - y0 < 1:
        y0, y1 = y0 - 5, y1 + 5
    s = float(o.get('sillH') or 0)
    h = float(o.get('height') or 200)
    return (x0, x1, y0, y1, s, s + h)


def vol(b):
    return max(b[1] - b[0], 0) * max(b[3] - b[2], 0) * max(b[5] - b[4], 0)


def inter(a, b):
    return (max(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), min(a[3], b[3]),
            max(a[4], b[4]), min(a[5], b[5]))


def contains(a, b, eps=0.01):
    return (a[0] <= b[0] + eps and a[1] >= b[1] - eps and a[2] <= b[2] + eps
            and a[3] >= b[3] - eps and a[4] <= b[4] + eps and a[5] >= b[5] - eps)


def center(b):
    return ((b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0, (b[4] + b[5]) / 2.0)


def pt_in(p, b, eps=0.01):
    return (b[0] - eps <= p[0] <= b[1] + eps and b[2] - eps <= p[1] <= b[3] + eps
            and b[4] - eps <= p[2] <= b[5] + eps)


SOLID_TYPES = set('''kitchen closet petbase pillar stub_wall shelf counter wall_cabinet
bathtub washstand toilet sink stove rangehood duct slide_zone panel glass pocket_panel
wall_shelf'''.split())


def base_and_no(s):
    u"""名前を 『基底』 と 『末尾連番』 に割る。 例 'LDK ダウンライト12' → ('LDK ダウンライト', '12')"""
    s = re.sub(u'[（(].*?[)）]', u'', s or u'').strip()
    m = re.search(r'(\d+)\s*$', s)
    if m:
        return s[:m.start()].strip(), m.group(1)
    return s, None


def main():
    rd, src, fix_types = load()
    ch = float(rd['ceilingH'])
    print(u'ROOM_DATA v%s  (%s)' % (rd['meta'].get('version'), TARGET))
    print(u'件数: ' + ' / '.join('%s=%d' % (k, len(rd[k])) for k in
                                ('rooms', 'openings', 'outlets', 'aircons', 'fixtures',
                                 'lights', 'zones', 'walls')))

    els = []   # (id, kind, name, bbox, raw)
    for o in rd['openings']:
        els.append((o['id'], 'opening', o.get('name', ''), bbox_open(o), o))
    for f in rd['fixtures']:
        els.append((f['id'], 'fixture', f.get('name', ''), bbox_fix(f, ch), f))
    for c in rd['outlets']:
        p, h = c['pos'], float(c.get('h') or 25)
        els.append((c['id'], 'outlet', c.get('name', ''),
                    (p[0] - 3.5, p[0] + 3.5, p[1] - 3.5, p[1] + 3.5, h - 6, h + 6), c))
    for a in rd['aircons']:
        p, y = a['pos'], float(a.get('bottomH') or 205)
        els.append((a['id'], 'aircon', a.get('name', ''),
                    (p[0] - 40, p[0] + 40, p[1] - 12, p[1] + 12, y, y + 26), a))
    for l in rd['lights']:
        p = l['pos']
        els.append((l['id'], 'light', l.get('name', ''),
                    (p[0] - 7, p[0] + 7, p[1] - 7, p[1] + 7, ch - 2, ch), l))

    # ── D1〜D3 空間重複 ──
    print(u'\n■ 重複検出 (空間)')
    for (i1, k1, n1, b1, r1), (i2, k2, n2, b2, r2) in itertools.combinations(els, 2):
        iv = inter(b1, b2)
        ov = vol(iv)
        if ov <= 0.001:
            continue
        ratio = ov / max(min(vol(b1), vol(b2)), 1e-9)
        allow = (i1, i2) in ALLOW_SET
        tag = u'%s「%s」× %s「%s」' % (i1, n1[:20], i2, n2[:20])
        if contains(b1, b2) or contains(b2, b1):
            (warn if allow else err)(u'D1 完全包含: ' + tag +
                                     (u'  ← 許容: ' + ALLOW_WHY[(i1, i2)] if allow else u''))
        elif ratio >= 0.8:
            (warn if allow else err)(u'D2 重なり %.0f%%: ' % (ratio * 100) + tag +
                                     (u'  ← 許容: ' + ALLOW_WHY[(i1, i2)] if allow else u''))
        elif pt_in(center(b1), b2) or pt_in(center(b2), b1):
            if not allow:
                warn(u'D3 中心が相手の内部 (重なり %.0f%%): ' % (ratio * 100) + tag)

    # ── D4/D5 意味重複 ──
    print(u'\n■ 重複検出 (意味)')
    for (i1, k1, n1, b1, r1), (i2, k2, n2, b2, r2) in itertools.combinations(els, 2):
        if k1 != k2:
            continue
        t1, t2 = r1.get('type'), r2.get('type')
        if t1 != t2 or t1 is None:
            continue
        s1 = (r1.get('shortLabel') or r1.get('short') or n1 or '').strip()
        s2 = (r2.get('shortLabel') or r2.get('short') or n2 or '').strip()
        if not s1 or not s2:
            continue
        b_1, no1 = base_and_no(s1)
        b_2, no2 = base_and_no(s2)
        if b_1 != b_2 or not b_1:
            continue
        if no1 and no2 and no1 != no2:
            continue          # 意図した連番シリーズ (ダウンライト12/13 等)
        c1, c2 = center(b1), center(b2)
        d = ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5
        tag = u'%s「%s」× %s「%s」 (中心間 %.1fcm)' % (i1, s1, i2, s2, d)
        if d <= 60:
            if (i1, i2) in ALLOW_SET:
                warn(u'D4 同 type+同名 かつ近接: ' + tag + u'  ← 許容')
            else:
                err(u'D4 同 type+同名 かつ近接 (同一実体の二重登録の疑い): ' + tag)
        else:
            warn(u'D5 同 type+同名 (別実体か要確認): ' + tag)

    # ── D6 実体のある fixture 同士の貫通 ──
    solids = [f for f in rd['fixtures'] if f.get('type') in SOLID_TYPES and f.get('rect')]
    for f1, f2 in itertools.combinations(solids, 2):
        b1, b2 = bbox_fix(f1, ch), bbox_fix(f2, ch)
        ov = vol(inter(b1, b2))
        if ov <= 100:
            continue
        if (f1['id'], f2['id']) in ALLOW_SET:
            continue
        warn(u'D6 実体のある設備が貫通している (%.0f cm³): %s「%s」× %s「%s」'
             % (ov, f1['id'], f1.get('name', '')[:18], f2['id'], f2.get('name', '')[:18]))

    # ── R1/R2 残骸 ──
    print(u'\n■ 残骸検出')
    for f in rd['fixtures']:
        if f['type'] not in fix_types:
            warn(u'R1 3D 非描画 fixture: %s「%s」 type=%s は FIX_STYLE に無く buildFixture が return する'
                 % (f['id'], f.get('name', ''), f['type']))
    used = set(f['type'] for f in rd['fixtures'])
    for t in sorted(fix_types - used):
        warn(u'R2 未使用の FIX_STYLE type (JS 側の残骸): %s' % t)

    # ── R3 ラベル座標と rect の食い違い ──
    for f in rd['fixtures']:
        if f.get('poly'):
            continue
        lab = f.get('label', '')
        r = f['rect']
        x0, x1 = r[0], r[0] + r[2]
        ms = re.findall(r'x(\d+(?:\.\d+)?)\.\.(\d+(?:\.\d+)?)', lab)
        if not ms:
            continue
        if not any(abs(float(a) - x0) < 1.0 and abs(float(b) - x1) < 1.0 for a, b in ms):
            warn(u'R3 ラベルの座標が rect と食い違う: %s「%s」 rect x%.1f..%.1f ↔ ラベル %s'
                 % (f['id'], f.get('name', '')[:20], x0, x1,
                    ' / '.join('x%s..%s' % (a, b) for a, b in ms[:2])))

    # ── R4 点要素が所属室の外 ──
    poly_of = dict((r['key'], r['poly']) for r in rd['rooms'])
    for arr, kind in ((rd['outlets'], u'コンセント'), (rd['lights'], u'照明'), (rd['aircons'], u'エアコン')):
        for e in arr:
            poly = poly_of.get(e.get('room'))
            if not poly:
                continue
            p = e['pos']
            if wallgen.point_in_poly(p, poly):
                continue
            xs = [q[0] for q in poly]
            ys = [q[1] for q in poly]
            d = max(xs[0] - p[0], p[0] - max(xs), min(ys) - p[1], p[1] - max(ys),
                    min(xs) - p[0])
            d = max(min(xs) - p[0], p[0] - max(xs), min(ys) - p[1], p[1] - max(ys))
            if d > 0.5:     # 壁面上 (d<=0) は正常。 外へはみ出しているものだけ
                warn(u'R4 %s が所属室の外: %s「%s」 pos=%s room=%s (ポリゴンから %.1fcm 外)'
                     % (kind, e['id'], e.get('name', '')[:24], p, e.get('room'), d))

    # ── S1 ID ──
    print(u'\n■ 構造整合')
    seen = {}
    for i, k, n, b, r in els:
        seen.setdefault(i, []).append(k)
    for i, ks in seen.items():
        if len(ks) > 1:
            err(u'S1 ID が重複: %s (%s)' % (i, ', '.join(ks)))
    for pre, arr, typ in (('OP', rd['openings'], 'open'), ('D', rd['openings'], None),
                          ('WIN', rd['openings'], 'window')):
        pass
    # ID は 「欠番を許して固定」 運用。 要素を削除しても後続を繰り上げない
    # (ユーザーが ID で部品を指定し、 ID付き平面図も配布済みのため ID の意味を変えない)。
    # 削除した ID は RETIRED_IDS に記録し、 二度と別の実体に再利用しない。
    for pre, ids in (('F', [f['id'] for f in rd['fixtures']]),
                     ('C', [c['id'] for c in rd['outlets']]),
                     ('L', [l['id'] for l in rd['lights']])):
        nums = [int(x.split('-')[1]) for x in ids]
        if nums != sorted(nums):
            err(u'S1 %s-NN が昇順でない: %s' % (pre, ids))
        if len(set(nums)) != len(nums):
            err(u'S1 %s-NN に重複がある: %s' % (pre, ids))
        holes = [n for n in range(1, max(nums) + 1) if n not in nums]
        unexpected = [n for n in holes if ('%s-%02d' % (pre, n)) not in RETIRED_IDS]
        if unexpected:
            err(u'S1 %s-NN に未登録の欠番: %s (削除したなら RETIRED_IDS に追記すること)'
                % (pre, ', '.join('%s-%02d' % (pre, n) for n in unexpected)))
        elif holes:
            print(u'   S1 %s-NN の欠番 %s = リタイア済み ID (正常)'
                  % (pre, ', '.join('%s-%02d' % (pre, n) for n in holes)))
        for n in nums:
            if ('%s-%02d' % (pre, n)) in RETIRED_IDS:
                err(u'S1 リタイア済み ID %s-%02d が再利用されている' % (pre, n))

    # ── S2 walls 再生成一致 ──
    regen = wallgen.regen(json.loads(json.dumps(rd)), OPEN_MATCH_TOL)
    J = lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True)
    if len(regen) != len(rd['walls']):
        err(u'S2 walls の件数が 再生成結果と違う: データ %d / 再生成 %d'
            % (len(rd['walls']), len(regen)))
    else:
        for a, b in zip(rd['walls'], regen):
            if J(a) != J(b):
                ks = [k for k in set(list(a) + list(b)) if a.get(k) != b.get(k)]
                err(u'S2 walls が 部屋ポリゴン+開口 から再生成した結果と違う: %s keys=%s cur=%s gen=%s'
                    % (a['id'], ks, {k: a.get(k) for k in ks}, {k: b.get(k) for k in ks}))

    # ── S3 開口が どの部屋の辺にも載っていない ──
    for o in rd['openings']:
        r0 = wallgen.opening_range(o)
        ok = False
        for r in rd['rooms']:
            poly = r['poly']
            for i in range(len(poly)):
                p1, p2 = poly[i], poly[(i + 1) % len(poly)]
                horiz = abs(p1[1] - p2[1]) < 0.01
                if horiz != r0['horiz']:
                    continue
                c = p1[1] if horiz else p1[0]
                if abs(c - r0['c']) > OPEN_MATCH_TOL:
                    continue
                a = min(p1[0], p2[0]) if horiz else min(p1[1], p2[1])
                b = max(p1[0], p2[0]) if horiz else max(p1[1], p2[1])
                if min(r0['b'], b) - max(r0['a'], a) > 2:
                    ok = True
        if not ok and not o.get('__fixtureFace'):
            warn(u'S3 開口が どの部屋ポリゴンの辺にも載らない (fixture 面に付く建具なら正常): %s「%s」'
                 % (o['id'], o.get('name', '')))

    print(u'\n════ 結果: ERROR %d 件 / WARN %d 件 ════' % (len(ERRORS), len(WARNS)))
    return 1 if ERRORS else 0


if __name__ == '__main__':
    sys.exit(main())

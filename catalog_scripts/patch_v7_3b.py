# -*- coding: utf-8 -*-
"""v7.3b: validator を 「ID は欠番を許して固定」 運用に合わせる。冪等。"""
import io, re, sys
P = r'C:\Users\t2262\aritomo-memo\catalog_scripts\validate_room_data.py'
s = io.open(P, encoding='utf-8').read()

if 'RETIRED_IDS' in s:
    print('適用0件 / skip 2件 (既に適用済み)'); sys.exit(0)

# ① ALLOW リストの F-ID を v7.2 の繰り上げ前 (=安定 ID) に戻す
head, sep, tail = s.partition('ALLOW_SET = set()')
def bump(m):
    n = int(m.group(1)); return 'F-%02d' % (n + 1) if 16 <= n <= 52 else m.group(0)
head2 = re.sub(r"F-(\d{2})\b", bump, head)
n_shift = sum(1 for _ in re.finditer(r"F-(\d{2})\b", head)) - sum(
    1 for a, b in zip(re.findall(r"F-(\d{2})\b", head), re.findall(r"F-(\d{2})\b", head2)) if a == b)
head2 = head2.replace(
    u'# ★v7.2 旧 F-16 (petbase) 削除にともなう繰り上げ (F-17→F-16 … F-53→F-52) に追従済み',
    u'# ★v7.3 ID は欠番を許して固定する運用 (繰り上げ禁止)。削除された ID は RETIRED_IDS へ。')
head2 = head2.replace(u'★v7.2 C-06 は', u'★v7.3 C-06 は')
s = head2 + sep + tail

# ② S1: 連番必須 → 「重複なし・昇順・欠番はリタイア済みのみ」 に緩和
old = u"""    for pre, ids in (('F', [f['id'] for f in rd['fixtures']]),
                     ('C', [c['id'] for c in rd['outlets']]),
                     ('L', [l['id'] for l in rd['lights']])):
        nums = [int(x.split('-')[1]) for x in ids]
        if nums != list(range(1, len(nums) + 1)):
            err(u'S1 %s-NN の連番が 1..%d の昇順でない: %s' % (pre, len(nums), ids))"""
new = u"""    # ID は 「欠番を許して固定」 運用。 要素を削除しても後続を繰り上げない
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
                err(u'S1 リタイア済み ID %s-%02d が再利用されている' % (pre, n))"""
assert old in s, 'S1 ブロックが見つからない'
s = s.replace(old, new)

# ③ RETIRED_IDS を ALLOW の直前に定義
anchor = u'ALLOW = ['
ret = u"""# ── リタイア済み ID (削除された要素。 二度と別の実体に再利用しない) ──
RETIRED_IDS = {
    'F-16': u'ペット小部屋 (petbase) — 実物は存在せず ただの白壁だった / v7.2 で削除',
    'OP-02': u'ペット小部屋の開口 62x66 — 旧 F-16 が同じものを描画していた二重定義 / v7.1 で削除',
}

"""
assert anchor in s
s = s.replace(anchor, ret + anchor, 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print(u'適用2件 (ALLOW の F-ID を安定 ID へ復元 / S1 を欠番許容に緩和 + RETIRED_IDS 新設)')

# -*- coding: utf-8 -*-
"""v7.3: F-ID の繰り上げを撤回し、ID を安定化する (F-16 は欠番として永久リタイア)。
v7.2 が petbase 削除に伴い F-17..F-53 → F-16..F-52 と繰り上げたが、
ユーザーは ID で部品を指定し、ID付き平面図も配布済みのため ID の意味が変わる方が有害。
以後「削除された ID は欠番のまま」の運用にする。冪等。"""
import io, re, json, hashlib, sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
SENT = '\x00RETIRED16\x00'

def catalog_sha(s):
    m = re.search(r'var CATALOG_SEED = (\{.*?\});\s*\n', s, re.S)
    return hashlib.sha256(m.group(1).encode()).hexdigest()

def fixture_ids(s):
    m = re.search(r'var ROOM_DATA = (\{.*?\});\s*\n', s, re.S)
    return [f['id'] for f in json.loads(m.group(1)).get('fixtures', [])]

src = io.open(P, encoding='utf-8').read()
cat_before = catalog_sha(src)
ids_before = fixture_ids(src)

if 'F-53' in src and 'F-16' not in [i for i in ids_before]:
    print('適用0件 / skip 1件 (既に ID 安定化済み・F-16 は欠番)')
    sys.exit(0)

# 「旧F-16(削除済)」= 削除された petbase への言及。シフト対象外なので退避。
n_prot = src.count('旧F-16')
src = src.replace('旧F-16', SENT)

# F-16..F-52 → F-17..F-53 (1パスのコールバックでカスケードを防ぐ)
shifted = [0]
def bump(m):
    n = int(m.group(1))
    if 16 <= n <= 52:
        shifted[0] += 1
        return 'F-%02d' % (n + 1)
    return m.group(0)
out = re.sub(r'F-(\d{2})\b', bump, src)
out = out.replace(SENT, '旧F-16')

# meta.version
out = re.sub(r'("version"\s*:\s*)"6\.8"', r'\1"6.9"', out, count=1)

ids_after = fixture_ids(out)
expect = ['F-%02d' % n for n in range(1, 54) if n != 16]
assert ids_after == expect, 'ID列が想定と不一致:\n  got %s' % ids_after
assert catalog_sha(out) == cat_before, 'CATALOG_SEED が変化した'
assert len(ids_after) == 52, 'fixture 数が変わった'

io.open(P, 'w', encoding='utf-8', newline='').write(out)
print('適用 %d件 (F-ID を +1 シフトして復元) / 旧F-16 言及の保護 %d件' % (shifted[0], n_prot))
print('CATALOG_SEED sha256 %s (不変)' % cat_before[:8])
print('fixtures: F-01..F-15, F-17..F-53  (F-16 = 欠番/リタイア)')

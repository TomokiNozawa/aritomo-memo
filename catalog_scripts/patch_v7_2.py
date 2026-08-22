# -*- coding: utf-8 -*-
u"""nozaROOM v7.2 — room.html への冪等パッチ (ROOM_DATA v6.7 → v6.8)

ユーザー確定 3件:
  ① F-16「ペット小部屋」(petbase) は実物に存在せず **ただの白壁** → ROOM_DATA から削除。
     関連コード (FIX_STYLE.petbase / buildFixture の petbase 分岐 = 開口62x66 の暗色パネル /
     SOLID_FIX_TYPES.petbase) も撤去。 ペットくぐり戸 (D-01/D-03/D-05 の petDoor) は別物なので残す。
  ② C-06「2口・台下」は その白壁 (旧 F-16 = x438..513) の一部にある → x559.5 (シューズBOX区間内) から移設。
  ③ PS / DPS が 2.5cm 重なっていた (v7.1 監査 D6) → 大元間取り図を再実測して PS・DPS・MB を是正。

F-16 を消すと F-NN が欠番になり バリデータ S1 が ERROR になるため、
v6.1 の前例どおり **F-17 以降を 1つずつ繰り上げる** (F-17→F-16 … F-53→F-52)。
参照している文字列 (labels / meta.notes) と JS 側の fixByIdRD / コメントも同時に書き換える。

安全装置:
  * CATALOG_SEED の sha256 が パッチ前後で **不変** であることを assert (カタログ側の並行作業を壊さない)
  * v7.0 が入れた F-51/F-52/F-53 (→ F-50/F-51/F-52)・WIN-05/06/07・AC-3 の
    ジオメトリが **1 値も変わっていない** ことを assert
  * 2回目以降の実行は 「適用 0 / skip N」 で終わる (冪等)

実行:  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v7_2.py
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wallgen  # noqa: E402

ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, 'room.html')
VALIDATOR = os.path.join(HERE, 'validate_room_data.py')

NEW_VERSION = '6.8'
OPEN_MATCH_TOL = 18.0

applied, skipped, problems = [], [], []


def ok(t):
    applied.append(t)
    print(u'  [APPLY] ' + t)


def sk(t):
    skipped.append(t)
    print(u'  [skip ] ' + t)


def die(t):
    print(u'  [FAIL ] ' + t)
    problems.append(t)


# ───────────────────────── 読み込み ─────────────────────────
src = io.open(TARGET, encoding='utf-8').read()
lines = src.split('\n')


def find_var(name):
    pre = 'var %s = ' % name
    for i, l in enumerate(lines):
        if l.startswith(pre + '{'):
            body = l[len(pre):].rstrip()
            if body.endswith(';'):
                body = body[:-1]
            return i, body
    raise SystemExit('not found: var %s' % name)


I_RD, RD_TXT = find_var('ROOM_DATA')
I_CS, CS_TXT = find_var('CATALOG_SEED')
SEED_SHA_BEFORE = hashlib.sha256(CS_TXT.encode('utf-8')).hexdigest()
RD_SHA_BEFORE = hashlib.sha256(RD_TXT.encode('utf-8')).hexdigest()
rd = json.loads(RD_TXT)

print(u'■ 入力')
print(u'  ROOM_DATA    line %d  version=%s  sha256=%s' % (I_RD + 1, rd['meta']['version'], RD_SHA_BEFORE))
print(u'  CATALOG_SEED line %d  sha256=%s' % (I_CS + 1, SEED_SHA_BEFORE))
print(u'  fixtures=%d outlets=%d walls=%d' % (len(rd['fixtures']), len(rd['outlets']), len(rd['walls'])))

# v7.0 の成果 (旧 id) を スナップショット。 ジオメトリキーだけ比較する
GEOM_KEYS = ('rect', 'poly', 'h', 'bottomH', 'railOffsets', 'railR', 'tassels', 'mount',
             'wallSide', 'room', 'type', 'width', 'sillH', 'height', 'wallFrom', 'wallTo',
             'pos', 'w', 'd', 'hgt', 'no')


def geom(e):
    return dict((k, e[k]) for k in GEOM_KEYS if k in e)


def by_id(arr, i):
    for e in arr:
        if e.get('id') == i:
            return e
    return None


def snap_by_name(arr, nm):
    for e in arr:
        if e.get('name') == nm:
            return geom(e)
    return None


V70_FIX = [u'カーテンレール(洋室6.2 高所小窓)', u'カーテンレール(洋室6.2 大窓)', u'室内物干し(天井付け)',
           u'カーテンレール(洋室4.8)']
V70_SNAP = dict((n, snap_by_name(rd['fixtures'], n)) for n in V70_FIX)
V70_OPEN = dict((i, geom(by_id(rd['openings'], i))) for i in ('WIN-05', 'WIN-06', 'WIN-07'))
V70_AC = dict((a['id'], geom(a)) for a in rd['aircons'])
for n, v in V70_SNAP.items():
    if v is None:
        die(u'v7.0 の成果物「%s」 が見つからない — room.html が想定より古い可能性' % n)
if problems:
    raise SystemExit(1)

# ───────────────────────── ROOM_DATA 変換 ─────────────────────────
DELETED_MARK = u'DEL16'


def remap_strings(obj, fn):
    u"""'id' フィールドは別処理なので触らない (二重変換を防ぐ)"""
    if isinstance(obj, dict):
        return dict((k, (v if k == 'id' else remap_strings(v, fn))) for k, v in obj.items())
    if isinstance(obj, list):
        return [remap_strings(v, fn) for v in obj]
    if isinstance(obj, (str, type(u''))):
        return fn(obj)
    return obj


# ── 新ラベル (新 id 基準) ───────────────────────────────────
LBL = {}
LBL['F-15'] = (
    u'ニッチ一体カウンター(幅169 x349..518/奥行50/グレーブラウン天板高75・厚4のスラブのみ=下は空洞・脚元オープン/'
    u'西≈94はキャットウォーク等・東75は白壁 (★v7.2 旧F-16「ペット小部屋」を削除。 その白壁に C-06 の2口が付く)/'
    u'天板に配線孔・黒ゴム蓋西寄り) ★v1.9 幅284.5→169(ユーザー確定チェーン)')
LBL['F-16'] = (
    u'吊戸棚(ダーク木目2枚開き/幅75x奥行30=6.jpg実測『張り出し61・30・75』★v2.7 旧86x35はestを置換/'
    u'下端h127〜天井238/内部棚板2枚/ニッチ東端揃え x438..513) '
    u'★v7.2 旧F-16「ペット小部屋」の削除にあわせて 「ペット小部屋の真上ピッタリ」 の記述を削除 '
    u'(真下は ただの白壁)。 ラベルの座標も rect と一致させた (旧記述 x443..518 は v1.9 の置き去り)')
LBL['F-19'] = (
    u'モニター(白枠黒画面 ≈18x14/中心h≈112/白棚の東隣 x444.5..462.5) '
    u'★v7.2 旧F-16「ペット小部屋」の削除にあわせて 「ペット小部屋開口の上方」 の記述を削除。 '
    u'ラベルの座標も rect と一致させた (旧記述 x449..467 は v1.9 の置き去り) ★v1.9 新ニッチ幅に追従')
LBL['F-36'] = (
    u'MB(メーターボックス/共用廊下側から開閉/下に消火器) '
    u'★v7.2 大元間取り図 (間取り図等\\09_その他\\間取り図_文字なし.jpg) の玄関まわりを最大ズームで再実測: '
    u'図面 px x637..731.5 ・ y701.5..748 を LDK内法アンカー (x236..1016px ↔ 103..790cm / '
    u'y243..634px ↔ 208.5..553.5cm ・ 0.8808cm/px) で cm 化 → x451..534.5 (幅83.5) ・ y613..654 (奥行41)。 '
    u'PS/DPS の真南、 共用廊下に面して張り出す位置。 旧 x467.5..550.5 y620.5..660.5 は 東へ16.5 ずれていた '
    u'⚠寸法は図面読み取り(est)')
LBL['F-37'] = (
    u'PS (パイプスペース) '
    u'★v7.2 大元間取り図を最大ズームで再実測: 図面 px x628.5..684.5 ・ y642.5..685 → '
    u'cm x443.5..493 (幅49.5) ・ y563.5..601 (奥行37.5)。 玄関ホール左の壁帯 (部屋ポリゴン外) で DPS の西隣、 '
    u'DPS との間は 7cm。 旧 x462.5..511.5 は DPS と 2.5cm 重なっていた (v7.1 監査 D6 = 20,400cm³) '
    u'⚠寸法・位置は間取り図読み取り(est)')
LBL['F-38'] = (
    u'DPS (パイプスペース/間取り図の表記は OPS とも読める・ユーザー呼称に合わせ DPS) '
    u'★v7.2 大元間取り図を最大ズームで再実測: 図面 px x692.5..743.5 ・ y642.5..685 → '
    u'cm x500..545 (幅45) ・ y563.5..601 (奥行37.5)。 東面 x545 = 玄関西壁 (内法555・壁厚10) の西面にフラッシュ。 '
    u'旧 x509..554.5 は PS と 2.5cm 重なり かつ 玄関西壁に食い込んでいた ⚠寸法・位置は間取り図読み取り(est)')

RECT = {
    'F-36': [451.0, 613.0, 83.5, 41.0],
    'F-37': [443.5, 563.5, 49.5, 37.5],
    'F-38': [500.0, 563.5, 45.0, 37.5],
}
EXPECT_NAME = {'F-15': u'ニッチ一体カウンター169', 'F-16': u'吊戸棚', 'F-19': u'モニター', 'F-36': u'MB', 'F-37': u'PS', 'F-38': u'DPS'}

C06_POS = [475.5, 553.5]
C06_NAME = u'コンセント No.6（ニッチ東側の白壁・カウンター台下）'
C06_LABEL = (
    u'ニッチカウンター台下(天板下75の下/h≈65) 2口 '
    u'★v7.2 ユーザー確定「旧ペット小部屋の位置は ただの白壁で、 C-06 はその白壁の一部にある」 により '
    u'x559.5 (新チェーンではシューズBOX区間内 = v1.9 から持ち越しの誤り) → x475.5 = 旧 F-16 (x438..513) の中央へ移設。 '
    u'根拠: 赤入り原本 7.jpg の 該当箇所の書き込みは「○2コ(台下)」で、 '
    u'大元間取り図との機械照合 (7.jpg px → 図面 px → LDK内法 cm の2段変換) では '
    u'この赤書き込みの枠 = cm x462..547 ≒ 旧F-16 の帯と一致する。 '
    u'帯の中での正確な x は 写真のパースで ±20cm より詰められないため 帯の中央を採用 (est)。 '
    u'高さ h65 は カウンター天板 (h75/下端71) の下 = 「台下」 のまま維持')

NOTE_V72 = (
    u'★v7.2 (2026-08-23) 【F-16 ペット小部屋の削除 / C-06 の移設 / PS・DPS・MB の是正】 '
    u'(1) **F-16 (petbase「ペット小部屋」) を削除** — ユーザー確定「ここはただの白壁です」。 '
    u'v6.6 で 開口 OP-02 を消した時点で 残っていたのは 「カウンター東端下の暗色ニッチ箱」 の描画だけで、 '
    u'実物には その箱自体が無い。 JS 側の FIX_STYLE.petbase / buildFixture の petbase 分岐 (開口62x66 の暗色パネル) / '
    u'SOLID_FIX_TYPES.petbase も撤去した。 **ペットくぐり戸 (D-01/D-03/D-05 の petDoor) は別物なので残す**。 '
    u'F-16 が欠番になると S1 が ERROR になるため v6.1 の前例どおり **F-17 以降を 1つ繰り上げ** (F-17→F-16 … F-53→F-52)。 '
    u'(2) **C-06 を x559.5 → x475.5 (旧F-16 の中央) へ移設** — ユーザー確定「ここの位置の一部に C-06 があるはずです」。 '
    u'旧位置は シューズBOX (F-33) の区間内で、 v1.9 の時点から 「次回壁面再確認」 と注記されていた。 '
    u'(3) **PS / DPS / MB を 大元間取り図の再実測で是正** — v7.1 監査の 「PS×DPS が 20,400cm³ 重なる」 '
    u'「PS/MB のラベル座標と実座標が食い違う」 を解消。 図面 px を LDK 内法アンカー (0.8808cm/px) で cm 化し、 '
    u'DPS 東面を 玄関西壁の西面 x545 にフラッシュさせて 帯全体を確定した。 '
    u'walls は fixtures 変更に追従して wallgen で再生成済み。')


def do_room_data():
    if rd['meta']['version'] == NEW_VERSION:
        sk(u'ROOM_DATA: 既に v%s' % NEW_VERSION)
        return False

    fx = rd['fixtures']
    pet = [f for f in fx if f.get('type') == 'petbase']
    if len(pet) != 1:
        die(u'petbase fixture が %d 件 (1件のはず)' % len(pet))
        return False
    old_pet_id = pet[0]['id']
    fx = [f for f in fx if f.get('type') != 'petbase']

    # 繰り上げマップ
    ren = {}
    for idx, f in enumerate(fx):
        ren[f['id']] = 'F-%02d' % (idx + 1)
    for f in fx:
        f['id'] = ren[f['id']]
    rd['fixtures'] = fx
    ok(u'ROOM_DATA: %s (petbase「ペット小部屋」) を削除 → fixtures %d → %d 件'
       % (old_pet_id, len(fx) + 1, len(fx)))
    moved = [(o, n) for o, n in sorted(ren.items()) if o != n]
    ok(u'ROOM_DATA: F-NN を繰り上げ (%s … %s) 計 %d 件'
       % ('→'.join(moved[0]), '→'.join(moved[-1]), len(moved)))

    # 文字列中の F-NN 参照を追従 (1パス。 削除された id は 「旧F-16(削除済)」 に置換)
    def fix_ref(s):
        if 'F-' not in s:
            return s
        s = s.replace(old_pet_id, DELETED_MARK)

        def rep(m):
            return ren.get(m.group(0), m.group(0))
        s = re.sub(r'\bF-\d{2}\b', rep, s)
        return s.replace(DELETED_MARK, u'旧%s(削除済)' % old_pet_id)

    for key in ('meta', 'rooms', 'openings', 'outlets', 'aircons', 'fixtures', 'lights', 'zones', 'walls'):
        rd[key] = remap_strings(rd[key], fix_ref)

    # 個別是正
    for nid, nm in EXPECT_NAME.items():
        f = by_id(rd['fixtures'], nid)
        if f is None or f.get('name') != nm:
            die(u'繰り上げ後の %s が「%s」ではない (実際: %s)' % (nid, nm, f and f.get('name')))
            return False
    for nid, r in RECT.items():
        f = by_id(rd['fixtures'], nid)
        old = list(f['rect'])
        f['rect'] = list(r)
        ok(u'ROOM_DATA: %s「%s」 rect %s → %s' % (nid, f['name'], old, r))
    for nid, lb in LBL.items():
        by_id(rd['fixtures'], nid)['label'] = lb
    ok(u'ROOM_DATA: F-15/F-16/F-19/F-36/F-37/F-38 の label を実座標・実態に合わせて更新')

    c6 = by_id(rd['outlets'], 'C-06')
    if c6 is None or c6.get('no') != 6:
        die(u'C-06 が見つからない')
        return False
    old_pos = list(c6['pos'])
    c6['pos'] = list(C06_POS)
    c6['name'] = C06_NAME
    c6['label'] = C06_LABEL
    c6['est'] = True
    ok(u'ROOM_DATA: C-06 pos %s → %s (旧F-16 x438..513 の中央)' % (old_pos, C06_POS))

    # walls 再生成 (feature は fixtures から作られるので追従が必要)
    before = json.dumps(rd['walls'], ensure_ascii=False, sort_keys=True)
    rd['walls'] = wallgen.regen(json.loads(json.dumps(rd)), OPEN_MATCH_TOL)
    after = json.dumps(rd['walls'], ensure_ascii=False, sort_keys=True)
    ok(u'ROOM_DATA: walls を再生成 (%d 件 / 内容変化 %s)' % (len(rd['walls']), 'あり' if before != after else 'なし'))

    rd['meta']['version'] = NEW_VERSION
    rd['meta'].setdefault('notes', []).append(NOTE_V72)
    ok(u'ROOM_DATA: meta.version %s → %s + v7.2 note 追記' % ('6.7', NEW_VERSION))
    return True


changed_rd = do_room_data()
if problems:
    raise SystemExit(1)

# ───────────────────────── JS 側 ─────────────────────────
JS_BLOCKS = [
    (u'FIX_STYLE から petbase を除去',
     u'  petbase:      { color: 0x8a7a6d, h: 240 },\n',
     u''),
    (u'buildFixture の petbase 分岐 (開口62x66 の暗色パネル) を除去',
     u"""  if (f.type === 'petbase') {
    // 開口 62x66 をLDK側(北面)に暗色パネルで表現 (床一段上げ8の上)
    const p = new THREE.Mesh(new THREE.PlaneGeometry(62, 66),
      new THREE.MeshBasicMaterial({ color: 0x3a3129, side: THREE.DoubleSide }));
    p.position.set(cx, 8 + 33, y - 0.4);
    g.add(p);
  }
""",
     u"""  // ★v7.2 fixture type 「pet_base」(ペット小部屋) は ユーザー確定「ここはただの白壁です」 により
  //        ROOM_DATA ごと削除。 開口62x66 の暗色パネル描画も撤去した。 ここに再び足さないこと。
  //        (ペットくぐり戸 D-01/D-03/D-05 の petDoor は別物なので存続)
"""),
    (u'SOLID_FIX_TYPES から petbase を除去',
     u'const SOLID_FIX_TYPES = { kitchen: 1, closet: 1, petbase: 1, pillar: 1,',
     u'const SOLID_FIX_TYPES = { kitchen: 1, closet: 1, pillar: 1,'),
    (u'SOLID_FIX_TYPES 直上コメントから「ペット小部屋」を除去',
     u'// ★v1.9 固定設備 (キッチン・クローゼット・ペット小部屋・仕切り壁・シューズBOX・柱・カウンター等) との',
     u'// ★v1.9 固定設備 (キッチン・クローゼット・仕切り壁・シューズBOX・柱・カウンター等) との  ★v7.2 petbase 削除'),
]


def apply_js(segs):
    u"""segs = [head, tail]。 どちらか一方に当たれば OK。 両方に無ければ FAIL。"""
    for name, old, new in JS_BLOCKS:
        hit = False
        for k in range(len(segs)):
            if old in segs[k]:
                segs[k] = segs[k].replace(old, new, 1)
                ok(u'JS: ' + name)
                hit = True
                break
        if hit:
            continue
        if (new and any(new in s for s in segs)) or (not new):
            # new が空 (= 行ごと削除) の場合は old が どこにも無い時点で 適用済み
            sk(u'JS: ' + name + u' (適用済み)')
        else:
            die(u'JS: ' + name + u' — 対象文字列も適用済み痕跡も見つからない')
    return segs


# ROOM_DATA / CATALOG_SEED 行は絶対に触らない
head = '\n'.join(lines[:I_RD])
mid = '\n'.join(lines[I_RD:I_CS + 1])
tail = '\n'.join(lines[I_CS + 1:])
assert I_RD < I_CS

head, tail = apply_js([head, tail])


# JS 側の F-NN 参照 (fixByIdRD / コメント) を 繰り上げに追従させる
def js_renumber(text, tag):
    hits = sorted(set(re.findall(r'\bF-\d{2}\b', text)))
    if not hits:
        return text, 0
    if not changed_rd:
        sk(u'JS(%s): F-NN 参照の繰り上げ (ROOM_DATA 未変更のため skip)' % tag)
        return text, 0
    ren = js_renumber.map

    def rep(m):
        return ren.get(m.group(0), m.group(0))
    out = re.sub(r'\bF-\d{2}\b', rep, text)
    if out != text:
        ok(u'JS(%s): F-NN 参照を繰り上げ (%s)' % (tag, ', '.join(hits)))
        return out, 1
    sk(u'JS(%s): F-NN 参照は繰り上げ対象なし (%s)' % (tag, ', '.join(hits)))
    return text, 0


js_renumber.map = {}
if changed_rd:
    # 旧→新 (F-17..F-53 → F-16..F-52)
    for k in range(17, 54):
        js_renumber.map['F-%02d' % k] = 'F-%02d' % (k - 1)

head, n3 = js_renumber(head, "head")
tail, n4 = js_renumber(tail, "tail")

if problems:
    raise SystemExit(1)

# ───────────────────────── 書き戻し ─────────────────────────
new_rd_txt = json.dumps(rd, ensure_ascii=False, separators=(',', ':'))
mid_lines = mid.split('\n')
mid_lines[0] = 'var ROOM_DATA = ' + new_rd_txt + ';'
mid = '\n'.join(mid_lines)

out = head + '\n' + mid + '\n' + tail
if out == src:
    print(u'\n■ 結果: 変更なし (完全に冪等・適用0 / skip %d)' % len(skipped))
else:
    io.open(TARGET, 'w', encoding='utf-8', newline='').write(out)
    print(u'\n■ 書き戻し完了: %s' % TARGET)

# ───────────────────────── 検証 ─────────────────────────
print(u'\n■ 検証')
src2 = io.open(TARGET, encoding='utf-8').read()
lines2 = src2.split('\n')


def find2(name):
    pre = 'var %s = ' % name
    for i, l in enumerate(lines2):
        if l.startswith(pre + '{'):
            b = l[len(pre):].rstrip()
            return i, (b[:-1] if b.endswith(';') else b)
    raise SystemExit('not found after write: ' + name)


i2, cs2 = find2('CATALOG_SEED')
sha_after = hashlib.sha256(cs2.encode('utf-8')).hexdigest()
assert sha_after == SEED_SHA_BEFORE, u'CATALOG_SEED が変化した! %s → %s' % (SEED_SHA_BEFORE, sha_after)
print(u'  ✓ CATALOG_SEED sha256 不変: %s' % sha_after)

j2, rt2 = find2('ROOM_DATA')
rd2 = json.loads(rt2)
print(u'  ✓ ROOM_DATA sha256: %s → %s' % (RD_SHA_BEFORE, hashlib.sha256(rt2.encode('utf-8')).hexdigest()))
print(u'    version=%s  fixtures=%d  outlets=%d  walls=%d'
      % (rd2['meta']['version'], len(rd2['fixtures']), len(rd2['outlets']), len(rd2['walls'])))

ids = [f['id'] for f in rd2['fixtures']]
assert ids == ['F-%02d' % (k + 1) for k in range(len(ids))], u'F-NN 連番が壊れた: %s' % ids
print(u'  ✓ F-NN 連番 F-01..%s 連続' % ids[-1])
assert not [f for f in rd2['fixtures'] if f.get('type') == 'petbase'], u'petbase が残っている'
js2 = src2.replace(rt2, '').replace(cs2, '')
for _pat in ('petbase:', "'petbase'", '"petbase"', 'petbase: 1'):
    assert _pat not in js2, u'JS 側に petbase のコードが残っている: ' + _pat
print(u'  ✓ petbase は ROOM_DATA / JS のコードから消えている (説明コメントのみ残置)')
assert "petDoor" in src2, u'petDoor が巻き添えで消えた'
n_pet_door = sum(1 for o in rd2['openings'] if o.get('petDoor'))
print(u'  ✓ ペットくぐり戸 (petDoor) は %d 件そのまま' % n_pet_door)

for nm, snap in V70_SNAP.items():
    cur = snap_by_name(rd2['fixtures'], nm)
    assert cur == snap, u'v7.0 の成果「%s」 が変化した\n  before=%s\n  after =%s' % (nm, snap, cur)
for i, snap in V70_OPEN.items():
    assert geom(by_id(rd2['openings'], i)) == snap, u'%s が変化した' % i
for i, snap in V70_AC.items():
    assert geom(by_id(rd2['aircons'], i)) == snap, u'%s が変化した' % i
print(u'  ✓ v7.0 の成果 (カーテンレール3本 / 室内物干し / WIN-05,06,07 / AC 全4機) のジオメトリ不変')

ps = by_id(rd2['fixtures'], 'F-37')
dps = by_id(rd2['fixtures'], 'F-38')
ov = min(ps['rect'][0] + ps['rect'][2], dps['rect'][0] + dps['rect'][2]) - max(ps['rect'][0], dps['rect'][0])
assert ov <= 0, u'PS×DPS がまだ %.1fcm 重なっている' % ov
print(u'  ✓ PS x%.1f..%.1f / DPS x%.1f..%.1f  重なりなし (すき間 %.1fcm)'
      % (ps['rect'][0], ps['rect'][0] + ps['rect'][2], dps['rect'][0], dps['rect'][0] + dps['rect'][2], -ov))
c6 = by_id(rd2['outlets'], 'C-06')
print(u'  ✓ C-06 pos=%s (旧F-16 x438..513 の中央)' % c6['pos'])

print(u'\n■ まとめ: 適用 %d 件 / skip %d 件' % (len(applied), len(skipped)))

# NOTE (v7.3): 本パッチは v7.2 時点の room.html 専用の履歴パッチ。
# v7.3 で F-ID の繰り上げを撤回した (F-16 を欠番にして以降を固定) ため、
# v7.3 以降の room.html に対して再実行しても precondition で FAIL して中断する (書き込みはしない)。
# 現行の正は patch_v7_3.py / patch_v7_3b.py を適用した状態。

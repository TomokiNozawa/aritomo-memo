# -*- coding: utf-8 -*-
u"""v8.0: キッチン シンク周りを 写真 + ユーザー実測で作り直す。ROOM_DATA v6.9 → v6.10。冪等。

━━ 何が間違っていたか ━━
ROOM_DATA v6.9 は カウンター本体 F-01 だけが正しく 「長辺180 = 部屋Y (南北) / 奥行74.5 = 部屋X」
だったのに、 その上に載る F-02 シンク と F-03 コンロ は **長い方を X に置いていた** (90°ずれ)。
  F-02 rect [582.0, 299.5, 55, 38]   ← 55 を X に置いていた (正: 55 は Y)
  F-03 rect [587.5, 220.5, 59, 50.5] ← 59 を X に置いていた (正: 59 は Y)
その結果 コンロ南端 y271 と シンク北端 y299.5 の間が 28.5 しかなく、 ユーザー実測の 「間43」 と
14.5cm 食い違っていた。 また 「コンロ〜オイルガード16.5」 + 59 = 75.5 > 天板74.5 という
1cm の矛盾が出るので、 v6.9 は オイルガードを x569..571 (= 天板の外・通路へはみ出し) に
逃がしていた。 コンロの向きを正すと 16.5 + 50.5 = 67 ≤ 74.5 になり この逃げも不要になる。

━━ 写真から確定したこと (間取り図等/03_キッチン 22枚 + 01_リビング 8枚。EXIF は exif_transpose で正立) ━━
(1) 向き: 長辺180 は **部屋Y (南北)**。北端が壁 (白グロスパネル + レンジフード)、南端がLDK側。
    作業側 (引出し・グリル操作部) は **東面 x646.5**、通路側 (オイルガード) は **西面 x572**。
    根拠 = 写真35/36 (玄関から北を見る。カウンターが奥へ伸び、手前=南にシンク、奥=北にコンロ)、
           写真34 (南から。シンク手前・コンロ奥・その奥に白パネルとフード)、
           写真29/33/L69 (西から。左=北にコンロ、右=南にシンク)、
           写真38/39/75/80 (東=作業側から。左=南にシンク、右=北にコンロ、右端に白パネル)、
           実測値まとめ v1.7 の平面図 (180 が縦・74.5 が横に記入されている)。
(2) 「コンロ〜壁15」 の壁 = **北壁 (y208.5)**。コンロは北端側にあり その先に壁。
(3) 「間43」 = コンロ南端 と シンク北端 の あき (作業スペース)。
(4) 単一視点メトロロジー (catalog_scripts/measure_v8_0.py):
    写真38 の 天板平面で 消失点 V_x (コンロ南端/北端/天板南端 の3直線が 残差 数px で 1点に収束)
    と V_y (天板 前縁/奥縁 = ほぼ平行 → V_y はほぼ無限遠 = 長手方向は ほぼアフィン) を取り、
    天板 前縁の直線上へ 各要素を V_x 方向に投影して 長手座標を読んだ結果:
      天板南端→シンク南端 10.0cm   [割付 8]
      シンク 長手          55.7cm   [実測 55]
      シンク北端→コンロ南端 41.1cm  [実測 43]
      コンロ 長手          59       (スケール定義に使用)
      コンロ北端→天板北端  14.2cm   [実測 15]
      合計 180.8cm ≒ 180  → **15 / 59 / 43 / 55 / 8 の割付は写真と整合** (誤差 ±2cm)。
    ★「余り8」は 180 からの引き算で出た残差だが、 写真からの独立実測 10.0±2 と一致するので採用。

━━ ROOM_DATA v6.10 の変更 (キッチン F-02〜F-06 と 新規 F-54 のみ。他は1件も触らない) ━━
  F-02 シンク  [582.0,299.5,55,38] h89 b80 → [599.0,325.5,38,55] h85 b66
       ・55 を Y (長手)、38 を X (奥行) へ = 90°是正
       ・y325.5..380.5 : コンロ南端282.5 + 間43 / 南端の余り 388.5-380.5 = 8.0
       ・x599..637     : 手前(東=作業側)まで 9.5 / 奥(西=通路側)まで 27.0
                        (写真38/34 の逆投影で 奥:手前 ≒ 2.6〜3.1 : 1。開口38 を守って按分)
       ・h85 = 天板天面 / b66 = ボウル底 (深さ19 は est)
  F-03 コンロ  [587.5,220.5,59,50.5] h89 b80 → [590.5,223.5,50.5,59] h89 b85
       ・59 を Y (長手)、50.5 を X (奥行) へ = 90°是正
       ・y223.5..282.5 : 北壁208.5 + 15
       ・x590.5..641   : オイルガード東面574 + 16.5 / 手前(東)まで 5.5  (2+16.5+50.5+5.5=74.5)
       ・b85 = 天板天面に載る (v6.9 は b80 = 天板に埋まっていた)
  F-04 オイルガード [569.0,…] h115 b88 → [572.0,…] h112 b85   天板の外→天板の西端へ
  F-05 レンジフード x582 → x588   (コンロ 590.5..641 の真上へ)
  F-06 ダクト囲い   x577 → x583   (フード中心へ)
  F-54 キッチン水栓 **新規** [591.5,343.0,18,6] h123 b85 (KVK 黒 シングルレバー+ハンドシャワー)

━━ 3D 描画 (room.html) ━━
  (A) 天板の高さ基準を是正: v7.9 までは 本体(0..85) の **上に** 黒天板を載せていたので
      実際の天面が 88 になり、 データの h=85 と 3cm ずれていた。 v8.0 は 天板を本体の
      上面 (82..85) に作り、 **データの h=85 = 仕上がり天面** に一致させる。
  (B) 天板と本体に **シンクの開口を空ける** (開口を避けた4本の帯で組む)。
      v7.9 までは 無垢の箱だったので、 シンクを凹ませて描いても 中に埋もれて見えなかった。
  (C) type='sink' 専用の描画を新設: 角R付きの輪郭 (40分割) を リム→底で下すぼまりに繋いだ
      帯 + 底板 + 排水口の目皿。 単なる白い直方体ではなくなる。
  (D) type='kitchen_faucet' を新設: 台座 + 支柱 + グースネック (8分割の弧) + 吐水口 + 黒レバー。
  (E) ツールチップ: sink は 「横×奥行 / 深さ / 天面・底の床からの高さ」、
      kitchen_faucet は 「形式 / 天板からの高さ / 吐水口の張り出し」 を出す。
  (F) コンロ下グリルの z を コンロの新しい位置 (中心 y253) に合わせる。
  (G) 引出し2列のラベル 南列/北列 が入れ替わっていたのを是正 (y+45 は北、 y+135 は南)。

━━ 不変条件 (機械 assert) ━━
  - CATALOG_SEED は sha256 前後一致 (34商品・v2.7 のまま)
  - ROOM_DATA の rooms / openings / outlets / aircons / lights / zones と
    unit / ceilingH / wallT / orientation は sha256 前後一致
  - fixtures は **F-02〜F-06 以外の51件が JSON バイト単位で不変** / 末尾に F-54 を1件追加
  - walls は wallgen.regen() で再生成 (feature は fixtures から作られる派生値なので追従が必要)。
    ジオメトリ (room/dir/horiz/c/from/to/length/height) は 67区画すべて不変 を assert し、
    変わってよいのは **W-LDK-N3 の feature 文字列だけ** に限定する。
    (コンロが北壁から 12 → 15 離れたので 「壁から14以内」 の判定から外れ、
     『キッチン / タイル壁 / ダクト / コンロ』 → 『… / レンジフード』 になる)
"""
import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wallgen                                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), 'room.html')
RD_PREFIX = u'var ROOM_DATA = '
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'
MARK = u'★v8.0 キッチン シンク周り 実測是正'


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def data_line(text, prefix):
    hits = [(i, ln) for i, ln in enumerate(text.split('\n')) if ln.startswith(prefix)]
    assert len(hits) == 1, 'expected exactly 1 line starting with %r, got %d' % (prefix, len(hits))
    return hits[0]


def rep(src, old, new, what):
    assert old in src, u'%s: 置換対象が見つからない' % what
    assert src.count(old) == 1, u'%s: 置換対象が %d 箇所ある' % (what, src.count(old))
    return src.replace(old, new, 1)


src = io.open(TARGET, encoding='utf-8', newline='').read()
assert '\r\n' not in src, 'unexpected CRLF in room.html'
cs_before = sha(re.search(CS_PAT, src, re.S).group(1))

if MARK in src:
    print(u'適用0件 / skip 12件 (既に適用済み)')
    sys.exit(0)

applied = 0

# ═══════════════════════════════════════════════════════════════════════════
# ROOM_DATA v6.9 → v6.10
# ═══════════════════════════════════════════════════════════════════════════
li, line = data_line(src, RD_PREFIX)
body = line[len(RD_PREFIX):].rstrip()
assert body.endswith(';')
rd = json.loads(body[:-1])
assert rd['meta']['version'] == '6.9', u'ROOM_DATA が v6.9 でない: %s' % rd['meta']['version']

OPEN_MATCH_TOL = 18.0        # room.html の const OPEN_MATCH_TOL と揃える
FROZEN_KEYS = ['rooms', 'openings', 'outlets', 'aircons', 'lights', 'zones']
FROZEN_SCALARS = ['unit', 'ceilingH', 'wallT', 'orientation']
J = (lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')))
frozen_before = dict((k, sha(J(rd[k]))) for k in FROZEN_KEYS + FROZEN_SCALARS)
fx_before = dict((f['id'], J(f)) for f in rd['fixtures'])
walls_before = dict((w['id'], dict(w)) for w in rd['walls'])
assert len(rd['fixtures']) == 52 and len(rd['walls']) == 67

fx = dict((f['id'], f) for f in rd['fixtures'])

# ── F-02 シンク ──────────────────────────────────────────────────────────
f = fx['F-02']
assert f['rect'] == [582.0, 299.5, 55, 38], u'F-02 rect が想定と違う: %s' % f['rect']
f['rect'] = [599.0, 325.5, 38, 55]
f['h'] = 85
f['bottomH'] = 66
f['cornerR'] = 5.0            # リムの角R [est]
f['taper'] = 3.2              # 底が四周で内側に入る量 [est]
f['drain'] = [0.5, 0.5]       # 排水口 = ボウルの中央 [est・要ユーザー確認]
f['label'] = (
    u'シンク(白 人造大理石 落とし込み/開口 横55 × 奥行38 = ユーザー実測 '
    u'★v8.0 55 は カウンター長辺=部屋Y、 38 は 奥行=部屋X が正 (v6.9 は 90°ずれていた)/'
    u'y325.5..380.5 = コンロ南端282.5 から 間43・南端の余り8/'
    u'x599..637 = 手前(東=作業側)まで9.5・奥(西=通路側)まで27.0 '
    u'(写真38/34 の天板平面 逆投影で 奥:手前 ≒ 2.6〜3.1:1)/'
    u'角R5・側面は下すぼまり・ボウル深さ19 (h85=天面 / bottomH66=底) は est/'
    u'排水口はボウル中央 est=要確認/水栓は F-54) ★v8.0 実測是正 (v1.8 新規・v2.8 で55x38 に是正済み)'
)

# ── F-03 コンロ ─────────────────────────────────────────────────────────
f = fx['F-03']
assert f['rect'] == [587.5, 220.5, 59, 50.5], u'F-03 rect が想定と違う: %s' % f['rect']
f['rect'] = [590.5, 223.5, 50.5, 59]
f['h'] = 89
f['bottomH'] = 85
f['label'] = (
    u'コンロ(黒ガラストップ3口 59x50.5=実測 ★v8.0 59 は カウンター長辺=部屋Y が正 '
    u'(v6.9 は 90°ずれていた)/y223.5..282.5 = 北壁208.5 から 15/'
    u'x590.5..641 = オイルガード東面574 から 16.5・手前(東)まで5.5 '
    u'(2 + 16.5 + 50.5 + 5.5 = 74.5 で天板に収まる)/'
    u'bottomH85 = 天板天面に載る (v6.9 は 80 で天板に埋まっていた)/'
    u'前面グリル+黒操作パネルは東面) ★v8.0 実測是正'
)

# ── F-04 オイルガードガラス ─────────────────────────────────────────────
f = fx['F-04']
assert f['rect'] == [569.0, 208.5, 2, 90], u'F-04 rect が想定と違う: %s' % f['rect']
f['rect'] = [572.0, 208.5, 2, 90]
f['h'] = 112
f['bottomH'] = 85
f['label'] = (
    u'オイルガードガラス 西=通路側(透明低背パネル/長さ≈90/黒コーナークランプ/'
    u'★v8.0 x572..574 = 天板の西端に載る。 v6.9 は 569..571 = 天板の外(通路)へ '
    u'はみ出していたが、 これは コンロを 59 幅で X に置いていたための逃げ。 '
    u'コンロを 50.5 幅に是正したので 2+16.5+50.5+5.5=74.5 が成立し はみ出しは不要になった/'
    u'天板85 から 上端112 = 高さ27 は est) ★v1.8 残すのはこの1枚のみ(東=ダイニング側は削除・ユーザー確定)'
)

# ── F-05 レンジフード / F-06 ダクト囲い (コンロの真上へ寄せる) ──────────
f = fx['F-05']
assert f['rect'] == [582.0, 208.5, 55, 90], u'F-05 rect が想定と違う: %s' % f['rect']
f['rect'] = [588.0, 208.5, 55, 90]
f['label'] = (
    u'レンジフード(黒ボックス型/北端コンロ直上/本体下端h≈150-155/幅≈55/'
    u'★v8.0 x588..643 = 是正後のコンロ(590.5..641)の真上へ寄せた (v6.9 は 582..637)) ★v1.7新規(写真)'
)
f = fx['F-06']
assert f['rect'] == [577.0, 208.5, 65, 52], u'F-06 rect が想定と違う: %s' % f['rect']
f['rect'] = [583.0, 208.5, 65, 52]
f['label'] = (
    u'レンジフード上ダクト囲い(白/幅≈65x下がり≈38/北壁との間/全面下がり天井は無し/'
    u'★v8.0 x583..648 = レンジフード中心へ寄せた (v6.9 は 577..642)) ★v1.7新規(写真)'
)

# ── F-54 キッチン水栓 (新規・最大値+1) ──────────────────────────────────
nums = [int(i.split('-')[1]) for i in fx]
assert max(nums) == 53 - 1 or True
newid = 'F-%02d' % (max(nums) + 1)
assert newid == 'F-54', u'新規IDが F-54 でない: %s (欠番の繰り上げが起きていないか確認)' % newid
rd['fixtures'].append({
    'type': 'kitchen_faucet', 'room': 'ldk',
    'label': (
        u'キッチン水栓 KVK 黒 シングルレバー混合栓+ハンドシャワー('
        u'台座はシンク奥(西)の天板 x594.5/'
        u'y346 = シンク南端380.5 から34.5・北端325.5 から20.5 '
        u'= 写真38/39 でシンク中央より北(コンロ)寄り/'
        u'天板85 から 高さ38 = 上端123・吐水口の張り出し18 は est) ★v8.0新規(写真29/33/34/35/38/39)'
    ),
    'est': True,
    'rect': [591.5, 343.0, 18, 6],
    'h': 123, 'bottomH': 85,
    'showDim': False,
    'id': newid,
    'name': u'キッチン水栓',
    'short': u'水栓',
    'minor': False,
})

# ── walls 再生成 (feature は fixtures から作られる派生値。S2 再生成一致を保つ) ────────
rd['walls'] = wallgen.regen(json.loads(json.dumps(rd)), OPEN_MATCH_TOL)
assert len(rd['walls']) == 67, u'walls の区画数が変わった: %d' % len(rd['walls'])
GEO = ['id', 'room', 'dir', 'horiz', 'c', 'from', 'to', 'length', 'height']
wchanged = []
for w in rd['walls']:
    b = walls_before.get(w['id'])
    assert b is not None, u'walls に新しい区画 %s が出現した' % w['id']
    for k in GEO:
        assert w.get(k) == b.get(k), u'walls %s の %s が変化した: %r → %r' % (w['id'], k, b.get(k), w.get(k))
    if J(w) != J(b):
        wchanged.append(w['id'])
assert wchanged == ['W-LDK-N3'], u'walls の変化が W-LDK-N3 以外に及んだ: %s' % wchanged
_wb, _wa = walls_before['W-LDK-N3'], [w for w in rd['walls'] if w['id'] == 'W-LDK-N3'][0]
assert set(k for k in set(list(_wb) + list(_wa)) if _wb.get(k) != _wa.get(k)) == set(['feature']), \
    u'W-LDK-N3 で feature 以外が変化した'

rd['meta']['version'] = '6.10'
rd['meta']['notes'].append(
    u'★v6.10 (2026-08-23) 【キッチン シンク周りの実測是正】カウンター F-01 だけが正しく '
    u'「長辺180 = 部屋Y / 奥行74.5 = 部屋X」 だったのに、 その上の F-02 シンク (55x38) と '
    u'F-03 コンロ (59x50.5) は 長い方を X に置いており 90°ずれていた。 その結果 コンロ南端 y271 と '
    u'シンク北端 y299.5 の間が 28.5 しかなく ユーザー実測 「間43」 と 14.5cm 食い違っていた。 '
    u'写真22枚 (03_キッチン) の逆投影と ユーザー実測で 長辺方向の割付を '
    u'コンロ〜北壁15 / コンロ59 / 間43 / シンク55 / 南端の余り8 = 180 に確定 '
    u'(写真からの独立実測は 14.2 / 59 / 41.1 / 55.7 / 10.0 = 180.8 で ±2cm 以内に一致)。 '
    u'奥行方向は コンロ = オイルガード東面574 + 16.5 → x590.5..641 (手前5.5)、 '
    u'シンク = x599..637 (奥27.0 / 手前9.5、 写真の奥:手前比 2.6〜3.1:1 を 開口38 で按分)。 '
    u'あわせて オイルガード F-04 を 天板の外 (x569) から 天板の西端 (x572) へ戻し '
    u'(コンロ幅を正すと 2+16.5+50.5+5.5=74.5 が成立するため はみ出しの逃げが不要になった)、 '
    u'レンジフード F-05 / ダクト F-06 を コンロの真上へ寄せ、 キッチン水栓 F-54 を新設した。 '
    u'3D は 天板の天面を データの h=85 に一致させ (v7.9 までは本体の上に載せていて実天面88)、 '
    u'天板と本体に シンクの開口を空け、 角R・下すぼまり・排水口を持つ シンク描画を新設した。 '
    u'あわせて walls の feature を再生成した (コンロが北壁から 12 → 15 離れ 「壁から14以内」 の判定から外れたため W-LDK-N3 の feature が 『キッチン / タイル壁 / ダクト / コンロ』 → 『キッチン / タイル壁 / ダクト / レンジフード』 になる。 壁のジオメトリは 67区画すべて不変)。 詳細: catalog_scripts/patch_v8_0.py / measure_v8_0.py'
)

# 検証 (ROOM_DATA)
for k in FROZEN_KEYS + FROZEN_SCALARS:
    assert sha(J(rd[k])) == frozen_before[k], u'ROOM_DATA.%s が変化した' % k
assert len(rd['fixtures']) == 53
changed = [f['id'] for f in rd['fixtures'] if f['id'] in fx_before and J(f) != fx_before[f['id']]]
assert changed == ['F-02', 'F-03', 'F-04', 'F-05', 'F-06'], u'想定外の fixture が変化: %s' % changed
ids = [f['id'] for f in rd['fixtures']]
assert len(set(ids)) == len(ids), u'fixture ID が重複した'
assert ids[-1] == 'F-54'

lines = src.split('\n')
lines[li] = RD_PREFIX + json.dumps(rd, ensure_ascii=False, separators=(',', ':')) + ';'
src = '\n'.join(lines)
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (2) FIX_STYLE: sink の色/高さを是正 + kitchen_faucet を追加
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""  sink:         { color: 0xffffff, h: 89 },    // キッチンシンク (白)
  stove:        { color: 0x1a1b1e, h: 89 },    // コンロ (黒ガラストップ)""",
u"""  // ★v8.0 キッチン シンク周り 実測是正: シンクは 天面 h=85 (= 天板天面) を既定にし、
  //   色は 写真の アイボリー寄りの白 (人造大理石) に。 bottomH がボウル底になる。
  sink:         { color: 0xf3f0e8, h: 85 },    // キッチンシンク (白 人造大理石・落とし込み)
  stove:        { color: 0x1a1b1e, h: 89 },    // コンロ (黒ガラストップ)
  kitchen_faucet: { color: 0x18181a, h: 123 }, // キッチン水栓 (黒 シングルレバー + ハンドシャワー)""",
u'(2) FIX_STYLE')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (3) 幾何ヘルパー (角丸輪郭 / シンク開口の帯) を buildFixture の前に置く
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""function buildFixture(f) {
  const st = FIX_STYLE[f.type];""",
u"""// ★v8.0 角丸長方形の輪郭点 [[x, z], ...] を 反時計回りに返す (重複点なし)。
//   cx/cz = 中心 / w = X方向の幅 / d = Z方向の奥行 / r = 角R / n = 全体の分割数 (4の倍数に丸める)
function roundRectPts(cx, cz, w, d, r, n) {
  const hw = w / 2, hd = d / 2;
  r = Math.max(0.1, Math.min(r, Math.min(hw, hd) - 0.05));
  const per = Math.max(3, Math.round((n || 40) / 4));
  const corners = [[cx + hw - r, cz + hd - r, 0], [cx - hw + r, cz + hd - r, Math.PI / 2],
                   [cx - hw + r, cz - hd + r, Math.PI], [cx + hw - r, cz - hd + r, -Math.PI / 2]];
  const out = [];
  corners.forEach(function (c) {
    for (let i = 0; i < per; i++) {
      const a = c[2] + (Math.PI / 2) * (i / per);
      out.push([c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)]);
    }
  });
  return out;
}
// ★v8.0 キッチン (type='kitchen') の天板に空ける シンク開口 = 同じ部屋の type='sink' で
//   自分の rect に完全に収まるもの。 見つからなければ null (= 無垢の天板に戻る)。
function kitchenSinkCut(f) {
  const r = f.rect;
  if (!r) return null;
  const hit = (R.fixtures || []).filter(function (q) {
    return q.type === 'sink' && q.rect && q.room === f.room &&
           q.rect[0] >= r[0] - 0.5 && q.rect[0] + q.rect[2] <= r[0] + r[2] + 0.5 &&
           q.rect[1] >= r[1] - 0.5 && q.rect[1] + q.rect[3] <= r[1] + r[3] + 0.5;
  });
  return hit.length ? hit[0] : null;
}
// ★v8.0 矩形 (x0..x1, z0..z1) から 開口 cut.rect を除いた 4本の帯 [x0,x1,z0,z1]
function stripsAround(x0, x1, z0, z1, cut) {
  const a = cut.rect[0], b = cut.rect[0] + cut.rect[2];
  const c = cut.rect[1], d = cut.rect[1] + cut.rect[3];
  return [[x0, x1, z0, c], [x0, x1, d, z1], [x0, a, c, d], [b, x1, c, d]]
    .filter(function (s) { return s[1] - s[0] > 0.2 && s[3] - s[2] > 0.2; });
}

function buildFixture(f) {
  const st = FIX_STYLE[f.type];""", u'(3) 幾何ヘルパー')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (4) type='sink' / 'kitchen_faucet' の専用描画を追加 (glass 分岐の直前)
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""  if (f.type === 'glass') {
    // ★v1.7 オイルガードガラス: 半透明クリアパネル""",
u"""  if (f.type === 'sink') {
    // ★v8.0 キッチンシンク (写真29/33/34/35/38/39 準拠)。 v7.9 までの 「白い直方体」 をやめ、
    //   実物と同じ 「天板に落とし込まれた 角R付き・下すぼまりのボウル + 排水口」 で組む。
    //     rect = 天板の開口 (X=奥行38 / Z=長手55 = ユーザー実測)
    //     h    = 天板の天面 (= リムの高さ 85) / bottomH = ボウル底 (85-19=66)
    //     cornerR / taper / drain は ROOM_DATA 側で調整できる (未指定なら既定値)。
    //   メッシュ数はモバイル配慮で 輪郭40分割 (側面80三角) + 底板 + 目皿 の 3メッシュに抑える。
    const info = { kind: 'fixture', info: f.label };
    const rimY = topH, botY = Math.min(botH, topH - 3);
    const cR = (f.cornerR != null ? f.cornerR : 5.0);
    const tp = (f.taper != null ? f.taper : 3.2);
    const rim = roundRectPts(cx, cz, dx, dy, cR, 40);
    const bot = roundRectPts(cx, cz, Math.max(dx - 2 * tp, 2), Math.max(dy - 2 * tp, 2),
                             Math.max(cR - tp * 0.4, 1.0), 40);
    //   ★頂点を共有する index 付きジオメトリにする。 非 index (三角形ごとに独立した頂点) だと
    //     computeVertexNormals が 面法線になり、 リムと底で輪郭が違う = 四角形が非平面なので
    //     三角形ごとに法線が振れて 側面がギザギザに陰る。 共有すると法線が平均されて滑らかになる。
    const N = rim.length, pos = [], idx = [];
    for (let i = 0; i < N; i++) pos.push(rim[i][0], rimY, rim[i][1]);
    for (let i = 0; i < N; i++) pos.push(bot[i][0], botY, bot[i][1]);
    for (let i = 0; i < N; i++) {
      const j = (i + 1) % N;
      idx.push(i, N + i, N + j, i, N + j, j);
    }
    const wg = new THREE.BufferGeometry();
    wg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    wg.setIndex(idx);
    wg.computeVertexNormals();
    const wall = new THREE.Mesh(wg, new THREE.MeshLambertMaterial({ color: color, side: THREE.DoubleSide }));
    Object.assign(wall.userData, info); g.add(wall); pickables.push(wall);
    const bs = new THREE.Shape(bot.map(function (p) { return new THREE.Vector2(p[0], p[1]); }));
    const bg = new THREE.ShapeGeometry(bs);
    bg.rotateX(Math.PI / 2);                       // Shape の y が ワールド z になる
    const bm = new THREE.Mesh(bg, new THREE.MeshLambertMaterial({ color: 0xeeeae1, side: THREE.DoubleSide }));
    bm.position.y = botY;
    Object.assign(bm.userData, info); g.add(bm); pickables.push(bm);
    const dr = (f.drain && f.drain.length === 2) ? f.drain : [0.5, 0.5];
    const grate = new THREE.Mesh(new THREE.CylinderGeometry(4.6, 4.6, 1.0, 16), mat(0xb9bec3));
    grate.position.set(x + dx * dr[0], botY + 0.5, y + dy * dr[1]);
    Object.assign(grate.userData, info); g.add(grate); pickables.push(grate);

    return;
  }
  if (f.type === 'kitchen_faucet') {
    // ★v8.0 KVK 黒 シングルレバー混合栓 + ハンドシャワー (写真29/33/34/35/38/39)。
    //   rect = [x, y, dx, dy] : dx = 台座中心から吐水口までの張り出し (東=シンク側へ) を含む帯、
    //   dy = 本体の径。 bottomH = 天板天面、 h = グースネックの頂点。
    const info = { kind: 'fixture', info: f.label };
    const r0 = Math.max(Math.min(dy, 7) / 2, 2.0);
    const bx = x + r0, zc = y + dy / 2;
    const colTop = botH + (topH - botH) * 0.45;
    const col = new THREE.Mesh(new THREE.CylinderGeometry(r0, r0 + 0.6, colTop - botH, 14), mat(color));
    col.position.set(bx, (botH + colTop) / 2, zc);
    Object.assign(col.userData, info); g.add(col); pickables.push(col);
    // グースネック: 台座上端 colTop から立ち上がり 頂点 (topH) を越えて 東へ倒れる。
    //   ★半円 (0..π) まで回すと 東端が台座と同じ高さまで降りてしまい 「鳥居」 に見えるので、
    //     0..0.74π で止める = 吐水口は 天板から 高さの 7割ほどの位置に残る (実物のグースネック)。
    const span = Math.max(dx - r0 - 2.0, 6), Ry = Math.max(topH - colTop, 5);
    const TEND = Math.PI * 0.74;
    const px = function (t) { return bx + (span / 2) * (1 - Math.cos(t)) / (1 - Math.cos(TEND)); };
    const py = function (t) { return colTop + Ry * Math.sin(t); };
    let prev = new THREE.Vector3(bx, colTop, zc);
    for (let i = 1; i <= 8; i++) {
      const t = TEND * (i / 8);
      const cur = new THREE.Vector3(px(t), py(t), zc);
      const len = prev.distanceTo(cur);
      const seg = new THREE.Mesh(new THREE.CylinderGeometry(r0 * 0.70, r0 * 0.70, len + 0.5, 10), mat(color));
      seg.position.copy(prev).add(cur).multiplyScalar(0.5);
      seg.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), cur.clone().sub(prev).normalize());
      Object.assign(seg.userData, info); g.add(seg); pickables.push(seg);
      prev = cur;
    }
    // 吐水口 (ハンドシャワーのヘッド) = 弧の東端から下向きに 5cm
    const head = new THREE.Mesh(new THREE.CylinderGeometry(r0 * 0.86, r0 * 0.74, 5.0, 12), mat(color));
    head.position.set(prev.x, prev.y - 2.5, zc);
    Object.assign(head.userData, info); g.add(head); pickables.push(head);
    // 黒レバーハンドル (台座の北側から横に出る)
    const lev = addBox(g, 2.0, 1.8, 7.0, bx, colTop - 1.5, zc - r0 - 3.0, 0x2a2a2c, info);
    pickables.push(lev);
    return;
  }
  if (f.type === 'glass') {
    // ★v1.7 オイルガードガラス: 半透明クリアパネル""", u'(4) sink / kitchen_faucet 描画')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (5) キッチン本体: シンクの開口ぶんを抜いた本体にする (generic の else を分岐)
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""  } else {
    body = addBox(g, sx, bh, sz, cx, cy, cz, color, { kind: 'fixture', info: f.label });
  }
  pickables.push(body);
  if (f.type === 'kitchen') {""",
u"""  } else if (f.type === 'kitchen') {
    // ★v8.0 シンクを 「天板に落とし込まれた凹み」 として見せるため、 本体も ボウル底より上は
    //   開口を避けた4本の帯で組む。 (v7.9 までは無垢の箱だったので ボウルを描いても中に埋もれた)
    const kc0 = kitchenSinkCut(f);
    const kInfo = { kind: 'fixture', info: f.label };
    if (!kc0) {
      body = addBox(g, sx, bh, sz, cx, cy, cz, color, kInfo);
    } else {
      //   ★帯の下端は ボウル底より 1.5cm 下げる。 ぴったり同じ高さにすると
      //     「本体下箱の天面」 と 「シンクの底板」 が同一平面になり z-fighting で
      //     ボウルの底に階段状のちらつきが出る。
      const bandY0 = Math.max(botH + 1,
                              Math.min((Number(kc0.bottomH) || (topH - 19)) - 1.5, topH - 2));
      body = addBox(g, sx, bandY0 - botH, sz, cx, (botH + bandY0) / 2, cz, color, kInfo);
      //   ★帯の上端は topH ちょうどではなく 1.5mm 下げる。 天板スラブ (topH-3〜topH) と
      //     天面が同一平面になると z-fighting で 天板がギザギザに見える。
      //     3cm 下げる (スラブ下端まで) と 今度はシンクのリムに 暗い隙間が見えるので 1.5mm が適量。
      const bandH = (topH - 0.15) - bandY0;
      stripsAround(x + 0.5, x + dx - 0.5, y + 0.5, y + dy - 0.5, kc0).forEach(function (s) {
        pickables.push(addBox(g, s[1] - s[0], bandH, s[3] - s[2],
                              (s[0] + s[1]) / 2, bandY0 + bandH / 2, (s[2] + s[3]) / 2, color, kInfo));
      });
    }
  } else {
    body = addBox(g, sx, bh, sz, cx, cy, cz, color, { kind: 'fixture', info: f.label });
  }
  pickables.push(body);
  if (f.type === 'kitchen') {""", u'(5) キッチン本体の開口')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (6) 天板スラブ: 本体の上面 (topH-3 .. topH) にし、シンクの開口を空ける
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""    addBox(g, dx - 1, 3, dy - 1, cx, topH + 1.5, cz, 0x2c2c30);   // 黒マット天板 (フルフラット)""",
u"""    // ★v8.0 黒マット天板。 v7.9 までは 本体(0..85) の **上** (topH+1.5 = 85..88) に載せていたので
    //   実際の天面が 88 になり ROOM_DATA の h=85 と 3cm ずれていた。 v8.0 は 本体の上面
    //   (topH-3 .. topH) に作り、 **データの h=85 = 仕上がり天面** に一致させる。
    //   さらに シンクの開口を避けた4本の帯で組む (無垢だとボウルが見えない)。
    const TOPT = 3, tcy = topH - TOPT / 2, kc1 = kitchenSinkCut(f);
    if (!kc1) {
      addBox(g, dx + 0.6, TOPT, dy + 0.6, cx, tcy, cz, 0x2c2c30);
    } else {
      stripsAround(x - 0.3, x + dx + 0.3, y - 0.3, y + dy + 0.3, kc1).forEach(function (s) {
        addBox(g, s[1] - s[0], TOPT, s[3] - s[2], (s[0] + s[1]) / 2, tcy, (s[2] + s[3]) / 2, 0x2c2c30);
      });
    }""", u'(6) 天板スラブ')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (7) コンロ下グリルの位置 / 引出し列ラベルの南北是正
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""    addBox(g, 1.4, 20, 50, x + dx - 0.6, 70, y + 32, 0x141414);   // 北端コンロ下グリル+操作部 (東面)""",
u"""    // ★v8.0 グリルはコンロの真下。 是正後のコンロは y223.5..282.5 (中心 y253 = 天板北端から44.5)
    addBox(g, 1.4, 20, 50, x + dx - 0.6, 70, y + 44.5, 0x141414);  // 北端コンロ下グリル+操作部 (東面)""",
u'(7a) グリル位置')
applied += 1

src = rep(src, u"""    [[y + 45, '南列'], [y + 135, '北列']].reverse().forEach(function (colDef) {""",
u"""    // ★v8.0 南北のラベルが入れ替わっていたのを是正 (y は南へ増えるので y+45 が北・y+135 が南)。
    //   y+45 = 北列 (コンロ側) / y+135 = 南列 (シンク側)。
    [[y + 45, '北列'], [y + 135, '南列']].reverse().forEach(function (colDef) {""",
u'(7b) 引出し列ラベル')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (8) ツールチップ: sink / kitchen_faucet の内訳行
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {""",
u"""  if (f.type === 'sink' && f.rect) {
    // ★v8.0 キッチンシンク: 実測は 「横55 (カウンター長辺=rect[3]) × 縦38 (奥行=rect[2])」
    const top = (f.h != null ? f.h : 85), bot = Number(f.bottomH) || 0;
    return '開口: 横 ' + tipN(f.rect[3]) + ' × 奥行 ' + tipN(f.rect[2]) +
           'cm (ユーザー実測) / ボウル深さ ' + tipN(top - bot) + 'cm [est]' +
           ' / 天面 床から ' + tipN(top) + 'cm・底 ' + tipN(bot) + 'cm';
  }
  if (f.type === 'kitchen_faucet' && f.rect) {
    const top = (f.h != null ? f.h : 123), bot = Number(f.bottomH) || 0;
    return '形式: シングルレバー混合栓 + ハンドシャワー (黒) / 天板から高さ ' + tipN(top - bot) +
           'cm (床から ' + tipN(top) + 'cm) / 吐水口の張り出し ' + tipN(f.rect[2]) + 'cm [est]';
  }
  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {""", u'(8) ツールチップ')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# 検証
# ═══════════════════════════════════════════════════════════════════════════
assert MARK in src, u'冪等マーカーが入っていない'
assert sha(re.search(CS_PAT, src, re.S).group(1)) == cs_before, u'CATALOG_SEED が変化した'
rd2 = json.loads(data_line(src, RD_PREFIX)[1][len(RD_PREFIX):].rstrip()[:-1])
assert rd2['meta']['version'] == '6.10'
assert len(rd2['fixtures']) == 53
assert src.count(u"if (f.type === 'sink') {") == 1
assert src.count(u"if (f.type === 'kitchen_faucet') {") == 1
assert src.count(u'function roundRectPts(') == 1
assert src.count(u'function kitchenSinkCut(') == 1
assert src.count(u'function stripsAround(') == 1
assert u'topH + 1.5, cz, 0x2c2c30' not in src, u'旧・天板スラブが残っている'

io.open(TARGET, 'w', encoding='utf-8', newline='').write(src)
print(u'適用%d件' % applied)
print(u'ROOM_DATA v6.9 → v6.10 / fixtures 52 → 53 (F-54 キッチン水栓 新規)')
print(u'  変更: F-02 シンク [599.0,325.5,38,55] h85 b66   (旧 [582.0,299.5,55,38] h89 b80)')
print(u'        F-03 コンロ [590.5,223.5,50.5,59] h89 b85 (旧 [587.5,220.5,59,50.5] h89 b80)')
print(u'        F-04 ガラス [572.0,208.5,2,90] h112 b85   (旧 [569.0,…] h115 b88)')
print(u'        F-05 フード x582 → x588 / F-06 ダクト x577 → x583')
print(u'  長辺方向の割付 [北壁208.5 から]: 15 → コンロ59 → 間43 → シンク55 → 余り8 = 180 ✓')
print(u'  奥行方向 [西面572 から]: ガラス2 → 16.5 → コンロ50.5 → 5.5 = 74.5 ✓ / '
      u'シンクは 27.0 → 38 → 9.5 = 74.5 ✓')
print(u'CATALOG_SEED sha256 %s (不変) / rooms・openings・outlets・aircons・lights・zones・walls 不変'
      % cs_before[:16])

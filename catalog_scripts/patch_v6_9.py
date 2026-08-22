# -*- coding: utf-8 -*-
u"""
nozaROOM room.html v6.9 (ROOM_DATA v6.4) 冪等パッチ

━━ ユーザー確定 2点 (①②) ━━

① 洋室4.8 南窓 2窓の離隔 (小壁) を 24.5 → 16.5cm へ是正 (「実測が正しいだろ」)

   ▼ 旧値 24.5 の出自
     24.5 = 254 - 56 - 43 - 12.5 - 118 の **閉合の余り** であって 実測値ではなかった。
     (254 = CL東面 x160.5 → 4.8帖 東壁 x414.5 の南壁チェーン全長)

   ▼ 今回の実測 = 写真59 の単一視点メトロロジー
     写真59 (05_4.8帖/..._59.jpg / EXIF orientation=1 / 4000x2250 / 2.68mm 超広角) は
     **南壁が SE入隅から CL東面まで丸ごと1枚に収まる唯一の写真**。
     手順 (v6.8 の写真60 と同じ逆投影の流儀):
       1. 南壁上の水平線を3本フィット
            見切り縁 y = -0.019230x + 1462.42 (rms 3.3px)
            床見切り y = -0.011176x + 2166.64
          → 交点 = 水平方向の消失点 VP = (-87437, 3144)
            (2本が独立に yv=3144 を与えるので相互検証済み)
       2. 消失点が分かれば 壁に沿った1次元射影写像は 2点アンカーで決まる:
            X = P + Q/(u - v),  v = -87437
          アンカーは チェーンの両端 = SE入隅 (X=414.5) と CL東面 (X=160.5) の2本の縦線。
          縦線は 行ごとの R-B (壁のベージュ ↔ 開口/白リビール) 交差点を線形フィットして得た
          (WIN-03 西端 rms 0.41px / WIN-04 東端 rms 0.78px / SE入隅 rms 1.12px / CL入隅 rms 0.53px)。
       3. y=900 の行で各特徴の u を評価 (壁の水平線は 2000px 進んで 40px しか下がらないので、
          同一行での評価による誤差は 0.5px 未満 = 0.06cm)。

     ▼ 読み取り結果 (cm)
            東壁 → WIN-04 東端        124.1   (データ 118   … +6.1)
            WIN-04 幅                  13.5   (データ 12.5  … +1.0 / 写真60 は 13.3)
            **2窓の離隔 (小壁)         16.1**  (データ 24.5  … ▲8.4 / 写真60 は 16.5)
            WIN-03 幅                  44.6   (データ 43    … +1.6 / 写真60 は 42.8)
            WIN-03 西端 → CL東面       55.7   (データ 56    … ▲0.3 ★一致)
       写真60 (別レンズ・別画角) の 16.5 と 写真59 の 16.1 が独立に一致し、
       かつ 同じ写像が 西側の壁 56 を 55.7 と再現している。 → 離隔 16.5 を採用。

   ▼ チェーンの吸収先 = **東側の壁 118 → 126**
       離隔を 24.5 → 16.5 にすると 8.0cm 余る。 写真59 は その 8.0cm が
       **東側の壁** (WIN-04 東端 → 東壁) にあると示している (実測 124.1 ≒ 126)。
       西側の壁 56 は 実測 55.7 で動かす理由がない。 窓幅 43 / 12.5 も写真2枚で追認済み。
       → WIN-04 を **西へ 8.0cm 平行移動** (284.0..296.5 → 276.0..288.5) するだけで閉じる。
            254 = 56 + 43 + 16.5 + 12.5 + 126
       WIN-03 は不動。 部屋ポリゴン (rooms) も 壁の位置も動かさない。
       walls の W-R48-S2 (24.5) / W-R48-S3 (118) は 開口で分割された派生データなので
       16.5 / 126.0 へ追従させる (これも今回の変更対象)。

② 窓の形式を 「横すべり出し (アワニング)」 へ是正 (「整合性重視で」)

   写真60・62 で **各サッシの下框 中央に横棒ハンドル** が見える (床上 約119cm と 約22.5cm)。
   縦すべり出し (WIN-03 の旧ラベル) なら ハンドルは縦框側に付き、FIX (WIN-04 の旧ラベル) なら
   ハンドルは付かない。 → 上下2枚とも 横すべり出し (アワニング) の 2連 が正。
   ラベルを是正し、ツールチップの 「種類」 も 横すべり出し窓 (アワニング) と出るように
   tipWindowKind() (v6.4-a) を更新する。
     ※ ラベルには改訂履歴が残る (WIN-04 は 「FIX」、WIN-03 は 「縦すべり出し」 の語が残る) ので、
       「横すべり出し」 が書かれていたら それを最終確定として最優先する分岐にした。

━━ ③ 他室のカーテンレール — 今回は F-50 の追従のみ ━━
   4.8帖の F-50 は WIN-04 が 8cm 動くので 写真59 で 再測して x を是正する
   (レール本体の長さ 95.5 / 天井付けダブル / 出2.7・9.0 / 下端237.5 は不変)。
   4.5帖 (写真49) / 6.2帖 / LDK (F-25) は **このパッチでは触らない** (理由は報告参照)。

━━ ROOM_DATA v6.4 の変更点 (これ以外は 1つも触らない) ━━
   meta.version 6.3 → 6.4 / meta.notes に v6.4 の記録を追記
   openings : WIN-04 wallFrom/wallTo を西へ8.0 (284.0..296.5 → 276.0..288.5) / label 追記
              WIN-03 label 追記 (形式のみ。 座標は不変)
   walls    : W-R48-S2 from/to/length/where (259.5..284.0 / 24.5 → 259.5..276.0 / 16.5)
              W-R48-S3 from/length/where     (296.5..414.5 / 118  → 288.5..414.5 / 126.0)
   fixtures : F-50 rect[0] 210.0 → 207.0 (長さ 95.5 は不変) / label 追記
   rooms / aircons / lights / zones / outlets / unit / ceilingH / wallT / orientation は不変 (assert)

━━ 不変アサート ━━
   CATALOG_SEED の 1 行 sha256 が パッチ前後で完全一致することを assert する。
   ROOM_DATA も 上記の凍結キーの sha256 一致を assert する。
   さらに 南壁チェーンが 254 で閉じること・離隔が 16.5 であることを機械 assert する。

━━ 冪等性 ━━
   各パッチは「適用済みマーカー」を持ち、既に入っていれば skip。
   再実行すると「適用 0 件 / skip N 件」になる。

━━ 並行編集への配慮 ━━
   読み込み → 加工 → 書き込み直前に 再読込して 内容が変わっていないことを確認し、
   変わっていたら 何も書かずに 中断する (exit 2)。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v6_9.py [--dry-run]
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), 'room.html')

RD_PREFIX = u'var ROOM_DATA = '
CS_PREFIX = u'var CATALOG_SEED = '


# ───────────────────────── 共通ユーティリティ ─────────────────────────
def read_text():
    with io.open(TARGET, encoding='utf-8', newline='') as f:
        t = f.read()
    assert '\r\n' not in t, 'unexpected CRLF in room.html'
    return t


def data_line(text, prefix):
    hits = [(i, ln) for i, ln in enumerate(text.split('\n')) if ln.startswith(prefix)]
    assert len(hits) == 1, 'expected exactly 1 line starting with %r, got %d' % (prefix, len(hits))
    return hits[0]


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def parse_json_line(line, prefix):
    body = line[len(prefix):].rstrip()
    semi = body.endswith(';')
    if semi:
        body = body[:-1]
    return json.loads(body), semi


def dump_json_line(obj, prefix, semi):
    return prefix + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + (';' if semi else '')


# ───────────────────────── JS パッチ ─────────────────────────
P_KIND = (
    u'P1 tipWindowKind() に 横すべり出し (アワニング) を追加 — 履歴語より最終確定を優先',
    u'★v6.9 形式は「最終確定が勝つ」',
    u"""function tipWindowKind(o) {
  const lb = (o.label || '') + ' ' + (o.name || ''), k = [];
  const sill = Number(o.sillH) || 0;
  if (/FIX|はめ殺し/i.test(lb)) k.push('FIX (はめ殺し)');""",
    u"""function tipWindowKind(o) {
  const lb = (o.label || '') + ' ' + (o.name || ''), k = [];
  const sill = Number(o.sillH) || 0;
  // ★v6.9 形式は「最終確定が勝つ」。ラベルには改訂履歴がそのまま残る (WIN-04 は旧「FIX」、
  //   WIN-03 は旧「縦すべり出し」) ので、後から確定した 横すべり出し (アワニング) を最優先する。
  //   根拠: 写真60・62 で 各サッシの下框 中央に横棒ハンドル (床上 約119 / 約22.5) が見える。
  if (/横すべり出し/.test(lb)) {
    return '横すべり出し窓 (アワニング)' + (/(\\d+)\\s*連/.test(lb) ? ' ' + RegExp.$1 + '連' : '');
  }
  if (/FIX|はめ殺し/i.test(lb)) k.push('FIX (はめ殺し)');""",
)

JS_PATCHES = [P_KIND]


# ───────────────────────── ROOM_DATA v6.4 ─────────────────────────
V64_NOTE = (
    u'★v6.4 (2026-08-22) 【ユーザー確定2点の反映】'
    u'(1) 洋室4.8 南窓の 2窓の離隔 (小壁) 24.5 → 16.5cm。 旧 24.5 は 254-56-43-12.5-118 の '
    u'**閉合の余り** であって実測ではなかった。 写真59 (南壁が SE入隅→CL東面 まで丸ごと1枚に収まる唯一の写真。'
    u'EXIF orientation=1 / 4000x2250 / 2.68mm 超広角) の逆投影で実測: '
    u'南壁上の水平線 (見切り縁 y=-0.019230x+1462.42 rms3.3px / 床見切り y=-0.011176x+2166.64) の交点から '
    u'水平消失点 VP=(-87437,3144) を得 (2本が独立に yv=3144 を与えるので相互検証済み)、'
    u'チェーン両端 (SE入隅 x414.5 / CL東面 x160.5 = 全長254) を2点アンカーに 1次元射影写像 X=P+Q/(u-v) を張り、'
    u'y=900 行で各縦線を評価した。 結果 東壁→WIN-04東端 124.1 / WIN-04幅 13.5 / **離隔 16.1** / '
    u'WIN-03幅 44.6 / WIN-03西端→CL東面 55.7。 別レンズ・別画角の写真60 が独立に 離隔 16.5 を与え、'
    u'同じ写像が 西側の壁 56 を 55.7 と再現しているので 16.5 を採用。 '
    u'(2) 8.0cm の吸収先は **東側の壁 118 → 126** (写真59 の実測 124.1 ≒ 126)。 '
    u'西側の壁 56 は 実測 55.7 でそのまま、 窓幅 43 / 12.5 も写真2枚で追認したので動かさない。 '
    u'→ WIN-04 を西へ 8.0cm 平行移動 (284.0..296.5 → 276.0..288.5) するだけで 254 = 56+43+16.5+12.5+126 が閉じる。 '
    u'WIN-03・部屋ポリゴン・壁の位置は不変。 walls の W-R48-S2 (24.5→16.5) / W-R48-S3 (118→126.0) は '
    u'開口で分割された派生データなので追従させた。 '
    u'(3) 南窓の形式を 縦すべり出し / FIX → **横すべり出し (アワニング) 2連** へ是正。 '
    u'写真60・62 で 上下2枚のサッシ それぞれの下框 中央に横棒ハンドル (床上 約119 と 約22.5) が見える '
    u'(縦すべり出しならハンドルは縦框側、 FIX ならハンドル無し)。 ツールチップの「種類」も '
    u'tipWindowKind() を更新して 横すべり出し窓 (アワニング) と出るようにした '
    u'(ラベルに残る改訂履歴の FIX / 縦すべり出し より 後から確定した 横すべり出し を優先する分岐)。 '
    u'(4) F-50 カーテンレール(洋室4.8) を WIN-04 の移動に合わせて 写真59 で再測し x210.0〜305.5 → x207.0〜302.5 '
    u'(長さ95.5・天井付けダブル・出2.7/9.0・下端237.5 は不変)。 '
    u'⚠未解決: 写真49 (4.5帖) には WIN-01 の上に 露出ダブルレール (正面付け・端部ブラケットと端キャップが見える) が '
    u'確かに写っているが、 同写真では 部屋入隅→窓開口の小壁が 約25〜30px しかないのに 窓開口 148cm が 約1377px あり '
    u'(=約5倍の縮尺差)、 単一視点の射影モデルでは カメラ距離が数cm という非現実解にしかならない。 '
    u'ROOM_DATA の WIN-01 (y108..256 / 南側の壁17.5) と写真が整合していない可能性が高く、 '
    u'WIN-01 の壁内位置を先に再確定しないと レールの水平範囲を出せない。 → 4.5帖レールは未追加。 '
    u'⚠未解決: 6.2帖のレール (ユーザーが挙げた「高所小窓2つ+白レール+エアコン+ダウンライト3灯+室内物干し」 の写真と '
    u'「バルコニー大窓+正面付けレール+房掛け+白窓台」 の写真) は 間取り図等\\04_6.2帖\\ の13枚 (86〜99) にも '
    u'他フォルダにも存在しない (全フォルダ走査済み)。 → 6.2帖レール・室内物干しは未追加。 '
    u'⚠未解決: LDK の F-25 は 写真65・67 を見る限り カーテンボックス(箱) ではなく 4.8帖と同じ露出ダブルレールだが、'
    u'「出隅から出隅まで」 の範囲を実測できる画角の写真が無いため 今回は未変更。'
)

WIN04_ADD = (
    u' ★v6.4 【x位置是正】写真59 の逆投影 (南壁が SE入隅→CL東面 まで丸ごと写る唯一の1枚) で '
    u'2窓の離隔 (小壁) を 16.1cm と実測し、 写真60 の 16.5 と一致したので **16.5 を採用**。 '
    u'旧 24.5 は 254-56-43-12.5-118 の閉合の余りで実測値ではなかった。 '
    u'余る 8.0cm の吸収先は **東側の壁 118 → 126** (写真59 実測 124.1)。 '
    u'西側の壁は写真59 で 55.7 (データ56) と再現されたので不動、 窓幅も 13.5/44.6 と追認。 '
    u'→ WIN-04 を西へ 8.0cm 平行移動 (284.0..296.5 → 276.0..288.5)。 '
    u'南壁チェーン 254 = CL東面160.5 +壁56 +WIN-03 43 +小壁16.5 +WIN-04 12.5 +壁126 で閉じる。'
    u' ★v6.4 【形式是正】FIX ではなく **横すべり出し (アワニング) 2連**。 '
    u'写真60・62 で 上下2枚のサッシ それぞれの下框 中央に横棒ハンドル (床上 約119 と 約22.5) が見える '
    u'(ユーザー確定「整合性重視で」)。'
)

WIN03_ADD = (
    u' ★v6.4 【形式是正】縦すべり出し・中間ハンドル ではなく **横すべり出し (アワニング) 2連**。 '
    u'写真60・62 で 上下2枚のサッシ それぞれの下框 中央に横棒ハンドル (床上 約119 と 約22.5) が見える '
    u'(縦すべり出しならハンドルは縦框側に付く)。 ユーザー確定「整合性重視で」。 '
    u'x位置は不変 — 写真59 の逆投影で 西側の壁 (CL東面→WIN-03西端) が 55.7cm (データ56) と再現されたため。 '
    u'東隣の小壁は 24.5 → 16.5 に是正 (WIN-04 が西へ8.0 移動)。'
)

F50_ADD = (
    u' ★v6.4 WIN-04 の 8cm 西移動に合わせて 写真59 (レール全長が1枚に写る) で再測: '
    u'レール両端を 画像 u=1757.7 (東端/奥レール)・1770.8 (東端/手前レール)・2563.1 (西端/手前)・2580.8 (西端/奥) で読み、'
    u'壁面射影写像 + カメラ横位置 x≈274・壁からの距離 D≈211cm (超広角 f≈1777px と壁面縮尺 8.40px/cm から) '
    u'による視差補正を掛けて 東端 ≈301〜303 / 西端 ≈206〜210。 '
    u'→ x210.0〜305.5 → **x207.0〜302.5** (長さ95.5・天井付けダブル・出2.7/9.0・下端237.5 は不変)。 '
    u'張り出しは WIN-03 西端(216.5) から 9.5 / WIN-04 東端(288.5) から 14.0。'
)

FROZEN_KEYS = ['rooms', 'aircons', 'lights', 'zones', 'outlets']
FROZEN_SCALARS = ['unit', 'ceilingH', 'wallT', 'orientation']

# 是正後の 4.8帖 南壁チェーン (CL東面 → 東壁)
CHAIN_W = 160.5     # CL 東面
CHAIN_E = 414.5     # 4.8帖 東壁
GAP_TARGET = 16.5   # 2窓の離隔 (ユーザー確定)


def _find_one(arr, key, val, what):
    hit = [x for x in arr if x.get(key) == val]
    assert len(hit) == 1, u'%s が 1 件ではない (%d 件)' % (what, len(hit))
    return hit[0]


def patch_room_data(rd):
    u"""ROOM_DATA を v6.4 へ。 返り値 (変更したか, ログ行のリスト)"""
    log, changed = [], False

    w3 = _find_one(rd['openings'], 'id', 'WIN-03', 'WIN-03')
    w4 = _find_one(rd['openings'], 'id', 'WIN-04', 'WIN-04')
    assert w3['wallFrom'] == [216.5, 819.5] and w3['wallTo'] == [259.5, 819.5], \
        u'WIN-03 の座標が想定外: %s → %s (並行編集?)' % (w3['wallFrom'], w3['wallTo'])

    # ── ① WIN-04 を西へ 8.0 ──
    if w4['wallFrom'] == [276.0, 819.5] and w4['wallTo'] == [288.5, 819.5]:
        log.append(u'  [skip ] openings: WIN-04 は既に 276.0..288.5')
    else:
        assert w4['wallFrom'] == [284.0, 819.5] and w4['wallTo'] == [296.5, 819.5], \
            u'WIN-04 の座標が 284.0..296.5 でも 276.0..288.5 でもない: %s → %s (並行編集?)' \
            % (w4['wallFrom'], w4['wallTo'])
        w4['wallFrom'] = [276.0, 819.5]
        w4['wallTo'] = [288.5, 819.5]
        log.append(u'  [apply] openings: WIN-04 を西へ 8.0cm 平行移動 '
                   u'(284.0..296.5 → 276.0..288.5 / 離隔 24.5 → 16.5・東壁側 118 → 126)')
        changed = True

    for w, add, wid in ((w4, WIN04_ADD, 'WIN-04'), (w3, WIN03_ADD, 'WIN-03')):
        if u'★v6.4' in (w.get('label') or u''):
            log.append(u'  [skip ] openings: %s.label は既に v6.4 記載あり' % wid)
        else:
            w['label'] = (w.get('label') or u'') + add
            log.append(u'  [apply] openings: %s.label に v6.4 の根拠を追記' % wid)
            changed = True

    # ── walls (開口で分割された派生データ) を追従 ──
    s2 = _find_one(rd['walls'], 'id', 'W-R48-S2', 'W-R48-S2')
    s3 = _find_one(rd['walls'], 'id', 'W-R48-S3', 'W-R48-S3')
    tgt2 = {'from': 259.5, 'to': 276.0, 'length': 16.5, 'where': u'x259.5〜276.0 (y819.5)'}
    tgt3 = {'from': 288.5, 'to': 414.5, 'length': 126.0, 'where': u'x288.5〜414.5 (y819.5)'}
    old2 = {'from': 259.5, 'to': 284.0, 'length': 24.5}
    old3 = {'from': 296.5, 'to': 414.5, 'length': 118.0}
    for w, tgt, old, wid in ((s2, tgt2, old2, 'W-R48-S2'), (s3, tgt3, old3, 'W-R48-S3')):
        if all(w.get(k) == v for k, v in tgt.items()):
            log.append(u'  [skip ] walls: %s は既に 目標値 (length %.1f)' % (wid, tgt['length']))
            continue
        assert all(w.get(k) == v for k, v in old.items()), \
            u'%s が 旧値でも 新値でもない: %s (並行編集?)' % (wid, json.dumps(w, ensure_ascii=False))
        w.update(tgt)
        log.append(u'  [apply] walls: %s %.1f → %.1f (%s)' % (wid, old['length'], tgt['length'], tgt['where']))
        changed = True

    # ── F-50 カーテンレール の x 追従 ──
    f50 = _find_one(rd['fixtures'], 'id', 'F-50', 'F-50')
    assert f50.get('type') == 'curtain_rail' and f50.get('room') == 'west4_8', u'F-50 が想定外'
    assert abs(float(f50['rect'][2]) - 95.5) < 1e-6, u'F-50 の長さが 95.5 ではない: %s' % f50['rect']
    if abs(float(f50['rect'][0]) - 207.0) < 1e-6:
        log.append(u'  [skip ] fixtures: F-50.rect[0] は既に 207.0')
    else:
        assert abs(float(f50['rect'][0]) - 210.0) < 1e-6, \
            u'F-50.rect[0] が 210.0 でも 207.0 でもない: %s' % f50['rect'][0]
        f50['rect'][0] = 207.0
        log.append(u'  [apply] fixtures: F-50.rect[0] 210.0 → 207.0 (x207.0〜302.5 / 長さ95.5 は不変)')
        changed = True
    if u'★v6.4' in (f50.get('label') or u''):
        log.append(u'  [skip ] fixtures: F-50.label は既に v6.4 記載あり')
    else:
        f50['label'] = (f50.get('label') or u'') + F50_ADD
        log.append(u'  [apply] fixtures: F-50.label に v6.4 の再測根拠を追記')
        changed = True

    # ── meta ──
    notes = rd['meta'].setdefault('notes', [])
    hit = [i for i, n in enumerate(notes) if u'★v6.4 (2026-08-22)' in n]
    assert len(hit) <= 1, u'meta.notes に v6.4 の記録が複数ある'
    if not hit:
        notes.append(V64_NOTE)
        log.append(u'  [apply] meta.notes: v6.4 の記録を追記')
        changed = True
    elif notes[hit[0]] != V64_NOTE:
        notes[hit[0]] = V64_NOTE
        log.append(u'  [apply] meta.notes: v6.4 の記録を最新値へ更新')
        changed = True
    else:
        log.append(u'  [skip ] meta.notes: v6.4 の記録は既に最新')

    ver = rd['meta'].get('version')
    if ver == '6.3':
        rd['meta']['version'] = '6.4'
        log.append(u'  [apply] meta.version 6.3 → 6.4')
        changed = True
    elif ver == '6.4':
        log.append(u'  [skip ] meta.version は既に 6.4')
    else:
        log.append(u'  [warn ] meta.version = %s (6.3 でも 6.4 でもないので触らない / 並行編集?)' % ver)

    return changed, log


def assert_chain(rd):
    u"""4.8帖 南壁チェーンが 254 で閉じ、離隔が 16.5 であることを機械 assert"""
    w3 = _find_one(rd['openings'], 'id', 'WIN-03', 'WIN-03')
    w4 = _find_one(rd['openings'], 'id', 'WIN-04', 'WIN-04')
    a3, b3 = w3['wallFrom'][0], w3['wallTo'][0]
    a4, b4 = w4['wallFrom'][0], w4['wallTo'][0]
    for w, a, b in ((w3, a3, b3), (w4, a4, b4)):
        assert abs((b - a) - float(w['width'])) < 1e-6, \
            u'%s の width %s と座標幅 %.2f が一致しない' % (w['id'], w['width'], b - a)
        assert w['wallFrom'][1] == 819.5 and w['wallTo'][1] == 819.5, u'%s が南壁 y819.5 に無い' % w['id']
    seg_w = a3 - CHAIN_W          # CL東面 → WIN-03 西端
    gap = a4 - b3                 # WIN-03 東端 → WIN-04 西端 (2窓の離隔)
    seg_e = CHAIN_E - b4          # WIN-04 東端 → 東壁
    total = seg_w + (b3 - a3) + gap + (b4 - a4) + seg_e
    print(u'  南壁チェーン: 壁%.1f + WIN-03 %.1f + 小壁%.1f + WIN-04 %.1f + 壁%.1f = %.1f'
          % (seg_w, b3 - a3, gap, b4 - a4, seg_e, total))
    assert abs(gap - GAP_TARGET) < 1e-6, u'2窓の離隔が %.2f (期待 %.2f)' % (gap, GAP_TARGET)
    assert abs(total - (CHAIN_E - CHAIN_W)) < 1e-6, \
        u'南壁チェーンが %.2f で閉じない (期待 %.2f)' % (total, CHAIN_E - CHAIN_W)
    assert abs(seg_w - 56.0) < 1e-6, u'西側の壁が 56 ではない: %.2f' % seg_w
    assert abs(seg_e - 126.0) < 1e-6, u'東側の壁が 126 ではない: %.2f' % seg_e
    # walls (派生データ) との整合
    s2 = _find_one(rd['walls'], 'id', 'W-R48-S2', 'W-R48-S2')
    s3 = _find_one(rd['walls'], 'id', 'W-R48-S3', 'W-R48-S3')
    assert s2['from'] == b3 and s2['to'] == a4 and abs(s2['length'] - gap) < 1e-6, \
        u'W-R48-S2 が 開口と整合しない: %s' % json.dumps(s2, ensure_ascii=False)
    assert s3['from'] == b4 and s3['to'] == CHAIN_E and abs(s3['length'] - seg_e) < 1e-6, \
        u'W-R48-S3 が 開口と整合しない: %s' % json.dumps(s3, ensure_ascii=False)
    # カーテンレールが 2窓を覆う
    f50 = _find_one(rd['fixtures'], 'id', 'F-50', 'F-50')
    r0, rl = float(f50['rect'][0]), float(f50['rect'][2])
    assert r0 <= a3 and r0 + rl >= b4, u'F-50 が 2窓を覆っていない: %.1f..%.1f' % (r0, r0 + rl)
    print(u'  F-50 レール: x%.1f〜%.1f (WIN-03 西端から %.1f / WIN-04 東端から %.1f 張り出し)'
          % (r0, r0 + rl, a3 - r0, r0 + rl - b4))
    # 形式ラベル
    for w in (w3, w4):
        assert u'横すべり出し' in w['label'], u'%s のラベルに 横すべり出し が無い' % w['id']


# ───────────────────────── main ─────────────────────────
def main():
    dry = '--dry-run' in sys.argv
    text = read_text()
    original = text

    _, cs_line = data_line(text, CS_PREFIX)
    cs_before = sha(cs_line)

    rd_idx, rd_line = data_line(text, RD_PREFIX)
    rd, rd_semi = parse_json_line(rd_line, RD_PREFIX)
    assert dump_json_line(rd, RD_PREFIX, rd_semi) == rd_line.rstrip(), \
        'ROOM_DATA の JSON round-trip が一致しない (整形方法が想定外)'
    frozen_before = dict((k, sha(json.dumps(rd[k], ensure_ascii=False, separators=(',', ':'))))
                         for k in FROZEN_KEYS + FROZEN_SCALARS)
    counts_before = dict((k, len(rd[k])) for k in ('rooms', 'openings', 'outlets', 'aircons',
                                                   'fixtures', 'lights', 'zones', 'walls'))

    print(u'CATALOG_SEED sha256 (before) : %s' % cs_before)
    print(u'ROOM_DATA    sha256 (before) : %s  version=%s' % (sha(rd_line), rd['meta'].get('version')))
    print('')

    # ── JS パッチ ──
    applied, skipped, failed = [], [], []
    for name, marker, old, new in JS_PATCHES:
        if marker in text:
            skipped.append(name)
            continue
        n = text.count(old)
        if n != 1:
            failed.append(u'%s : アンカー一致 %d 件 (期待 1)' % (name, n))
            continue
        text = text.replace(old, new, 1)
        applied.append(name)

    for n in applied:
        print(u'  [apply] %s' % n)
    for n in skipped:
        print(u'  [skip ] %s' % n)
    for n in failed:
        print(u'  [FAIL ] %s' % n)

    # ── ROOM_DATA パッチ ──
    rd_changed, rd_log = patch_room_data(rd)
    for l in rd_log:
        print(l)
    if rd_changed:
        lines = text.split('\n')
        i2, _ = data_line(text, RD_PREFIX)
        lines[i2] = dump_json_line(rd, RD_PREFIX, rd_semi)
        text = '\n'.join(lines)

    # ── 不変アサート ──
    _, cs_after_line = data_line(text, CS_PREFIX)
    assert sha(cs_after_line) == cs_before, \
        'CATALOG_SEED CHANGED!\n  before=%s\n  after =%s' % (cs_before, sha(cs_after_line))
    _, rd_after_line = data_line(text, RD_PREFIX)
    rd_after, _ = parse_json_line(rd_after_line, RD_PREFIX)
    frozen_after = dict((k, sha(json.dumps(rd_after[k], ensure_ascii=False, separators=(',', ':'))))
                        for k in FROZEN_KEYS + FROZEN_SCALARS)
    for k in FROZEN_KEYS + FROZEN_SCALARS:
        assert frozen_before[k] == frozen_after[k], \
            u'ROOM_DATA.%s が変更されている (このパッチは meta / openings / walls / fixtures しか触らない)' % k
    for k, v in counts_before.items():
        assert len(rd_after[k]) == v, u'%s の件数が %d → %d に変わった' % (k, v, len(rd_after[k]))

    print('')
    print(u'  ── 幾何アサート ──')
    assert_chain(rd_after)

    print('')
    print(u'CATALOG_SEED sha256 (after)  : %s  ← 不変 OK' % sha(cs_after_line))
    print(u'ROOM_DATA    sha256 (after)  : %s  version=%s' % (sha(rd_after_line), rd_after['meta'].get('version')))
    print(u'ROOM_DATA 不変アサート OK : %s' % ' / '.join(FROZEN_KEYS + FROZEN_SCALARS))
    print(u'件数不変 OK : %s' % ' / '.join('%s=%d' % (k, v) for k, v in sorted(counts_before.items())))
    print('')
    print(u'JS: 適用 %d 件 / skip %d 件 / 失敗 %d 件 / ROOM_DATA 変更 %s'
          % (len(applied), len(skipped), len(failed), u'あり' if rd_changed else u'なし'))

    if failed:
        print(u'\n!! 失敗があるので書き戻しません (並行編集でアンカーが変わった可能性)')
        return 1
    if dry:
        print(u'(dry-run: 書き込みなし)')
        return 0
    if text == original:
        print(u'→ 変更なし (全て適用済み)')
        return 0
    if read_text() != original:
        print(u'\n!! room.html が読み込み後に別プロセスで変更されました。 書き込みを中断します。 再実行してください。')
        return 2
    with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(u'→ %s を更新しました' % TARGET)
    return 0


if __name__ == '__main__':
    sys.exit(main())

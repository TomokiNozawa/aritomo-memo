# -*- coding: utf-8 -*-
u"""
nozaROOM room.html v7.1 (ROOM_DATA v6.6) 冪等パッチ — 重複要素の整理

━━ ユーザー指摘 ━━
① 「OP-02 (ペット小部屋 開口) は実物にはないので削除」
② 「同じものに別IDが付与されているものがいくつかありますね? なぜですか?」

━━ ② の答え (原因) ━━
ID は annotate_names_*.py が **配列順で機械採番** する。 そのため
「修正のたびに 新しい要素を足し、 古い等価な要素を消し忘れる」 と
実体が1つなのに ID が2つ生える。 実際に過去
  ・AC-2 のラベルに 「旧A5=同一実機の二重登録を統合」 と 統合の痕跡が残っている
  ・v6.1 で 「シューズBOX に埋没していた フックレール / 丸型給気口」 を削除している
という 同型の事故が 2回起きている。 OP-02 は その3例目で、
**F-16 (petbase) の buildFixture が すでに 62x66 の開口パネルを描いている** のに
openings 側にも 同じ 62x66 の穴が 別 ID で登録されていた。

━━ 今回やること ━━
(1) openings から **OP-02 を削除** (ユーザー確定)。
    OP-01 が type='open' の唯一の要素になるので **OP 系の連番繰り上がりは発生しない**。
    room.html に OP-02 を名指しするコードは無い (grep 済み) ので 描画・判定への影響は
    「LDK 南壁の穴が1つ減る」 だけ。 ペット小部屋の見た目は F-16 側のパネルで維持される。

(2) walls を **部屋ポリゴン + 開口 から決定論的に再生成** (wallgen.py)。
    OP-02 が LDK 南辺を x445..507 で割っていたので、
        旧 W-LDK-S1 (185..445) + 旧 W-LDK-S2 (507..632) → 新 W-LDK-S1 (185..632 / 447cm)
        旧 W-LDK-S3 (706..790)                          → 新 W-LDK-S2
    となり **W-LDK-S3 が消滅、 LDK 南壁だけ ID が1つ繰り上がる** (walls 68 → 67)。
    同時に、 v6.6 (アプリ) で足した F-48 洗面棚板 が walls の feature に未追従だった
    取りこぼしも 再生成で解消する (W-WSH-N1 / W-WSH-E1)。

(3) 3D で 使われなくなった FIX_STYLE の `hook_rail` を削除。
    実体 (フックレール fixture) は v6.1 でユーザー確定により削除済みで、
    ROOM_DATA のどこからも参照されていない JS 側の残骸。

(4) meta.version 6.6 / meta.notes に 監査結果を記録。

※ 併走タスク (v7.0 = 6.2帖 カーテンレール実測) と 触る配列が違う (あちらは fixtures)。
   本スクリプトは冪等なので、 v7.0 が後から入った場合は もう一度実行すれば良い。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v7_1.py [--dry-run]
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wallgen  # noqa: E402

TARGET = os.path.join(os.path.dirname(HERE), 'room.html')
RD_PREFIX = u'var ROOM_DATA = '
CS_PREFIX = u'var CATALOG_SEED = '
OPEN_MATCH_TOL = 18.0        # room.html の同名定数
NEW_VER = u'6.6'


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
P_HOOKRAIL = (
    u'P1 FIX_STYLE から 未使用の hook_rail を削除 (v6.1 で実体を削除済みの残骸)',
    u'★v7.1 hook_rail は削除済み',
    u"""  hook_rail:    { color: 0xffffff, h: 173 },   // フックレール (白小物)
  vent:         { color: 0xf6f6f6, h: 208 },   // 給気口 (白小物)""",
    u"""  // ★v7.1 hook_rail は削除済み — 実体だった 『シューズBOX 内のフックレール』 は
  //   ROOM_DATA v6.1 でユーザー確定により削除された。 type を残すと 「消したはずの物が
  //   まだ描ける」 状態になり 二重登録の再発源になるので スタイル定義ごと落とす。
  vent:         { color: 0xf6f6f6, h: 208 },   // 給気口 (白小物)""",
)

JS_PATCHES = [P_HOOKRAIL]


# ───────────────────────── ROOM_DATA v6.6 ─────────────────────────
V66_NOTE = (
    u'★v6.6 (2026-08-22) 【重複要素の全数監査と整理】'
    u'(1) **OP-02 (ペット小部屋 開口 62x66) を削除** (ユーザー確定「実物にはない」)。 '
    u'これは F-16 (petbase) の buildFixture が すでに 62x66 の開口パネルを描いているのと '
    u'**同じ実体の二重登録**だった。 openings 側の OP-02 は LDK 南壁 (y553.5) を x445..507 で '
    u'くり抜く「穴」として効いていたが、 実物のペット小部屋は 壁を貫通する開口ではなく '
    u'カウンター東端下のニッチなので、 穴は不要。 削除後も 見た目は F-16 のパネルで維持される。 '
    u'(2) 二重登録が生まれる仕組み: ID は annotate_names_*.py が **配列順で機械採番** するため、 '
    u'修正のたびに新しい要素を足して 古い等価な要素を消し忘れると 実体1つに ID が2つ生える。 '
    u'同型の事故は過去2回あり、 AC-2 のラベルに残る「旧A5=同一実機の二重登録を統合」 と '
    u'v6.1 の「シューズBOX に埋没していた フックレール / 丸型給気口 を削除」 がそれ。 OP-02 は3例目。 '
    u'(3) walls を 部屋ポリゴン+開口 から再生成 (68 → 67 区画)。 OP-02 が割っていた LDK 南辺が '
    u'つながり 旧 W-LDK-S1(185..445) + 旧 W-LDK-S2(507..632) → 新 W-LDK-S1(185..632 / 447cm)、 '
    u'旧 W-LDK-S3(706..790) → 新 W-LDK-S2 へ **LDK 南壁だけ ID が1つ繰り上がる**。 '
    u'あわせて アプリ v6.6 で追加した F-48 (洗面 上部の棚板) が walls の feature に未追従だった '
    u'取りこぼし (W-WSH-N1 / W-WSH-E1) も解消。 部屋ポリゴン・開口座標・実測チェーンは一切不変。 '
    u'(4) 再発防止として catalog_scripts/validate_room_data.py を新設。 '
    u'完全包含 / bbox80%重複 / 中心が相手の内部 / 同 type+同名の近接 / 実体のある設備同士の貫通 / '
    u'3D非描画 fixture / ラベル座標と rect の食い違い / 点要素が所属室の外 / walls の再生成一致 を '
    u'ERROR・WARN で常設検出する (意図的な重なりは ALLOW リストで明示的に許容)。 '
    u'⚠残った要ユーザー判断 (今回は削除せず保留): '
    u'[a] AC-2 (LDK 南壁 x397.5) と AC-4 (4.8帖 北壁 x385) は 同じ間仕切りの表裏 12.5cm 違いで、 '
    u'AC-2 のラベルに A5 統合の前科があるため 別実機か二重登録か 要確認。 '
    u'[b] F-38 (玄関PS) が F-16 (ペット小部屋) を 116,620cm³ 貫通し、 F-38 と F-39 (DPS) も '
    u'20,400cm³ 重なる。 3点とも est:true の推定配置で、 ラベルに書かれた座標 '
    u'(PS x445..494 y613.5..647.5 等) と rect が一致していない。 帯の PS/DPS/MB は 要再配置。 '
    u'[c] C-06 は「ニッチカウンター台下」 と書かれているのに x559.5 で シューズBOX (523.5..632) の中。 '
    u'[d] F-45 (柱9.5 / x103..112.5) が D-03 (引き戸開口 x103..185) の中に立っている。 '
    u'[e] L-15/L-16/L-18 が 所属室のポリゴン外 (v6.1 の帯 10cm 北移動に未追従)。 '
    u'[f] F-32 玄関土間 / F-46 メインバルコニー / F-47 小バルコニー は FIX_STYLE に type が無く '
    u'3D では一切描画されない データだけの枠 (床・手すりで表現済み)。 F-47 は 198x75 で '
    u'部屋ポリゴン R-BLN (255x60.5) とも食い違う。 '
    u'[g] ラベルの座標記述が rect と食い違う fixture が 11 件 (F-14/16/17/18/20/23/27/37/38/39/42)。'
)

F16_ADD = (
    u' ★v6.6 【OP-02 を削除】 開口 62x66 は この petbase fixture が 自前で '
    u'暗色パネルとして描いている (buildFixture の petbase 分岐)。 openings 側にあった '
    u'OP-02 は 同じ実体の二重登録で、 かつ LDK 南壁を貫通する穴として効いていたため '
    u'ユーザー確定 (「実物にはない」) により削除した。 **ここに再び openings を足さないこと**。'
)

FROZEN_KEYS = ['rooms', 'outlets', 'aircons', 'lights', 'zones']
FROZEN_SCALARS = ['unit', 'ceilingH', 'wallT', 'orientation']

# 監査で「保留」にした要素 = 触っていないことを assert する
KEEP_IDS = ['AC-2', 'AC-4', 'F-38', 'F-39', 'F-16', 'F-32', 'F-45', 'F-46', 'F-47']


def _find(arr, _id):
    hit = [x for x in arr if x.get('id') == _id]
    assert len(hit) <= 1, u'%s が複数ある' % _id
    return hit[0] if hit else None


def patch_room_data(rd):
    log, changed = [], False

    # (1) OP-02 削除
    op2 = _find(rd['openings'], 'OP-02')
    if op2 is None:
        log.append(u'  [skip ] OP-02 は既に削除済み')
    else:
        assert op2['type'] == 'open' and abs(op2['width'] - 62) < 0.01, \
            u'OP-02 が想定と違う: %s' % json.dumps(op2, ensure_ascii=False)[:200]
        opens = [o for o in rd['openings'] if o.get('type') == 'open']
        assert [o['id'] for o in opens] == ['OP-01', 'OP-02'], \
            u"type='open' の並びが想定外: %s" % [o['id'] for o in opens]
        rd['openings'] = [o for o in rd['openings'] if o.get('id') != 'OP-02']
        changed = True
        log.append(u'  [apply] OP-02 (ペット小部屋 開口 62x66) を削除 '
                   u'→ openings %d 件。 OP-01 が唯一の open なので OP 連番の繰り上がり無し'
                   % len(rd['openings']))

    # (2) F-16 のラベルに 削除の由来を残す
    f16 = _find(rd['fixtures'], 'F-16')
    assert f16 is not None and f16['type'] == 'petbase', u'F-16 (petbase) が見つからない'
    if u'★v6.6 【OP-02 を削除】' not in f16.get('label', ''):
        f16['label'] = f16.get('label', '') + F16_ADD
        changed = True
        log.append(u'  [apply] F-16 ラベルに OP-02 削除の由来を追記')
    else:
        log.append(u'  [skip ] F-16 ラベルは追記済み')

    # (2b) F-48 に shortLabel を与える
    #   walls の feature は compact_fix_name() が shortLabel → label の順で短名を作る。
    #   F-48 は shortLabel が無く label が長いため 「洗面脱衣室 上部の棚…」 と省略記号付きの
    #   見苦しい名前になる (v6.6 で fixture を足した時に walls を再生成していなかったので
    #   今まで表面化していなかった)。 壁の目印として読める短名を与える。
    f48 = _find(rd['fixtures'], 'F-48')
    if f48 is not None and not f48.get('shortLabel'):
        f48['shortLabel'] = u'上部棚板'
        changed = True
        log.append(u'  [apply] F-48 に shortLabel「上部棚板」を付与 (walls の feature 省略記号を解消)')
    else:
        log.append(u'  [skip ] F-48 の shortLabel は設定済み')

    # (3) walls 再生成
    before = json.dumps(rd['walls'], ensure_ascii=False, sort_keys=True)
    regen = wallgen.regen(json.loads(json.dumps(rd)), OPEN_MATCH_TOL)
    if json.dumps(regen, ensure_ascii=False, sort_keys=True) != before:
        old_ids = [w['id'] for w in rd['walls']]
        rd['walls'] = regen
        changed = True
        new_ids = [w['id'] for w in regen]
        log.append(u'  [apply] walls を再生成 %d → %d 区画 (消滅: %s)'
                   % (len(old_ids), len(new_ids),
                      ', '.join(sorted(set(old_ids) - set(new_ids))) or u'なし'))
    else:
        log.append(u'  [skip ] walls は再生成結果と一致済み (%d 区画)' % len(rd['walls']))

    # (4) meta
    if rd['meta'].get('version') != NEW_VER:
        log.append(u'  [apply] meta.version %s → %s' % (rd['meta'].get('version'), NEW_VER))
        rd['meta']['version'] = NEW_VER
        changed = True
    if not any(n.startswith(u'★v6.6 (2026-08-22) 【重複要素') for n in rd['meta']['notes']):
        rd['meta']['notes'].append(V66_NOTE)
        changed = True
        log.append(u'  [apply] meta.notes に v6.6 監査ノートを追記')
    else:
        log.append(u'  [skip ] meta.notes は追記済み')

    return changed, log


# ───────────────────────── 幾何アサート ─────────────────────────
def assert_geometry(rd):
    u"""部屋ポリゴン・実測チェーンが 不変であることを確かめる"""
    poly = dict((r['key'], r['poly']) for r in rd['rooms'])
    assert poly['ldk'] == [[103.0, 283.5], [364.0, 283.5], [364.0, 208.5], [790.0, 208.5],
                           [790.0, 553.5], [103.0, 553.5]], u'LDK ポリゴンが変わっている'
    assert poly['west4_8'] == [[103.0, 563.5], [414.5, 563.5], [414.5, 819.5], [103.0, 819.5]], \
        u'4.8帖 ポリゴンが変わっている'
    print(u'    部屋ポリゴン (LDK / 4.8帖) 不変 OK')

    # 4.8帖 南壁チェーン 254 = 壁56 + WIN-03 43 + 小壁16.5 + WIN-04 12.5 + 壁126
    o = dict((x['id'], x) for x in rd['openings'])
    cl_e, wall_e = 160.5, 414.5
    a3, b3 = o['WIN-03']['wallFrom'][0], o['WIN-03']['wallTo'][0]
    a4, b4 = o['WIN-04']['wallFrom'][0], o['WIN-04']['wallTo'][0]
    seg = [a3 - cl_e, b3 - a3, a4 - b3, b4 - a4, wall_e - b4]
    assert [round(v, 2) for v in seg] == [56.0, 43.0, 16.5, 12.5, 126.0], \
        u'4.8帖 南壁チェーンが変わっている: %s' % seg
    assert abs(sum(seg) - 254.0) < 0.01
    print(u'    4.8帖 南壁チェーン 254 = %s OK' % ' + '.join('%g' % v for v in seg))

    # E壁チェーン 169 + 7 + 169 = 345
    stub = _find(rd['fixtures'], 'F-08')
    d06 = o['D-06']
    assert abs(stub['rect'][3] - 7.0) < 0.01 and abs(d06['width'] - 169.0) < 0.01, u'E壁チェーン破損'
    assert abs((stub['rect'][1] - 208.5) - 169.0) < 0.01, u'冷蔵庫スペース 169 が変わっている'
    print(u'    LDK E壁チェーン 169 + 7 + 169 = 345 OK')

    # LDK 南壁が 3 区画 → 2 区画に、 かつ 合計長 + 開口幅 = 687
    s = [w for w in rd['walls'] if w['id'].startswith('W-LDK-S')]
    assert len(s) == 2, u'LDK 南壁が %d 区画 (期待 2)' % len(s)
    assert [(w['id'], w['from'], w['to']) for w in s] == \
        [('W-LDK-S1', 185.0, 632.0), ('W-LDK-S2', 706.0, 790.0)], \
        u'LDK 南壁の区画が想定外: %s' % [(w['id'], w['from'], w['to']) for w in s]
    tot = sum(w['length'] for w in s) + 82.0 + 74.0     # D-03 82 + D-05 74
    assert abs(tot - 687.0) < 0.01, u'LDK 南壁 全長 %s (期待 687)' % tot
    print(u'    LDK 南壁 = W-LDK-S1(185..632) + D-03 82 + D-05 74 + W-LDK-S2(706..790) = 687 OK')

    # OP-02 が消えていること / 他の開口が全部残っていること
    ids = [x['id'] for x in rd['openings']]
    assert 'OP-02' not in ids and 'OP-01' in ids, u'OP の状態が想定外: %s' % ids
    assert len([i for i in ids if i.startswith('D-')]) == 11, u'ドアの件数が変わっている'
    assert len([i for i in ids if i.startswith('WIN-')]) == 7, u'窓の件数が変わっている'
    print(u'    openings: ドア11 / 窓7 / 開口1 (OP-02 削除済) OK')


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
    fix_geo_before = dict((f['id'], json.dumps([f.get('rect'), f.get('poly'), f.get('h'),
                                                f.get('bottomH'), f.get('type'), f.get('room')],
                                               ensure_ascii=False)) for f in rd['fixtures'])
    open_geo_before = dict((o['id'], json.dumps([o.get('wallFrom'), o.get('wallTo'), o.get('width'),
                                                 o.get('sillH'), o.get('height'), o.get('type')],
                                                ensure_ascii=False)) for o in rd['openings'])
    walls_geo_before = dict((w['id'], (w['room'], w['dir'], w['c'], w['from'], w['to']))
                            for w in rd['walls'])

    print(u'CATALOG_SEED sha256 (before) : %s' % cs_before)
    print(u'ROOM_DATA    sha256 (before) : %s  version=%s' % (sha(rd_line), rd['meta'].get('version')))
    print(u'件数 (before): ' + ' / '.join('%s=%d' % (k, len(rd[k])) for k in
                                          ('openings', 'fixtures', 'walls')))
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

    for k in FROZEN_KEYS + FROZEN_SCALARS:
        assert frozen_before[k] == sha(json.dumps(rd_after[k], ensure_ascii=False,
                                                  separators=(',', ':'))), \
            u'ROOM_DATA.%s が変更されている (このパッチは meta / openings / walls / F-16ラベル しか触らない)' % k

    # fixtures: ジオメトリは 1件も動かない (F-16 は label のみ変更)
    fix_geo_after = dict((f['id'], json.dumps([f.get('rect'), f.get('poly'), f.get('h'),
                                               f.get('bottomH'), f.get('type'), f.get('room')],
                                              ensure_ascii=False)) for f in rd_after['fixtures'])
    assert fix_geo_before == fix_geo_after, u'fixtures のジオメトリが変わっている'
    # openings: OP-02 以外は 1件も動かない
    open_geo_after = dict((o['id'], json.dumps([o.get('wallFrom'), o.get('wallTo'), o.get('width'),
                                                o.get('sillH'), o.get('height'), o.get('type')],
                                               ensure_ascii=False)) for o in rd_after['openings'])
    open_geo_before.pop('OP-02', None)      # 2回目以降は そもそも存在しない (冪等)
    assert open_geo_before == open_geo_after, u'OP-02 以外の開口が変わっている'
    # 保留にした要素は 1つも触っていない
    for _id in KEEP_IDS:
        a = _find(rd_after['fixtures'], _id) or _find(rd_after['aircons'], _id)
        assert a is not None, u'保留対象 %s が消えている' % _id
    # walls: LDK 南壁 以外は ジオメトリ不変
    walls_geo_after = dict((w['id'], (w['room'], w['dir'], w['c'], w['from'], w['to']))
                           for w in rd_after['walls'])
    for wid, g in walls_geo_after.items():
        if wid.startswith('W-LDK-S'):
            continue
        assert walls_geo_before.get(wid) == g, u'%s のジオメトリが変わっている: %s → %s' \
            % (wid, walls_geo_before.get(wid), g)
    moved = [w for w in walls_geo_before if w not in walls_geo_after]
    print(u'\n  ── 幾何アサート ──')
    print(u'    walls: LDK 南壁以外の %d 区画は ジオメトリ不変 OK / 消滅した ID = %s'
          % (len(walls_geo_after) - 2, ', '.join(moved) or u'なし'))
    assert_geometry(rd_after)

    print('')
    print(u'CATALOG_SEED sha256 (after)  : %s  ← 不変 OK' % sha(cs_after_line))
    print(u'ROOM_DATA    sha256 (after)  : %s  version=%s' % (sha(rd_after_line),
                                                              rd_after['meta'].get('version')))
    print(u'ROOM_DATA 不変アサート OK : %s' % ' / '.join(FROZEN_KEYS + FROZEN_SCALARS))
    print(u'件数 (after) : ' + ' / '.join('%s=%d' % (k, len(rd_after[k])) for k in
                                          ('openings', 'fixtures', 'walls')))
    print(u'JS: 適用 %d 件 / skip %d 件 / 失敗 %d 件 / ROOM_DATA 変更 %s'
          % (len(applied), len(skipped), len(failed), u'あり' if rd_changed else u'なし'))

    if failed:
        print(u'\n!! 失敗があるので書き戻しません (並行編集でアンカーが変わった可能性)')
        return 1
    if text == original:
        print(u'\n変更なし (すでに v7.1 適用済み) — 書き戻ししません')
        return 0
    if dry:
        print(u'\n--dry-run のため 書き戻ししません')
        return 0
    with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(u'\n書き戻し完了: %s' % TARGET)
    return 0


if __name__ == '__main__':
    sys.exit(main())

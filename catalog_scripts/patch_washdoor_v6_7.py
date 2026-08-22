# -*- coding: utf-8 -*-
u"""
nozaROOM room.html 「脱衣所へのドア (D-07) が3Dで見えない」 v6.7 冪等パッチ

■ 原因 (機械監査 _audit2.py の結果)
  D-07 (キッチン背面通路→洗面 引き戸74.5) の座標 wallFrom[434.0,192.0]→wallTo[508.5,192.0] は
  **洗面室 南壁 (y=192.0, x434〜597) の線上に 誤差0.0 で正しく乗っている**。
  問題は 向かい合う LDK 北壁 の方で、 ROOM_DATA v6.1 の平差が 「E壁チェーン 169+7+169=345」 と
  「LDK南北内法 実測 351.5」 の 6.5cm の差を **洗面/浴室 ↔ LDK の壁帯 (10 → 16.5)** に吸収したため、
  LDK 北壁 は y=202.0 から y=208.5 へ移動した。
  buildWalls() は 開口を エッジに載せるとき 「Math.abs(開口のc - エッジのc) <= 12」 で拾うので、
  Δ = |208.5 - 192.0| = **16.5 > 12** → LDK 北壁 (W-LDK-N2 x364〜790) は くり抜かれず、
  戸のパネルは 洗面室側の壁帯に描かれているのに **通路側から見ると 426cm の白壁で塞がれていた**。

■ 修正方針
  ジオメトリ (部屋ポリゴン・開口座標) は 1mm も動かさない。
  開口マッチングの許容差 12 → 18 (= 外壁厚 wallT.ext) に拡げ、 実在する壁帯 (最大16.5) を
  貫通できるようにする。 全開口 × 全部屋エッジ の総当たり監査で、 この変更で 新規に一致するのは
  D-07 × LDK北壁 のみ (WIN-01/02/05 × バルコニー手すりは isBal && touchesBuilding で先に skip される)
  であることを確認済み。

■ ROOM_DATA v6.2 (変更点のみ)
  - meta.version 6.1 → 6.2 / meta.notes に 本件の記録を追記
  - walls: 旧 W-LDK-N2 (x364.0〜790.0 / 426cm) を D-07 で 2 分割
      W-LDK-N2 x364.0〜434.0 (70cm)
      W-LDK-N3 x508.5〜790.0 (281.5cm / キッチン設備は全てこちら側)
    ldk|N グループの of を 2 → 3 に更新。 他の要素は 一切変更しない。

■ 不変アサート
  CATALOG_SEED の 1 行 sha256 が パッチ前後で完全一致することを assert する。
  ROOM_DATA は 上記の変更点だけであることを 差分レポートで出す (rooms/openings/fixtures/
  outlets/aircons/lights/zones の sha256 が不変であることも assert)。

■ 冪等性
  各パッチは「適用済みマーカー」を持ち、既に入っていれば skip。
  再実行すると「適用 0 件 / skip N 件」になる。

■ 並行編集への配慮
  別セッションが同じ room.html (洗濯機パン v6.6 等) を編集している可能性があるため、
  読み込み → 加工 → **書き込み直前に 再読込して 内容が変わっていないことを確認** し、
  変わっていたら 何も書かずに 中断する。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_washdoor_v6_7.py [--dry-run]
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
P_TOL_CONST = (
    u'P1 開口マッチング許容差を定数化 (12 → 18 = 外壁厚)',
    u'OPEN_MATCH_TOL',
    u"const WT = 5;                        // 描画上の壁厚(片側)。隣接室が背中合わせに描いて実壁厚を埋める",
    u"""const WT = 5;                        // 描画上の壁厚(片側)。隣接室が背中合わせに描いて実壁厚を埋める
// ★v6.7 開口 (ドア/窓/開口) を 部屋ポリゴンのエッジに載せるときの 許容差 [cm]。
//   開口は「片方の部屋の内法面」の座標で1本の線として持つので、 向かい合う相手室の壁も
//   この許容内なら 同じ開口でくり抜く = 壁帯 (2室の内法面の距離) を貫通する穴になる。
//   ROOM_DATA v6.1 の平差で 洗面/浴室 ↔ LDK の壁帯が 10 → 16.5 になり、 旧値 12 では
//   D-07 (脱衣所ドア) の LDK 側がくり抜かれず 白壁で塞がっていた (v6.7 で是正)。
//   18 = wallT.ext (この住戸に実在する最大の壁厚)。 これを超える「壁帯」はデータ上存在しない。
const OPEN_MATCH_TOL = 18;""",
)

P_BUILDWALLS = (
    u'P2 buildWalls() の開口マッチングを OPEN_MATCH_TOL 化',
    u'Math.abs(x.r.c - c) <= OPEN_MATCH_TOL',
    u"return x.r.horiz === horiz && Math.abs(x.r.c - c) <= 12 && Math.min(x.r.b, b) - Math.max(x.r.a, a) > 2;",
    u"return x.r.horiz === horiz && Math.abs(x.r.c - c) <= OPEN_MATCH_TOL && Math.min(x.r.b, b) - Math.max(x.r.a, a) > 2;   // ★v6.7",
)

P_DERIVE = (
    u'P3 deriveWallSegs() の開口マッチングを OPEN_MATCH_TOL 化 (buildWalls と同一手順を維持)',
    u'Math.abs(r0.c - c) <= OPEN_MATCH_TOL',
    u"return r0.horiz === horiz && Math.abs(r0.c - c) <= 12 && Math.min(r0.b, b) - Math.max(r0.a, a) > 2;",
    u"return r0.horiz === horiz && Math.abs(r0.c - c) <= OPEN_MATCH_TOL && Math.min(r0.b, b) - Math.max(r0.a, a) > 2;   // ★v6.7",
)

P_HOOK = (
    u'P4 検証フック __noza.openings() を追加 (全開口のメッシュ生成/くり抜き状況)',
    u'openings: function () {',
    u"""      doors: function () {
        // ★v2.2 検証用: ドア一覧 (id / ラベル / 開閉状態)""",
    u"""      // ★v6.7 検証用: 全開口 (ドア11 / 窓7 / 開口2) が 実際に3Dへ描画されたかの機械確認。
      //   meshes  = userData.opId が刻まれたメッシュ数 (0 なら建具が1枚も立っていない)
      //   drawn   = buildOpeningPanel が走ったか
      //   cut     = この開口がくり抜いた 部屋エッジ の一覧
      //   blocked = 重なっているのに 許容差を超えていて くり抜けなかった エッジ (= 開口の前に立つ壁)
      openings: function () {
        const cnt = {};
        scene.traverse(function (m) {
          const id = m.userData && m.userData.opId;
          if (!id) return;
          if (!cnt[id]) cnt[id] = { mesh: 0, pickOnly: 0 };
          cnt[id].mesh++;
          if (m.userData.pickOnly) cnt[id].pickOnly++;
        });
        return R.openings.map(function (o) {
          const r0 = openingRange(o), cut = [], blocked = [];
          R.rooms.forEach(function (rm) {
            const poly = rm.poly, n = poly.length;
            for (let i = 0; i < n; i++) {
              const p1 = poly[i], p2 = poly[(i + 1) % n];
              const horiz = Math.abs(p1[1] - p2[1]) < 0.01;
              if (horiz !== r0.horiz) continue;
              const c = horiz ? p1[1] : p1[0];
              const a = horiz ? Math.min(p1[0], p2[0]) : Math.min(p1[1], p2[1]);
              const b = horiz ? Math.max(p1[0], p2[0]) : Math.max(p1[1], p2[1]);
              if (b - a < 0.5) continue;
              if (rm.key.indexOf('balcony') === 0 && touchesBuilding(horiz, c, a, b)) continue;
              if (Math.min(r0.b, b) - Math.max(r0.a, a) <= 2) continue;
              const d = Math.round(Math.abs(r0.c - c) * 100) / 100;
              const tag = rm.key + '@' + c + ' (d' + d + ')';
              if (d <= OPEN_MATCH_TOL) cut.push(tag); else if (d <= 40) blocked.push(tag);
            }
          });
          const k = cnt[o.id] || { mesh: 0, pickOnly: 0 };
          return { id: o.id, type: o.type, room: o.room, name: o.name,
                   c: r0.c, from: r0.a, to: r0.b,
                   meshes: k.mesh, pickOnly: k.pickOnly, drawn: !!o.__drawn,
                   cut: cut, blocked: blocked };
        });
      },
      doors: function () {
        // ★v2.2 検証用: ドア一覧 (id / ラベル / 開閉状態)""",
)

JS_PATCHES = [P_TOL_CONST, P_BUILDWALLS, P_DERIVE, P_HOOK]


# ───────────────────────── ROOM_DATA v6.2 ─────────────────────────
V62_NOTE = (
    u'★v6.2 (2026-08-22) 【3D描画バグ是正 = 脱衣所ドアの消失】 D-07 (キッチン背面通路→洗面 引き戸74.5) の '
    u'座標 y=192.0 は 洗面室 南壁 の線上に 誤差 0.00cm で 正しく乗っていた。 消えていた原因は 向かい側で、 '
    u'v6.1 が 6.5cm の未解決差を 洗面/浴室 ↔ LDK の壁帯 (10 → 16.5) に吸収した結果 LDK 北壁 が y=202.0 → 208.5 へ動き、 '
    u'|208.5 - 192.0| = 16.5 が buildWalls() の開口マッチング許容 12cm を超えて LDK 北壁 (旧 W-LDK-N2 = 426cm) が '
    u'くり抜かれず、 通路側から見ると 戸が 白壁で塞がれていた。 許容差を 18 (= wallT.ext) へ拡げて是正 '
    u'(ジオメトリの数値は 一切変更していない)。 これに伴い 旧 W-LDK-N2 は D-07 で2分割され '
    u'W-LDK-N2 (x364.0〜434.0) / W-LDK-N3 (x508.5〜790.0) になる。 '
    u'全20開口 × 全部屋エッジ の総当たり監査で 同種のくり抜き漏れは D-07 のみであることを確認済み '
    u'(D-04 は 部屋ポリゴンではなく クローゼット fixture 面の建具で、 buildStatic の後段で描画される正常系)。'
)

LDK_N2_NEW = {
    u'id': u'W-LDK-N2', u'name': u'LDK北壁②', u'room': u'ldk', u'dir': u'N', u'horiz': True,
    u'c': 208.5, u'from': 364.0, u'to': 434.0, u'length': 70.0, u'height': 240, u'outSign': -1,
    u'where': u'x364.0〜434.0 (y208.5)', u'seq': 2, u'of': 3, u'minor': False,
}
LDK_N3_NEW = {
    u'id': u'W-LDK-N3', u'name': u'LDK北壁③（キッチン）', u'room': u'ldk', u'dir': u'N', u'horiz': True,
    u'c': 208.5, u'from': 508.5, u'to': 790.0, u'length': 281.5, u'height': 240, u'outSign': -1,
    u'where': u'x508.5〜790.0 (y208.5)', u'seq': 3, u'of': 3, u'minor': False,
    u'feature': u'キッチン / タイル壁 / ダクト / コンロ',
}

FROZEN_KEYS = ['rooms', 'openings', 'outlets', 'aircons', 'fixtures', 'lights', 'zones']


def patch_room_data(rd):
    """ROOM_DATA を v6.2 へ。 返り値 (変更したか, ログ行のリスト)"""
    log, changed = [], False

    walls = rd['walls']
    ids = [w.get('id') for w in walls]
    if 'W-LDK-N3' in ids:
        log.append(u'  [skip ] walls: W-LDK-N3 は既に存在')
    else:
        idx = [i for i, w in enumerate(walls)
               if w.get('id') == 'W-LDK-N2' and w.get('room') == 'ldk' and w.get('dir') == 'N']
        assert len(idx) == 1, 'W-LDK-N2 (ldk/N) が 1 件ではない: %d' % len(idx)
        old = walls[idx[0]]
        assert abs(old['from'] - 364.0) < 1e-6 and abs(old['to'] - 790.0) < 1e-6, \
            u'W-LDK-N2 の範囲が想定外 (%s〜%s) — 並行編集で先に分割された可能性' % (old['from'], old['to'])
        assert abs(old['c'] - 208.5) < 1e-6, u'W-LDK-N2 の c が想定外: %s' % old['c']
        walls[idx[0]:idx[0] + 1] = [dict(LDK_N2_NEW), dict(LDK_N3_NEW)]
        log.append(u'  [apply] walls: W-LDK-N2 (x364.0〜790.0 / 426cm) → '
                   u'W-LDK-N2 (x364.0〜434.0 / 70cm) + W-LDK-N3 (x508.5〜790.0 / 281.5cm)')
        changed = True

    n1 = [w for w in walls if w.get('id') == 'W-LDK-N1']
    assert len(n1) == 1, 'W-LDK-N1 が 1 件ではない'
    if n1[0].get('of') != 3:
        n1[0]['of'] = 3
        log.append(u'  [apply] walls: W-LDK-N1.of 2 → 3')
        changed = True
    else:
        log.append(u'  [skip ] walls: W-LDK-N1.of は既に 3')

    notes = rd['meta'].setdefault('notes', [])
    if any(u'★v6.2 (2026-08-22)' in n for n in notes):
        log.append(u'  [skip ] meta.notes: v6.2 の記録は既に存在')
    else:
        notes.append(V62_NOTE)
        log.append(u'  [apply] meta.notes: v6.2 の記録を追記')
        changed = True

    ver = rd['meta'].get('version')
    if ver == '6.1':
        rd['meta']['version'] = '6.2'
        log.append(u'  [apply] meta.version 6.1 → 6.2')
        changed = True
    elif ver == '6.2':
        log.append(u'  [skip ] meta.version は既に 6.2')
    else:
        log.append(u'  [warn ] meta.version = %s (6.1 でも 6.2 でもないので触らない / 並行編集?)' % ver)

    return changed, log


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
                         for k in FROZEN_KEYS)

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
        new_rd_line = dump_json_line(rd, RD_PREFIX, rd_semi)
        lines = text.split('\n')
        i2, _ = data_line(text, RD_PREFIX)
        lines[i2] = new_rd_line
        text = '\n'.join(lines)

    # ── 不変アサート ──
    _, cs_after_line = data_line(text, CS_PREFIX)
    assert sha(cs_after_line) == cs_before, \
        'CATALOG_SEED CHANGED!\n  before=%s\n  after =%s' % (cs_before, sha(cs_after_line))
    _, rd_after_line = data_line(text, RD_PREFIX)
    rd_after, _ = parse_json_line(rd_after_line, RD_PREFIX)
    frozen_after = dict((k, sha(json.dumps(rd_after[k], ensure_ascii=False, separators=(',', ':'))))
                        for k in FROZEN_KEYS)
    for k in FROZEN_KEYS:
        assert frozen_before[k] == frozen_after[k], \
            u'ROOM_DATA.%s が変更されている (このパッチは meta と walls しか触らない)' % k

    print('')
    print(u'CATALOG_SEED sha256 (after)  : %s  ← 不変 OK' % sha(cs_after_line))
    print(u'ROOM_DATA    sha256 (after)  : %s  version=%s' % (sha(rd_after_line), rd_after['meta'].get('version')))
    print(u'ROOM_DATA 不変アサート OK : %s' % ' / '.join(FROZEN_KEYS))
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
    # 並行編集ガード: 読み込み後にファイルが変わっていたら 何も書かない
    if read_text() != original:
        print(u'\n!! room.html が読み込み後に別プロセスで変更されました。 書き込みを中断します。 再実行してください。')
        return 2
    with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(u'→ %s を更新しました' % TARGET)
    return 0


if __name__ == '__main__':
    sys.exit(main())

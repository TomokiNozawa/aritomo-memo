# -*- coding: utf-8 -*-
u"""
nozaROOM room.html v6.8 (ROOM_DATA v6.3) 冪等パッチ

━━ ユーザー確定 2点 ━━

① 洗面のコンセント C-13 (No.13 / 洗濯機パン上) の取付高さ 110 → 131cm
   v6.6 の写真42 逆投影 (パン天面の4隅=外寸64x64 既知 → カメラ姿勢を LM で解き、
   JIS 1連プレート 120x70mm でスケール補正) で 「プレート中心 ≈ 131cm、
   洗濯水栓 (F-29 下端 131.8cm) とほぼ同じ高さ」 と確定済み。
   座標 pos[565.0, 18.0] と wallSide は 一切変更しない。est は写真実測扱いで解除。

② 洋室4.8帖の南窓 (WIN-03 / WIN-04) を 写真60 準拠に是正 + カーテンレールを新規追加
   ユーザー指示: 「画像60を参考に修正してください。高さとカーテンレール部分が異なるかと思います」

   ▼ 写真60 (05_4.8帖/..._60.jpg) の単一視点メトロロジー
     ・この写真は EXIF orientation=6 (右90度回転) が入っている。生ピクセルのままだと
       窓が横倒しに見えるので ImageOps.exif_transpose した 2250x4000 で計測した。
     ・カメラは南壁にほぼ正対。壁は平面なので 1つの画像列 x では 高さ→画像y が線形に写る:
           h(y) = 240 * (y_floor(x) - y) / (y_floor(x) - y_ceil(x))
       天井見切り線と 床見切り線 (巾木下端) をそれぞれ画像から直線近似して使った。
           y_ceil (x)  = 361.5 - 0.01964 x     (rail に隠れない x<405 / x>1770 の実測を直線当て)
           y_floor(x)  = 3649.4 - 0.0079  x     (巾木下端。巾木上端は -45.8px で平行)
       → 壁面での縮尺 k ≈ 13.78 px/cm。
     ▼ 縮尺の相互検証 (これが効いている)
       同じ k で 窓の開口幅を測ると
           広い方 (WIN-03) 画像 x1065..1655 = 590px → 42.8cm  … ROOM_DATA 43 と一致
           細い方 (WIN-04) 画像 x 655.. 838 = 183px → 13.3cm  … ROOM_DATA 12.5 と ±0.8
       ので 高さ方向の縮尺も信用してよい。

   ▼ 読み取り結果 (2つの窓で独立に計測 → 上端・下端とも 0.1cm 差で一致)
       開口 上端 (壁面):  WIN-03 y=434 → 232.7cm  /  WIN-04 y=446 → 232.6cm
       開口 下端 (窓台):  WIN-03 y=3414 → 16.3cm  /  WIN-04 y=3420 → 16.2cm
         ※ 窓台は壁面より 2〜3cm 手前に出ているぶん 画像では下に写る。
            その分を戻すと +1.1cm → 17.4cm。
     → sillH 10 → 17.5 / height 200 → 215 (上端 232.5cm)。誤差は ±1.5cm 程度。
       旧値 (sill10 / h200 = 上端210) は v1.7 で動画 t≈0:57 から起こした概算だった。

   ▼ 窓枠の見え方 (参考・データは変更しない)
       ・見込み (壁仕上げ面 → 障子面) ≈ 14.3cm。額縁 (木枠) は無く クロス巻き込み + 白の窓台。
       ・枠はダークブロンズ。上下2枚のガラスに分かれ、各サッシの下框 中央に横棒ハンドル
         (中間 = 床から約119cm / 最下 = 約22.5cm)。
       ・2窓の離隔 (小壁) は 画像 x838..1065 = 227px → 16.5cm。
         ROOM_DATA の 24.5 (= 254 - 56 - 43 - 12.5 - 118 の実測閉合の余り) と 8cm 食い違う。
         → x 座標系は 今回のスコープ外なので触らない。報告のみ。

   ▼ カーテンレール (写真60 + 写真62)
       ・カーテンボックス (箱) ではなく 露出レール。**天井付け (天井にブラケット)**。
         根拠: 左右の端部ブラケットに 見えるビスが 2本あり、 その2本が 画像で
         「y が違う (=奥行きが違う) 上に x も 画面中心から外へずれる」。
         壁付けの縦プレートなら 2本のビスは同じ x に並ぶので、水平プレート = 天井付け。
         さらに レール本体が 天井見切り線より上に写る (= 壁面より手前に出ている) こととも整合。
       ・天井高 240 は既知なので、天井にあるビスは 画像 y から 壁からの出が直に読める:
         右端ブラケットの 手前ビス = 壁から 5.3cm / 奥ビス = 0.0cm (= 壁際)。
         → ブラケットの水平プレートは 壁際〜約6cm。
       ・ダブルレール。上記プレートに合わせて 手前レールを 壁から 9.0cm と置くと、
         2本のレールの画像 y から逆算した取付高さが 238.1 / 238.1 と一致する
         (奥レールは 壁から 2.7cm)。市販の天井付けダブルブラケットの寸法とも整合。
       ・レール高さ = 天井直下。レール中心 床から ≈238.1 / 下端 ≈237.5 / ブラケット上端 = 天井240。
       ・左右範囲: 同画角レンダリングと写真60 を突き合わせる反復で追い込み、
         手前レールから 209.8〜305.8 / 奥レールから 210.3〜305.4 と 独立に一致。
         → x 210.0〜305.5 (長さ 95.5) を採用 = WIN-03 西端から 6.5 / WIN-04 東端から 9.0 の張り出し。
         (初回値 x208.5〜306.5・出4.5/13.5・下端235.4 は この突合で是正した)

━━ ROOM_DATA v6.3 の変更点 (これ以外は 1つも触らない) ━━
   meta.version 6.2 → 6.3 / meta.notes に v6.3 の記録を追記
   outlets  : C-13   h 110 → 131 / est true → false / label 追記
   openings : WIN-03 sillH 10 → 17.5 / height 200 → 215 / label 追記
              WIN-04 sillH 10 → 17.5 / height 200 → 215 / label 追記
   fixtures : F-50 カーテンレール(洋室4.8) を末尾に追加
   rooms / aircons / lights / zones / walls / unit / ceilingH / wallT / orientation は不変 (assert)

━━ 不変アサート ━━
   CATALOG_SEED の 1 行 sha256 が パッチ前後で完全一致することを assert する。
   ROOM_DATA も 上記 4 キー以外の sha256 一致を assert する。

━━ 冪等性 ━━
   各パッチは「適用済みマーカー」を持ち、既に入っていれば skip。
   再実行すると「適用 0 件 / skip N 件」になる。

━━ 並行編集への配慮 ━━
   読み込み → 加工 → 書き込み直前に 再読込して 内容が変わっていないことを確認し、
   変わっていたら 何も書かずに 中断する (exit 2)。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v6_8.py [--dry-run]
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
P_STYLE = (
    u'P1 FIX_STYLE に curtain_rail (露出カーテンレール) を追加',
    u'curtain_rail:',
    u"  curtain_box:  { color: 0xf7f7f7, h: 240 },   // カーテンボックス (白)",
    u"""  curtain_box:  { color: 0xf7f7f7, h: 240 },   // カーテンボックス (白)
  // ★v6.8 露出カーテンレール (箱ではなく レールが見えているタイプ)。写真60・62 の逆投影で
  //   洋室4.8 のレールは 天井付け・ダブル と確定。h は天井 (ブラケットの上端)。
  curtain_rail: { color: 0xcfcbc3, h: 240 },   // カーテンレール (アルミシルバー)""",
)

P_BUILD = (
    u'P2 buildFixture() に curtain_rail の描画分岐を追加 (天井ブラケット + レール2本)',
    u"if (f.type === 'curtain_rail') {",
    u"""  if (f.type === 'washer_pan') {""",
    u"""  if (f.type === 'curtain_rail') {
    // ★v6.8 露出カーテンレール。写真60・62 の逆投影より
    //   ・天井付け  … 端部ブラケットのビス2本が「奥行き違い」に並ぶ = 水平プレート = 天井直付け
    //   ・ダブル    … 壁からの出が 約4.5cm (レース用) と 約13.5cm (ドレープ用) の2本
    //   ・高さ      … ブラケット上端 = 天井 (h)、レール下端 = bottomH
    //   rect = [x, y, dx, dy] は「壁からの張り出し帯」。壁面は wallSide 側の辺。
    //   railOffsets = 壁仕上げ面から 各レール中心までの距離 [cm] (既定 4.5 / 13.5)。
    const info = { kind: 'fixture', info: f.label };
    const side = f.wallSide || 'S';
    const along = (side === 'N' || side === 'S');          // true: レールは x 方向へ伸びる
    const len = Math.max(along ? dx : dy, 1);
    const wallC = side === 'S' ? y + dy : side === 'N' ? y : side === 'E' ? x + dx : x;
    const sign = (side === 'S' || side === 'E') ? -1 : 1;   // 壁面から室内へ向かう向き
    const offs = (f.railOffsets && f.railOffsets.length) ? f.railOffsets : [4.5, 13.5];
    const RR = f.railR || 1.1;                             // レール半径
    const railY = botH + RR;                               // レール中心の高さ
    const brC = f.bracketColor ? new THREE.Color(f.bracketColor).getHex() : 0xeeece6;
    offs.forEach(function (o) {
      const c = wallC + sign * o;
      const tube = new THREE.Mesh(new THREE.CylinderGeometry(RR, RR, len, 12), mat(color));
      if (along) tube.rotation.z = Math.PI / 2; else tube.rotation.x = Math.PI / 2;
      tube.position.set(along ? x + dx / 2 : c, railY, along ? c : y + dy / 2);
      Object.assign(tube.userData, info);
      g.add(tube); pickables.push(tube);
    });
    const dep = Math.max.apply(null, offs) + 2.2;          // ブラケットの奥行き
    const nb = Math.max(2, Math.round(len / 50) + 1);      // 端部 + 約50cm ピッチ
    const bt = Math.max(topH - railY - RR, 0.8);           // ブラケットの高さ (レール上端〜天井)
    for (let i = 0; i < nb; i++) {
      const t = (along ? x : y) + 2.5 + (len - 5) * (i / (nb - 1));
      const bc = wallC + sign * dep / 2;
      pickables.push(addBox(g, along ? 3.0 : dep, bt, along ? dep : 3.0,
                            along ? t : bc, railY + RR + bt / 2, along ? bc : t, brC, info));
    }
    return;
  }
  if (f.type === 'washer_pan') {""",
)

P_TIP = (
    u'P3 ツールチップ tipFixInner() に カーテンレールの仕様行を追加',
    u'★v6.8 レールは「壁からの出」',
    u"""function tipFixInner(f) {
  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {""",
    u"""function tipFixInner(f) {
  if (f.type === 'curtain_rail') {
    // ★v6.8 レールは「壁からの出」が分からないと使えないので 本数と出を明示する
    const offs = (f.railOffsets && f.railOffsets.length) ? f.railOffsets : [4.5, 13.5];
    return '形式: ' + (f.mount === 'face' ? '正面付け' : '天井付け') +
           (offs.length >= 2 ? ' ダブル' : ' シングル') +
           ' / 壁からの出: ' + offs.map(tipN).join('cm・') + 'cm' +
           ' / 有効長: ' + tipN(f.rect ? f.rect[2] : 0) + 'cm';
  }
  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {""",
)

P_HOOK = (
    u'P4 検証フック __noza.win48() を追加 (4.8帖の窓 + レールの実効値)',
    u'win48: function () {',
    u"""      doors: function () {
        // ★v2.2 検証用: ドア一覧 (id / ラベル / 開閉状態)""",
    u"""      // ★v6.8 検証用: 洋室4.8 の窓 (WIN-03 / WIN-04) と カーテンレール (F-50) の実効値。
      //   写真60 の実測 (上端232.6 / 下端16.3+補正 / レール長97.7) と突き合わせるために出す。
      win48: function () {
        const wins = R.openings.filter(function (o) { return o.room === 'west4_8' && o.type === 'window'; })
          .map(function (o) {
            const s = Number(o.sillH) || 0, h = Number(o.height) || 0;
            return { id: o.id, width: o.width, sill: s, top: s + h, height: h, est: !!o.est };
          });
        const rails = R.fixtures.filter(function (f) { return f.type === 'curtain_rail'; })
          .map(function (f) {
            return { id: f.id, room: f.room, wallSide: f.wallSide || 'S',
                     x: [f.rect[0], f.rect[0] + f.rect[2]], len: f.rect[2],
                     y: [f.rect[1], f.rect[1] + f.rect[3]],
                     railOffsets: f.railOffsets, bottomH: f.bottomH, topH: f.h,
                     meshes: (function () {
                       let n = 0;
                       scene.traverse(function (m) { if (m.userData && m.userData.info === f.label) n++; });
                       return n;
                     })() };
          });
        return { windows: wins, rails: rails, ceilingH: CH };
      },
      doors: function () {
        // ★v2.2 検証用: ドア一覧 (id / ラベル / 開閉状態)""",
)

JS_PATCHES = [P_STYLE, P_BUILD, P_TIP, P_HOOK]


# ───────────────────────── ROOM_DATA v6.3 ─────────────────────────
V63_NOTE = (
    u'★v6.3 (2026-08-22) 【ユーザー確定2点の反映】'
    u'(1) C-13 (洗濯機パン上コンセント) の取付高さ 110 → 131cm。 v6.6 の写真42 逆投影 '
    u'(パン天面4隅=外寸64x64 でカメラ姿勢を解き JIS 1連プレート 120x70mm でスケール補正) より '
    u'プレート中心 ≈ 131cm = 洗濯水栓 (F-29 下端 131.8cm) とほぼ同高。 座標 (565.0, 18.0) は変更なし・est 解除。 '
    u'(2) 洋室4.8 南窓 WIN-03 / WIN-04 を 写真60 準拠に是正: sillH 10 → 17.5 / height 200 → 215 '
    u'(開口 上端 232.5cm)。 写真60 (EXIF orientation=6 を補正した 2250x4000) で 天井見切り線と巾木下端を '
    u'直線近似し 壁面縮尺 k ≈ 13.78 px/cm を得て逆投影。 同じ k で測った 開口幅が WIN-03 42.8cm (データ43)・'
    u'WIN-04 13.3cm (データ12.5) と一致することで縮尺を相互検証済み。 2窓で独立に測った上端 232.7 / 232.6、'
    u'下端 16.3 / 16.2 (窓台の出 2〜3cm ぶんを戻して 17.4) が 0.1cm 差で一致した。 旧値 sill10/h200 は '
    u'v1.7 で動画 t≈0:57 から起こした概算。 誤差は ±1.5cm 程度。 '
    u'(3) F-50 カーテンレール(洋室4.8) を新規追加。 写真60・62 より カーテンボックス(箱) ではなく '
    u'**天井付けの露出ダブルレール**。 端部ブラケットのビス2本が「奥行き違い」に並ぶ (画面中心から外へ x もずれる) '
    u'ため 水平プレート = 天井直付けと判定。 天井高240 が既知なので 手前側のビスは 壁から5.3cm と直接読める。 '
    u'同画角レンダリングと写真60 を突き合わせる反復で レール中心 床から ≈238.1 (下端≈237.5)・'
    u'壁からの出 2.7cm (レース用) と 9.0cm (ドレープ用)・x 210.0〜305.5 (長さ95.5 = WIN-03 西端から6.5 / WIN-04 東端から9.0 の張り出し) '
    u'に収束。 2本のレールから独立に逆算した端部 (209.8〜305.8 / 210.3〜305.4) が一致することで相互検証済み。 '
    u'⚠写真60 で測った 2窓の離隔 (小壁) は 16.5cm で、 ROOM_DATA の 24.5 (実測閉合の余り) と 8cm 食い違う。 '
    u'x 座標系は 今回変更していない (要再実測)。 '
    u'⚠写真60・62 では 各サッシの下框 中央に横棒ハンドルが付いており (床から約119cm と約22.5cm)、 '
    u'ラベルの 「縦すべり出し・中間ハンドル」 より 横すべり出し (アワニング) 2連 の可能性が高い。 形式は未変更 (要確認)。 '
    u'⚠写真60・62 には 床から約86cm の高さで壁を水平に回る薄い見切り縁と、 窓脇の小金物 (ふさ掛け?) が写っている。 未モデル化。'
)

RAIL_F50 = {
    u'type': u'curtain_rail', u'room': u'west4_8',
    u'label': (u'カーテンレール(天井付けダブル/洋室4.8 南窓 WIN-03+WIN-04 を1本でカバー) '
               u'★v6.3 写真60・62 の逆投影で確定: カーテンボックス(箱)ではなく露出レール。 '
               u'天井直付けブラケット (端部ブラケットのビス2本が奥行き違いに並ぶ=水平プレート。 '
               u'手前側のビスは 天井高240 のまま壁から5.3cm の位置に写る) に '
               u'レース用(壁から約2.7cm)+ドレープ用(壁から約9.0cm) の2本を吊る。 '
               u'レール中心 床から≈238.1 (下端≈237.5) / ブラケット上端=天井240。 '
               u'x210.0〜305.5=長さ95.5 (WIN-03 西端から6.5・WIN-04 東端から9.0 張り出す)。 '
               u'★v6.8-2 同画角レンダリングと写真60 の突合で 初回値 (x208.5〜306.5 / 出4.5・13.5 / 下端235.4) を是正: '
               u'2本のレールそれぞれから独立に逆算した端部 (209.8〜305.8 / 210.3〜305.4) が一致することを確認'),
    u'est': True,
    u'rect': [210.0, 807.5, 95.5, 12.0],
    u'wallSide': u'S',
    u'mount': u'ceiling',
    u'railOffsets': [2.7, 9.0],
    u'railR': 0.6,
    u'h': 240, u'bottomH': 237.5,
    u'color': u'#cfcbc3', u'bracketColor': u'#eeece6',
    u'showDim': False,
    u'id': u'F-50', u'name': u'カーテンレール(洋室4.8)', u'short': u'カーテンレール', u'minor': False,
}

WIN_LABEL_ADD = (
    u' ★v6.3 写真60 逆投影で sill/height 是正: 床上10・高さ200 (上端210) → '
    u'床上17.5・高さ215 (上端232.5)。 天井見切り線と巾木下端から求めた壁面縮尺 k≈13.78px/cm を、'
    u'同じ写真で測った開口幅 (WIN-03 42.8cm / WIN-04 13.3cm) で相互検証済み。 2窓で独立計測した '
    u'上端 232.7/232.6・下端 16.3/16.2 (窓台の出2〜3cmを戻して17.4) が0.1cm差で一致 (誤差±1.5cm)。 '
    u'見込み(壁面→障子)≈14.3cm・額縁なしのクロス巻き込み+白窓台。 '
    u'カーテンレールは天井付けダブル (F-50)'
)

FROZEN_KEYS = ['rooms', 'aircons', 'lights', 'zones', 'walls']
FROZEN_SCALARS = ['unit', 'ceilingH', 'wallT', 'orientation']


def _find_one(arr, key, val, what):
    hit = [x for x in arr if x.get(key) == val]
    assert len(hit) == 1, u'%s が 1 件ではない (%d 件)' % (what, len(hit))
    return hit[0]


def patch_room_data(rd):
    u"""ROOM_DATA を v6.3 へ。 返り値 (変更したか, ログ行のリスト)"""
    log, changed = [], False

    # ── ① C-13 ──
    c13 = _find_one(rd['outlets'], 'id', 'C-13', 'C-13')
    assert c13['pos'] == [565.0, 18.0], u'C-13 の座標が想定外: %s (並行編集?)' % (c13['pos'],)
    if abs(float(c13.get('h', 0)) - 131.0) < 1e-6:
        log.append(u'  [skip ] outlets: C-13.h は既に 131')
    else:
        assert abs(float(c13['h']) - 110.0) < 1e-6, u'C-13.h が 110 でも 131 でもない: %s' % c13['h']
        c13['h'] = 131
        log.append(u'  [apply] outlets: C-13.h 110 → 131 (座標 [565.0, 18.0] は不変)')
        changed = True
    if c13.get('est') is False:
        log.append(u'  [skip ] outlets: C-13.est は既に false')
    else:
        c13['est'] = False
        log.append(u'  [apply] outlets: C-13.est true → false (写真42 逆投影の実測扱い)')
        changed = True
    if u'★v6.3' in (c13.get('label') or u''):
        log.append(u'  [skip ] outlets: C-13.label は既に v6.3 記載あり')
    else:
        c13['label'] = (c13.get('label') or u'') + (
            u' ★v6.3 取付高さ 110 → 131cm (写真42 逆投影 = プレート中心131 / '
            u'洗濯水栓 F-29 下端131.8 とほぼ同高。ユーザー確定)')
        log.append(u'  [apply] outlets: C-13.label に v6.3 の根拠を追記')
        changed = True

    # ── ② WIN-03 / WIN-04 ──
    for wid in ('WIN-03', 'WIN-04'):
        w = _find_one(rd['openings'], 'id', wid, wid)
        assert w.get('room') == 'west4_8', u'%s の room が west4_8 ではない' % wid
        if abs(float(w.get('sillH', 0)) - 17.5) < 1e-6 and abs(float(w.get('height', 0)) - 215.0) < 1e-6:
            log.append(u'  [skip ] openings: %s は既に sill17.5 / h215' % wid)
        else:
            assert abs(float(w['sillH']) - 10.0) < 1e-6 and abs(float(w['height']) - 200.0) < 1e-6, \
                u'%s が sill10/h200 でも sill17.5/h215 でもない (sill=%s h=%s / 並行編集?)' \
                % (wid, w.get('sillH'), w.get('height'))
            w['sillH'] = 17.5
            w['height'] = 215
            log.append(u'  [apply] openings: %s sillH 10 → 17.5 / height 200 → 215 (上端 210 → 232.5)' % wid)
            changed = True
        if u'★v6.3' in (w.get('label') or u''):
            log.append(u'  [skip ] openings: %s.label は既に v6.3 記載あり' % wid)
        else:
            w['label'] = (w.get('label') or u'') + WIN_LABEL_ADD
            log.append(u'  [apply] openings: %s.label に v6.3 の根拠を追記' % wid)
            changed = True

    # ── ③ F-50 カーテンレール ──
    #    追加だけでなく「既に入っている F-50 を目標値へ揃える」ところまでを冪等に扱う。
    #    (写真突合の反復で 数値を追い込むため。何周しても最終形は RAIL_F50 の1つに収束する)
    rails = [f for f in rd['fixtures'] if f.get('type') == 'curtain_rail' or f.get('id') == 'F-50']
    tgt = json.loads(json.dumps(RAIL_F50))
    if not rails:
        assert len(rd['fixtures']) == 49, \
            u'fixtures が 49 件ではない (%d 件) — 連番 F-50 が衝突する可能性' % len(rd['fixtures'])
        rd['fixtures'].append(tgt)
        log.append(u'  [apply] fixtures: F-50 カーテンレール(洋室4.8) を追加 '
                   u'(x210.0〜305.5 / 壁からの出 2.7・9.0 / 237.5〜240)')
        changed = True
    else:
        assert len(rails) == 1, u'curtain_rail / F-50 が 1 件ではない (%d 件 / 並行編集?)' % len(rails)
        cur = rails[0]
        assert cur.get('id') == 'F-50' and cur.get('room') == 'west4_8', \
            u'既存 F-50 の id/room が想定外 (%s / %s)' % (cur.get('id'), cur.get('room'))
        diff = sorted(k for k in set(list(cur.keys()) + list(tgt.keys())) if cur.get(k) != tgt.get(k))
        if not diff:
            log.append(u'  [skip ] fixtures: F-50 (カーテンレール) は既に目標値')
        else:
            i = rd['fixtures'].index(cur)
            rd['fixtures'][i] = tgt
            log.append(u'  [apply] fixtures: F-50 を目標値へ更新 (差分: %s)' % u', '.join(diff))
            changed = True

    # ── meta ──
    notes = rd['meta'].setdefault('notes', [])
    hit = [i for i, n in enumerate(notes) if u'★v6.3 (2026-08-22)' in n]
    assert len(hit) <= 1, u'meta.notes に v6.3 の記録が複数ある'
    if not hit:
        notes.append(V63_NOTE)
        log.append(u'  [apply] meta.notes: v6.3 の記録を追記')
        changed = True
    elif notes[hit[0]] != V63_NOTE:
        notes[hit[0]] = V63_NOTE
        log.append(u'  [apply] meta.notes: v6.3 の記録を最新値へ更新')
        changed = True
    else:
        log.append(u'  [skip ] meta.notes: v6.3 の記録は既に最新')

    ver = rd['meta'].get('version')
    if ver == '6.2':
        rd['meta']['version'] = '6.3'
        log.append(u'  [apply] meta.version 6.2 → 6.3')
        changed = True
    elif ver == '6.3':
        log.append(u'  [skip ] meta.version は既に 6.3')
    else:
        log.append(u'  [warn ] meta.version = %s (6.2 でも 6.3 でもないので触らない / 並行編集?)' % ver)

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
                         for k in FROZEN_KEYS + FROZEN_SCALARS)

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
            u'ROOM_DATA.%s が変更されている (このパッチは meta / outlets / openings / fixtures しか触らない)' % k
    # 件数の不変 (差し替えのみ・追加は fixtures の 1 件だけ)
    assert len(rd_after['outlets']) == len(rd['outlets']) == 24, u'outlets の件数が変わった'
    assert len(rd_after['openings']) == 20, u'openings の件数が変わった'
    assert len(rd_after['fixtures']) == 50, u'fixtures が 50 件になっていない: %d' % len(rd_after['fixtures'])

    print('')
    print(u'CATALOG_SEED sha256 (after)  : %s  ← 不変 OK' % sha(cs_after_line))
    print(u'ROOM_DATA    sha256 (after)  : %s  version=%s' % (sha(rd_after_line), rd_after['meta'].get('version')))
    print(u'ROOM_DATA 不変アサート OK : %s' % ' / '.join(FROZEN_KEYS + FROZEN_SCALARS))
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

# -*- coding: utf-8 -*-
u"""
nozaROOM room.html 洗濯機パン + 上部棚 実物準拠化 v6.6 冪等パッチ

ユーザー確定 (2026-08-22):
  「洗濯機パンが実物と違う。画像41,42にある通り厚みが結構ある。
    この厚みのあるパンの天面から蛇口までの高さが115cm。その上の棚も反映して」

実装:
  1. F-28 洗濯機パン … 縁高6cm の薄型 → かさ上げ (高床) タイプ 全高 16.8cm
     ・内寸 60x60 / 外寸 64x64 は据え置き (ユーザー実測確定)
     ・天面 = 洗濯機の設置面 (= ユーザー実測『天面→蛇口 115cm』の基準面)
     ・3D は 外周リブ + 一段下がったデッキ + 四隅の脚受け凹み + 右奥の排水トラップ
  2. F-29 洗濯水栓 … 床から 119〜127 → 131.8〜139.8 (= 天面16.8 + 115)
  3. F-48 棚板 (白・ブラケット2本) / F-49 ハンガーパイプ (クロム) を新規追加
  4. 洗濯機は「床」ではなく「パン天面」に載る (ドラッグ/キー移動/掴み直しの全経路)
  5. 収まり判定を パン天面基準に更新 (通常時=水栓 / ふた開放時=棚板下端)

写真からの寸法推定 (単一視点メトロロジー / 写真42 = Xperia1VI 超広角 16mm相当):
  ・パン天面の4隅 (外寸64x64 既知) から カメラ姿勢を LM で解き、
    手前(SW)・右(SE) の垂直稜線の足元から パン全高 H を同時推定 → H = 17.3cm (rms 8.0px)
  ・同じ姿勢で 壁面 (y=18) へ逆投影した JIS 1連プレート (120x70mm) が 12.55cm と出たため
    スケール補正 k = 12.0/12.55 = 0.956 を適用 → H = 16.6cm
  ・同補正で 水栓の最下端 = 床から 130.7cm → 天面からは 114.1cm
    (ユーザー実測 115cm と ±1cm 一致 = 相互検証OK)
  ・棚ブラケット壁プレート上端 (=棚板下端) = 補正後 187.5〜190.9cm → 中央値 189cm を採用
  → パン全高 16.8cm / 棚板下端 189cm を採用 (いずれも est)

冪等性:
  各パッチは「適用済みマーカー」を持ち、既に入っていれば skip する。
  再実行すると「適用 0 件 / skip N 件」になる。

不変アサート:
  CATALOG_SEED の 1 行 sha256 は パッチ前後で必ず一致 (assert)。
  ROOM_DATA は F-28 / F-29 の置換 + F-48 / F-49 の追記のみ行い、前後の sha256 を表示する。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_washpan_v6_6.py [--dry-run]
"""
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), 'room.html')

MARK = u'★v6.6'   # ★v6.6

PAN_H = 16.8          # パン全高 (= 天面 / 洗濯機の設置面)
FAUCET_CLR = 115      # 天面 → 洗濯水栓 (ユーザー実測確定)
FAUCET_BOT = 131.8    # = PAN_H + FAUCET_CLR
FAUCET_TOP = 139.8
SHELF_BOT = 189.0     # 棚板 下端 (est)
SHELF_TOP = 191.0     # 棚板 上端 (板厚 2cm)
PIPE_BOT = 178.7      # ハンガーパイプ 下端 (est)
PIPE_TOP = 181.3


# ───────────────────────── ハッシュ ─────────────────────────
def data_line_hashes(text):
    out = {}
    for key in (u'var ROOM_DATA = ', u'var CATALOG_SEED = '):
        lines = [ln for ln in text.split('\n') if ln.startswith(key)]
        assert len(lines) == 1, 'expected exactly 1 line starting with %r, got %d' % (key, len(lines))
        out[key.strip()] = hashlib.sha256(lines[0].encode('utf-8')).hexdigest()
    return out


# ═══════════════════ ROOM_DATA (fixtures のみ) ═══════════════════

def room_data_line(text):
    ls = [ln for ln in text.split('\n') if ln.startswith(u'var ROOM_DATA = ')]
    assert len(ls) == 1
    return ls[0]


def fixture_obj(text, fid):
    u"""ROOM_DATA 行の中から fixtures の 1 オブジェクト (中括弧まるごと) を切り出す。
    literal を手打ちしないので 転記ミスで壊れることがない。"""
    line = room_data_line(text)
    key = u'"id":"%s"' % fid
    i = line.find(key)
    assert i > 0, 'fixture %s not found' % fid
    s = line.rfind(u'{', 0, i)
    e = line.find(u'}', i)
    assert s > 0 and e > i, 'brace scan failed for %s' % fid
    obj = line[s:e + 1]
    assert text.count(obj) == 1, 'fixture %s object is not unique in file' % fid
    return obj


NEW_F28 = (u'{"type":"washer_pan","room":"washroom","label":"洗濯機パン かさ上げ(高床)タイプ'
           u'(内寸60x60=ユーザー実測確定・洗濯機の設置面はこの内側/外寸64x64/'
           u'★v6.6 全高(厚み)=16.8cm ユーザー確定「画像41,42の通り厚みが結構ある」→ '
           u'写真42の単一視点メトロロジー(天面4隅=既知64x64からカメラ姿勢をLMで解き、'
           u'手前SW・右SEの垂直稜線の足元でH=17.33cm/rms8.0px)に'
           u'スケール補正(壁面のJIS1連プレート120mm基準 k=0.974 → 16.88 / '
           u'ユーザー実測115cm基準 k=0.963 → 16.70)を掛けた中央値=est。'
           u'再現= catalog_scripts/estimate_washpan_v6_6.py/'
           u'天面(=設置面)から洗濯水栓まで115cm=ユーザー実測確定 → 水栓は床から131.8cm/'
           u'天面は外周リブ(幅2cm)が立ち上がり内側は一段下がったデッキ・四隅に脚受けの凹み・'
           u'東寄りやや手前(西端から東へ約45cm・北壁から約39cm)に排水トラップ/'
           u'右=E側ブロック 写真41・42)","est":false,'
           u'"rect":[533.0,18.0,64,64],"h":16.8,"shortLabel":"洗濯機パン",'
           u'"id":"F-28","name":"洗濯機パン","short":"洗濯機パン","minor":false}')

NEW_F29 = (u'{"type":"faucet","room":"washroom","label":"洗濯水栓(壁出し単水栓・N壁のパン上方 '
           u'東寄り x583..591/★v6.6 パンのかさ上げに追従: 下端=パン天面16.8+115=床から131.8cm '
           u'(115cm はユーザー実測確定。旧 h≈121 は パン縁高6cm 前提だったので是正)/'
           u'写真42の逆投影でも 水栓最下端=床から133.2cm(k=0.974) / 天面から116.2cm と '
           u'ユーザー実測115cm に ±1.2cm で一致 (相互検証OK)/'
           u'コンセントNo.13の東隣・写真41で栓は パン右寄り上方 写真41・42)","est":true,'
           u'"rect":[583.0,18.0,8,6],"h":139.8,"bottomH":131.8,"showDim":false,'
           u'"id":"F-29","name":"洗濯水栓","short":"洗濯水栓","minor":true}')

NEW_SHELF = (u'{"type":"wall_shelf","room":"washroom","label":"洗面脱衣室 上部の棚板'
             u'(白・ブラケット2本で支持 ★v6.6 新規: ユーザー確定「その上の棚も反映して」'
             u'/写真41・42 に写る 洗面台の東端(x514)から東壁(x597)まで通しの白い棚板/'
             u'下端=床から189cm・板厚2cm・奥行30cm=est。根拠は写真42の逆投影で'
             u'ブラケット壁プレート上端(=棚板下端)が 補正前 左195.9/右194.6 → '
             u'スケール補正 k=0.974 で 190.9/189.6、k=0.963 で 188.7/187.5 → 中央値189/'
             u'この下端が 洗濯機のふた開放時 (BW-DX100J = パン天面+146.6cm) の頭上上限になる)",'
             u'"est":true,"rect":[514.0,18.0,83,30],"h":191.0,"bottomH":189.0,'
             u'"id":"F-48","name":"洗面脱衣室 上部の棚板","short":"棚板","minor":false}')

NEW_PIPE = (u'{"type":"hanger_pipe","room":"washroom","label":"物干し用ハンガーパイプ'
            u'(クロム丸パイプ ★v6.6 新規: 棚板 F-48 の下面にブラケットで吊られる/'
            u'写真41・42 で 棚板の下・前寄りを東西に通る/中心=床から180cm'
            u'(棚板下端189の約9cm下 = 写真42でブラケット壁プレートの上から約30%の位置)・'
            u'壁から約20cm・φ2.6 はいずれも写真からの推定=est)","est":true,'
            u'"rect":[514.0,37.0,83,2.6],"h":181.3,"bottomH":178.7,'
            u'"id":"F-49","name":"物干しハンガーパイプ","short":"ハンガーパイプ","minor":true}')


def room_data_patches(text):
    u"""ROOM_DATA (fixtures のみ) の (名前, マーカー, old, new) を組み立てる。
    old は必ずファイル内の実テキストから切り出すので、v6.5 素の状態からでも
    v6.6 の途中適用状態からでも 同じ最終形に収束する (転記ミスも起きない)。"""
    f28 = fixture_obj(text, 'F-28')
    f29 = fixture_obj(text, 'F-29')
    if u'"id":"F-48"' in text:                 # 既に追加済み → オブジェクト単位で最終形へ置換
        shelf_old, shelf_new = fixture_obj(text, 'F-48'), NEW_SHELF
        pipe_old, pipe_new = fixture_obj(text, 'F-49'), NEW_PIPE
    else:                                      # 未追加 → F-47 の直後へ追記
        f47 = fixture_obj(text, 'F-47')
        shelf_old = f47 + u']'
        assert text.count(shelf_old) == 1, 'fixtures 配列の末尾アンカーが一意でない'
        shelf_new = f47 + u',' + NEW_SHELF + u',' + NEW_PIPE + u']'
        pipe_old, pipe_new = u'', u''          # 上でまとめて入るので単独パッチは空 (marker で skip)
    return [
        (u'P1 ROOM_DATA F-28 洗濯機パン → かさ上げ 全高16.8cm', u'"h":16.8,"shortLabel"', f28, NEW_F28),
        (u'P2 ROOM_DATA F-29 洗濯水栓 → 床から131.8〜139.8 (天面+115)', u'"bottomH":131.8', f29, NEW_F29),
        (u'P3 ROOM_DATA F-48 棚板 (下端189)', u'"h":191.0,"bottomH":189.0', shelf_old, shelf_new),
        (u'P3b ROOM_DATA F-49 ハンガーパイプ (中心180)', u'"h":181.3,"bottomH":178.7', pipe_old, pipe_new),
    ]


# ═══════════════════ JS パッチ ═══════════════════

FIX_STYLE_OLD = u'''  washer_pan:   { color: 0xf4f4f2, h: 6 },     // 洗濯機パン (外枠64x64・縁高6 + 内寸60x60 凹み表現)
  faucet:       { color: 0xc9ced3, h: 127 }    // 洗濯水栓 (壁出し単水栓・パン上面+115cm)
};'''

FIX_STYLE_NEW = u'''  // ★v6.6 洗濯機パンは かさ上げ(高床)タイプ 全高16.8cm / 水栓は パン天面+115cm = 床から131.8cm
  washer_pan:   { color: 0xf1efea, h: 16.8 },  // 洗濯機パン (外寸64x64・全高16.8 = 天面が洗濯機の設置面 / 内寸60x60)
  faucet:       { color: 0xc9ced3, h: 139.8 }, // 洗濯水栓 (壁出し単水栓・下端=パン天面+115)
  // ★v6.6 洗面脱衣室 上部の棚板 + ハンガーパイプ (写真41・42)
  wall_shelf:   { color: 0xf7f7f5, h: 191 },   // 白い棚板 (ブラケット2本で支持)
  hanger_pipe:  { color: 0xc7ccd1, h: 181.3 }  // クロムのハンガーパイプ (棚板の下に吊る)
};'''

PAN_BUILD_OLD = u'''  if (f.type === 'washer_pan') {
    // ★v2.7 洗濯機パン (ROOM_DATA v2.5): 底板 + 4辺の縁 (縁幅2・縁高6) で内寸60x60 の凹みを表現。
    //        衝突ブロックしない (洗濯機サイズの箱をパンに重ねて置ける)。ドロップ時に内寸適合をトースト判定
    const rim = 2;
    const base = new THREE.Mesh(new THREE.BoxGeometry(dx, 1.2, dy), mat(color));
    base.position.set(cx, 0.6, cz);
    base.userData.kind = 'fixture'; base.userData.info = f.label;
    g.add(base); pickables.push(base);
    [[cx, y + rim / 2, dx, rim], [cx, y + dy - rim / 2, dx, rim],
     [x + rim / 2, cz, rim, dy - 2 * rim], [x + dx - rim / 2, cz, rim, dy - 2 * rim]
    ].forEach(function (rb) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(rb[2], topH, rb[3]), mat(color));
      m.position.set(rb[0], topH / 2, rb[1]);
      m.userData.kind = 'fixture'; m.userData.info = f.label;
      g.add(m); pickables.push(m);
    });
    return;
  }'''

PAN_BUILD_NEW = u'''  if (f.type === 'washer_pan') {
    // ★v6.6 かさ上げ(高床)タイプの防水パン — 写真41・42 実物準拠。
    //   ・全高 topH (=16.8cm) の天面が 洗濯機の設置面。ユーザー実測「天面→蛇口115cm」の基準面。
    //   ・天面は外周リブが立ち上がり、内側は一段下がったデッキ (basin)。四隅は脚受けの凹み。
    //   ・右奥 (北東寄り) に排水トラップ (丸い目皿 + 白いトラップ本体 + 横向きの排水口)。
    //   衝突ブロックはしない (洗濯機をパンに載せられる)。適合は checkWasherPanFit がトースト判定。
    const info = { kind: 'fixture', info: f.label };
    const RIB = 4.0;                                   // 外周リブの幅
    const DECK = Math.max(topH - 3.2, 1.0);            // 内側デッキ (basin) の高さ
    const SKIRT = color, DECKC = 0xf7f6f2, CUP = 0xe6e3dd, TRAPC = 0xe8e6e0, GRATEC = 0xb4b8bd;
    const body = addBox(g, dx, DECK, dy, cx, DECK / 2, cz, SKIRT, info);              // スカート本体 (床〜デッキ)
    pickables.push(body);
    addBox(g, dx - 2 * RIB + 0.6, 0.5, dy - 2 * RIB + 0.6, cx, DECK + 0.25, cz, DECKC, info);  // デッキ面
    [[cx, y + RIB / 2, dx, RIB], [cx, y + dy - RIB / 2, dx, RIB],
     [x + RIB / 2, cz, RIB, dy - 2 * RIB], [x + dx - RIB / 2, cz, RIB, dy - 2 * RIB]
    ].forEach(function (rb) {                                                         // 天面の外周リブ (4辺)
      pickables.push(addBox(g, rb[2], topH - DECK, rb[3], rb[0], (topH + DECK) / 2, rb[1], SKIRT, info));
    });
    const PW = 11, PT = 2.0, PH = 1.3;                 // 脚受け: 一回り高い枠 → 中央がへこんで見える
    [[x + RIB + PW / 2 + 1, y + RIB + PW / 2 + 1], [x + dx - RIB - PW / 2 - 1, y + RIB + PW / 2 + 1],
     [x + RIB + PW / 2 + 1, y + dy - RIB - PW / 2 - 1], [x + dx - RIB - PW / 2 - 1, y + dy - RIB - PW / 2 - 1]
    ].forEach(function (p) {
      const yy = DECK + 0.5 + PH / 2;
      addBox(g, PW, PH, PT, p[0], yy, p[1] - PW / 2 + PT / 2, CUP, info);
      addBox(g, PW, PH, PT, p[0], yy, p[1] + PW / 2 - PT / 2, CUP, info);
      addBox(g, PT, PH, PW - 2 * PT, p[0] - PW / 2 + PT / 2, yy, p[1], CUP, info);
      addBox(g, PT, PH, PW - 2 * PT, p[0] + PW / 2 - PT / 2, yy, p[1], CUP, info);
    });
    const tx = x + dx * 0.80, tz = y + dy * 0.28;      // 排水トラップ (右奥 = 東寄り・壁側)
    const grate = new THREE.Mesh(new THREE.CylinderGeometry(6.2, 6.2, 1.0, 20), mat(GRATEC));
    grate.position.set(tx, DECK + 0.9, tz);
    Object.assign(grate.userData, info); g.add(grate); pickables.push(grate);
    const tb = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 4.0, 5.4, 16), mat(TRAPC));
    tb.position.set(tx + 1.4, DECK + 3.4, tz);
    Object.assign(tb.userData, info); g.add(tb); pickables.push(tb);
    const sp = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 5.6, 14), mat(TRAPC));
    sp.rotation.z = Math.PI / 2;
    sp.position.set(tx + 4.6, DECK + 4.6, tz);
    Object.assign(sp.userData, info); g.add(sp);
    return;
  }
  if (f.type === 'wall_shelf') {
    // ★v6.6 洗面脱衣室 上部の白い棚板 (写真41・42): 棚板 + L字ブラケット2本 (壁プレート/水平アーム/斜め筋交い)
    const info = { kind: 'fixture', info: f.label };
    const MET = 0xfafaf8;
    const T = Math.max(topH - botH, 1.2);
    pickables.push(addBox(g, dx, T, dy, cx, botH + T / 2, cz, color, info));           // 棚板
    const BH = 26, inset = Math.min(14, Math.max(dx * 0.12, 6));
    [x + inset, x + dx - inset].forEach(function (bx0) {
      addBox(g, 4.6, BH, 1.6, bx0, botH - BH / 2, y + 0.8, MET, info);                 // 壁付けプレート
      addBox(g, 3.2, 2.0, dy - 4, bx0, botH - 1.0, y + 2 + (dy - 4) / 2, MET, info);    // 水平アーム
      const rise = BH - 5, run = dy - 8;                                                // 斜め筋交い
      const br = addBox(g, 2.0, 1.6, Math.sqrt(rise * rise + run * run),
                        bx0, botH - 3 - rise / 2, y + 3 + run / 2, MET, info);
      br.rotation.x = -Math.atan2(rise, run);
    });
    return;
  }
  if (f.type === 'hanger_pipe') {
    // ★v6.6 棚板の下に吊られたクロムのハンガーパイプ (物干し竿受け)
    const info = { kind: 'fixture', info: f.label };
    const r = Math.max(Math.min(dy, topH - botH) / 2, 0.8), yc = (botH + topH) / 2;
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(r, r, dx, 16), mat(color));
    pipe.rotation.z = Math.PI / 2;
    pipe.position.set(cx, yc, cz);
    Object.assign(pipe.userData, info); g.add(pipe); pickables.push(pipe);
    [x + r + 0.5, x + dx - r - 0.5].forEach(function (hx) {                             // 両端の吊り金具
      addBox(g, 1.6, 7, 1.6, hx, yc + 3.5, cz, 0xfafaf8, info);
    });
    return;
  }'''

SOLID_OLD = (u"                          pocket_panel: 1 };      // ★v2.6 6.2引き戸 "
             u"戸袋の固定袖 (3D描画はドア一式側)")
SOLID_NEW = (u"                          pocket_panel: 1,        // ★v2.6 6.2引き戸 "
             u"戸袋の固定袖 (3D描画はドア一式側)\n"
             u"                          wall_shelf: 1 };        // ★v6.6 上部の棚板 (bottomH189〜191 の高さ帯だけブロック)")

PANFIT_OLD = u'''// ★v2.7 洗濯機パン 置けるか判定 (ROOM_DATA v2.5 ユーザー実測: 内寸60x60 / パン上面→洗濯水栓115cm)。
//        パンと重なる位置に家具をドロップしたら、設置面が内寸60x60に収まるか + 水栓高さに収まるかをトースト
const WASHER_PAN = { outer: [538, 18, 64, 64], inner: [540, 20, 60, 60], faucetClr: 115 };
function checkWasherPanFit(itemId) {
  const it = workItems[itemId]; if (!it) return;
  const a = itemAabb(it);
  const o = WASHER_PAN.outer;
  if (a.maxX <= o[0] || a.minX >= o[0] + o[2] || a.maxZ <= o[1] || a.minZ >= o[1] + o[3]) return;
  // ★v2.8 baseW/baseD (設置面=脚間寸法。カタログ由来) があれば設置面AABBで判定 —
  //        洗濯機の外形 (ホース・手掛け込み) はパン縁に被さってよく、脚がパン内寸に収まれば設置可 (BW-DX100J 公式寸法図)
  const fx = a.maxX - a.minX, fz = a.maxZ - a.minZ;
  let bx = fx, bz = fz, byBase = false;
  const bW = Number(it.baseW) || 0, bD = Number(it.baseD) || 0;
  if (bW > 0 && bD > 0) {
    const iw = Number(it.w) || 0, id_ = Number(it.d) || 0;
    const xIsW = Math.abs(fx - iw) <= Math.abs(fx - id_);   // 回転で w/d どちらが x 軸かを判定
    bx = xIsW ? bW : bD; bz = xIsW ? bD : bW; byBase = true;
  }
  const cx = (a.minX + a.maxX) / 2, cz = (a.minZ + a.maxZ) / 2;
  const minX = cx - bx / 2, maxX = cx + bx / 2, minZ = cz - bz / 2, maxZ = cz + bz / 2;
  const n = WASHER_PAN.inner, EPS = 0.3;
  const w = Math.round(bx * 10) / 10, dd = Math.round(bz * 10) / 10;
  const fits = minX >= n[0] - EPS && maxX <= n[0] + n[2] + EPS &&
               minZ >= n[1] - EPS && maxZ <= n[1] + n[3] + EPS;
  const h = Number(it.h) || 0;
  const lbl = byBase ? '設置面(脚間) ' : '設置面 ';
  toast(fits
    ? '\U0001f9fa 洗濯機パン: ' + lbl + w + '×' + dd + ' は内寸60×60に収まります' +
      (h > WASHER_PAN.faucetClr ? ' ⚠高さ' + h + 'cmは洗濯水栓 (パン上面+115cm) に干渉のおそれ'
                                : ' (高さ' + h + 'cm・水栓まで115cm OK)')
    : '\U0001f9fa 洗濯機パン: ' + lbl + w + '×' + dd + ' は内寸60×60からはみ出します');
}'''

PANFIT_NEW = u'''// ═══ ★v6.6 洗濯機パン (かさ上げタイプ) の設置面スナップ + 収まり判定 ═══
//   ・パンの外寸・全高は ROOM_DATA の F-28 を正とする (v6.6: 全高 6 → 16.8cm)。内寸60x60 はユーザー実測確定。
//   ・洗濯機の設置面は「床」ではなく「パン天面」。パンの上へドロップすると y=天面 に上がる。
//   ・洗濯水栓 (F-29) の下端 = パン天面 +115cm (ユーザー実測)。本体上端がここを超えたら干渉。
//   ・ふた開放時 (カタログ specNote の「ふた開け時高さ NNcm」) は 上部の棚板 (F-48) 下端と突き合わせる。
function fixByIdRD(id) {
  const a = R.fixtures || [];
  for (let i = 0; i < a.length; i++) if (a[i].id === id) return a[i];
  return null;
}
const WASHER_PAN = (function () {
  const f = fixByIdRD('F-28'), sh = fixByIdRD('F-48'), fa = fixByIdRD('F-29');
  const o = (f && f.rect) ? [f.rect[0], f.rect[1], f.rect[2], f.rect[3]] : [533, 18, 64, 64];
  const top = (f && f.h) ? Number(f.h) : 16.8;         // パン天面 = 洗濯機の設置面 (床から)
  const IW = 60, ID = 60;                              // 内寸 (ユーザー実測確定)
  return {
    room: (f && f.room) || 'washroom', outer: o, top: top,
    inner: [o[0] + (o[2] - IW) / 2, o[1] + (o[3] - ID) / 2, IW, ID],
    faucetClr: 115,                                    // 天面 → 洗濯水栓 (ユーザー実測確定)
    faucetH: (fa && fa.bottomH != null) ? Number(fa.bottomH) : top + 115,   // 床から
    shelfH: (sh && sh.bottomH != null) ? Number(sh.bottomH) : null          // 棚板 下端 (床から)
  };
})();
// 設置面 (脚間) の AABB。baseW/baseD (カタログ由来) があればそれを使う —
// 洗濯機の外形 (ホース・手掛け込み) はパン縁に被さってよく、脚がパン内寸に収まれば設置可 (BW-DX100J 公式寸法図)
function washerPanBase(it) {
  const a = itemAabb(it);
  const fx = a.maxX - a.minX, fz = a.maxZ - a.minZ;
  let bx = fx, bz = fz, byBase = false;
  const bW = Number(it.baseW) || 0, bD = Number(it.baseD) || 0;
  if (bW > 0 && bD > 0) {
    const iw = Number(it.w) || 0, id_ = Number(it.d) || 0;
    const xIsW = Math.abs(fx - iw) <= Math.abs(fx - id_);   // 回転で w/d どちらが x 軸かを判定
    bx = xIsW ? bW : bD; bz = xIsW ? bD : bW; byBase = true;
  }
  const cx = (a.minX + a.maxX) / 2, cz = (a.minZ + a.maxZ) / 2;
  return { a: a, bx: bx, bz: bz, byBase: byBase,
           minX: cx - bx / 2, maxX: cx + bx / 2, minZ: cz - bz / 2, maxZ: cz + bz / 2 };
}
function washerPanOverlaps(it) {
  const a = itemAabb(it), o = WASHER_PAN.outer;
  return !(a.maxX <= o[0] || a.minX >= o[0] + o[2] || a.maxZ <= o[1] || a.minZ >= o[1] + o[3]);
}
// パン天面に載せられるか (= 設置面がパン外寸の中に収まっているか)。載るなら天面高さを返す
function washerPanTopFor(it) {
  if (!it || !washerPanOverlaps(it)) return null;
  const b = washerPanBase(it), o = WASHER_PAN.outer, E = 1.0;
  const on = b.minX >= o[0] - E && b.maxX <= o[0] + o[2] + E &&
             b.minZ >= o[1] - E && b.maxZ <= o[1] + o[3] + E;
  return on ? WASHER_PAN.top : null;
}
function washerLidOpenH(it) {
  const m = /ふた開け[^0-9]{0,8}([0-9]+(?:\\.[0-9]+)?)\\s*cm/.exec(specTextOf(it));
  return m ? Number(m[1]) : null;
}
// 収まり判定の本体 (トーストと検証フックで共用)
function washerPanReport(it) {
  if (!it || !washerPanOverlaps(it)) return null;
  const R1 = function (v) { return Math.round(v * 10) / 10; };
  const b = washerPanBase(it), n = WASHER_PAN.inner, EPS = 0.3;
  const w = R1(b.bx), dd = R1(b.bz);
  const fits = b.minX >= n[0] - EPS && b.maxX <= n[0] + n[2] + EPS &&
               b.minZ >= n[1] - EPS && b.maxZ <= n[1] + n[3] + EPS;
  const lbl = b.byBase ? '設置面(脚間) ' : '設置面 ';
  const top = WASHER_PAN.top, h = Number(it.h) || 0, faucetH = WASHER_PAN.faucetH;
  const rep = { fits: fits, baseW: w, baseD: dd, byBase: b.byBase, panTop: top,
                itemH: h, itemTop: R1(top + h), faucetH: R1(faucetH),
                faucetGap: R1(faucetH - (top + h)), faucetOk: (top + h) <= faucetH + 0.05,
                lidOpen: null, lidTop: null, shelfH: WASHER_PAN.shelfH, lidGap: null, lidOk: null };
  if (!fits) {
    rep.msg = '🧺 洗濯機パン: ' + lbl + w + '×' + dd + ' は内寸60×60からはみ出します';
    return rep;
  }
  const parts = ['🧺 パン天面' + R1(top) + 'cmに設置OK (' + lbl + w + '×' + dd + '≦内寸60×60)'];
  parts.push(rep.faucetOk
    ? '本体上端' + rep.itemTop + ' / 水栓' + rep.faucetH + '(天面+115)まで' + rep.faucetGap + 'cm ✅'
    : '⚠本体上端' + rep.itemTop + ' が 水栓' + rep.faucetH + '(天面+115)に' + R1(-rep.faucetGap) + 'cm干渉');
  const lid = washerLidOpenH(it);
  if (lid !== null) {
    rep.lidOpen = lid; rep.lidTop = R1(top + lid);
    if (WASHER_PAN.shelfH !== null) {
      rep.lidGap = R1(WASHER_PAN.shelfH - (top + lid));
      rep.lidOk = (top + lid) <= WASHER_PAN.shelfH + 0.05;
      parts.push(rep.lidOk
        ? 'ふた開放' + rep.lidTop + ' / 棚板下端' + R1(WASHER_PAN.shelfH) + 'まで' + rep.lidGap + 'cm ✅'
        : '⚠ふた開放' + rep.lidTop + ' が 棚板下端' + R1(WASHER_PAN.shelfH) + 'に' + R1(-rep.lidGap) + 'cm干渉');
    }
  }
  rep.msg = parts.join(' / ');
  return rep;
}
function checkWasherPanFit(itemId) {
  const it = workItems[itemId]; if (!it) return;
  const rep = washerPanReport(it);
  if (rep) toast(rep.msg);
}'''

BEGIN_DRAG_OLD = u'''  if (!TOP_STACK_TYPES[itemTypeOf(it)] && !isMattressItem(it) && (Number(it.y) || 0) !== 0) {
    it.y = 0;
    const gm = furnMeshes[itemId];
    if (gm) syncItemMesh(gm, it);
  }'''
BEGIN_DRAG_NEW = u'''  const panY0 = washerPanTopFor(it);   // ★v6.6 洗濯機パンに載っている物は「浮いている」ではないので落とさない
  const onPan0 = panY0 !== null && Math.abs((Number(it.y) || 0) - panY0) < 0.6;
  if (!TOP_STACK_TYPES[itemTypeOf(it)] && !isMattressItem(it) && (Number(it.y) || 0) !== 0 && !onPan0) {
    it.y = 0;
    const gm = furnMeshes[itemId];
    if (gm) syncItemMesh(gm, it);
  }'''

AUTOY_OLD = u'''           autoY: isMountedItem(it) || y0 === 0 ||   // ★v4.1 アームから外したら床/天面へ落とす
                  (sup0 !== null && Math.abs(y0 - sup0) < 0.6) ||
                  (bed0 !== null && Math.abs(y0 - bedFloorH(bed0)) < 0.6) };'''
AUTOY_NEW = u'''           autoY: isMountedItem(it) || y0 === 0 ||   // ★v4.1 アームから外したら床/天面へ落とす
                  (sup0 !== null && Math.abs(y0 - sup0) < 0.6) ||
                  onPan0 ||                            // ★v6.6 パン天面に載っている状態も autoY 対象
                  (bed0 !== null && Math.abs(y0 - bedFloorH(bed0)) < 0.6) };'''

RESOLVE_OLD = u'''    const sup = supportTopFor(drag.itemId, it);
    if (sup !== null && sup + (Number(it.h) || 1) <= CH + 0.01) {
      it.y = sup;                                // 天面へ載せる (ライブプレビュー)
    } else if (sup === null && drag.autoY) {
      it.y = 0;                                  // 支えから離れたら床へ (ベッドから外れた時も床へ)
    }'''
RESOLVE_NEW = u'''    const sup = supportTopFor(drag.itemId, it);
    const panTop = washerPanTopFor(it);          // ★v6.6 洗濯機パンの天面 (かさ上げ16.8cm) が設置面
    if (sup !== null && sup + (Number(it.h) || 1) <= CH + 0.01) {
      it.y = sup;                                // 天面へ載せる (ライブプレビュー)
    } else if (panTop !== null && panTop + (Number(it.h) || 1) <= CH + 0.01) {
      it.y = panTop;                             // ★v6.6 パン天面へ載せる (床ではない)
    } else if (sup === null && drag.autoY) {
      it.y = 0;                                  // 支えから離れたら床へ (ベッドから外れた時も床へ)
    }'''

KEYMOVE_OLD = u'''    if (isMattressItem(it)) {                                               // ★v2.0 キー移動でもベッド床板面/床へ追従
      const kb = bedUnder(selectedItemId, it);
      if (kb) it.y = bedFloorH(kb);
      else if (supportTopFor(selectedItemId, it) === null) it.y = 0;
    }'''
KEYMOVE_NEW = u'''    if (isMattressItem(it)) {                                               // ★v2.0 キー移動でもベッド床板面/床へ追従
      const kb = bedUnder(selectedItemId, it);
      if (kb) it.y = bedFloorH(kb);
      else if (supportTopFor(selectedItemId, it) === null) it.y = 0;
    }
    const kPan = washerPanTopFor(it);                                       // ★v6.6 キー移動でも パン天面 ⇔ 床 を追従
    if (kPan !== null) it.y = kPan;
    else if (Math.abs((Number(it.y) || 0) - WASHER_PAN.top) < 0.6 &&
             supportTopFor(selectedItemId, it) === null) it.y = 0;'''

TIPINNER_OLD = u'''  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {
    return '内寸: ' + tipN(WASHER_PAN.inner[2]) + ' × ' + tipN(WASHER_PAN.inner[3]) +
           'cm (パン上面→洗濯水栓 ' + tipN(WASHER_PAN.faucetClr) + 'cm)';
  }
  return null;'''
TIPINNER_NEW = u'''  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {
    // ★v6.6 かさ上げタイプ: 天面 (=洗濯機の設置面) の床からの高さと、天面基準のクリアランスを出す
    return '内寸: ' + tipN(WASHER_PAN.inner[2]) + ' × ' + tipN(WASHER_PAN.inner[3]) +
           'cm / 天面(設置面) 床から ' + tipN(WASHER_PAN.top) + 'cm' +
           ' / 天面→洗濯水栓 ' + tipN(WASHER_PAN.faucetClr) + 'cm (床から ' + tipN(WASHER_PAN.faucetH) + 'cm)' +
           (WASHER_PAN.shelfH === null ? '' : ' / 天面→棚板下端 ' + tipN(WASHER_PAN.shelfH - WASHER_PAN.top) + 'cm');
  }
  return null;'''

DEBUG_OLD = (u"      panFit: function (id) { checkWasherPanFit(id); return document.getElementById('vpHint').textContent; },"
             u"   // ★v2.7 検証用: 洗濯機パン適合トースト")
DEBUG_NEW = (u"      panFit: function (id) { checkWasherPanFit(id); return document.getElementById('vpHint').textContent; },"
             u"   // ★v2.7 検証用: 洗濯機パン適合トースト\n"
             u"      // ★v6.6 検証用: 洗濯機パンの収まり判定 (トーストと同じ計算の生データ) と パン/棚の諸元\n"
             u"      panSpec: function () { return JSON.parse(JSON.stringify(WASHER_PAN)); },\n"
             u"      panReport: function (id) { const it = workItems[id]; return it ? washerPanReport(it) : null; },")

CSS_OLD = (u"  padding: 4px 12px; border-radius: 14px; border: 1px solid var(--border); white-space: nowrap;\n"
           u"  pointer-events: none; z-index: 40; max-width: 94%; overflow: hidden; text-overflow: ellipsis;")
CSS_NEW = (u"  padding: 4px 12px; border-radius: 14px; border: 1px solid var(--border);\n"
           u"  /* ★v6.6 収まり判定は 3項目 (内寸/水栓/ふた開放) 出るので 1行固定をやめて最大3行まで折り返す */\n"
           u"  white-space: normal; text-align: center; line-height: 1.45; max-height: 4.6em;\n"
           u"  pointer-events: none; z-index: 40; max-width: 94%; overflow: hidden; text-overflow: ellipsis;")


JS_PATCHES = [
    (u'P4 FIX_STYLE: washer_pan/faucet 更新 + wall_shelf/hanger_pipe 追加', u'wall_shelf:   { color', FIX_STYLE_OLD, FIX_STYLE_NEW),
    (u'P5 buildFixture: パン実物準拠 + 棚板 + ハンガーパイプ', u"f.type === 'wall_shelf'", PAN_BUILD_OLD, PAN_BUILD_NEW),
    (u'P6 SOLID_FIX_TYPES に wall_shelf を追加', u'wall_shelf: 1 };', SOLID_OLD, SOLID_NEW),
    (u'P7 WASHER_PAN/収まり判定を ROOM_DATA 由来 + 天面基準に刷新', u'function washerPanReport', PANFIT_OLD, PANFIT_NEW),
    (u'P8 beginDrag: パンに載っている物を掴んでも床へ落とさない', u'const panY0 = washerPanTopFor(it);', BEGIN_DRAG_OLD, BEGIN_DRAG_NEW),
    (u'P9 beginDrag autoY に パン天面 を追加', u'onPan0 ||', AUTOY_OLD, AUTOY_NEW),
    (u'P10 resolveDragPos: パン天面へ y スナップ', u'const panTop = washerPanTopFor(it);', RESOLVE_OLD, RESOLVE_NEW),
    (u'P11 キー移動でも パン天面 ⇔ 床 を追従', u'const kPan = washerPanTopFor(it);', KEYMOVE_OLD, KEYMOVE_NEW),
    (u'P12 ツールチップ: パン天面/水栓/棚板クリアランス', u'天面(設置面) 床から', TIPINNER_OLD, TIPINNER_NEW),
    (u'P13 検証フック panSpec / panReport', u'panReport: function (id)', DEBUG_OLD, DEBUG_NEW),
    (u'P14 #vpHint を最大3行の折り返しに (判定3項目が切れないように)', u'★v6.6 収まり判定は 3項目', CSS_OLD, CSS_NEW),
    # ── 写真との並列比較 (1周目) で見つかった 2 点の是正 ──
    (u'P15a 外周リブ幅 4.0 → 2.0 (内寸60x60 を潰さない実物の縁厚)',
     u'const RIB = 2.0;',
     u'    const RIB = 4.0;                                   // 外周リブの幅',
     u'    const RIB = 2.0;                                   // 外周リブの幅 (★v6.6-a 外寸64 - 内寸60 = 片側2cm。'
     u'4.0 だと内寸60x60 を潰してしまうので実物の縁厚に是正)'),
    (u'P15b 排水トラップ位置を写真42の逆投影値へ (東70%・南61%)',
     u"const tx = x + dx * 0.70, tz = y + dy * 0.60;",
     u"    const tx = x + dx * 0.80, tz = y + dy * 0.28;      // 排水トラップ (右奥 = 東寄り・壁側)",
     u"    // ★v6.6-a 排水トラップ位置: 写真42 の天面ホモグラフィで逆投影 → パン西端から東へ45cm(=70%)・"
     u"北壁から南へ39cm(=61%)\n"
     u"    const tx = x + dx * 0.70, tz = y + dy * 0.60;"),
    (u'P15c buildFixture コメントのトラップ位置表記を是正',
     u'//   ・排水トラップ (丸い目皿',
     u'    //   ・右奥 (北東寄り) に排水トラップ (丸い目皿 + 白いトラップ本体 + 横向きの排水口)。',
     u'    //   ・排水トラップ (丸い目皿 + 白いトラップ本体 + 横向きの排水口) は 東寄りやや手前。'),
    # ── 2周目: コンセントプレートの天地を輝度プロファイルで測り直し (影の帯 5px を除外) →
    #    スケール補正 k = 0.956 → 0.974 に修正。ユーザー実測115cm 基準の k=0.963 と平均して
    #    パン全高 16.5→16.8 / 棚板下端 187→189 / パイプ中心 178→180 へ。
    #    (v6.5 素の状態から一発で流した場合は 上の P4〜P10 が最終値を入れるので ここは全て skip される)
    (u'P18a FIX_STYLE を最終実測値へ (16.8 / 139.8 / 191 / 181.3)',
     u'washer_pan:   { color: 0xf1efea, h: 16.8 },',
     u'''  // ★v6.6 洗濯機パンは かさ上げ(高床)タイプ 全高16.5cm / 水栓は パン天面+115cm = 床から131.5cm
  washer_pan:   { color: 0xf1efea, h: 16.5 },  // 洗濯機パン (外寸64x64・全高16.5 = 天面が洗濯機の設置面 / 内寸60x60)
  faucet:       { color: 0xc9ced3, h: 139.5 }, // 洗濯水栓 (壁出し単水栓・下端=パン天面+115)
  // ★v6.6 洗面脱衣室 上部の棚板 + ハンガーパイプ (写真41・42)
  wall_shelf:   { color: 0xf7f7f5, h: 189 },   // 白い棚板 (ブラケット2本で支持)
  hanger_pipe:  { color: 0xc7ccd1, h: 179.3 }  // クロムのハンガーパイプ (棚板の下に吊る)''',
     FIX_STYLE_NEW[:-3].rstrip('\n')),
    (u'P18b buildFixture コメントの全高を 16.8 へ',
     u'//   ・全高 topH (=16.8cm) の天面が',
     u'    //   ・全高 topH (=16.5cm) の天面が 洗濯機の設置面。ユーザー実測「天面→蛇口115cm」の基準面。',
     u'    //   ・全高 topH (=16.8cm) の天面が 洗濯機の設置面。ユーザー実測「天面→蛇口115cm」の基準面。'),
    (u'P18c SOLID_FIX_TYPES コメントの高さ帯を 189〜191 へ',
     u'(bottomH189〜191 の高さ帯だけブロック)',
     u'// ★v6.6 上部の棚板 (bottomH187〜189 の高さ帯だけブロック)',
     u'// ★v6.6 上部の棚板 (bottomH189〜191 の高さ帯だけブロック)'),
    (u'P18d WASHER_PAN の説明コメントを 16.8 へ',
     u'(v6.6: 全高 6 → 16.8cm)',
     u'(v6.6: 全高 6 → 16.5cm)',
     u'(v6.6: 全高 6 → 16.8cm)'),
    (u'P18e WASHER_PAN のフォールバック値を 16.8 へ',
     u'Number(f.h) : 16.8;',
     u'  const top = (f && f.h) ? Number(f.h) : 16.5;         // パン天面 = 洗濯機の設置面 (床から)',
     u'  const top = (f && f.h) ? Number(f.h) : 16.8;         // パン天面 = 洗濯機の設置面 (床から)'),
    (u'P18f resolveDragPos コメントを 16.8 へ',
     u'洗濯機パンの天面 (かさ上げ16.8cm) が設置面',
     u'// ★v6.6 洗濯機パンの天面 (かさ上げ16.5cm) が設置面',
     u'// ★v6.6 洗濯機パンの天面 (かさ上げ16.8cm) が設置面'),
    (u'P16 F-28 ラベルのトラップ位置表記を実測値へ是正',
     u'東寄りやや手前(西端から東へ約45cm・北壁から約39cm)に排水トラップ',
     u'右奥(北東寄り)に排水トラップ',
     u'東寄りやや手前(西端から東へ約45cm・北壁から約39cm)に排水トラップ'),
]


def main():
    dry = '--dry-run' in sys.argv
    with io.open(TARGET, encoding='utf-8', newline='') as f:
        text = f.read()
    assert '\r\n' not in text, 'unexpected CRLF in room.html'

    before = data_line_hashes(text)
    applied, skipped, failed = [], [], []
    patches = room_data_patches(text) + JS_PATCHES

    for name, marker, old, new in patches:
        if marker in text:
            skipped.append(name)
            continue
        n = text.count(old)
        if n != 1:
            failed.append(u'%s : anchor matched %d times (expected 1)' % (name, n))
            continue
        text = text.replace(old, new, 1)
        applied.append(name)

    after = data_line_hashes(text)
    assert before[u'var CATALOG_SEED ='] == after[u'var CATALOG_SEED ='], (
        'CATALOG_SEED CHANGED!\n  before=%s\n  after =%s'
        % (before[u'var CATALOG_SEED ='], after[u'var CATALOG_SEED =']))

    print(u'CATALOG_SEED sha256 : %s (unchanged / assert OK)' % before[u'var CATALOG_SEED ='])
    print(u'ROOM_DATA sha256 before : %s' % before[u'var ROOM_DATA ='])
    print(u'ROOM_DATA sha256 after  : %s%s'
          % (after[u'var ROOM_DATA ='],
             u'  (unchanged)' if before[u'var ROOM_DATA ='] == after[u'var ROOM_DATA ='] else u'  (CHANGED: F-28/F-29 置換 + F-48/F-49 追加)'))
    print(u'')
    for n in applied:
        print(u'  [apply] %s' % n)
    for n in skipped:
        print(u'  [skip ] %s' % n)
    for n in failed:
        print(u'  [FAIL ] %s' % n)
    print(u'')
    print(u'適用 %d 件 / skip %d 件 / 失敗 %d 件' % (len(applied), len(skipped), len(failed)))

    if failed:
        print(u'\n!! 失敗があるので書き戻しません (並行編集でアンカーが変わった可能性)')
        return 1
    if dry:
        print(u'(dry-run: 書き込みなし)')
        return 0
    if applied:
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        print(u'→ %s を更新しました' % TARGET)
    else:
        print(u'→ 変更なし (全て適用済み)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

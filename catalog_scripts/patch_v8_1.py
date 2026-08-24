# -*- coding: utf-8 -*-
u"""v8.1: ニトリ 収納付きベッドフレーム シングル (アザン3 棚・コンセント・ライト付き 浅型 WW /
       商品コード 2050630) を追加。 あわせて **ベッドの3D描画を BED_MODELS のデータ駆動へ共通化** する。冪等。

━━ なぜ共通化するのか ━━
v8.0 まで type 'bed' の描画は 1本のコードの中に `/Aerus|宮棚/` `/Aerus/` の if が
直接埋まっていて、 機種が増えるたびに if を足す作りだった。 v7.5 で冷蔵庫を
FRIDGE_MODELS へデータ化したのと同じ理由 (1機種を直しても他機種へ伝わらない) で、
ベッドも **骨格の寸法・構成だけをデータで持ち、描画は 1本の共通コードに集約** する。
  → 新機種は BED_MODELS に 1エントリ足すだけ。
  → 既存 RASIK Aerus 3種は **メッシュ台帳 (snap_bed_mesh.py) が完全一致** することで
    「1メッシュも変わっていない」 ことを機械証明する。

━━ 汎用フィールドの拡張 (ベッド専用の欄を作らない) ━━
  ・itemDrawerSet に `face` ('front'|'left'|'right') と `hideOpen` / `handle` を追加
    → 「長辺 (側面) から引く引き出し」 が リガーレ・エトナと同じ仕組みで動く
  ・install に `openKind`('drawer') と `doorSide:'both'` を追加
    → 「引き出しの向き: 左右どちらの側面にも取り付け可 → 引く側へ 47cm 必要」 と出る
  ・item.drawerSide (left/right) を新設し、 buildKey と cleanItem に通す

━━ ROOM_DATA ━━ 一切変更しない (sha256 前後一致を assert)。 CATALOG_SEED v2.7 → v2.8 (34 → 35商品)。

実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_1.py
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), 'room.html')
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'
MARK = u'★v8.1 ベッドの構成レジストリ'


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def shapat(pat, s):
    m = re.search(pat, s, re.S)
    assert m, u'パターンが見つからない: %s' % pat[:40]
    return sha(m.group(1))


def rep(src, old, new, what):
    assert old in src, u'%s: 置換対象が見つからない' % what
    assert src.count(old) == 1, u'%s: 置換対象が %d 箇所ある' % (what, src.count(old))
    return src.replace(old, new, 1)


src = io.open(TARGET, encoding='utf-8', newline='').read()
assert '\r\n' not in src, 'unexpected CRLF in room.html'
rd_before = shapat(RD_PAT, src)
items_before = json.loads(re.search(CS_PAT, src, re.S).group(1))['items']

if MARK in src:
    print(u'適用0件 / skip 12件 (既に適用済み)')
    sys.exit(0)

applied = 0

# ═══════════════════════════════════════════════════════════════════════════
# (1) itemDrawerSet: 引き出す向き (face) / 開時に隠す閉状態パーツ (hideOpen) /
#     ハンドルの有無 (handle) に対応。 face 既定 'front' は従来と完全に同じ挙動。
# ═══════════════════════════════════════════════════════════════════════════
OLD_DS = u"""function itemDrawerSet(g, it, defs, ctx) {
  const iid = g.userData.itemId;
  if (!iid) return;
  const w = ctx.w, d = ctx.d, zF = d / 2;
  defs.forEach(function (def) {
    const bw = def.bw || (w - 8);                 // 引き出し幅 (ローカルx)
    const x0 = def.x0 || 0;                       // 中心x (リガーレ 下台左40cm/右60cm ユニットの中心)
    const yMid = def.y0 + def.rh / 2;
    const mkP = function (sx, sy, sz, px, py, pz, col) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(Math.max(sx, 0.5), Math.max(sy, 0.5), Math.max(sz, 0.5)),
        new THREE.MeshLambertMaterial({ color: col }));
      m.position.set(px, py, pz);
      g.add(m);
      return m;
    };
    // クリックプレート (前面フラッシュ・本体色)
    const plate = mkP(bw, Math.max(def.rh, 6), 1.0, x0, yMid, zF + 0.35, ctx.base);
    const boxes = [];
    if (def.kind === 'drawer') {
      boxes.push(mkP(bw - 3, def.rh - 4, def.depth, x0, yMid, zF + def.depth / 2, ctx.dark.clone().lerp(ctx.base, 0.4)));
      boxes.push(mkP(bw, def.rh - 1.5, 1.6, x0, yMid, zF + def.depth + 0.6, ctx.base));            // 前板
      boxes.push(mkP(bw * 0.3, 1.8, 1.3, x0, def.y0 + def.rh - 3.2, zF + def.depth + 1.4, ctx.silver)); // ハンドル
    } else {
      boxes.push(mkP(bw, 2.2, def.depth, x0, yMid, zF + def.depth / 2, ctx.lite));                  // スライド板
      boxes.push(mkP(bw, 1.4, 1.0, x0, yMid, zF + def.depth + 0.4, ctx.silver));                    // 前縁
    }
    boxes.forEach(function (m) { m.visible = false; m.userData.drawerBox = true; });
    plate.userData.drawerId = boxes[0].userData.drawerId = boxes[1].userData.drawerId = regDrawer({
      id: 'i_' + iid + '_' + def.key, label: def.label, boxes: boxes, depth: def.depth, originOff: 0.6,
      rayFn: function () {
        g.updateMatrixWorld();
        const dir = new THREE.Vector3(0, 0, 1).applyQuaternion(g.quaternion).normalize();
        return {
          origins: [g.localToWorld(new THREE.Vector3(x0, yMid, zF + 0.6)),
                    g.localToWorld(new THREE.Vector3(x0 - bw * 0.35, yMid, zF + 0.6)),
                    g.localToWorld(new THREE.Vector3(x0 + bw * 0.35, yMid, zF + 0.6))],
          dir: dir, exclude: g,
          labelPos: g.localToWorld(new THREE.Vector3(x0, def.y0 + def.rh + 12, zF + def.depth))
        };
      }
    });
  });
}"""

NEW_DS = u"""//   ★v8.1 def.face で **引き出す向き** を選べるようにした (既定 'front' = 従来と同じ)。
//     'front' … 家具の前面 (ローカル +z) へ引く … リガーレ / エトナ / キッチン本体
//     'left'  … 左側面 (ローカル −x) へ引く    ┐ 収納ベッドのように 長辺から引く引き出し。
//     'right' … 右側面 (ローカル +x) へ引く    ┘ 左右付け替え可の商品は item.drawerSide で切替
//     面の座標系を 「along = 面に沿う方向 / out = 面から外へ出る方向」 に統一し、
//     face ごとに (along, out) → ローカル (x, z) の写像 (LP/LV) だけを差し替える。
//   ★v8.1 def.hideOpen = 開いた時に隠す 閉状態のパーツ (収納ベッドの手掛け等)。
//     洗濯機のふたで既に使っている regDrawer の汎用フィールドをそのまま流用する。
//   ★v8.1 def.handle = 'none' で 銀のバーハンドルを描かない (ニトリ アザン3 は手掛けだけで
//     金物ハンドルが無い)。 既定は従来どおりハンドルあり。
function itemDrawerSet(g, it, defs, ctx) {
  const iid = g.userData.itemId;
  if (!iid) return;
  const w = ctx.w, d = ctx.d;
  defs.forEach(function (def) {
    const face = def.face || 'front';
    const front = (face === 'front');
    const sgn = (face === 'left') ? -1 : 1;       // 引き出す向き (front/right = +, left = −)
    const span = front ? w : d;                   // 面に沿う方向の全長
    const zF = (front ? d : w) / 2;               // 中心から面までの距離
    const bw = def.bw || (span - 8);              // 引き出し幅 (面に沿う方向)
    const x0 = def.x0 || 0;                       // 面に沿う方向の中心 (リガーレ 下台左40cm/右60cm ユニットの中心)
    const yMid = def.y0 + def.rh / 2;
    const LP = function (sAlong, sy, sOut) {      // サイズ (along, y, out) → (x, y, z)
      return front ? [sAlong, sy, sOut] : [sOut, sy, sAlong];
    };
    const LV = function (along, y, out) {         // 位置 (along, y, out) → ローカル座標
      return front ? new THREE.Vector3(along, y, zF + out)
                   : new THREE.Vector3(sgn * (zF + out), y, along);
    };
    const mkP = function (sAlong, sy, sOut, along, py, out, col) {
      const s = LP(sAlong, sy, sOut), p = LV(along, py, out);
      const m = new THREE.Mesh(new THREE.BoxGeometry(Math.max(s[0], 0.5), Math.max(s[1], 0.5), Math.max(s[2], 0.5)),
        new THREE.MeshLambertMaterial({ color: col }));
      m.position.set(p.x, p.y, p.z);
      g.add(m);
      return m;
    };
    // クリックプレート (面にフラッシュ・本体色)
    const plate = mkP(bw, Math.max(def.rh, 6), 1.0, x0, yMid, 0.35, ctx.base);
    const boxes = [];
    if (def.kind === 'drawer') {
      boxes.push(mkP(bw - 3, def.rh - 4, def.depth, x0, yMid, def.depth / 2, ctx.dark.clone().lerp(ctx.base, 0.4)));
      boxes.push(mkP(bw, def.rh - 1.5, 1.6, x0, yMid, def.depth + 0.6, ctx.base));            // 前板
      if (def.handle !== 'none') {
        boxes.push(mkP(bw * 0.3, 1.8, 1.3, x0, def.y0 + def.rh - 3.2, def.depth + 1.4, ctx.silver)); // ハンドル
      }
    } else {
      boxes.push(mkP(bw, 2.2, def.depth, x0, yMid, def.depth / 2, ctx.lite));                  // スライド板
      boxes.push(mkP(bw, 1.4, 1.0, x0, yMid, def.depth + 0.4, ctx.silver));                    // 前縁
    }
    boxes.forEach(function (m) { m.visible = false; m.userData.drawerBox = true; });
    plate.userData.drawerId = boxes[0].userData.drawerId = boxes[1].userData.drawerId = regDrawer({
      id: 'i_' + iid + '_' + def.key, label: def.label, boxes: boxes, depth: def.depth, originOff: 0.6,
      hideOpen: def.hideOpen || [],
      rayFn: function () {
        g.updateMatrixWorld();
        const dir = (front ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(sgn, 0, 0))
          .applyQuaternion(g.quaternion).normalize();
        return {
          origins: [g.localToWorld(LV(x0, yMid, 0.6)),
                    g.localToWorld(LV(x0 - bw * 0.35, yMid, 0.6)),
                    g.localToWorld(LV(x0 + bw * 0.35, yMid, 0.6))],
          dir: dir, exclude: g,
          labelPos: g.localToWorld(LV(x0, def.y0 + def.rh + 12, def.depth))
        };
      }
    });
  });
}"""
src = rep(src, OLD_DS, NEW_DS, u'(1) itemDrawerSet の face / hideOpen / handle 対応')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (2) BED_MODELS レジストリを新設 (FRIDGE_MODELS と同じ層)
# ═══════════════════════════════════════════════════════════════════════════
ANCHOR = u"""function fridgeModelOf(nm) {
  for (let i = 0; i < FRIDGE_MODELS.length; i++) {
    if (FRIDGE_MODELS[i].test.test(nm)) return FRIDGE_MODELS[i];
  }
  return null;
}"""
BED_REG = ANCHOR + u"""

// ═══ ★v8.1 ベッドの構成レジストリ (type 'bed') ═══
//   v8.0 まで ベッドの描画は 1本のコードの中に `/Aerus|宮棚/` `/Aerus/` の if が直接
//   埋まっていて、 機種が増えるたびに if を足す作りだった。 v7.5 で冷蔵庫を
//   FRIDGE_MODELS へデータ化したのと同じ理由 (1機種を直しても他機種へ伝わらない) で、
//   ベッドも **骨格の寸法・構成だけをデータで持ち、描画は 1本の共通コードへ集約** する。
//   新機種は BED_MODELS に 1エントリ足すだけで描ける。
//
//   test    … 商品名+specNote+memo (specTextOf) への正規表現。 null = 既定 (フォールバック)
//   headT   … ヘッドボードの奥行 [cm] (ローカル z。 頭側の面から室内側へ)
//   shelf   … 宮棚。 kind で構成が変わる (専用の if を増やさないための唯一の分岐)
//     kind:'over'  … ヘッドボードの前面に **載る/張り出す** 宮棚 (RASIK Aerus)
//                    { t:天板厚, d:棚の奥行, inset:棚板が左右から入る量,
//                      lh:棚板の厚み, ld:棚板の奥行, ly:天面から棚板中心までの下がり }
//     kind:'niche' … ヘッドボードに **彫り込まれた** 宮 (ニトリ アザン3)
//                    { tw:天板の幅, t:天板厚, y0:棚板の上面高さ, open は h-t-y0 で決まる,
//                      d:宮の奥行 (内寸), post:天板の外に出る側柱の幅, lip:前の幕板の高さ,
//                      div:仕切りの厚み, divAt:[仕切り中心x(cm)…] }
//   light   … 宮の照明 { comps:[点灯する区画index], col:色, t:見付 } | null
//   outlet  … 宮のコンセント { caps:口数, comp:区画index } | null
//   deck    … 床板まわり { side:サイド枠の見付, foot:フット枠の見付,
//                          slats:すのこ本数 (0 = 一枚板の床板), slatT:床板の厚み,
//                          sideCol:'dark'(枠が見える) | 'base'(側板が本体と同色) }
//   floorH  … { def:既定の床面高, opts:[切替できる値] | null }
//   storage … 床下収納 { count:杯数, depth:引き出し時の張り出し, side:'left'|'right'(既定側),
//                        y0:前板の下端, rh:前板の高さ, gap:杯どうし・両端のあき,
//                        label / labelSuffix, handle:'none' で金物ハンドル無し } | null
//   mattress… セット表示するマットレス [{ test, w, d, h, col, label }] (test:null = 既定) | null
const BED_MODELS = [
  {
    // RASIK Aerus すのこベッド (S / SS / D)。★v8.0 までの描画をそのままデータ化したもの
    test: /Aerus/,
    label: 'すのこベッド・宮棚付き (RASIK Aerus)',
    headT: 11,
    shelf: { kind: 'over', t: 3, d: 8, inset: 6, lh: 4, ld: 6, ly: 8 },
    light: null, outlet: null,
    deck: { side: 3.5, foot: 3.5, slats: 7, slatT: 2, sideCol: 'dark' },
    floorH: { def: 32, opts: [19.5, 32] },
    storage: null,
    mattress: [
      { test: /セミシングル/, w: 85, d: 198, h: 38, col: 0x3e4147, label: 'ニトリLH3 SS 85×198×38' },
      { test: /ダブル/, w: 140, d: 195, h: 25, col: 0x4a4a52, label: 'GOKUMIN B01D 140×195×25' },
      { test: null, w: 97, d: 198, h: 38, col: 0x3e4147, label: 'ニトリLH3 97×198×38' }
    ]
  },
  {
    // ★v8.1 ニトリ 収納付きベッドフレーム シングル
    //   「アザン3 棚・コンセント・ライト付き 浅型 WW」 商品コード 2050630
    //   ⚠数値の出典は **公式サイズ図** (公式画像 205063014.jpg / 「サイズ(約) ※単位:cm」):
    //     外形 97 × 211 × 85 / 床板高さ 25 / ヘッドボード奥行 14 /
    //     天板 幅93 × 厚1 × 奥行8 / 宮の開口高さ 15 / 宮の奥行 9.5 / 宮部の高さ 25.5 /
    //     宮の下の板 43 / 中央区画の幅 42 / 床板 (内寸) 長さ 196.5 /
    //     床板下スペース内寸 95 × 36 × 18(有効内寸) /
    //     引き出し 外寸長さ96 × 奥行47 × 高さ11 (有効内寸12.5) / 引き出し内寸長さ 87
    //   [est] 板厚 (side 1.8 / foot 0.5 / div 1.5 / 棚板)・前板の高さ 18.5・
    //         区画の割付 (右区画 20.7 は公式図の画素実測、 左 27.3 は 93 からの引き算)・
    //         照明とコンセントの正確な位置 は 公式に記載が無いので est。
    //   ★フット板 0.5 は 公式の寸法チェーン 14 + 196.5 = 210.5 ≒ 211 が閉じる値
    //     (実物の板厚は公式非公表。 「約」 表記なので 0.5〜1.8 の幅がある)
    test: /アザン/,
    label: '収納付きベッド・宮 (棚+照明+コンセント) + 床下引き出し2杯 (ニトリ アザン3 浅型)',
    headT: 14,
    shelf: { kind: 'niche', tw: 93, t: 1, y0: 69, d: 9.5, post: 2, lip: 4,
             div: 1.5, divAt: [-18.45, 25.05] },
    light: { comps: [0, 2], col: 0xffd9a0, t: 0.9 },
    outlet: { caps: 2, comp: 2 },
    deck: { side: 1.8, foot: 0.5, slats: 0, slatT: 1.8, sideCol: 'base' },
    floorH: { def: 25, opts: null },
    storage: { count: 2, depth: 47, side: 'left', y0: 1.5, rh: 18.5, gap: 1.5,
               handle: 'none', label: 'アザン3 引き出し',
               labelSuffix: ' (外寸96×47×高11/有効内寸12.5・スライドレール)' },
    mattress: null
  },
  {
    // 宮棚付き とだけ分かっているベッド (自由入力)。 v8.0 の `/Aerus|宮棚/` 分岐 = 棚は描くが
    // マットレスのセット表示はしない、 という挙動をそのまま保つためのエントリ
    test: /宮棚/,
    label: 'ベッドフレーム・宮棚付き (汎用)',
    headT: 11,
    shelf: { kind: 'over', t: 3, d: 8, inset: 6, lh: 4, ld: 6, ly: 8 },
    light: null, outlet: null,
    deck: { side: 3.5, foot: 3.5, slats: 7, slatT: 2, sideCol: 'dark' },
    floorH: { def: 32, opts: null },
    storage: null, mattress: null
  },
  {
    // 既定 (自由入力のベッド) = v8.0 の 「どの if にも当たらない」 描画そのもの
    test: null,
    label: 'ベッドフレーム (汎用)',
    headT: 11,
    shelf: null, light: null, outlet: null,
    deck: { side: 3.5, foot: 3.5, slats: 7, slatT: 2, sideCol: 'dark' },
    floorH: { def: 32, opts: null },
    storage: null, mattress: null
  }
];
function bedModelOf(nm) {
  for (let i = 0; i < BED_MODELS.length; i++) {
    const t = BED_MODELS[i].test;
    if (!t || t.test(nm)) return BED_MODELS[i];
  }
  return BED_MODELS[BED_MODELS.length - 1];
}
// セット表示するマットレスの仕様 (サイズ違いは test で選ぶ)
function bedMattressOf(BM, nm) {
  const list = BM.mattress || [];
  for (let i = 0; i < list.length; i++) {
    if (!list[i].test || list[i].test.test(nm)) return list[i];
  }
  return null;
}
// 宮 (niche) の区画 = 仕切りで割った各コマの { c:中心x, w:幅 }
function bedNicheComps(NI) {
  const e = [-NI.tw / 2];
  NI.divAt.forEach(function (dx) { e.push(dx - NI.div / 2, dx + NI.div / 2); });
  e.push(NI.tw / 2);
  const out = [];
  for (let i = 0; i + 1 < e.length; i += 2) out.push({ c: (e[i] + e[i + 1]) / 2, w: e[i + 1] - e[i] });
  return out;
}
// ★v8.1 収納ベッドの引き出しを どちら側に引くか。 実物は左右どちらにも取り付けられるので
//   item.drawerSide ('left'|'right') で切り替え、 未設定なら BED_MODELS の既定側を使う。
function bedDrawerSide(it) {
  const s = it && it.drawerSide;
  if (s === 'left' || s === 'right') return s;
  const BM = bedModelOf(specTextOf(it));
  return (BM.storage && BM.storage.side) || 'left';
}"""
src = rep(src, ANCHOR, BED_REG, u'(2) BED_MODELS レジストリ')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (3) ベッドの描画を BED_MODELS 駆動の 共通コード 1本へ差し替え
#     ★Aerus は メッシュの生成順・サイズ・位置・色を 1つも変えない
#       (snap_bed_mesh.py の台帳が完全一致することで機械証明する)
# ═══════════════════════════════════════════════════════════════════════════
OLD_BED = u"""  if (type === 'bed') {
    // ★v2.0 フレームのみ (内蔵マットレス削除。マットレスは別商品として上に載せる運用)
    //        床面高 floorH (Aerus: 19.5⇔32 切替、既定32) にすのこ天面。ヘッドボード + 宮棚は従来通り
    const hbT = 11;
    const fh = Math.min(Math.max(Number(it.floorH) || 32, 10), Math.max(h - 10, 10));
    P(w, h, hbT, 0, h / 2, -d / 2 + hbT / 2, base);                       // ヘッドボード
    if (/Aerus|宮棚/.test(nm)) {
      P(w, 3, 8, 0, h - 1.5, -d / 2 + hbT + 4, base);                     // 宮棚 天板
      P(w - 6, 4, 6, 0, h - 8, -d / 2 + hbT + 3, dark);                   // 棚内段差
    }
    P(3.5, fh, d - hbT, -(w / 2 - 1.75), fh / 2, hbT / 2, dark);          // サイドフレーム 左
    P(3.5, fh, d - hbT, (w / 2 - 1.75), fh / 2, hbT / 2, dark);           // サイドフレーム 右
    P(w - 7, fh, 3.5, 0, fh / 2, d / 2 - 1.75, dark);                     // フットフレーム
    const slatN = 7, slatSpan = (d - hbT - 5) / slatN;
    for (let si = 0; si < slatN; si++) {                                  // すのこ天面 (床面高 fh)
      P(w - 8, 2, Math.max(slatSpan - 4, 3), 0, fh - 1, -d / 2 + hbT + 2 + slatSpan * (si + 0.5), lite);
    }
    // ★v2.2[7] すのこ+マットレスのセット化: Aerus は item.mattress (既定ON) で対応マットレスを内蔵描画。
    //          D=GOKUMIN B01D 140×195×25 / S=ニトリLH3 97×198×38 / SS=LH3 SS 85×198×38
    //          (SS はフレーム80より幅広 → はみ出して描画される = 現実のはみ出し警告)
    if (/Aerus/.test(nm) && it.mattress !== false) {
      let mw, md, mh, mCol;
      if (/セミシングル/.test(nm)) { mw = 85; md = 198; mh = 38; mCol = new THREE.Color(0x3e4147); }
      else if (/ダブル/.test(nm)) { mw = 140; md = 195; mh = 25; mCol = new THREE.Color(0x4a4a52); }
      else { mw = 97; md = 198; mh = 38; mCol = new THREE.Color(0x3e4147); }   // シングル
      const mz = -d / 2 + hbT + md / 2;                                   // 頭側=ヘッドボード直後から敷く
      const mDk = mCol.clone().multiplyScalar(0.78);
      const mLt = mCol.clone().lerp(new THREE.Color(0xffffff), 0.45);
      const mB = Math.max(mh * 0.45, 2);
      P(mw, mB, md, 0, fh + mB / 2, mz, mDk.clone().lerp(mCol, 0.55));    // 下層 (側面ボーダー)
      P(mw - 2.5, mh - mB, md - 2.5, 0, fh + mB + (mh - mB) / 2, mz, mCol); // 上層 (角丸風)
      P(mw - 8, 0.8, 2, 0, fh + mh - 0.1, mz - md * 0.17, mLt);           // キルト風ライン1
      P(mw - 8, 0.8, 2, 0, fh + mh - 0.1, mz + md * 0.17, mLt);           // キルト風ライン2
    }
  } else if (type === 'mattress') {"""

NEW_BED = u"""  if (type === 'bed') {
    // ★v8.1 ベッドは BED_MODELS のデータ + この共通コード 1本だけで描く。
    //   機種ごとの if を足さない = 1機種の直しが全機種へ伝わる (FRIDGE_MODELS と同じ流儀)。
    //   骨格の順序 (ヘッドボード → 宮 → サイド枠 → フット枠 → 床板 → 床下収納 → マットレス) は共通で、
    //   寸法・本数・色・有無だけが BED_MODELS のエントリから来る。
    const BM = bedModelOf(nm), DK = BM.deck;
    const hbT = BM.headT;
    const fh = Math.min(Math.max(Number(it.floorH) || BM.floorH.def, 10), Math.max(h - 10, 10));
    const frameCol = (DK.sideCol === 'base') ? base : dark;
    const zB = -d / 2;                                                    // ヘッドボード 背面
    const NI = (BM.shelf && BM.shelf.kind === 'niche') ? BM.shelf : null;
    if (!NI) {
      P(w, h, hbT, 0, h / 2, zB + hbT / 2, base);                         // ヘッドボード (一枚板)
      if (BM.shelf) {                                                     // kind:'over' の宮棚 (Aerus)
        const S = BM.shelf;
        P(w, S.t, S.d, 0, h - S.t / 2, zB + hbT + S.d / 2, base);         // 宮棚 天板
        P(w - S.inset, S.lh, S.ld, 0, h - S.ly, zB + hbT + S.ld / 2, dark);   // 棚内段差
      }
    } else {
      // ★v8.1 kind:'niche' = ヘッドボードに彫り込まれた宮 (ニトリ アザン3)。
      //   引き算ができないので 下部パネル / 奥壁 / 側柱 / 天板 / 前の幕板 / 仕切り の板で組む。
      const topB = h - NI.t;                                              // 天板 下端
      const backD = Math.max(hbT - NI.d, 1);                              // 宮の奥壁の厚み
      P(w, NI.y0, hbT, 0, NI.y0 / 2, zB + hbT / 2, base);                 // 下部パネル (床〜棚板の上面)
      P(NI.tw, topB - NI.y0, backD, 0, (NI.y0 + topB) / 2, zB + backD / 2,
        base.clone().multiplyScalar(0.90));                               // 宮の奥壁 (奥まって見えるよう少し暗く)
      [-1, 1].forEach(function (s) {                                      // 側柱 (天板93 の外側 = 各2cm)
        P(NI.post, h - NI.y0, hbT, s * (w / 2 - NI.post / 2), (NI.y0 + h) / 2, zB + hbT / 2, base);
      });
      P(NI.tw, NI.t, hbT, 0, h - NI.t / 2, zB + hbT / 2, base);           // 天板
      P(NI.tw, NI.lip, 1.5, 0, NI.y0 + NI.lip / 2, zB + hbT - 0.75, base);   // 前の幕板 (落下止め)
      NI.divAt.forEach(function (dx) {                                    // 仕切り ×2
        P(NI.div, topB - NI.y0, NI.d, dx, (NI.y0 + topB) / 2, zB + hbT - NI.d / 2, base);
      });
      const comps = bedNicheComps(NI);
      if (BM.light) {                                                     // 宮の LED 照明 (点灯する区画のみ)
        BM.light.comps.forEach(function (ci) {
          const C = comps[ci];
          if (C) P(C.w * 0.72, BM.light.t, 1.0, C.c, topB - BM.light.t, zB + backD + 1.0, BM.light.col);
        });
      }
      if (BM.outlet) {                                                    // 宮のコンセント (2口プレート)
        const C = comps[BM.outlet.comp] || comps[comps.length - 1];
        const oy = NI.y0 + (topB - NI.y0) * 0.42;
        P(3.0 * BM.outlet.caps + 1.4, 4.4, 0.7, C.c, oy, zB + backD + 0.35, lite);
        for (let oi = 0; oi < BM.outlet.caps; oi++) {
          P(0.9, 2.2, 0.5, C.c + (oi - (BM.outlet.caps - 1) / 2) * 3.0, oy, zB + backD + 0.8, dark);
        }
      }
    }
    P(DK.side, fh, d - hbT, -(w / 2 - DK.side / 2), fh / 2, hbT / 2, frameCol);   // サイドフレーム 左
    P(DK.side, fh, d - hbT, (w / 2 - DK.side / 2), fh / 2, hbT / 2, frameCol);    // サイドフレーム 右
    P(w - DK.side * 2, fh, DK.foot, 0, fh / 2, d / 2 - DK.foot / 2, frameCol);    // フットフレーム
    if (DK.slats > 0) {
      const slatSpan = (d - hbT - 5) / DK.slats;
      for (let si = 0; si < DK.slats; si++) {                             // すのこ天面 (床面高 fh)
        P(w - DK.side * 2 - 1, DK.slatT, Math.max(slatSpan - 4, 3), 0, fh - DK.slatT / 2,
          zB + hbT + 2 + slatSpan * (si + 0.5), lite);
      }
    } else {
      const inn = d - hbT - DK.foot;                                      // 一枚板の床板 (収納ベッド)
      P(w - DK.side * 2, DK.slatT, inn, 0, fh - DK.slatT / 2, zB + hbT + inn / 2, lite);
    }
    if (BM.storage) {
      // ★v8.1 床下収納の引き出し。 実物は左右どちらにも取り付けられるので item.drawerSide で切替。
      //   開閉は既存の drawers レジストリ (リガーレ・エトナ・洗濯機のふたと同じ流儀。視覚のみ・保存対象外)。
      //   itemDrawerSet に v8.1 で face を足したので、 長辺 (側面) から引く動きがそのまま出せる。
      const ST = BM.storage, dside = bedDrawerSide(it), sg = (dside === 'left' ? -1 : 1);
      const silver = new THREE.Color(0xa8abae);
      const seamCol = dark.clone().lerp(base, 0.35);
      const xf = sg * (w / 2 + 0.15);                                     // 側面のすぐ外 (見切り線を置く面)
      const inner = d - hbT - DK.foot;                                    // 引き出しが並ぶ長さ
      const fw = (inner - ST.gap * (ST.count + 1)) / ST.count;            // 前板1枚の幅
      const z0 = zB + hbT;
      const defs = [];
      P(0.7, 0.6, inner, xf, ST.y0, z0 + inner / 2, seamCol);                       // 前板 下端の見切り
      P(0.7, 0.6, inner, xf, ST.y0 + ST.rh, z0 + inner / 2, seamCol);               // 前板 上端の見切り
      for (let gi = 0; gi <= ST.count; gi++) {                                      // 杯どうし・両端の縦見切り
        P(0.7, ST.rh, 0.6, xf, ST.y0 + ST.rh / 2, z0 + gi * (ST.gap + fw) + ST.gap / 2, seamCol);
      }
      for (let di = 0; di < ST.count; di++) {
        const along = z0 + ST.gap * (di + 1) + fw * (di + 0.5);
        // 閉じている時の手掛け (前板の上端の掘り込み)。開くと hideOpen で隠れる
        const hd = P(0.9, 1.3, fw * 0.30, sg * (w / 2 + 0.7), ST.y0 + ST.rh - 2.2, along, seamCol);
        defs.push({ key: 'd' + (di + 1), face: dside, kind: 'drawer', hideOpen: [hd],
                    handle: ST.handle || null,
                    label: ST.label + (di + 1) + (ST.labelSuffix || ''),
                    x0: along, bw: fw, y0: ST.y0, rh: ST.rh, depth: ST.depth });
      }
      itemDrawerSet(g, it, defs, { w: w, d: d, base: base, dark: dark, lite: lite, silver: silver });
    }
    // ★v2.2[7] マットレスのセット化: item.mattress (既定ON) で対応マットレスを内蔵描画。
    //          どれを敷くかは BED_MODELS の mattress[] が持つ (D=GOKUMIN B01D / S・SS=ニトリLH3)。
    //          (SS はフレーム80より幅広 → はみ出して描画される = 現実のはみ出し警告)
    const MS = (BM.mattress && it.mattress !== false) ? bedMattressOf(BM, nm) : null;
    if (MS) {
      const mw = MS.w, md = MS.d, mh = MS.h, mCol = new THREE.Color(MS.col);
      const mz = zB + hbT + md / 2;                                       // 頭側=ヘッドボード直後から敷く
      const mDk = mCol.clone().multiplyScalar(0.78);
      const mLt = mCol.clone().lerp(new THREE.Color(0xffffff), 0.45);
      const mB = Math.max(mh * 0.45, 2);
      P(mw, mB, md, 0, fh + mB / 2, mz, mDk.clone().lerp(mCol, 0.55));    // 下層 (側面ボーダー)
      P(mw - 2.5, mh - mB, md - 2.5, 0, fh + mB + (mh - mB) / 2, mz, mCol); // 上層 (角丸風)
      P(mw - 8, 0.8, 2, 0, fh + mh - 0.1, mz - md * 0.17, mLt);           // キルト風ライン1
      P(mw - 8, 0.8, 2, 0, fh + mh - 0.1, mz + md * 0.17, mLt);           // キルト風ライン2
    }
  } else if (type === 'mattress') {"""
src = rep(src, OLD_BED, NEW_BED, u'(3) ベッド描画の共通化')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (4) bedFloorH の既定値も BED_MODELS から取る (Aerus は 32 のままなので挙動不変)
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""function bedFloorH(bed) {
  const h = Number(bed.h) || 66;
  return Math.min(Math.max(Number(bed.floorH) || 32, 10), Math.max(h - 10, 10));
}""",
u"""function bedFloorH(bed) {
  const h = Number(bed.h) || 66;
  // ★v8.1 既定の床面高は機種ごと (Aerus 32 / ニトリ アザン3 は浅型で 25) → BED_MODELS から取る
  const BM = bedModelOf(specTextOf(bed));
  return Math.min(Math.max(Number(bed.floorH) || BM.floorH.def, 10), Math.max(h - 10, 10));
}""", u'(4) bedFloorH の既定値')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (5) 家具シートの 床面高 / マットレス ブロックの出し分けも BED_MODELS 駆動に。
#     あわせて 収納ベッド用の 「引き出しの向き」 セグメントを追加。
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""  // ★v2.0 Aerus 床面高 2段階切替 (すのこ面 19.5 ⇔ 32、既定32)。マットレスの載せ高さに反映
  const fh = (workItems[selectedItemId] && itemTypeOf(it) === 'bed') ? (Number(it.floorH) || 32) : null;
  const floorHBlock = (itemTypeOf(it) === 'bed' && /Aerus|床面高/.test(specTextOf(it)))
    ? '<div class="form-group"><label class="form-label">床面高 (すのこ面の高さ)</label>' +
      '<div class="floorh-seg">' +
      '<button class="floorh-btn' + (fh === 19.5 ? ' active' : '') + '" onclick="setBedFloorH(19.5)">19.5cm (ロー)</button>' +
      '<button class="floorh-btn' + (fh !== 19.5 ? ' active' : '') + '" onclick="setBedFloorH(32)">32cm (ハイ)</button>' +
      '</div></div>'
    : '';
  // ★v2.2[7] Aerus マットレスON/OFF (セット化): ON時は対応マットレスをベッドモデルに内蔵描画 (item.mattress として保存)
  let mattressBlock = '';
  if (itemTypeOf(it) === 'bed' && /Aerus/.test(specTextOf(it))) {
    const bnm = specTextOf(it);
    const mName = /セミシングル/.test(bnm) ? 'ニトリLH3 SS 85×198×38' :
                  /ダブル/.test(bnm) ? 'GOKUMIN B01D 140×195×25' : 'ニトリLH3 97×198×38';
    const mOn = it.mattress !== false;
    mattressBlock =
      '<div class="form-group"><label class="form-label">マットレス (セット表示: ' + esc(mName) + ')</label>' +
      '<div class="floorh-seg">' +
      '<button class="floorh-btn' + (mOn ? ' active' : '') + '" onclick="setBedMattress(true)">ON</button>' +
      '<button class="floorh-btn' + (!mOn ? ' active' : '') + '" onclick="setBedMattress(false)">OFF (フレームのみ)</button>' +
      '</div>' +
      (/セミシングル/.test(bnm)
        ? '<div class="dim-note">⚠ SS はマットレス幅85cm &gt; フレーム80cm — 実物同様はみ出して表示されます</div>'
        : '') +
      '</div>';
  }""",
u"""  // ★v8.1 ベッドの機種ごとの UI (床面高の切替 / マットレスのセット表示 / 引き出しの向き) は
  //        BED_MODELS のデータで出し分ける (商品名の正規表現を UI 側にも書かない)。
  const isBed = itemTypeOf(it) === 'bed';
  const BMu = isBed ? bedModelOf(specTextOf(it)) : null;
  // ★v2.0 床面高 2段階切替 (Aerus すのこ面 19.5 ⇔ 32、既定32)。マットレスの載せ高さに反映
  const fh = (workItems[selectedItemId] && isBed) ? (Number(it.floorH) || BMu.floorH.def) : null;
  const floorHBlock = (isBed && BMu.floorH.opts && BMu.floorH.opts.length >= 2)
    ? '<div class="form-group"><label class="form-label">床面高 (すのこ面の高さ)</label>' +
      '<div class="floorh-seg">' +
      BMu.floorH.opts.map(function (v, i) {
        const on = (fh === v) || (i === BMu.floorH.opts.length - 1 && BMu.floorH.opts.indexOf(fh) < 0);
        return '<button class="floorh-btn' + (on ? ' active' : '') + '" onclick="setBedFloorH(' + v + ')">' +
               v + 'cm (' + (i === 0 ? 'ロー' : 'ハイ') + ')</button>';
      }).join('') +
      '</div></div>'
    : '';
  // ★v2.2[7] マットレスON/OFF (セット化): ON時は対応マットレスをベッドモデルに内蔵描画 (item.mattress として保存)
  let mattressBlock = '';
  if (isBed && BMu.mattress) {
    const ms = bedMattressOf(BMu, specTextOf(it));
    const mOn = it.mattress !== false;
    mattressBlock =
      '<div class="form-group"><label class="form-label">マットレス (セット表示: ' + esc(ms ? ms.label : '') + ')</label>' +
      '<div class="floorh-seg">' +
      '<button class="floorh-btn' + (mOn ? ' active' : '') + '" onclick="setBedMattress(true)">ON</button>' +
      '<button class="floorh-btn' + (!mOn ? ' active' : '') + '" onclick="setBedMattress(false)">OFF (フレームのみ)</button>' +
      '</div>' +
      (ms && ms.w > (Number(it.w) || 0)
        ? '<div class="dim-note">⚠ マットレス幅' + ms.w + 'cm &gt; フレーム' + tipN(it.w) +
          'cm — 実物同様はみ出して表示されます</div>'
        : '') +
      '</div>';
  }
  // ★v8.1 収納ベッド: 引き出しを左右どちらに付けるか (実物が左右付替え可の商品だけ出る)
  let drawerSideBlock = '';
  if (isBed && BMu.storage) {
    const dsv = bedDrawerSide(it);
    drawerSideBlock =
      '<div class="form-group"><label class="form-label">引き出しの向き (左右付け替え可)</label>' +
      '<div class="floorh-seg">' +
      '<button class="floorh-btn' + (dsv === 'left' ? ' active' : '') + '" onclick="setBedDrawerSide(\\'left\\')">左側に引く</button>' +
      '<button class="floorh-btn' + (dsv === 'right' ? ' active' : '') + '" onclick="setBedDrawerSide(\\'right\\')">右側に引く</button>' +
      '</div>' +
      '<div class="dim-note">📐 引き出しきると本体側面から ' + tipN(BMu.storage.depth) +
      'cm 張り出します — 3Dで引き出しをクリックすると前方の残り幅が出ます</div>' +
      '</div>';
  }""", u'(5) 家具シートの機種別ブロック')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (6) 家具シートの組み立てに drawerSideBlock を差し込む
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""    colorBlock + floorHBlock + mattressBlock + vesaBlock + hangBlock + mountBlock + insideBlock + levelBlock +""",
u"""    colorBlock + floorHBlock + mattressBlock + drawerSideBlock +   // ★v8.1 収納ベッドの引き出し向き
    vesaBlock + hangBlock + mountBlock + insideBlock + levelBlock +""", u'(6) 家具シートへ差し込み')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (7) setBedDrawerSide (引き出しの向きを保存 = メッシュを組み直す)
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""// ★v4.1 モニターアームの VESA高さ (天板から画面中心まで)。公式 Lift 330mm の範囲。""",
u"""// ★v8.1 収納ベッド 引き出しの向き (左右付け替え可の実物仕様)。item.drawerSide として保存
window.setBedDrawerSide = function (v) {
  const it = workItems[selectedItemId];
  if (!it || itemTypeOf(it) !== 'bed') return;
  it.drawerSide = (v === 'right') ? 'right' : 'left';
  const m = furnMeshes[selectedItemId];
  if (m) syncItemMesh(m, it);
  markDirty();
  openItemSheet();
  toast('引き出しを ' + (it.drawerSide === 'right' ? '右' : '左') + '側へ引く向きにしました');
};
// ★v4.1 モニターアームの VESA高さ (天板から画面中心まで)。公式 Lift 330mm の範囲。""",
u'(7) setBedDrawerSide')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (8) メッシュ組み直しキーに drawerSide を足す (足さないと左右を切り替えても再構築されない)
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""  const key = [it.w, it.d, it.h, it.color, itemTypeOf(it), it.name, it.floorH || '',
               it.mattress === false ? 'M0' : 'M1',
               it.mounted ? 'AM1' : 'AM0', it.vesaH || '',
               it.standH || '', it.shelfH || ''].join('|');   // ★v2.0 floorH / ★v2.2 mattress / ★v4.1 マウント・VESA高さ / ★v6.5 TVスタンドの取付高さ・棚高さ""",
u"""  const key = [it.w, it.d, it.h, it.color, itemTypeOf(it), it.name, it.floorH || '',
               it.mattress === false ? 'M0' : 'M1',
               it.mounted ? 'AM1' : 'AM0', it.vesaH || '',
               it.standH || '', it.shelfH || '',
               it.drawerSide || ''].join('|');   // ★v2.0 floorH / ★v2.2 mattress / ★v4.1 マウント・VESA高さ / ★v6.5 TVスタンドの取付高さ・棚高さ / ★v8.1 収納ベッドの引き出し向き""",
u'(8) buildKey に drawerSide')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (9) 保存データ (cleanItem) に drawerSide を足す (足さないと保存で消える)
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""    mattress: it.mattress === false ? false : true,   // ★v2.2 Aerusマットレス内蔵表示 (既定ON)""",
u"""    mattress: it.mattress === false ? false : true,   // ★v2.2 Aerusマットレス内蔵表示 (既定ON)
    // ★v8.1 収納ベッドの引き出しを左右どちらに付けるか (null = BED_MODELS の既定側)
    drawerSide: (it.drawerSide === 'left' || it.drawerSide === 'right') ? it.drawerSide : null,""",
u'(9) cleanItem に drawerSide')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (10) install (据付必要すきま) を 「引き出し」 と 「左右どちらにも付けられる」 に対応させる。
#      ベッド専用の欄を作らず、 v7.5 で作った汎用フィールドを 2つ拡張するだけにする。
# ═══════════════════════════════════════════════════════════════════════════
src = rep(src, u"""//     doorFront           … 扉/引き出しを開いた時に前方へ必要な寸法 (本体前面から)
//     doorSide            … ★v7.6 扉がどちら側へ開くか 'left'|'right' (置き場所の判断に効く)
//     doorSideCm          … その側方へ必要な寸法 (本体側面から cm)""",
u"""//     doorFront           … 扉/引き出しを開いた時に前方へ必要な寸法 (本体前面から)
//     doorSide            … ★v7.6 扉がどちら側へ開くか 'left'|'right' (置き場所の判断に効く)
//                           ★v8.1 'both' = 左右どちらにも付けられる (収納ベッドの引き出し等)
//     doorSideCm          … その側方へ必要な寸法 (本体側面から cm)
//     openKind            … ★v8.1 'door' (既定) | 'drawer'。 表示の言い回しが 扉→引き出し に変わる""",
u'(10a) install のコメント')
applied += 1

src = rep(src, u"""  if (ins.doorSide === 'left' || ins.doorSide === 'right') {
    rows.push('扉の開き: ' + (ins.doorSide === 'left' ? '左開き (吊元=右)' : '右開き (吊元=左)') +
              (N(ins.doorSideCm) === null ? ''
                : ' → ' + (ins.doorSide === 'left' ? '左' : '右') + 'へ ' + tipN(N(ins.doorSideCm)) + 'cm 必要'));
  }
  if (N(ins.doorFront) !== null) {
    rows.push('扉の開放: 本体前面から ' + tipN(N(ins.doorFront)) + 'cm' +
              (ins.doorNote ? ' (' + ins.doorNote + ')' : ''));
  }""",
u"""  const oKind = (ins.openKind === 'drawer') ? '引き出し' : '扉';   // ★v8.1
  if (ins.doorSide === 'both') {
    // ★v8.1 左右どちらにも付けられる (収納ベッドの引き出し等)
    rows.push(oKind + 'の向き: 左右どちらの側面にも取り付け可' +
              (N(ins.doorSideCm) === null ? ''
                : ' → 引く側へ ' + tipN(N(ins.doorSideCm)) + 'cm 必要 (本体側面から)'));
  } else if (ins.doorSide === 'left' || ins.doorSide === 'right') {
    rows.push(oKind + 'の開き: ' + (ins.doorSide === 'left' ? '左開き (吊元=右)' : '右開き (吊元=左)') +
              (N(ins.doorSideCm) === null ? ''
                : ' → ' + (ins.doorSide === 'left' ? '左' : '右') + 'へ ' + tipN(N(ins.doorSideCm)) + 'cm 必要'));
  }
  if (N(ins.doorFront) !== null) {
    rows.push(oKind + 'の開放: 本体前面から ' + tipN(N(ins.doorFront)) + 'cm' +
              (ins.doorNote ? ' (' + ins.doorNote + ')' : ''));
  }""", u'(10b) install の表示')
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (11) CATALOG_SEED: ニトリ アザン3 を1件追加 (既存34件は触らない)
# ═══════════════════════════════════════════════════════════════════════════
SPECNOTE = (
    u'ニトリ 収納付きベッドフレーム シングル「アザン3 棚・コンセント・ライト付き 浅型 WW」'
    u'**商品コード 2050630** / 39,990円(税込) / 組立式 (組立時間 約30分・玄関先までの配送、'
    u'配送員設置は +6,600円) / 保証5年 / 質量 約65kg / 材質 プリント紙化粧繊維板 / '
    u'梱包4個 (100×43×10 / 102×67×54 / 102×22×92 / 102×27×6 cm)。'
    u'出典 = ニトリ公式 商品ページ https://www.nitori-net.jp/ec/product/2050630/ '
    u'(仕様・サイズ表はクライアント側描画のため 実ブラウザで取得) + '
    u'**公式サイズ図 (公式画像 205063014.jpg「サイズ(約) ※単位:cm」)**。'
    u'\n★公式サイズ図の実数: 外形 幅97 × 奥行211 × 高さ85 / 床板高さ 25 / '
    u'ヘッドボード奥行 14 / 宮の天板 幅93×厚1×奥行8 / 宮の開口高さ 15 / 宮の奥行 9.5 / '
    u'宮部の高さ 25.5 / 宮の下の板 43 / 宮の中央区画の幅 42 / 床板(内寸)長さ 196.5 / '
    u'床板下スペース内寸 95 × 36 × 18(有効内寸) ×2区画 / '
    u'引き出し 外寸長さ96 × 奥行47 × 高さ11 (有効内寸12.5)・内寸長さ87・スライドレール付き / '
    u'コンセントコード長さ 100。'
    u'\n★機能: ヘッドボードに **2口コンセント** と **LED照明** (公式商品説明)。'
    u'引き出しは **2杯・左右どちらにも取り付け可** (公式明記。組立説明書 2050610 も'
    u'「引出し左側スタイルで説明いたします」と左右対応を前置き)。対応マットレスは'
    u' **シングル 97×195cm** (マットレスは別売)。'
    u'\n⚠**商品コード 2050620 との違い**: 2050620 は **色違いでも深型/浅型違いでもなく、'
    u'廃番になった旧 MBR (ミドルブラウン) のコード**。 現在 /ec/product/2050620/ を開くと '
    u'canonical は 2050620 のまま 表示される商品コードは 2050630・カラーは ホワイトウォッシュ に'
    u'フォールバックする (breadcrumb 構造化データも欠落)。公式 JSON-LD の ProductGroup (2023190s) が'
    u'列挙する全16バリアント (S/SD/D/Q × 4色) にも 2050620 は存在せず、旧 Yahoo!ニトリ店の'
    u' nitori-net/2050620.html (タイトル「アザン3 浅型/MBR」) は現在404。'
    u'現行の MBR は別コード **2190600013390 (MBR2)** に置き換わっている (両者とも浅型・同一仕様)。'
    u'\n★カラー4色の商品コード (シングル・各39,990円。全て公式で実確認): '
    u'WW ホワイトウォッシュ 2050630 / GY グレーウォッシュ 2076510 / '
    u'LBR3 ライトブラウン 2076500 / MBR2 ミドルブラウン 2190600013390。'
    u'色の16進は **各色の公式製品画像の面材を画素実測** (中央値): '
    u'WW=公式画像 205063004.jpg の足元側 側板 #beb5a6 / GY=207651004.jpg 同 #988372 / '
    u'LBR3=207650004.jpg 同 #ae8452 / MBR2=219060001339001.jpg 同 #7b5437。'
    u'⚠いずれも **室内カットの写真から採った実測値** なので、ショールームで見る面材より'
    u'やや暗い (照明込みの値)。推定色は使っていない。'
    u'\n⚠**公式に記載が無い項目** (est も置いていない): 耐荷重 / コンセントの定格W数 / '
    u'照明の明るさ・スイッチ位置 / 組立必要人数 / 宮の左右区画の正確な幅 (公式図の画素実測で '
    u'右20.7・左27.3) / 引き出しを引き切った時の張り出し量。'
    u'\n⚠**張り出し 47cm は est**: 公式は「引き出し 奥行47cm・スライドレール付き」までしか'
    u'書いていないため、フルスライド前提で 奥行 = 張り出し量 として扱っている (レール分の余りは未算入)。'
    u'\n⚠**マットレスの組み合わせ注意**: 本カタログの「ニトリ Nスリープ ラグジュアリー LH3 シングル」は'
    u' 97×198cm で、アザン3 の床板内寸 196.5cm に対して **1.5cm 長い** (公式の対応サイズは 97×195)。'
    u'\n★3Dモデル: BED_MODELS の 1エントリ (宮=kind:\'niche\' / 床下収納 2杯 / 床板=一枚板)。'
    u'板厚 (側板1.8・フット0.5・仕切り1.5)・引き出し前板の高さ18.5・照明とコンセントの位置は est。'
    u'フット板 0.5 は 公式チェーン 14 + 196.5 = 210.5 ≒ 211 が閉じる値。'
)

SEED = {
    "name": u"ニトリ 収納付きベッド アザン3 シングル (浅型 WW)",
    "model": u"アザン3 棚・コンセント・ライト付き 浅型 WW / 商品コード 2050630",
    "room": "east62",
    "w": 97,
    "d": 211,
    "h": 85,
    "color": "#beb5a6",
    "colors": [
        {"name": u"ホワイトウォッシュ (WW / 2050630)", "hex": "#beb5a6"},
        {"name": u"グレーウォッシュ (GY / 2076510)", "hex": "#988372"},
        {"name": u"ライトブラウン (LBR3 / 2076500)", "hex": "#ae8452"},
        {"name": u"ミドルブラウン (MBR2 / 2190600013390)", "hex": "#7b5437"},
    ],
    "type": "bed",
    "url": "https://www.nitori-net.jp/ec/product/2050630/",
    "floorH": 25,
    "install": {
        "doorSide": "both",
        "doorSideCm": 47,
        "openKind": "drawer",
        "note": (u"引き出しは左右どちらの側面にも取り付け可 (公式明記)。"
                 u"引き切った時の張り出しは公式に記載が無く、引き出し奥行47cm (公式) を"
                 u"フルスライド前提でそのまま張り出し量として扱っている [est]。"
                 u"壁からのすきま・上方のすきまは公式に指定なし"),
    },
    "specNote": SPECNOTE,
    "memo": "",
}

m = re.search(CS_PAT, src, re.S)
cs = json.loads(m.group(1))
assert not any(u'アザン' in it.get('name', '') for it in cs['items']), u'既にアザン3がある'
assert cs['version'] == '2.7', u'CATALOG_SEED が v2.7 でない: %s' % cs['version']
cs['items'].append(SEED)
cs['version'] = '2.8'
cs['updatedAt'] = '2026-08-24'
cs['_comment'] += (
    u' ★v2.8 の変更点 (2026-08-24): **ニトリ 収納付きベッドフレーム シングル '
    u'「アザン3 棚・コンセント・ライト付き 浅型 WW」(商品コード 2050630) を1点追加** '
    u'(room=east62 / type=\'bed\' / 97 × 211 × 85・床板高さ25)。寸法は ニトリ公式の商品ページ と '
    u'**公式サイズ図 (公式画像 205063014.jpg)** が出典で、色の16進は 各色の公式製品画像から画素実測。'
    u'一次資料は catalog\\商品公式資料\\ニトリ_アザン3_収納ベッド\\ に README 付きで保存。'
    u'⚠検索で出てくる 2050620 は 色違いではなく **廃番の旧MBRコード** (現行MBRは 2190600013390)。'
    u'あわせて **ベッドの3D描画を BED_MODELS のデータ駆動へ共通化** した '
    u'(v7.5 の FRIDGE_MODELS と同じ流儀。機種ごとの if を足さない。既存 RASIK Aerus 3種は '
    u'メッシュ台帳が完全一致することを snap_bed_mesh.py で機械証明済み)。'
    u'汎用フィールドも3つ拡張: ①itemDrawerSet の `face`(front/left/right) と `hideOpen`/`handle` '
    u'= 長辺 (側面) から引く引き出しが リガーレ・エトナと同じ仕組みで動く ②install の '
    u'`openKind`(\'drawer\') と `doorSide:\'both\'` = 「引き出しの向き: 左右どちらの側面にも取り付け可」 '
    u'③item.drawerSide (left/right) = 引き出しの向きを保存する ★アプリ v8.1'
)
src = (src[:m.start()]
       + 'var CATALOG_SEED = ' + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n'
       + src[m.end():])
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# 検証
# ═══════════════════════════════════════════════════════════════════════════
assert MARK in src, u'冪等マーカーが入っていない'
assert shapat(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
cs_after = json.loads(re.search(CS_PAT, src, re.S).group(1))
items_after = cs_after['items']
assert len(items_before) == 34, u'適用前の商品数が 34 でない: %d' % len(items_before)
assert len(items_after) == 35, u'適用後の商品数が 35 でない: %d' % len(items_after)
J = (lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True))
changed = [i for i, (a, b) in enumerate(zip(items_after[:34], items_before)) if J(a) != J(b)]
assert not changed, u'既存商品が変化した (index): %s' % changed
# ★バイト単位の不変も確認 (json.dumps を通さず、シリアライズ後の文字列で照合)
seed_json = json.dumps(SEED, ensure_ascii=False, separators=(',', ':'))
before_body = json.dumps({'items': items_before}, ensure_ascii=False, separators=(',', ':'))
after_body = json.dumps({'items': items_after[:34]}, ensure_ascii=False, separators=(',', ':'))
assert sha(before_body) == sha(after_body), u'既存34商品がバイト単位で不変でない'
assert cs_after['version'] == '2.8'
assert items_after[34]['type'] == 'bed'
assert items_after[34]['memo'] == '', u'memo は空でなければならない'
assert items_after[34]['install']['doorSide'] == 'both'
assert len(items_after[34]['colors']) == 4
# Aerus 3種が消えていない
aerus = [i for i in items_after if 'Aerus' in i['name']]
assert len(aerus) == 3, u'RASIK Aerus が %d 件 (3件でなければならない)' % len(aerus)
assert seed_json in json.dumps(cs, ensure_ascii=False, separators=(',', ':'))
assert src.count(u'const BED_MODELS = [') == 1
assert src.count(u'function bedModelOf(') == 1
assert src.count(u'function bedDrawerSide(') == 1
assert src.count(u"if (/Aerus|宮棚/.test(nm)) {") == 0, u'旧・Aerus 専用の if が残っている'
assert src.count(u"if (/Aerus/.test(nm) && it.mattress !== false)") == 0
assert src.count(u"/Aerus|床面高/.test(specTextOf(it))") == 0, u'旧・床面高UIの正規表現が残っている'

io.open(TARGET, 'w', encoding='utf-8', newline='').write(src)
print(u'適用%d件' % applied)
print(u'CATALOG_SEED v2.7 → v2.8 / 商品 34 → 35 (ニトリ アザン3 収納ベッド シングル 2050630)')
print(u'  外形 97 × 211 × 85 / 床板高さ 25 / 引き出し 2杯 (96×47×高11) 左右付替可 / 宮=棚+LED+2口コンセント')
print(u'  ROOM_DATA sha256 %s (不変) / 既存34商品 バイト単位不変' % rd_before[:16])
print(u'  ベッド描画は BED_MODELS (4エントリ) のデータ駆動へ共通化 — Aerus のメッシュ台帳は不変')

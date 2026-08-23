# -*- coding: utf-8 -*-
u"""v7.8: 丸型の壁掛け時計 (セイコークロック KX397A 電波掛時計) を商品として追加し、壁に掛かるようにする。冪等。

ユーザー指示: 「丸型の壁掛け時計を商品として追加し、カレンダーと同じように壁に掛けられるように」

主な変更
  (A) 汎用フィールド `shape` を新設 ('round' = 正面から見て円形 / w=h=直径・d=厚み)。
      寸法の文章表記を itemDimsText() / itemDimsShort() に集約し、丸型は
      「直径○cm × 厚み○cm」と出す (時計専用の分岐にしない = 鏡・丸テーブルも値を足すだけ)。
  (B) 汎用フィールド colors[].variant を新設。カラースウォッチが「色」だけでなく
      「見た目バリエーション」も切り替えられるようにする (itemColorVariantOf)。
      → セイコー KX397A(アイボリー) と KX397B(濃茶) は **色違いではなく文字盤ごと違う別モデル**
        (A=アラビア数字・黒の中空針・白秒針 / B=ローマ数字・白の中実針・オレンジ秒針) なので、
        濃茶スウォッチを選ぶと文字盤も KX397B の見た目に切り替わる。
  (C) CLOCK_FACES レジストリ + clockFaceTexture() を新設。文字盤 (枠リング・木目・数字・分目盛・
      SEIKO ロゴ・針) を CanvasTexture 1枚に全部描く (カレンダー v7.4 と同じ方針。メッシュを増やさない)。
  (D) buildItemParts に type 'clock' を新設。円は CylinderGeometry (openEnded の筒を X軸90°で倒す)
      + CircleGeometry で作る。合計 5メッシュ (側面 / 裏板 / 文字盤 / ガラス / 銀ツメ4個を1メッシュ)。
  (E) WALL_HANG_TYPES に clock を1行追加 → v7.4 の壁掛け機構 (吸着・高さスライダー・外すと床) が
      そのまま効く。丸型でも当たり判定は w×h の外接矩形で、直径をそのまま幅として扱えば正しい。
  (F) CATALOG_SEED に 1件追加 (33 → 34件)。

不変条件
  - ROOM_DATA は一切変更しない (sha256 前後一致を assert)
  - CATALOG_SEED v2.5 -> v2.6。**既存33商品はバイト単位で不変** (追加のみ) を assert
"""
import io
import re
import json
import hashlib
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'
MARK = u'v7.8 丸型 壁掛け時計'

# ═══ 実測カラー (公式製品画像 500x500 からの画素サンプリング。出典は specNote / Box README) ═══
#   中心 (254,248) / 外周半径 230px でリング状に切り出した RGB の中央値。
C_IVORY = '#DAD8CC'   # KX397A アイボリー枠 (r200-224 / 輝度170-246 の median。p25 #D7D4C8 - p75 #DDDCD2)
C_DBROWN = '#373632'  # KX397B 濃茶枠      (r200-224 / 輝度10-140  の median。p25 #33322E - p75 #3F3E3A)

SEED = {
    "name": u"壁掛け時計 セイコー 電波 φ32",
    "model": "KX397A",
    "room": "ldk",
    "w": 32,
    "d": 4.6,
    "h": 32,
    "color": C_IVORY,
    "type": "clock",
    "shape": "round",
    "url": "https://www.seiko-clock.co.jp/product-personal/wall_clock/standard/kx397a.html",
    "memo": "",
    "colors": [
        {"name": u"アイボリー (KX397A)", "hex": C_IVORY, "variant": "KX397A"},
        {"name": u"濃茶 (KX397B)", "hex": C_DBROWN, "variant": "KX397B"},
    ],
    "specNote": u"セイコークロック 電波掛時計 KX397A。★出典 = セイコーウオッチ株式会社 公式製品ページ "
                u"https://www.seiko-clock.co.jp/product-personal/wall_clock/standard/kx397a.html の「仕様」表 "
                u"(製品番号 KX397A / 枠材 プラスチック枠 (アイボリー塗装)・前面 ガラス / サイズ・重さ 直径320x46mm 970g / "
                u"電池 単3(マンガン)x1・電池寿命約1年間 / 機能 電波修正機能(40kHz/60kHz自動選局・受信OFF機能つき)・"
                u"ステップセコンド・おやすみ秒針(光センサーによる自動秒針停止機能。一定以下の暗さになると12時の位置で"
                u"自動的に秒針が止まる) / 11,000円 税込 [本体価格10,000円])。★寸法の取り方: 公式「直径320x46mm」= "
                u"丸型なので nozaROOM では w32.0 = h32.0 = 直径 / d4.6 = 厚み として持つ (shape:'round' フラグ付き。"
                u"UI の寸法表記は「直径32cm × 厚み4.6cm」になる)。★掛け方 (公式取扱説明書 説明書番号 AKX-070W): "
                u"付属品に「木ねじ 1本 (厚い木の壁・木の柱専用)」。厚い木の壁・木の柱 = 付属の木ねじ / "
                u"石膏ボードの壁 = 付属の木ねじは使用せず市販の掛け具 / コンクリート等 = 市販の掛け具。"
                u"「掛ける場所、壁の材質・構造を確認のうえ、本製品の重さに充分耐えられる掛け具を選ぶこと」。"
                u"⚠この部屋の壁が石膏ボードかどうかは未確認 (実物を掛ける時は掛け具を別途用意)。"
                u"★関連製品 (公式同ページ「関連製品」欄で実在を確認): **KX397B** = 同寸 (直径320x46mm 970g)・"
                u"プラスチック枠 (濃茶塗装)・11,000円。**KX398A** = 300x300x46mm 1.1kg・アイボリー塗装・同機能・"
                u"11,000円。**KX398B** = 398A の濃茶。⚠KX398A は『ひと回り小さい丸型』ではなく **角型 300x300mm** "
                u"(丸型の小径版は公式ラインナップに無い)。⚠KX397B は『KX397A の色違い』ではなく **文字盤デザインまで"
                u"違う別モデル** — 公式製品画像を実見すると A=アラビア数字12個(セリフ体・立体貼付)・木目(明)文字盤・"
                u"黒の中空(輪郭)針・**秒針は白**、B=ローマ数字・木目(暗)文字盤・白の中実針・**秒針はオレンジ**。"
                u"そのため カラースウォッチの濃茶を選ぶと 3Dの文字盤も KX397B の見た目に切り替わる "
                u"(colors[].variant → CLOCK_FACES)。★カラー hex は公式製品画像 (500x500) からの画素実測: "
                u"アイボリー枠 #DAD8CC (r200-224 の median・p25 #D7D4C8 / p75 #DDDCD2) / 濃茶枠 #373632 "
                u"(p25 #33322E / p75 #3F3E3A)。⚠公式表記は「濃茶塗装」だが実測はほぼ黒に近いダークグレー。"
                u"文字盤の木目 #CCC4B6 (木理 #B5AA94) / 数字 #081713 / KX397B は 木目 #4D3C32・数字 #BBCBC9・"
                u"秒針 #DB7143 も同じ手順で実測。★3Dモデル: buildItemParts の type 'clock' 分岐。"
                u"円は CylinderGeometry (openEnded の筒を X軸90°で倒す) + CircleGeometry で作り、Box を並べて"
                u"円を作る重い実装はしない。文字盤 (枠リング・木目・アラビア数字12個・分目盛の丸ドット・5分ごとの"
                u"小さな四角・SEIKO ロゴ・時針/分針/秒針) は CanvasTexture 1枚に全部描画 = 合計 5メッシュ "
                u"(側面 / 裏板 / 文字盤 / ガラス / 12・3・6・9 の銀ツメ4個を束ねた1メッシュ)。文字盤の造形比率は"
                u"公式画像の半径ヒストグラム実測: 木目文字盤の外周 0.73R / 数字の中心 0.79R / 分目盛 0.59R / "
                u"SEIKO ロゴ 0.43R (R=外周半径)。針は公式画像と同じ 10:10 付近の見栄え位置 (3Dは 10:08:40 固定描画。"
                u"実時刻とは連動しない)。★壁掛け: type 'clock' を WALL_HANG_TYPES に登録済みで、壁へドラッグすると "
                u"ROOM_DATA.walls の壁区画に吸着する (既定の上端高さ 175cm。掛ける高さは家具シートのスライダーで変更)。"
                u"★一次資料は Box catalog\\商品公式資料\\セイコー_KX397A_掛時計\\ (公式ページ3本・公式製品画像4枚・"
                u"取扱説明書PDF・README に実測手順) に保存。",
}


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


src = io.open(P, encoding='utf-8').read()
rd_before = sha(RD_PAT, src)
items_before = json.loads(re.search(CS_PAT, src, re.S).group(1))['items']

if MARK in src:
    print(u'適用0件 / skip 6件 (既に適用済み)')
    sys.exit(0)

applied = 0

# ═══════════════════════════════════════════════════════════════════════════
# (1) 汎用フィールド shape / 寸法テキストの共通化 / colors[].variant
# ═══════════════════════════════════════════════════════════════════════════
old = u"""function itemTopColorOf(it) {
  if (!it) return null;
  const c = it.catalogId ? catalogData[it.catalogId] : null;
  return (c && c.topColor) || it.topColor || null;
}"""
new = old + u"""
// ★v7.8 形状フラグ。直方体表記 (W×D×H) が意味を成さない商品のための共通フィールド。
//   時計専用の分岐にせず カタログシードの `shape` を読むだけにする
//   (丸鏡 / 丸テーブル / 円形ラグ も 値を足すだけで同じ表記になる。topColor と同じ流儀)。
//   'round' = 正面から見て円形。**w = h = 直径 / d = 厚み** として持つ。null = 直方体 (従来どおり)。
function itemShapeOf(it) {
  if (!it) return null;
  const c = it.catalogId ? catalogData[it.catalogId] : null;
  return (c && c.shape) || it.shape || null;
}
function isRoundItem(it) { return itemShapeOf(it) === 'round'; }
// 寸法の文章表記 (家具シートの 📐 サマリー)。丸型は「直径○cm × 厚み○cm」
function itemDimsText(it) {
  return isRoundItem(it)
    ? ('直径 ' + tipN(it.w) + 'cm × 厚み ' + tipN(it.d) + 'cm')
    : ('幅W ' + tipN(it.w) + ' × 奥行D ' + tipN(it.d) + ' × 高さH ' + tipN(it.h) + 'cm');
}
// 一覧行の短い寸法表記 (カタログ一覧 / 配置済み一覧)。丸型は φ直径×厚
function itemDimsShort(it) {
  return isRoundItem(it) ? ('φ' + it.w + '×厚' + it.d) : (it.w + '×' + it.d + '×' + it.h);
}
// ★v7.8 いま選ばれているカラースウォッチのエントリ (colors[] の要素) を返す。
//   colors[] の要素に `variant` を持たせておくと、モデル側がそれを見て別デザインを描ける
//   = 「色違いに見えて 実は別モデル」の商品 (セイコー KX397A / KX397B) を 1商品で扱える。
function itemColorVariantOf(it) {
  if (!it) return null;
  const c = it.catalogId ? catalogData[it.catalogId] : null;
  const list = (c && c.colors) || it.colors || [];
  const hex = String(it.color || '').toLowerCase();
  for (let i = 0; i < list.length; i++) {
    if (String(list[i].hex || '').toLowerCase() === hex) return list[i];
  }
  return null;
}"""
assert old in src, u'(1) itemTopColorOf が見つからない'
src = src.replace(old, new, 1)
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (2) 家具シートの 📐 寸法サマリー 1行目を 共通関数へ (丸型は 直径×厚み)
# ═══════════════════════════════════════════════════════════════════════════
old = u"""  rows.push('幅W ' + tipN(it.w) + ' × 奥行D ' + tipN(it.d) + ' × 高さH ' + tipN(it.h) + 'cm');
  installClearanceRows(it).forEach(function (r) { rows.push(r); });   // ★v7.5 据付必要すきま (放熱スペース)"""
new = u"""  rows.push(itemDimsText(it));   // ★v7.8 丸型 (shape:'round') は「直径○cm × 厚み○cm」
  installClearanceRows(it).forEach(function (r) { rows.push(r); });   // ★v7.5 据付必要すきま (放熱スペース)"""
assert old in src, u'(2) 寸法サマリー1行目が見つからない'
src = src.replace(old, new, 1)
applied += 1

# ── (2b) 一覧行の寸法も共通関数へ (カタログ / 配置済み) ──
old = u"""    (c.memo ? '<div class="cat-memo">' + esc(String(c.memo).slice(0, 42)) + '</div>' : '') + '</span>' +
    '<span class="cat-dims">' + c.w + '×' + c.d + '×' + c.h + '</span></button>';"""
new = u"""    (c.memo ? '<div class="cat-memo">' + esc(String(c.memo).slice(0, 42)) + '</div>' : '') + '</span>' +
    '<span class="cat-dims">' + esc(itemDimsShort(c)) + '</span></button>';   // ★v7.8 丸型は φ直径×厚"""
assert old in src, u'(2b) catRow の寸法表記が見つからない'
src = src.replace(old, new, 1)

old = u"""        '<span class="cat-dims">' + it.w + '×' + it.d + '×' + it.h + '</span></button>';"""
new = u"""        '<span class="cat-dims">' + esc(itemDimsShort(it)) + '</span></button>';   // ★v7.8 丸型は φ直径×厚"""
assert old in src, u'(2b) 配置済み一覧の寸法表記が見つからない'
src = src.replace(old, new, 1)

# ── (2c) 3D 上の寸法ラベル (選択中家具の頭上) も丸型対応 ──
old = u"""      txt = 'W' + it.w + ' × D' + it.d + ' × H' + it.h;"""
new = u"""      txt = isRoundItem(it)                                   // ★v7.8 丸型は φ直径 × 厚
        ? ('φ' + it.w + ' × 厚' + it.d)
        : ('W' + it.w + ' × D' + it.d + ' × H' + it.h);"""
assert old in src, u'(2c) 3D 寸法ラベルが見つからない'
src = src.replace(old, new, 1)

# ═══════════════════════════════════════════════════════════════════════════
# (3) CLOCK_FACES レジストリ + 文字盤 CanvasTexture
# ═══════════════════════════════════════════════════════════════════════════
ANCHOR = u"// ═══ ★v7.5 冷蔵庫 (type 'fridge') の扉構成レジストリ ═══"
assert ANCHOR in src, u'(3) 挿入位置 (v7.5 冷蔵庫レジストリ) が見つからない'
CLOCK_JS = u"""// ═══ ★v7.8 丸型 壁掛け時計 (type 'clock') の文字盤レジストリ ═══
//   セイコークロック KX397A / KX397B は **同寸法の色違いではなく 文字盤ごと違う別モデル**
//   (公式製品画像を実見: A = アラビア数字12個(セリフ体・立体貼付)・木目(明)文字盤・黒の中空(輪郭)針・
//    秒針は白 / B = ローマ数字・木目(暗)文字盤・白の中実針・秒針はオレンジ)。
//   そこで **カラースウォッチの variant で文字盤ごと切り替える** (FRIDGE_MODELS / WALL_HANG_TYPES と
//   同じレジストリ流儀。機種が増えても 1エントリ足すだけで if を増やさない)。
//   ★色・比率は すべて 公式製品画像 (500x500) からの画素実測。出典は specNote / Box README。
const CLOCK_FACES = {
  KX397A: {                       // 公式 KX397A (プラスチック枠 アイボリー塗装 / 前面ガラス)
    frame: '#DAD8CC', dial: '#CCC4B6', grain: '#B5AA94',
    numerals: 'arabic', numColor: '#081713', numPx: 66,
    mark: '#141a17', hand: '#14150f', handStyle: 'outline',
    second: '#eef1f4', logo: '#1a1a1a', cap: '#c9cacc'
  },
  KX397B: {                       // 公式 KX397B (プラスチック枠 濃茶塗装 / 前面ガラス)
    frame: '#373632', dial: '#4D3C32', grain: '#3E3028',
    numerals: 'roman', numColor: '#BBCBC9', numPx: 40,
    mark: '#d7dedb', hand: '#eef1ef', handStyle: 'solid',
    second: '#DB7143', logo: '#e6e9e6', cap: '#d8d9db'
  }
};
// 文字盤の造形比率 (外周半径 R = 1.0)。公式画像の「暗い画素の半径ヒストグラム」からの実測値
const CLOCKF = { dialR: 0.73, numR: 0.79, markR: 0.59, logoR: 0.43,
                 hourL: 0.42, minL: 0.62, secL: 0.66, secTail: 0.15 };
const CLOCK_ROMAN = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'];
const CLOCK_FONT = '"Times New Roman","Yu Mincho","Hiragino Mincho ProN",serif';
const clockTexCache = {};
// 文字盤を CanvasTexture 1枚に全部描く (枠リング・木目・数字・分目盛・SEIKO ロゴ・針)。
//   カレンダー (v7.4 calendarPaperTexture) と同じ方針 = 描画物を増やしてもメッシュは増やさない。
//   針は 10:08:40 固定 (公式製品画像と同じ 10:10 付近の見栄え位置。実時刻とは連動しない)。
function clockFaceTexture(key) {
  if (clockTexCache[key]) return clockTexCache[key];
  const F = CLOCK_FACES[key] || CLOCK_FACES.KX397A;
  const S = 512, R = S / 2, cx = R, cy = R;
  const cv = document.createElement('canvas');
  cv.width = S; cv.height = S;
  const c = cv.getContext('2d');
  const TAU = Math.PI * 2;
  const disc = function (r) { c.beginPath(); c.arc(cx, cy, r * R, 0, TAU); };
  // ── 枠リング (アイボリー / 濃茶。この上に数字が乗る) + 上からの光の当たり ──
  c.fillStyle = F.frame; disc(1.0); c.fill();
  c.save(); disc(1.0); c.clip();
  const lg = c.createLinearGradient(0, 0, S * 0.35, S);
  lg.addColorStop(0, 'rgba(255,255,255,0.16)');
  lg.addColorStop(0.55, 'rgba(255,255,255,0)');
  lg.addColorStop(1, 'rgba(0,0,0,0.16)');
  c.fillStyle = lg; c.fillRect(0, 0, S, S);
  c.restore();
  // ── 木目の文字盤 (一段奥まっている) ──
  c.save(); disc(CLOCKF.dialR); c.clip();
  c.fillStyle = F.dial; c.fillRect(0, 0, S, S);
  let sd = 20260823;                                   // 木目は毎回同じ絵にする (決定論 PRNG)
  const rnd = function () { sd = (sd * 1103515245 + 12345) & 0x7fffffff; return sd / 0x7fffffff; };
  c.strokeStyle = F.grain;
  for (let i = 0; i < 46; i++) {                       // 縦方向の木理
    c.globalAlpha = 0.10 + rnd() * 0.22;
    c.lineWidth = 0.6 + rnd() * 2.4;
    const x0 = rnd() * S;
    c.beginPath(); c.moveTo(x0, -10);
    c.bezierCurveTo(x0 + (rnd() - 0.5) * 12, S * 0.35, x0 + (rnd() - 0.5) * 12, S * 0.65, x0, S + 10);
    c.stroke();
  }
  c.globalAlpha = 1;
  c.restore();
  disc(CLOCKF.dialR); c.strokeStyle = 'rgba(0,0,0,0.22)'; c.lineWidth = 5; c.stroke();   // 段差の影
  disc(CLOCKF.dialR - 0.012); c.strokeStyle = 'rgba(255,255,255,0.13)'; c.lineWidth = 2; c.stroke();
  // ── 分目盛 (分 = 丸ドット / 5分ごと = 小さな四角) ──
  for (let i = 0; i < 60; i++) {
    const a = (i * 6 - 90) * Math.PI / 180;
    const px = cx + Math.cos(a) * CLOCKF.markR * R, py = cy + Math.sin(a) * CLOCKF.markR * R;
    c.fillStyle = F.mark;
    if (i % 5 === 0) c.fillRect(px - 3.4, py - 3.4, 6.8, 6.8);
    else { c.beginPath(); c.arc(px, py, 2.3, 0, TAU); c.fill(); }
  }
  // ── 数字 (アラビア = 立体貼付なので影を1枚敷く / ローマ = 外向きに回転) ──
  c.textAlign = 'center'; c.textBaseline = 'middle';
  c.font = 'bold ' + F.numPx + 'px ' + CLOCK_FONT;
  for (let n = 1; n <= 12; n++) {
    const a = (n * 30 - 90) * Math.PI / 180;
    const px = cx + Math.cos(a) * CLOCKF.numR * R, py = cy + Math.sin(a) * CLOCKF.numR * R;
    if (F.numerals === 'roman') {
      c.save(); c.translate(px, py); c.rotate(a + Math.PI / 2);
      c.fillStyle = F.numColor; c.fillText(CLOCK_ROMAN[n % 12], 0, 0);
      c.restore();
    } else {
      c.fillStyle = 'rgba(0,0,0,0.20)'; c.fillText(String(n), px + 2, py + 3);   // 貼付数字の影
      c.fillStyle = F.numColor; c.fillText(String(n), px, py);
    }
  }
  // ── SEIKO ロゴ + その下の小さなドット ──
  c.fillStyle = F.logo;
  c.font = 'bold 21px "Arial","Helvetica",sans-serif';
  c.fillText('S E I K O', cx, cy - CLOCKF.logoR * R);
  c.beginPath(); c.arc(cx, cy - CLOCKF.logoR * R + 26, 3.6, 0, TAU); c.fill();
  // ── 針 (10:08:40 固定) ──
  const hand = function (deg, len, half, col, filled) {
    c.save(); c.translate(cx, cy); c.rotate((deg - 90) * Math.PI / 180);
    c.beginPath();
    c.moveTo(-0.05 * R, -half); c.lineTo(len * R, -half * 0.20);
    c.lineTo(len * R, half * 0.20); c.lineTo(-0.05 * R, half);
    c.closePath();
    if (filled) { c.fillStyle = col; c.fill(); }
    else { c.strokeStyle = col; c.lineWidth = 3.0; c.lineJoin = 'round'; c.stroke(); }
    c.restore();
  };
  const solid = F.handStyle === 'solid';
  const hDeg = (10 + 8 / 60 + 40 / 3600) / 12 * 360;   // 時針 (10:08:40)
  const mDeg = (8 + 40 / 60) / 60 * 360;               // 分針
  const sDeg = 40 / 60 * 360;                          // 秒針
  hand(hDeg, CLOCKF.hourL, 9, F.hand, solid);
  hand(mDeg, CLOCKF.minL, 7.5, F.hand, solid);
  if (!solid) {                                        // 中空針は中心側だけ実体がある (公式画像どおり)
    c.save(); c.translate(cx, cy); c.rotate((hDeg - 90) * Math.PI / 180);
    c.fillStyle = F.hand;
    c.beginPath(); c.moveTo(-0.06 * R, -8); c.lineTo(0.15 * R, -3); c.lineTo(0.15 * R, 3);
    c.lineTo(-0.06 * R, 8); c.closePath(); c.fill();
    c.restore();
  }
  c.save(); c.translate(cx, cy); c.rotate((sDeg - 90) * Math.PI / 180);
  c.strokeStyle = F.second; c.fillStyle = F.second; c.lineWidth = 2.4; c.lineCap = 'round';
  c.beginPath(); c.moveTo(-CLOCKF.secTail * R, 0); c.lineTo(CLOCKF.secL * R, 0); c.stroke();
  c.beginPath(); c.arc(-CLOCKF.secTail * R, 0, 5, 0, TAU); c.fill();
  c.restore();
  c.beginPath(); c.arc(cx, cy, 7.5, 0, TAU); c.fillStyle = F.cap; c.fill();
  c.strokeStyle = 'rgba(0,0,0,0.30)'; c.lineWidth = 1.2; c.stroke();
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  clockTexCache[key] = tex;
  return tex;
}

"""
src = src.replace(ANCHOR, CLOCK_JS + ANCHOR, 1)
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (4) buildItemParts に type 'clock' を新設 (カレンダー分岐の直前)
# ═══════════════════════════════════════════════════════════════════════════
old = u"""  } else if (type === 'calendar') {
    // ★v7.4 壁掛けカレンダー (新日本カレンダー NK163 / A2「THE・文字」 公式 610×425mm)。"""
new = u"""  } else if (type === 'clock') {
    // ★v7.8 丸型 壁掛け時計 (セイコークロック KX397A/KX397B 電波掛時計。公式 直径320 × 厚み46mm)。
    //   丸い形は **CylinderGeometry (openEnded の筒) を X軸に90°倒して円盤の側面** にする。
    //   Box を並べて円を作るとメッシュが跳ね上がる (モバイル負荷) ので使わない。
    //   文字盤 (枠リング・木目・数字・分目盛・SEIKO ロゴ・針) は CanvasTexture 1枚に描く
    //   → 合計 5メッシュ: 側面リム / 裏板 / 文字盤 / ガラス / 12・3・6・9 の銀ツメ4個 (1メッシュに束ねる)。
    //   壁に掛かっている時は 背面が壁に密着し、正面 (ローカル +z) が室内を向く (rotY は wallHangPose が決める)。
    //   ★カラースウォッチの variant で文字盤ごと切り替わる (アイボリー=KX397A / 濃茶=KX397B)。
    const va = itemColorVariantOf(it);
    const fk = (va && va.variant && CLOCK_FACES[va.variant]) ? va.variant : 'KX397A';
    const rad = Math.min(w, h) / 2;                    // 丸型は w = h = 直径 (shape:'round')
    const th = Math.max(d, 1);                         // 厚み (公式 46mm)
    const yc = h / 2;                                  // 円の中心 (ローカル原点は下端)
    const rim = new THREE.Mesh(
      new THREE.CylinderGeometry(rad, rad, th, 44, 1, true),
      new THREE.MeshLambertMaterial({ color: base, side: THREE.DoubleSide }));
    rim.rotation.x = Math.PI / 2;                      // 円筒の軸を z 方向へ (= 正面を向いた円盤)
    rim.position.set(0, yc, 0);
    g.add(rim);
    const back = new THREE.Mesh(new THREE.CircleGeometry(rad, 44),
      new THREE.MeshLambertMaterial({ color: base.clone().multiplyScalar(0.82) }));
    back.position.set(0, yc, -th / 2);
    back.rotation.y = Math.PI;                         // 裏板は 背面 (-z) を向く
    g.add(back);
    const recess = Math.min(th * 0.24, 1.2);           // ガラスより少し奥に文字盤 (前面はガラス)
    const face = new THREE.Mesh(new THREE.CircleGeometry(rad * 0.985, 48),
      new THREE.MeshLambertMaterial({ map: clockFaceTexture(fk) }));
    face.position.set(0, yc, th / 2 - recess);
    g.add(face);
    const glass = new THREE.Mesh(new THREE.CircleGeometry(rad * 0.99, 48),
      new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.10 }));
    glass.position.set(0, yc, th / 2 - 0.12);
    g.add(glass);
    const tb = rad * 0.11, tz = th * 0.15;             // 12/3/6/9 の外周にある小さな銀色のツメ (公式画像)
    MERGE([[tb, 1.6, th * 0.5, 0, yc + rad * 0.95, tz],
           [tb, 1.6, th * 0.5, 0, yc - rad * 0.95, tz],
           [1.6, tb, th * 0.5, -rad * 0.95, yc, tz],
           [1.6, tb, th * 0.5, rad * 0.95, yc, tz]], 0xc9cacc);
  } else if (type === 'calendar') {
    // ★v7.4 壁掛けカレンダー (新日本カレンダー NK163 / A2「THE・文字」 公式 610×425mm)。"""
assert old in src, u'(4) calendar 分岐が見つからない'
src = src.replace(old, new, 1)
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (5) WALL_HANG_TYPES に clock を1行追加 (= v7.4 の壁掛け機構がそのまま効く)
# ═══════════════════════════════════════════════════════════════════════════
old = u"""//   ポスター / 壁掛け時計 / 鏡 なども WALL_HANG_TYPES に type を足すだけで同じ挙動になる
//   (TOP_STACK_TYPES / SOLID_FIX_TYPES と同じレジストリ流儀)。"""
new = u"""//   ポスター / 壁掛け時計 / 鏡 なども WALL_HANG_TYPES に type を足すだけで同じ挙動になる
//   (TOP_STACK_TYPES / SOLID_FIX_TYPES と同じレジストリ流儀)。
//   ★v7.8 実証: 丸型の壁掛け時計 (type 'clock') は **この1行の追加だけ** で
//     吸着 / 掛ける高さスライダー / 壁から外すと床へ / 矢印キーで壁沿い移動 が全部効いた。
//     丸型でも判定は w×h の外接矩形 (直径をそのまま幅・高さとして持つ) なので、
//     wallHangPose の左右クランプ (from + w/2 … to − w/2) も 直径基準で正しく働く。"""
assert old in src, u'(5) WALL_HANG_TYPES のコメントが見つからない'
src = src.replace(old, new, 1)

old = u"const WALL_HANG_TYPES = { calendar: 1 };"
new = u"const WALL_HANG_TYPES = { calendar: 1, clock: 1 };   // ★v7.8 clock 追加"
assert old in src, u'(5) WALL_HANG_TYPES が見つからない'
src = src.replace(old, new, 1)
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# (6) CATALOG_SEED: 壁掛け時計を1件 追加 (既存33件は触らない)
# ═══════════════════════════════════════════════════════════════════════════
m = re.search(CS_PAT, src, re.S)
cs = json.loads(m.group(1))
assert not any(u'掛け時計' in it.get('name', '') for it in cs['items']), u'既に時計がある'
cs['items'].append(SEED)
cs['version'] = '2.6'
cs['updatedAt'] = '2026-08-23'
cs['_comment'] += (
    u' ★v2.6 の変更点 (2026-08-23): **丸型の壁掛け時計 セイコークロック KX397A 電波掛時計 を1点追加** '
    u'(room=ldk / type=\'clock\' 新設 / shape=\'round\' 新設 / 直径32 × 厚み4.6cm)。寸法・機能・カラーは '
    u'セイコーウオッチ株式会社 公式製品ページ (直径320x46mm 970g / 電波修正・ステップセコンド・おやすみ秒針 / '
    u'11,000円税込) と 公式取扱説明書 AKX-070W が出典、色は公式製品画像からの画素実測。'
    u'一次資料は catalog\\商品公式資料\\セイコー_KX397A_掛時計\\ に README 付きで保存。'
    u'あわせて 汎用フィールドを2つ新設: ①**shape** (\'round\' = 正面から見て円形。w=h=直径 / d=厚み。'
    u'UI の寸法表記が「直径○cm × 厚み○cm」になる。丸鏡・丸テーブルも値を足すだけで効く) '
    u'②**colors[].variant** (カラースウォッチが色だけでなく見た目バリエーションも切り替える。'
    u'セイコー KX397A(アイボリー・アラビア数字) と KX397B(濃茶・ローマ数字) は色違いではなく別文字盤の'
    u'別モデルなので、スウォッチで文字盤ごと切り替わる)。3Dモデルは buildItemParts に type \'clock\' を新設 '
    u'(CylinderGeometry の筒 + CircleGeometry + CanvasTexture 1枚 = 5メッシュ)。'
    u'壁掛けは v7.4 の WALL_HANG_TYPES に clock を1行足すだけで成立 ★アプリ v7.8'
)
src = (src[:m.start()]
       + 'var CATALOG_SEED = ' + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n'
       + src[m.end():])
applied += 1

# ═══════════════════════════════════════════════════════════════════════════
# 検証
# ═══════════════════════════════════════════════════════════════════════════
assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
cs_after = json.loads(re.search(CS_PAT, src, re.S).group(1))
items_after = cs_after['items']
assert len(items_before) == 33, u'適用前の商品数が 33 でない: %d' % len(items_before)
assert len(items_after) == 34, u'適用後の商品数が 34 でない: %d' % len(items_after)
J = (lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True))
changed = [i for i, (a, b) in enumerate(zip(items_after[:33], items_before)) if J(a) != J(b)]
assert not changed, u'既存商品が変化した (index): %s' % changed
assert cs_after['version'] == '2.6'
assert items_after[33]['type'] == 'clock' and items_after[33]['shape'] == 'round'
assert items_after[33]['memo'] == '', u'memo は空でなければならない'

io.open(P, 'w', encoding='utf-8', newline='').write(src)
print(u'適用%d件 (丸型 壁掛け時計 セイコー KX397A を追加 / shape・variant を汎用新設 / WALL_HANG_TYPES に clock)' % applied)
print(u'ROOM_DATA sha256 %s (不変)' % rd_before[:16])
print(u'CATALOG_SEED v2.5 -> v2.6 / 商品 33 -> 34件 (既存33件はバイト単位で不変)')
print(u'追加: %s (%s) 直径%s × 厚み%s cm'
      % (SEED['name'], SEED['model'], SEED['w'], SEED['d']))

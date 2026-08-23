# -*- coding: utf-8 -*-
u"""nozaROOM v7.4 — room.html への冪等パッチ (CATALOG_SEED v2.1 → v2.2 / 壁掛け機構 新設)

やること:
  ① CATALOG_SEED に 「壁掛けカレンダー A2 THE・文字 (2026年)」 (NK163 / 名入れ版 NK-8163) を1点追加。
     公式 610×425mm → w42.5 / h61 / d0.5(est) / room=ldk / type='calendar'
  ② **壁掛け機構 (汎用)** を新設。 カレンダー専用にせず WALL_HANG_TYPES レジストリで
     ポスター / 壁掛け時計 / 鏡 も後から足せる形にする (TOP_STACK_TYPES と同じ流儀)。
     壁面は ROOM_DATA.walls (開口で分割済み) を正とする = 建具の上には掛からない。
     保存フィールド: wallId (壁区画 id / null) と hangH (床〜アイテム上端 cm / null=既定175)。
  ③ buildItemParts に type 'calendar' 分岐 (CanvasTexture 1枚 = メッシュ2個。モバイル負荷を上げない)。
  ④ 家具シートに 高さスライダー (standH / shelfH と同じ作り・同じ見た目) + 壁から外すボタン。
  ⑤ ツールチップ (v6.4 itemDimSummaryHtml) に 壁掛け行を合流。

安全装置:
  * ROOM_DATA の sha256 が パッチ前後で **不変** であることを assert (今回は触らない)
  * CATALOG_SEED の sha256 が **変わる** ことを assert (前 90bc1a97…)
  * 2回目以降の実行は 「適用 0 / skip N」 で終わる (冪等)

実行:  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v7_4.py
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, 'room.html')

CATALOG_SHA_BEFORE = '90bc1a97fc56c56dd5869a9ffd4fd482fec9063b8525aa7014bfc62d2b467552'

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


src = io.open(TARGET, encoding='utf-8').read()
orig = src


def seed_block(s):
    m = re.search(r'var CATALOG_SEED = (\{.*?\});\n', s, re.S)
    assert m, 'CATALOG_SEED が見つからない'
    return m.group(1)


def room_block(s):
    m = re.search(r'var ROOM_DATA = (\{.*?\});\n', s, re.S)
    assert m, 'ROOM_DATA が見つからない'
    return m.group(1)


ROOM_SHA_BEFORE = hashlib.sha256(room_block(src).encode('utf-8')).hexdigest()
seed_before = seed_block(src)
if hashlib.sha256(seed_before.encode('utf-8')).hexdigest() != CATALOG_SHA_BEFORE:
    if 'NK163' not in seed_before:
        die(u'CATALOG_SEED の sha256 が想定 (90bc1a97…) と違い、 かつ NK163 も未適用 '
            u'— 想定外の版なので中断する')
        sys.exit(1)


def edit(tag, old, new, marker):
    u"""old → new の単発置換。 marker が既にあれば skip。 old が無い/複数あれば FAIL。"""
    global src
    if marker in src:
        sk(tag)
        return
    n = src.count(old)
    if n != 1:
        die(u'%s: アンカーが %d 箇所 (1 でない) — %r' % (tag, n, old[:70]))
        return
    src = src.replace(old, new, 1)
    ok(tag)


# ═══════════════════════════════════════════════════════════════════
# ① CATALOG_SEED: 壁掛けカレンダーを1点追加 + v2.1 → v2.2
# ═══════════════════════════════════════════════════════════════════
CAL_SPEC = (
    u'新日本カレンダー株式会社「壁掛けカレンダー A2 THE・文字」2026年版。'
    u'★出典 = 新日本カレンダー 公式商品ページ '
    u'https://www.nkcalendar.co.jp/products/calendar/wall-calendar/nk-8163.html '
    u'(品番 NK-8163 = 名入れ版の型番 / JAN 4985849125182 / サイズ 610×425mm / 12枚 / '
    u'紙製本 / 定価1,100円 税抜 / 3色文字月表 / 六曜あり / 元号あり / '
    u'付録「縁起のいい日」年間カレンダー)。Amazon 等の一般流通版は 型番表記が NK163、'
    u'2026年版は年表付き。'
    u'★寸法の取り方: 公式 610×425mm は 縦610 × 横425 の縦長 → 幅 W42.5 × 高さ H61.0cm。'
    u'⚠★est (公式に記載が無い値): **奥行 D0.5cm は est** — 公式ページに 厚み・吊り具・'
    u'吊り下げ穴の有無 の記載は一切無く、紙製本12枚 (表紙+12ヶ月) の束の厚みからの推定値。'
    u'同じく **壁への吊り方 (穴/金具/紐) も公式に記載が無い** ため、3Dモデルの上端中央の'
    u'吊り下げ穴は 一般的な壁掛けカレンダーの表現であって 公式確認済みの仕様ではない。'
    u'★3Dモデル: buildItemParts の type "calendar" 分岐。紙面は CanvasTexture 1枚を'
    u'板の正面に貼る構成 (紙の束 + 上部の綴じ + 紙面 の3メッシュのみ。'
    u'日付グリッド・曜日帯・六曜は全部2D描画でメッシュを増やさない = モバイル負荷を上げない)。紙面の内容 '
    u'(月表・曜日帯の色・六曜) は Amazon 商品画像の構成に合わせた再現で、'
    u'六曜は (旧暦月+旧暦日) mod 6 の標準式で算出 '
    u'(旧暦朔日 = 国立天文台 暦要項: 旧暦11/1=2025-12-20 / 12/1=2026-01-19 / '
    u'正月1日=2026-02-17。便利ジャパン・ゼクシィの公表値と 2026年1月 全31日一致を確認済)。'
    u'★壁掛け: type "calendar" は WALL_HANG_TYPES に登録済みで、壁へドラッグすると '
    u'ROOM_DATA.walls の壁区画に吸着する (既定の上端高さ 175cm)。'
)

CAL_ITEM = {
    u'name': u'壁掛けカレンダー A2 THE・文字 (2026年)',
    u'model': u'NK163',
    u'room': u'ldk',
    u'w': 42.5,
    u'd': 0.5,
    u'h': 61,
    u'color': u'#ffffff',
    u'type': u'calendar',
    u'url': u'https://www.nkcalendar.co.jp/products/calendar/wall-calendar/nk-8163.html',
    u'memo': u'',
    u'specNote': CAL_SPEC,
}

SEED_NOTE = (
    u' ★v2.2 の変更点 (2026-08-23): **壁掛けカレンダー A2 THE・文字 (2026年) '
    u'(新日本カレンダー NK163 / 名入れ版 NK-8163) を1点追加** (room=ldk / type=\'calendar\' 新設 / '
    u'W42.5×D0.5×H61)。寸法は公式商品ページの 610×425mm が出典 (縦長)。'
    u'⚠奥行 D0.5cm だけは公式に記載が無く 紙製本12枚からの est。'
    u'あわせて **アイテムを壁面に掛ける汎用機構** を新設 '
    u'(WALL_HANG_TYPES レジストリ = TOP_STACK_TYPES と同じ流儀。'
    u'ポスター/壁掛け時計/鏡 も type を足すだけで同じ挙動になる)。'
    u'壁面は ROOM_DATA.walls (開口で分割済みの壁区画) を正とし、'
    u'背面が壁から30cm以内 かつ 区画の from..to に収まる時だけ吸着するので '
    u'ドア・窓の上には掛からない。保存フィールドは wallId / hangH (床〜上端cm・既定175)。'
    u'3Dモデルは buildItemParts の type \'calendar\' 分岐 '
    u'(紙面は CanvasTexture 1枚 = メッシュ2個) ★アプリ v7.4'
)

seed_obj = json.loads(seed_before)
if any((it.get('model') == 'NK163') for it in seed_obj['items']):
    sk(u'CATALOG_SEED: 壁掛けカレンダー NK163 は追加済み')
else:
    seed_obj['items'].append(CAL_ITEM)
    seed_obj['_comment'] = seed_obj['_comment'] + SEED_NOTE
    seed_obj['version'] = '2.2'
    seed_obj['updatedAt'] = '2026-08-23'
    seed_new = json.dumps(seed_obj, ensure_ascii=False, separators=(',', ':'))
    assert src.count(seed_before) == 1
    src = src.replace(seed_before, seed_new, 1)
    ok(u'CATALOG_SEED v2.1 → v2.2 (壁掛けカレンダー NK163 を追加 / 31 → 32 商品)')


# ═══════════════════════════════════════════════════════════════════
# ② 壁掛け機構 (汎用) の中核ブロック
# ═══════════════════════════════════════════════════════════════════
HANG_CORE = u'''
// ═══ ★v7.4 壁掛け機構 (汎用) ═══
//   「壁面に貼り付けて掛けられる」アイテムの共通機構。カレンダー専用ではなく、
//   ポスター / 壁掛け時計 / 鏡 なども WALL_HANG_TYPES に type を足すだけで同じ挙動になる
//   (TOP_STACK_TYPES / SOLID_FIX_TYPES と同じレジストリ流儀)。
//   ・壁面は ROOM_DATA.walls を正とする。walls は 開口 (ドア・窓) で既に分割済みなので、
//     「区画の from..to に収まるか」だけ見れば **建具の上には載らない**。
//   ・walls の c = 室内側の壁面 / outSign = 室外向き → 室内は -outSign 方向。
//   ・保存フィールド: wallId (掛かっている壁区画 id / null) と hangH (床〜アイテム上端 cm / null=既定)。
const WALL_HANG_TYPES = { calendar: 1 };
const WALLHANG = {
  reach: 30,        // ドラッグ中に壁が背面を掴む距離 (背面〜壁面 cm)
  hold: 45,         // 掛かった後に外れる距離 (ヒステリシス。mountTargetFor と同じ流儀)
  behind: 25,       // 背面が壁を越えて外側にある時でも掴む余裕
  gap: 0.3,         // 壁面と背面のすきま
  topDef: 175,      // 既定の上端高さ (床から)
  topMin: 100, topMax: 235, topStep: 1,
  ceilClr: 5        // 天井とのクリアランス (上端の上限 = 壁高 − 5 → 240壁なら235)
};
function isWallHangItem(it) { return !!WALL_HANG_TYPES[itemTypeOf(it)]; }
function isHungItem(it) { return !!(it && it.wallId && isWallHangItem(it)); }
// 現在の部屋の壁区画 (ROOM_DATA.walls をそのまま使う)
function roomWallSegs() {
  const dk = dataKeyOf(currentRoom);
  if (!dk) return [];
  return (R.walls || []).filter(function (wl) { return wl.room === dk && (wl.height || 0) >= 100; });
}
function wallSegById(id) {
  if (!id) return null;
  const a = roomWallSegs();
  for (let i = 0; i < a.length; i++) if (a[i].id === id) return a[i];
  return null;
}
function wallInSign(wl) { return -(wl.outSign || 1); }   // 室内向き (outSign は室外向き)
// 室内を向く rotY [度]。mesh は m.rotation.y = -(rotY*PI/180) なので ローカル +z が正面
function wallFaceRotY(wl) {
  return wl.horiz ? (wl.outSign < 0 ? 0 : 180) : (wl.outSign > 0 ? 90 : 270);
}
// 掛ける高さ (床〜アイテム上端 cm)。null=既定175。天井・床でクランプ
function hangTopH(it, wl) {
  const h = Math.max(Number(it && it.h) || 1, 1);
  const v = Number(it && it.hangH);
  const hi = Math.min(WALLHANG.topMax, ((wl && wl.height) || CH) - WALLHANG.ceilClr);
  const lo = Math.min(Math.max(WALLHANG.topMin, h), hi);   // 床にめり込まない
  const raw = isFinite(v) && v > 0 ? v : WALLHANG.topDef;
  return Math.round(Math.min(Math.max(raw, lo), hi) * 10) / 10;
}
// 壁区画に掛けた時の姿勢。along = 壁に沿った位置 (horiz なら x / vert なら z)
function wallHangPose(it, wl, along) {
  const w = Math.max(Number(it.w) || 1, 1), d = Math.max(Number(it.d) || 1, 0.4);
  const lo = wl.from + w / 2, hi = wl.to - w / 2;
  const a = Math.round(Math.min(Math.max(along, Math.min(lo, hi)), Math.max(lo, hi)) * 10) / 10;
  const off = Math.round((wl.c + wallInSign(wl) * (d / 2 + WALLHANG.gap)) * 10) / 10;
  const top = hangTopH(it, wl);
  return { x: wl.horiz ? a : off, z: wl.horiz ? off : a,
           y: Math.round((top - Math.max(Number(it.h) || 1, 1)) * 10) / 10,
           rotY: wallFaceRotY(wl), top: top, fits: (wl.to - wl.from) >= w - 0.5 };
}
function applyHangPose(it, wl, along) {
  const p = wallHangPose(it, wl,
    (along === undefined || along === null) ? (wl.horiz ? it.x : it.z) : along);
  it.wallId = wl.id; it.x = p.x; it.z = p.z; it.y = p.y; it.rotY = p.rotY;
  return p;
}
function clearHangPose(it) { it.wallId = null; it.y = 0; }
// ドラッグ中に吸着すべき壁区画 (背面が一番近いもの)。無ければ null。mountTargetFor と同じ流儀
function wallHangTargetFor(it) {
  if (!isWallHangItem(it)) return null;
  const w = Math.max(Number(it.w) || 1, 1), d = Math.max(Number(it.d) || 1, 0.4);
  let best = null, bestGap = 1e9;
  roomWallSegs().forEach(function (wl) {
    if ((wl.to - wl.from) < w - 0.5) return;              // 区画が家具より短い = 掛けられない
    const ctr = wl.horiz ? it.z : it.x;                   // 壁法線方向の中心座標
    const along = wl.horiz ? it.x : it.z;                 // 壁に沿った方向の中心座標
    const gap = (ctr - wl.c) * wallInSign(wl) - d / 2;    // 背面〜壁面 (室内側が +)
    const rad = (it.wallId === wl.id) ? WALLHANG.hold : WALLHANG.reach;
    if (gap > rad || gap < -WALLHANG.behind) return;
    if (along < wl.from - w / 2 || along > wl.to + w / 2) return;
    if (gap < bestGap) { bestGap = gap; best = { wall: wl, along: along, gap: gap }; }
  });
  return best;
}
// 壁から外して床へ戻す (モニターアームの dropOffArm と同じ思想)
function dropOffWall(id, it) {
  clearHangPose(it);
  clampItem(it);
  if (blockedAny(id, it)) findFreeSpot(id, it);
  const m = furnMeshes[id];
  if (m) syncItemMesh(m, it);
}
// 保存済みの wallId / hangH から姿勢を組み直す (rebuildFurniture の後。syncMounts と同じ役割)
function syncHangs() {
  Object.keys(workItems).forEach(function (id) {
    const it = workItems[id];
    if (!it.wallId || !isWallHangItem(it)) return;
    const wl = wallSegById(it.wallId);
    if (!wl) { dropOffWall(id, it); return; }             // 壁が見つからない (部屋違い等) → 床へ
    applyHangPose(it, wl, wl.horiz ? it.x : it.z);
    const m = furnMeshes[id];
    if (m) syncItemMesh(m, it);
  });
}
// ドラッグ確定時の 掛けた/外した トースト (was = ドラッグ開始時の wallId or null)
function reportHangChange(id, it, was) {
  const now = isHungItem(it) ? it.wallId : null;
  if (now === was) return;
  if (now) {
    const wl = wallSegById(now), top = hangTopH(it, wl);
    toast('🖼 「' + (wl ? (wl.name || wl.id) : '壁') + '」に掛けました (上端 ' + top +
          'cm / 下端 ' + (Math.round((top - (Number(it.h) || 0)) * 10) / 10) + 'cm)');
  } else {
    toast('壁から外しました (床置きに戻しました)');
  }
}

'''

edit(u'JS: 壁掛け機構の中核ブロックを新設 (WALL_HANG_TYPES / WALLHANG / 判定・姿勢・同期)',
     u"// ★v1.9 デスク載せスナップ: XZ で重なる他アイテムのうち、自分以上の footprint を持つものの最高天面。",
     HANG_CORE.lstrip('\n') +
     u"// ★v1.9 デスク載せスナップ: XZ で重なる他アイテムのうち、自分以上の footprint を持つものの最高天面。",
     u'const WALL_HANG_TYPES')


# ③ cleanItem に保存フィールド追加
edit(u'JS: cleanItem に wallId / hangH を追加 (保存フィールド)',
     u"""    insideOf: it.insideOf || null,""",
     u"""    // ★v7.4 壁掛け: wallId=掛かっている壁区画の id (ROOM_DATA.walls) / hangH=床〜アイテム上端 cm (null=既定175)
    wallId: it.wallId || null,
    hangH: (it.hangH === undefined || it.hangH === null || it.hangH === '') ? null : Number(it.hangH),
    insideOf: it.insideOf || null,""",
     u'wallId: it.wallId || null,')


# ④ resolveDragPos に壁掛けブロック
edit(u'JS: resolveDragPos に 壁掛け吸着/解除 を追加',
     u"""  // ★v6.2 ゴミ箱 × キッチンボード/レンジボードの オープン部:""",
     u"""  // ★v7.4 壁掛け (汎用): 背面が壁面から reach (30cm) 以内 かつ その壁区画の from..to に収まるなら、
  //   背面を壁にぴったり (すきま 0.3cm) 付け、rotY を室内向きへ自動で合わせて掛ける。
  //   壁から離すと解除され、通常の床置きに戻る (モニターアームの dropOffArm と同じ思想)。
  if (isWallHangItem(it)) {
    const wt = wallHangTargetFor(it);
    if (wt) {
      applyHangPose(it, wt.wall, wt.along);
      drag.vx = it.x; drag.vz = it.z; drag.vy = it.y;
      return;                                    // 壁の上なので 部屋ポリゴン/設備/家具の判定は不要
    }
    if (it.wallId) {
      clearHangPose(it);                         // 壁から離れた → 床置きへ
      drag.ig = overlapState(drag.itemId, it);   // 解除直後に生じた重なりは分離まで免除
    }
  }
  // ★v6.2 ゴミ箱 × キッチンボード/レンジボードの オープン部:""",
     u'if (isWallHangItem(it)) {\n    const wt = wallHangTargetFor(it);')


# ⑤ beginDrag: 壁掛け中は掴んだ瞬間に落とさない / autoY / wasHung
edit(u'JS: beginDrag が 壁掛け中のアイテムを床へ落とさないように',
     u"""  if (!TOP_STACK_TYPES[itemTypeOf(it)] && !isMattressItem(it) && (Number(it.y) || 0) !== 0 && !onPan0) {""",
     u"""  if (!TOP_STACK_TYPES[itemTypeOf(it)] && !isMattressItem(it) && (Number(it.y) || 0) !== 0 && !onPan0 &&
      !isHungItem(it)) {   // ★v7.4 壁に掛かっている物は「浮いている」ではない""",
     u'!isHungItem(it)) {   // ★v7.4 壁に掛かっている物は')

edit(u'JS: beginDrag に wasHung (壁掛けの変化報告用) と autoY 追加',
     u"""           wasMounted: isMountedItem(it) ? it.mountArm : null,   // ★v4.1 マウント状態の変化をドラッグ確定時に報告""",
     u"""           wasMounted: isMountedItem(it) ? it.mountArm : null,   // ★v4.1 マウント状態の変化をドラッグ確定時に報告
           wasHung: it.wallId || null,          // ★v7.4 壁掛けの変化をドラッグ確定時に報告""",
     u'wasHung: it.wallId || null,')

edit(u'JS: beginDrag の autoY に 壁掛け解除を追加',
     u"""           autoY: isMountedItem(it) || y0 === 0 ||   // ★v4.1 アームから外したら床/天面へ落とす""",
     u"""           autoY: isMountedItem(it) || isHungItem(it) || y0 === 0 ||   // ★v4.1 アームから外したら床/天面へ落とす ★v7.4 壁から外したら床へ""",
     u'isMountedItem(it) || isHungItem(it) || y0 === 0')


# ⑥ finishDrag に報告
edit(u'JS: finishDrag に 壁掛け イン/アウト トーストを追加',
     u"""    if (dit && isTrashItem(dit)) reportCavityChange(drag, dit);   // ★v6.2 収納スペース イン/アウト トースト""",
     u"""    if (dit && isWallHangItem(dit)) reportHangChange(drag.itemId, dit, drag.wasHung);   // ★v7.4 壁掛け イン/アウト トースト
    if (dit && isTrashItem(dit)) reportCavityChange(drag, dit);   // ★v6.2 収納スペース イン/アウト トースト""",
     u'reportHangChange(drag.itemId, dit, drag.wasHung)')


# ⑦ pairCollides / supportCandidates
edit(u'JS: pairCollides — 壁に掛かっている物は床置き家具の配置を邪魔しない',
     u"""  // ★v6.2 収納のオープン部に収まっているアイテムは、その収納との衝突判定から外す (中に入っているため)""",
     u"""  // ★v7.4 壁に掛かっている物は「壁面の飾り」扱い。床置き家具の配置を邪魔しない (マウント中モニターと同じ)
  if (isHungItem(it) || isHungItem(ot)) return false;
  // ★v6.2 収納のオープン部に収まっているアイテムは、その収納との衝突判定から外す (中に入っているため)""",
     u'if (isHungItem(it) || isHungItem(ot)) return false;')

edit(u'JS: supportCandidates — 壁掛け中は天面スナップの対象外',
     u"""function supportCandidates(selfId, it) {
  if (isMountedItem(it)) return [];""",
     u"""function supportCandidates(selfId, it) {
  if (isMountedItem(it)) return [];
  if (isHungItem(it)) return [];                       // ★v7.4 壁に掛かっている間は天面に載らない""",
     u'if (isHungItem(it)) return [];                       // ★v7.4')


# ⑧ rebuildFurniture で復元
edit(u'JS: rebuildFurniture で 保存済みの壁掛けを復元 (syncHangs)',
     u"""    syncMounts();   // ★v4.1 保存済みのマウント状態をアーム先端の実座標へ合わせ直す (アーム欠落時は床へ)""",
     u"""    syncMounts();   // ★v4.1 保存済みのマウント状態をアーム先端の実座標へ合わせ直す (アーム欠落時は床へ)
    syncHangs();    // ★v7.4 保存済みの壁掛け (wallId / hangH) を壁面の実座標へ合わせ直す (壁欠落時は床へ)""",
     u'syncHangs();    // ★v7.4')


# ⑨ rotateItem のガード
edit(u'JS: rotateItem — 壁掛け中は向きが壁で決まる',
     u"""  if (isMountedItem(it)) { toast(isTvItem(it) ? '取付中はテレビスタンド側を回転してください (テレビは追従します)' : 'マウント中はアーム側を回転してください (モニターは追従します)'); return; }   // ★v4.1 / ★v6.5""",
     u"""  if (isMountedItem(it)) { toast(isTvItem(it) ? '取付中はテレビスタンド側を回転してください (テレビは追従します)' : 'マウント中はアーム側を回転してください (モニターは追従します)'); return; }   // ★v4.1 / ★v6.5
  if (isHungItem(it)) { toast('壁掛け中は向きが壁で決まります (壁から外すと回せます)'); return; }   // ★v7.4""",
     u"'壁掛け中は向きが壁で決まります (壁から外すと回せます)'")


# ⑩ 家具シート: 高さスライダー
HANG_BLOCK = u"""  // ★v7.4 壁掛け: 掛ける高さ (床〜アイテム上端) のスライダー。
  //        テレビスタンドの TV取付高さ (standH) / 可動棚 (shelfH) と同じ作り・同じ見た目に揃える。
  let hangBlock = '';
  if (isHungItem(it)) {
    const hw = wallSegById(it.wallId), top0 = hangTopH(it, hw);
    const hiH = Math.min(WALLHANG.topMax, ((hw && hw.height) || CH) - WALLHANG.ceilClr);
    const loH = Math.min(Math.max(WALLHANG.topMin, Math.max(Number(it.h) || 1, 1)), hiH);
    hangBlock =
      '<div class="form-group"><label class="form-label">掛ける高さ (床〜上端): ' +
      '<b id="hangVal">' + top0 + '</b> cm</label>' +
      '<input class="form-input" type="range" min="' + loH + '" max="' + hiH + '" step="' + WALLHANG.topStep + '" ' +
      'value="' + top0 + '" oninput="setHangH(this.value, true)" onchange="setHangH(this.value)" ' +
      'aria-label="掛ける高さ" style="padding:0;">' +
      '<div class="floorh-seg" style="margin-top:6px;">' +
      '<button class="floorh-btn" onclick="nudgeHangH(-5)">− 5cm</button>' +
      '<button class="floorh-btn" onclick="setHangH(' + WALLHANG.topDef + ')">既定 ' + WALLHANG.topDef + 'cm</button>' +
      '<button class="floorh-btn" onclick="nudgeHangH(5)">＋ 5cm</button>' +
      '</div>' +
      '<div class="dim-note">🖼 「' + esc(hw ? (hw.name || hw.id) : '壁') + '」に掛かっています ' +
      '(下端 ' + (Math.round((top0 - (Number(it.h) || 0)) * 10) / 10) + 'cm / 壁とのすきま ' + WALLHANG.gap + 'cm)。' +
      '壁に沿ってドラッグ・矢印キーで左右に動かせます / 壁から ' + WALLHANG.hold +
      'cm 以上 離すと床置きに戻ります</div>' +
      '<button class="btn-secondary" style="width:100%;margin-top:6px;" onclick="unhangItem()">⤓ 壁から外す (床に置く)</button></div>';
  } else if (isWallHangItem(it)) {
    hangBlock =
      '<div class="form-group"><label class="form-label">壁掛け</label>' +
      '<div class="dim-note">🖼 壁へドラッグして 背面が壁から ' + WALLHANG.reach +
      'cm 以内に入ると 壁に掛かります (上端 既定 ' + WALLHANG.topDef +
      'cm。掛かると高さスライダーが出ます)。ドア・窓の上には掛かりません</div></div>';
  }
"""
edit(u'JS: 家具シートに 壁掛けブロック (高さスライダー + 壁から外す) を追加',
     u"""  // ★v4.1 モニター: アームへのマウント状態表示 + 解除ボタン
  let mountBlock = '';""",
     HANG_BLOCK + u"""  // ★v4.1 モニター: アームへのマウント状態表示 + 解除ボタン
  let mountBlock = '';""",
     u"let hangBlock = '';")

edit(u'JS: 家具シート innerHTML に hangBlock を差し込み',
     u"""    colorBlock + floorHBlock + mattressBlock + vesaBlock + mountBlock + insideBlock + levelBlock +""",
     u"""    colorBlock + floorHBlock + mattressBlock + vesaBlock + hangBlock + mountBlock + insideBlock + levelBlock +""",
     u'vesaBlock + hangBlock + mountBlock')


# ⑪ setHangH / nudgeHangH / unhangItem
HANG_SETTERS = u"""// ★v7.4 壁掛けの高さ (床〜アイテム上端 cm)。天井・床でクランプ (クランプは hangTopH に一本化)。
//        live=true (スライダー操作中) は数値ラベルだけ更新して DOM は組み直さない (つまみが飛ぶため)
window.setHangH = function (v, live) {
  const it = workItems[selectedItemId];
  if (!it || !isHungItem(it)) return;
  const wl = wallSegById(it.wallId);
  it.hangH = Number(v) || WALLHANG.topDef;
  it.hangH = hangTopH(it, wl);
  if (wl) applyHangPose(it, wl, wl.horiz ? it.x : it.z);
  const m = furnMeshes[selectedItemId];
  if (m) syncItemMesh(m, it);
  markDirty();
  const lab = document.getElementById('hangVal');
  if (lab) lab.textContent = it.hangH;
  if (!live) toast('掛ける高さ (上端) を ' + it.hangH + 'cm にしました (下端 ' +
                   (Math.round((it.hangH - (Number(it.h) || 0)) * 10) / 10) + 'cm)');
};
window.nudgeHangH = function (dv) {
  const it = workItems[selectedItemId];
  if (!it || !isHungItem(it)) return;
  window.setHangH(hangTopH(it, wallSegById(it.wallId)) + Number(dv));
  openItemSheet();                       // スライダーのつまみ位置を反映
};
// ★v7.4 壁から外して床へ (アームの unmountMonitor と同じ導線)
window.unhangItem = function () {
  const it = workItems[selectedItemId];
  if (!it || !isHungItem(it)) return;
  dropOffWall(selectedItemId, it);
  markDirty();
  openItemSheet();
  toast('壁から外しました (床置きに戻しました)');
};
"""
edit(u'JS: setHangH / nudgeHangH / unhangItem を追加',
     u"""window.nudgeVesaH = function (d) {""",
     HANG_SETTERS + u"""window.nudgeVesaH = function (d) {""",
     u'window.setHangH = function (v, live) {')


# ⑫ ツールチップ (itemDimSummaryHtml) に合流
edit(u'JS: ツールチップ (itemDimSummaryHtml) に 壁掛け行を追加',
     u"""    rows.push('収納: 「' + (cav ? cav.label : (host.name || '収納')) + '」の中');
  }
  if (isMountedItem(it)) {""",
     u"""    rows.push('収納: 「' + (cav ? cav.label : (host.name || '収納')) + '」の中');
  }
  if (isHungItem(it)) {   // ★v7.4 壁掛け: 掛かっている壁の名前 + 上端/下端の高さ
    const hw = wallSegById(it.wallId);
    rows.push('壁掛け: 「' + (hw ? (hw.name || hw.id) : '壁') + '」' + (hw ? ' [' + hw.id + ']' : '') +
              ' / 上端 ' + tipN(y + h) + 'cm ・ 下端 ' + tipN(y) + 'cm (壁とのすきま ' + WALLHANG.gap + 'cm)');
  }
  if (isMountedItem(it)) {""",
     u"rows.push('壁掛け: 「'")


# ⑬ updItem の y は 壁掛け中は hangH へ
edit(u'JS: updItem の「床からの高さ」は 壁掛け中は hangH (上端) へ橋渡し',
     u"""  } else if (field === 'y') {
    it.y = Math.max(Number(val) || 0, 0);""",
     u"""  } else if (field === 'y') {
    // ★v7.4 壁掛け中の高さは hangH (床〜上端) が正。床からの高さ入力は上端へ換算して橋渡しする
    if (isHungItem(it)) { window.setHangH((Number(val) || 0) + (Number(it.h) || 0)); return; }
    it.y = Math.max(Number(val) || 0, 0);""",
     u'if (isHungItem(it)) { window.setHangH((Number(val) || 0) + (Number(it.h) || 0)); return; }')


# ⑭ キーボード: 壁に沿ってスライド
edit(u'JS: 矢印キーで 壁掛け中のアイテムを壁に沿ってスライド',
     u"""  const step = e.shiftKey ? 10 : 1;
  let used = true;""",
     u"""  // ★v7.4 壁掛け中の矢印キー: 壁に沿ってスライド (壁からは外れない)
  if (isHungItem(it) && /^Arrow/.test(e.key)) {
    e.preventDefault();
    const hw = wallSegById(it.wallId);
    if (!hw) return;
    const hs = e.shiftKey ? 10 : 1;
    const hdx = (e.key === 'ArrowLeft' ? -hs : e.key === 'ArrowRight' ? hs : 0);
    const hdz = (e.key === 'ArrowUp' ? -hs : e.key === 'ArrowDown' ? hs : 0);
    applyHangPose(it, hw, hw.horiz ? it.x + hdx : it.z + hdz);
    const hm = furnMeshes[selectedItemId];
    if (hm) syncItemMesh(hm, it);
    markDirty();
    return;
  }
  const step = e.shiftKey ? 10 : 1;
  let used = true;""",
     u'if (isHungItem(it) && /^Arrow/.test(e.key)) {')


# ⑮ デバッグフック
DEBUG_HOOKS = u"""      // ★v7.4 壁掛けの検証フック (壁区画一覧 / 掛かっている物 / 高さ操作 / 取り外し)
      walls: function () {
        return roomWallSegs().map(function (wl) {
          return { id: wl.id, name: wl.name, dir: wl.dir, horiz: !!wl.horiz, c: wl.c,
                   from: wl.from, to: wl.to, length: wl.length, outSign: wl.outSign,
                   faceRotY: wallFaceRotY(wl) };
        });
      },
      hangs: function () {
        return Object.keys(workItems).filter(function (k) { return isWallHangItem(workItems[k]); })
          .map(function (k) {
            const it = workItems[k], wl = wallSegById(it.wallId);
            return { id: k, name: it.name, hung: isHungItem(it),
                     wallId: it.wallId || null, wallName: wl ? wl.name : null,
                     x: it.x, y: it.y, z: it.z, rotY: it.rotY || 0,
                     top: Math.round(((Number(it.y) || 0) + (Number(it.h) || 0)) * 10) / 10,
                     hangH: (it.hangH === undefined || it.hangH === null) ? null : Number(it.hangH),
                     aabb: itemAabb(it) };
          });
      },
      hangh: function (id, v) {
        const prev = selectedItemId;
        selectedItemId = id;
        window.setHangH(v);
        selectedItemId = prev;
        const it = workItems[id];
        return { hangH: it.hangH, y: it.y, top: Math.round((it.y + it.h) * 10) / 10 };
      },
      unhang: function (id) {
        const prev = selectedItemId;
        selectedItemId = id;
        window.unhangItem();
        selectedItemId = prev;
        return { wallId: workItems[id].wallId || null, y: workItems[id].y };
      },
"""
edit(u'JS: __noza に 壁掛け検証フック (walls / hangs / hangh / unhang) を追加',
     u"""      // ★v6.5 テレビスタンド / テレビ の検証フック
      stands: function () {""",
     DEBUG_HOOKS + u"""      // ★v6.5 テレビスタンド / テレビ の検証フック
      stands: function () {""",
     u'// ★v7.4 壁掛けの検証フック')


# ═══════════════════════════════════════════════════════════════════
# ⑯ カレンダー紙面テクスチャ + buildItemParts の calendar 分岐
# ═══════════════════════════════════════════════════════════════════
CAL_TEX = u'''// ═══ ★v7.4 壁掛けカレンダー (新日本カレンダー NK163 / A2「THE・文字」) の紙面テクスチャ ═══
//   実物 (Amazon 商品画像) の紙面構成を CanvasTexture 1枚に描いて板に貼る。
//   メッシュを増やさない (モバイル負荷を上げない) ため、月表・曜日帯・日付グリッド・六曜は全部 2D 描画。
//   六曜 = (旧暦月 + 旧暦日) mod 6 → 大安/赤口/先勝/友引/先負/仏滅 の標準式。
//   旧暦の朔日は 国立天文台 暦要項 (旧暦11/1=2025-12-20 / 12/1=2026-01-19 / 正月1日=2026-02-17)。
//   2026年1月の全31日を 便利ジャパン・ゼクシィの公表値と突合して一致を確認済み
//   (1/18 仏滅 → 1/19 赤口 の朔日リセットも再現される)。
const CAL_ROKU = ['大安', '赤口', '先勝', '友引', '先負', '仏滅'];
const CAL_LUNAR_NEW = [                     // 旧暦 月初 (朔) [西暦年, 月, 日, 旧暦月]
  [2025, 12, 20, 11], [2026, 1, 19, 12], [2026, 2, 17, 1], [2026, 3, 19, 2]
];
const CAL_MONTH_EN = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
  'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'];
const CAL_FONT = '"Yu Gothic UI","Yu Gothic","Meiryo","Hiragino Kaku Gothic ProN",sans-serif';
function calRokuyou(y, m, d) {
  const t = Date.UTC(y, m - 1, d);
  let at = null, lm = 0;
  CAL_LUNAR_NEW.forEach(function (n) {
    const nt = Date.UTC(n[0], n[1] - 1, n[2]);
    if (nt <= t && (at === null || nt > at)) { at = nt; lm = n[3]; }
  });
  if (at === null) return '';
  return CAL_ROKU[(lm + Math.round((t - at) / 86400000) + 1) % 6];
}
const calTexCache = {};
function calendarPaperTexture(year, month) {
  const key = year + '-' + month;
  if (calTexCache[key]) return calTexCache[key];
  const W = 512, H = 735;                   // 紙面 425 × 610mm の比率 (0.6967)
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const c = cv.getContext('2d');
  const RED = '#c8102e', BLU = '#0d5bb5', BLK = '#1a1a1a';
  c.fillStyle = '#ffffff'; c.fillRect(0, 0, W, H);
  // 上端中央の吊り下げ穴 (⚠公式に吊り具・穴の記載は無い → 一般的な壁掛けカレンダーの表現)
  c.beginPath(); c.arc(W / 2, 26, 9, 0, Math.PI * 2);
  c.fillStyle = '#eceae6'; c.fill();
  c.lineWidth = 1.5; c.strokeStyle = '#b3b0aa'; c.stroke();
  c.beginPath(); c.arc(W / 2, 26, 5.5, 0, Math.PI * 2);
  c.fillStyle = '#6f6f72'; c.fill();
  // 前月 / 翌月 の小カレンダー (黒 + 日曜赤 / 土曜青)
  const mini = function (x0, y0, ww, yy, mm) {
    const first = new Date(yy, mm - 1, 1).getDay(), dim = new Date(yy, mm, 0).getDate();
    const cw = ww / 7, ch = 11;
    c.textAlign = 'center'; c.textBaseline = 'middle';
    c.font = 'bold 12px ' + CAL_FONT; c.fillStyle = '#444';
    c.fillText(mm + '月', x0 + ww / 2, y0 - 8);
    c.font = '8px ' + CAL_FONT;
    for (let i = 0; i < 7; i++) {
      c.fillStyle = i === 0 ? RED : (i === 6 ? BLU : '#666');
      c.fillText('SMTWTFS'.charAt(i), x0 + cw * (i + 0.5), y0 + ch * 0.5);
    }
    c.font = '9px ' + CAL_FONT;
    for (let dd = 1; dd <= dim; dd++) {
      const idx = first + dd - 1, col = idx % 7, row = Math.floor(idx / 7) + 1;
      c.fillStyle = col === 0 ? RED : (col === 6 ? BLU : BLK);
      c.fillText(String(dd), x0 + cw * (col + 0.5), y0 + ch * (row + 0.5));
    }
  };
  const pm = month === 1 ? 12 : month - 1, py = month === 1 ? year - 1 : year;
  const nm = month === 12 ? 1 : month + 1, ny = month === 12 ? year + 1 : year;
  mini(22, 66, 96, py, pm);
  mini(394, 66, 96, ny, nm);
  // 中央: 令和N年 / 西暦 / 英語月名
  c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillStyle = '#444'; c.font = 'bold 15px ' + CAL_FONT;
  c.fillText('令和' + (year - 2018) + '年', 190, 66);
  c.fillStyle = BLK; c.font = 'bold 30px ' + CAL_FONT;
  c.fillText(String(year), 190, 96);
  c.fillStyle = '#666'; c.font = 'bold 12px ' + CAL_FONT;
  c.fillText(CAL_MONTH_EN[month - 1], 190, 122);
  // 大きな赤い月数字
  c.fillStyle = RED; c.font = 'bold 104px ' + CAL_FONT;
  c.fillText(String(month), 305, 100);
  // 曜日ヘッダ帯 (日=赤地 / 月〜金=黒地 / 土=青地、いずれも白抜き)
  const gx0 = 18, gx1 = W - 18, gw = (gx1 - gx0) / 7, hy = 168, hh = 30;
  const JA = ['日', '月', '火', '水', '木', '金', '土'];
  for (let i = 0; i < 7; i++) {
    c.fillStyle = i === 0 ? RED : (i === 6 ? BLU : '#1c1c1e');
    c.fillRect(gx0 + gw * i + 0.8, hy, gw - 1.6, hh);
    c.fillStyle = '#ffffff'; c.font = 'bold 17px ' + CAL_FONT;
    c.fillText(JA[i], gx0 + gw * (i + 0.5), hy + hh / 2 + 1);
  }
  // 日付グリッド (日曜=赤 / 土曜=青 / 平日=黒。各セルの下に六曜の小文字)
  const first = new Date(year, month - 1, 1).getDay(), dim = new Date(year, month, 0).getDate();
  const gy0 = hy + hh + 8, gy1 = H - 22, rowsN = Math.ceil((first + dim) / 7);
  const rh = (gy1 - gy0) / rowsN;
  c.strokeStyle = '#e2e0dc'; c.lineWidth = 1;
  for (let r0 = 1; r0 < rowsN; r0++) {
    c.beginPath(); c.moveTo(gx0, gy0 + rh * r0); c.lineTo(gx1, gy0 + rh * r0); c.stroke();
  }
  c.textBaseline = 'alphabetic';
  for (let dd = 1; dd <= dim; dd++) {
    const idx = first + dd - 1, col = idx % 7, row = Math.floor(idx / 7);
    const cx = gx0 + gw * (col + 0.5), cy = gy0 + rh * row;
    c.fillStyle = col === 0 ? RED : (col === 6 ? BLU : BLK);
    c.font = 'bold ' + Math.round(rh * 0.46) + 'px ' + CAL_FONT;
    c.fillText(String(dd), cx, cy + rh * 0.58);
    c.fillStyle = '#8d8a85';
    c.font = Math.round(rh * 0.18) + 'px ' + CAL_FONT;
    c.fillText(calRokuyou(year, month, dd), cx, cy + rh * 0.87);
  }
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  calTexCache[key] = tex;
  return tex;
}
'''
edit(u'JS: カレンダー紙面 CanvasTexture (六曜計算つき) を新設',
     u"""function buildItemParts(g, it) {""",
     CAL_TEX + u"""function buildItemParts(g, it) {""",
     u'function calendarPaperTexture(year, month) {')

CAL_BRANCH = u"""  } else if (type === 'calendar') {
    // ★v7.4 壁掛けカレンダー (新日本カレンダー NK163 / A2「THE・文字」 公式 610×425mm)。
    //   紙面は CanvasTexture 1枚を 板の正面 (ローカル +z) に貼るだけ = メッシュ 3個。
    //   壁に掛かっている時は 背面が壁に密着し、正面 (+z) が室内を向く (rotY は wallHangPose が決める)。
    //   ⚠ 厚み 0.5cm は est (公式に厚み・吊り具の記載なし。紙製本12枚からの推定)。
    const cd = Math.max(Number(it.d) || 0.5, 0.4);
    const paperT = Math.min(cd, 1.2);
    P(w, h, paperT, 0, h / 2, cd / 2 - paperT / 2, 0xf4f2ec);            // 紙の束 (表紙+12ヶ月)
    P(w * 0.92, h * 0.012, paperT + 0.15, 0, h - h * 0.006, cd / 2 - paperT / 2, 0xc9c7c2);   // 上部の綴じ (紙製本)
    const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
      new THREE.MeshLambertMaterial({ map: calendarPaperTexture(2026, 1) }));
    face.position.set(0, h / 2, cd / 2 + 0.02);
    g.add(face);
  } else {
    // その他/自由サイズ: 従来の単純ボックス + エッジ"""
edit(u"JS: buildItemParts に type 'calendar' 分岐 (紙面テクスチャを板に貼る)",
     u"""  } else {
    // その他/自由サイズ: 従来の単純ボックス + エッジ""",
     CAL_BRANCH,
     u"} else if (type === 'calendar') {")


# ═══════════════════════════════════════════════════════════════════
# 書き出し + 検証
# ═══════════════════════════════════════════════════════════════════
if problems:
    print(u'\n════ 失敗 %d 件 — 書き込みを中止 ════' % len(problems))
    sys.exit(1)

if src == orig:
    print(u'\n════ 適用0件 / skip %d件 (既に適用済み。room.html は変更なし) ════' % len(skipped))
    sys.exit(0)

# 安全装置: ROOM_DATA は不変 / CATALOG_SEED は変わる
room_after = hashlib.sha256(room_block(src).encode('utf-8')).hexdigest()
seed_after_raw = seed_block(src)
seed_after = hashlib.sha256(seed_after_raw.encode('utf-8')).hexdigest()
assert room_after == ROOM_SHA_BEFORE, \
    u'ROOM_DATA の sha256 が変わった (%s → %s) — 今回は触らないはず' % (ROOM_SHA_BEFORE[:12], room_after[:12])
assert seed_after != CATALOG_SHA_BEFORE, u'CATALOG_SEED が変わっていない'
seed_obj_after = json.loads(seed_after_raw)
assert seed_obj_after['version'] == '2.2', u'CATALOG_SEED version が 2.2 でない'
assert len(seed_obj_after['items']) == 32, u'商品数が 32 でない: %d' % len(seed_obj_after['items'])
cal = [x for x in seed_obj_after['items'] if x.get('model') == 'NK163']
assert len(cal) == 1 and cal[0]['memo'] == '' and cal[0]['w'] == 42.5 and cal[0]['h'] == 61 \
    and cal[0]['d'] == 0.5 and cal[0]['room'] == 'ldk' and cal[0]['type'] == 'calendar', \
    u'追加した商品の値が想定と違う'

io.open(TARGET, 'w', encoding='utf-8', newline='').write(src)

print(u'\n  ROOM_DATA    sha256 %s → %s  (不変 ✓)' % (ROOM_SHA_BEFORE[:12], room_after[:12]))
print(u'  CATALOG_SEED sha256 %s → %s  (変化 ✓)' % (CATALOG_SHA_BEFORE[:12], seed_after[:12]))
print(u'════ 適用 %d件 / skip %d件 ════' % (len(applied), len(skipped)))

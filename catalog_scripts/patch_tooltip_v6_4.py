# -*- coding: utf-8 -*-
"""
nozaROOM room.html ツールチップ寸法表示 v6.4 冪等パッチ

目的 (ユーザー要望):
  「各パーツのIDを押した際に長さや高さが分かるようにして。今は一部のものしか記載されてない」
  → 壁 (W-) だけでなく ドア (D-) / 窓 (WIN-) / 開口 (OP-) / 設備 (F-) / コンセント (C-) /
    エアコン (AC-) / 照明 (L-) / 配置した家具 の全種別で 寸法・高さ・位置 を出す。

冪等性:
  各パッチは「適用済みマーカー」を持ち、既に入っていれば skip する。
  再実行すると「適用 0 件 / skip N 件」になる。

不変アサート:
  ROOM_DATA (行 581 相当) と CATALOG_SEED (行 584 相当) の 1 行を sha256 で採り、
  パッチ前後で一致することを assert する (ジオメトリ・カタログには一切触れない)。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_tooltip_v6_4.py [--dry-run]
"""
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), 'room.html')

MARK = u'★v6.4'   # ★v6.4


# ───────────────────────── 不変アサート ─────────────────────────
def data_line_hashes(text):
    """ROOM_DATA / CATALOG_SEED の 1 行まるごとの sha256 を返す。"""
    out = {}
    for key in ('var ROOM_DATA = ', 'var CATALOG_SEED = '):
        lines = [ln for ln in text.split('\n') if ln.startswith(key)]
        assert len(lines) == 1, 'expected exactly 1 line starting with %r, got %d' % (key, len(lines))
        out[key.strip()] = hashlib.sha256(lines[0].encode('utf-8')).hexdigest()
    return out


# ───────────────────────── 追加コード本体 ─────────────────────────

# [P5] 新モジュール: 種別ごとの寸法行ビルダー + showTooltip 差し替え
TIP_MODULE = u'''
// ═══════ ★v6.4 ツールチップ 寸法表示 (全要素タイプで 長さ・高さを出す) ═══════
// 【要望】「各パーツのIDを押した際に長さや高さが分かるようにして。今は一部のものしか記載されてない」
//   - 数値は cm・小数第1位まで (整数なら整数表示)。ROOM_DATA に値があるものはそれを正とする。
//   - 行数が増えるので <br> 区切りの複数行にし、モバイル (375px) でも読める長さ (最大 6 行) に収める。
function tipN(v) {
  if (v === undefined || v === null || v === '') return null;
  const n = Math.round(Number(v) * 10) / 10;
  if (!isFinite(n)) return null;
  return (Math.abs(n - Math.round(n)) < 1e-9) ? String(Math.round(n)) : n.toFixed(1);
}
function tipRoomJa(key) { return NAME_ROOM_SHORT[key] || key || ''; }
function tipAxisRange(horiz, a, b) { return (horiz ? 'x' : 'y') + tipN(a) + '〜' + tipN(b) + 'cm'; }
function tipClean(s) { return String(s || '').split('★')[0].replace(/\\s+/g, ' ').trim(); }

// 開口 (ドア/窓/開口) が どの部屋の どの向きの壁に載っているか
function tipOpeningDir(o) {
  const r0 = openingRange(o);
  const ws = (ensureNameIndex().walls) || [];
  const w = ws.find(function (x) {
    return x.room === o.room && x.horiz === r0.horiz && Math.abs(x.c - r0.c) <= 12 &&
           Math.min(x.to, r0.b) - Math.max(x.from, r0.a) > -1.0;
  });
  if (w) return w.dir;
  const room = R.rooms.find(function (x) { return x.key === o.room; });   // 壁区画が無い場合 (固定設備面の建具等) の保険
  if (!room) return null;
  const mid = (r0.a + r0.b) / 2;
  const inNeg = pointInPoly(r0.horiz ? [mid, r0.c - 2] : [r0.c - 2, mid], room.poly);
  return r0.horiz ? (inNeg ? 'S' : 'N') : (inNeg ? 'E' : 'W');
}
function tipOpeningPos(o) {
  const r0 = openingRange(o), d = tipOpeningDir(o);
  return tipRoomJa(o.room) + (d ? ' ' + NAME_DIR_JA[d] + '側' : '') + ' / ' + tipAxisRange(r0.horiz, r0.a, r0.b);
}
// 建具の種類 (開き戸・両開き・片引き・引違い)
function tipDoorKind(o) {
  const lb = (o.label || '') + ' ' + (o.name || '');
  if (o.type === 'sliding') {
    if (o.panels >= 2 || o.bypass) {
      return '引違い戸 (' + (o.panels || 2) + '枚' +
             (o.panelW ? '・各' + tipN(o.panelW) + 'cm' : '') + ')';
    }
    return (o.outsetRail ? 'アウトセット' : '') + '片引き戸 (1枚)';
  }
  const leaves = o.leaves || (/両開き/.test(lb) ? 2 : 1);
  if (leaves >= 4) return '両開き扉 2組' + leaves + '枚';
  if (leaves === 2) return '両開き扉 (2枚)';
  if (/折戸/.test(lb)) return '折戸';
  return '開き戸 (1枚)';
}
// 開閉方向 (吊元・スライド方向)
function tipDoorMotion(o) {
  const D = NAME_DIR_JA;
  if (o.type === 'sliding') {
    if (o.panels >= 2 || o.bypass) return '開閉: 引違い (クリックしたパネル側が開く)';
    return '開閉: ' + (o.slideDir ? D[o.slideDir] + 'へスライド' : 'スライド (方向データなし)');
  }
  const r0 = openingRange(o), parts = [];
  let sw = o.swing ? D[o.swing] + '側へ開く' : null;
  if (!sw) {
    const m = /([^\\/(（、]{1,12})へ開く/.exec(o.label || '');
    if (m) sw = tipClean(m[1]) + 'へ開く';
  }
  if (sw) parts.push(sw);
  const he = (o.hinge === 'e') || /ヒンジ南/.test(o.label || '');
  const hs = (o.hinge === 's');
  if (he || hs) parts.push('吊元: ' + (he ? (r0.horiz ? '東' : '南') : (r0.horiz ? '西' : '北')) + '端');
  return parts.length ? ('開閉: ' + parts.join(' / ')) : null;
}
// 窓の種類
function tipWindowKind(o) {
  const lb = (o.label || '') + ' ' + (o.name || ''), k = [];
  if (/FIX|はめ殺し/i.test(lb)) k.push('FIX (はめ殺し)');
  if (/すべり出し/.test(lb)) k.push((/縦すべり出し/.test(lb) ? '縦' : '') + 'すべり出し窓');
  if (/掛け出し/.test(lb)) k.push('掛け出し窓');
  if (/掃き出し/.test(lb)) k.push('掃き出し窓');
  if (/腰窓/.test(lb)) k.push('腰窓');
  if (/引違い/.test(lb)) k.push('引違い');
  if (!k.length) {
    const s = Number(o.sillH) || 0;
    k.push(s < 5 ? '掃き出し窓' : (s >= 140 ? '高所窓' : '腰窓'));
  }
  return k.join('・');
}
// 設備の平面外形 (rect 優先、poly は外接矩形)
function tipFixBox(f) {
  if (f.rect) return { x0: f.rect[0], y0: f.rect[1], w: f.rect[2], d: f.rect[3] };
  if (f.poly && f.poly.length) {
    const xs = f.poly.map(function (p) { return p[0]; }), ys = f.poly.map(function (p) { return p[1]; });
    const x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    const y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    return { x0: x0, y0: y0, w: x1 - x0, d: y1 - y0, poly: true };
  }
  return null;
}
// 設備の内寸 (ROOM_DATA に内寸フィールドは無いので、アプリ側が持つ実測内寸を使う)
function tipFixInner(f) {
  if (f.type === 'washer_pan' && typeof WASHER_PAN !== 'undefined') {
    return '内寸: ' + tipN(WASHER_PAN.inner[2]) + ' × ' + tipN(WASHER_PAN.inner[3]) +
           'cm (パン上面→洗濯水栓 ' + tipN(WASHER_PAN.faucetClr) + 'cm)';
  }
  return null;
}

// 要素の種別ごとに ツールチップ本文の行を組み立てる (プレーンテキストの配列)
function tipRows(a, ud) {
  const rows = [], D = NAME_DIR_JA;
  if (!a) return rows;
  // ── 壁 W- (現状維持: 区間・長さ・高さ・目印)
  if (a.kind === 'wall' && a.wall) {
    const w = a.wall;
    rows.push('区間: ' + tipAxisRange(w.horiz, w.from, w.to));
    rows.push('長さ: ' + tipN(w.length) + 'cm / 高さ: ' + tipN(w.height) + 'cm');
    rows.push('位置: ' + tipRoomJa(w.room) + ' ' + (D[w.dir] || '') + '側');
    if (w.feature) rows.push('目印: ' + w.feature);
    return rows;
  }
  const o = a.src;
  if (!o) return rows;
  // ── 開口 D- / WIN- / OP-
  if (a.kind === 'opening') {
    const sill = Number(o.sillH) || 0, hh = Number(o.height) || 0;
    if (o.type === 'window') {
      rows.push('幅: ' + tipN(o.width) + 'cm / 高さ: ' + tipN(hh) + 'cm');
      rows.push('床から: 下端 ' + tipN(sill) + 'cm 〜 上端 ' + tipN(sill + hh) + 'cm');
      rows.push('種類: ' + tipWindowKind(o));
      rows.push('位置: ' + tipOpeningPos(o));
    } else if (o.type === 'open') {
      rows.push('開口幅: ' + tipN(o.width) + 'cm / 高さ: ' + tipN(hh) + 'cm');
      if (sill > 0.05) rows.push('床から: ' + tipN(sill) + 'cm 上げた位置から');
      rows.push('用途: ' + (a.name || '開口') + ' (建具なしの通り抜け)');
      rows.push('位置: ' + tipOpeningPos(o));
    } else {
      rows.push('開口幅: ' + tipN(o.width) + 'cm / 高さ: ' + tipN(hh) + 'cm');
      rows.push('種類: ' + tipDoorKind(o));
      const mo = tipDoorMotion(o);
      if (mo) rows.push(mo);
      rows.push('ペットくぐり戸: ' + (o.petDoor ? 'あり' : 'なし'));
      rows.push('位置: ' + tipOpeningPos(o));
    }
    if (o.est) rows.push('※ 寸法は推定値');
    return rows;
  }
  // ── 設備 F-
  if (a.kind === 'fixture') {
    const st = (typeof FIX_STYLE !== 'undefined' && FIX_STYLE[o.type]) || null;
    const topH = Number(o.h) || (st && st.h) || 0;
    const botH = Number(o.bottomH) || 0;
    const bx = tipFixBox(o);
    if (bx) {
      rows.push('幅W ' + tipN(bx.w) + ' × 奥行D ' + tipN(bx.d) +
                ' × 高さH ' + tipN(Math.max(topH - botH, 0)) + 'cm' + (bx.poly ? ' (外接矩形)' : ''));
    } else {
      rows.push('高さH ' + tipN(topH) + 'cm');
    }
    rows.push(botH > 0.05
      ? ('取付: 床から ' + tipN(botH) + 'cm 〜 ' + tipN(topH) + 'cm')
      : ('設置: 床置き (床から 0 〜 ' + tipN(topH) + 'cm)'));
    const inner = tipFixInner(o);
    if (inner) rows.push(inner);
    if (bx) {
      rows.push('位置: ' + tipRoomJa(o.room) + ' / x' + tipN(bx.x0) + '〜' + tipN(bx.x0 + bx.w) +
                ', y' + tipN(bx.y0) + '〜' + tipN(bx.y0 + bx.d));
    }
    if (o.est) rows.push('※ 寸法は推定値');
    return rows;
  }
  // ── コンセント C-
  if (a.kind === 'outlet') {
    const caps = [(o.caps || 2) + '口'];
    if (o.tv) caps.push('テレビ端子');
    if (o.lan) caps.push('LAN');
    rows.push('口数: ' + caps.join(' + '));
    rows.push('取付高さ: 床から ' + tipN(o.h || 25) + 'cm (プレート中心)');
    rows.push('位置: ' + tipRoomJa(o.room) + ' ' + (D[o.wallSide] || '') + '壁 / x' +
              tipN(o.pos[0]) + ', y' + tipN(o.pos[1]));
    if (o.label) rows.push('目印: ' + tipClean(o.label));
    if (o.est) rows.push('※ 位置は推定');
    return rows;
  }
  // ── エアコン AC-
  if (a.kind === 'aircon') {
    const bot = Number(o.bottomH) || 0;
    rows.push('位置: ' + tipRoomJa(o.room) + ' ' + (D[o.wallSide] || '') + '壁 / x' +
              tipN(o.pos[0]) + ', y' + tipN(o.pos[1]));
    rows.push(bot
      ? ('下端高さ: 床から ' + tipN(bot) + 'cm (上端 ' + tipN(bot + 26) + 'cm)')
      : '下端高さ: 未実測 → 3Dは天井際 (床から 205〜231cm) で表示');
    rows.push('表示サイズ: 幅80 × 奥行24 × 高さ26cm (壁掛け機の目安)');
    if (o.label) rows.push('目印: ' + tipClean(o.label));
    return rows;
  }
  // ── 照明 L- (3D には描画していないので ID検索経由で参照される)
  if (a.kind === 'light') {
    rows.push('種類: ' + (o.type === 'downlight' ? 'ダウンライト (天井埋込)'
             : o.type === 'ceiling_socket' ? '引掛シーリング (器具取付口)' : o.type));
    rows.push('位置: ' + tipRoomJa(o.room) + ' / x' + tipN(o.pos[0]) + ', y' + tipN(o.pos[1]));
    rows.push('取付高さ: 天井 (床から ' + tipN(CH) + 'cm)');
    if (o.est) rows.push('※ 位置は推定');
    return rows;
  }
  return rows;
}
function tipIcon(a) {
  if (!a) return '';
  if (a.kind === 'wall') return '🧱';
  if (a.kind === 'outlet') return '🔌';
  if (a.kind === 'aircon') return '❄️';
  if (a.kind === 'light') return '💡';
  if (a.kind === 'opening') return (a.src && a.src.type === 'window') ? '🪟' : '🚪';
  return '📦';
}
// 配置した家具 (カタログ商品) の 寸法サマリー (家具シートの先頭に出す)
function itemDimSummaryHtml(id, it) {
  if (!it) return '';
  const rows = [];
  rows.push('幅W ' + tipN(it.w) + ' × 奥行D ' + tipN(it.d) + ' × 高さH ' + tipN(it.h) + 'cm');
  const rot = ((Math.round(Number(it.rotY) || 0) % 360) + 360) % 360;
  const y = Number(it.y) || 0, h = Number(it.h) || 0;
  rows.push('回転: ' + rot + '° / 床から: ' + tipN(y) + 'cm' + (y < 0.05 ? ' (床置き)' : '') +
            ' / 上端: ' + tipN(y + h) + 'cm');
  if (it.insideOf && workItems[it.insideOf]) {
    const host = workItems[it.insideOf], cav = openCavityOf(host);
    rows.push('収納: 「' + (cav ? cav.label : (host.name || '収納')) + '」の中');
  }
  if (isMountedItem(it)) {
    const arm = workItems[it.mountArm];
    rows.push('マウント: 「' + (arm ? (arm.name || 'モニターアーム') : 'モニターアーム') +
              '」のアーム上 (画面中心 床から ' + tipN(y) + 'cm)');
  }
  return '<div class="dim-note">📐 ' + rows.map(esc).join('<br>') + '</div>';
}
'''

# showTooltip 差し替え (旧実装 → v6.4)
SHOWTIP_OLD = u'''function showTooltip(e, ud) {
  const tt = document.getElementById('tooltip');
  let html = '';
  // ★v3.9 要素ID: ツールチップの先頭に 【W-LDK-S1】LDK南壁① の形で必ず出す
  const nm = nameOfInfo(ud);
  const idLine = nm ? '<div class="tt-title">【' + esc(nm.id) + '】' + esc(nm.name || '') + '</div>' : '';
  if (ud.kind === 'outlet') {
    const o = ud.info;
    const parts = [(o.caps || 2) + '口'];
    if (o.tv) parts.push('テレビ端子');
    if (o.lan) parts.push('LAN');
    html = '<div class="tt-title">🔌 ' + esc(nm ? '【' + nm.id + '】' : '') + 'コンセント No.' + o.no + '</div>' +
      '<div class="tt-body">' + parts.join(' + ') + '<br>' + esc(o.label || '') +
      '<br>高さ約' + (o.h || 25) + 'cm' + (o.est ? ' (位置は推定)' : '') + '</div>';
  } else {
    html = idLine + '<div class="tt-body">' + esc(typeof ud.info === 'string' ? ud.info : (ud.info && ud.info.label) || '') + '</div>';
  }
  tt.innerHTML = html;
  tt.style.display = 'block';
  const vp = document.getElementById('viewport').getBoundingClientRect();
  tt.style.left = Math.max(4, Math.min(e.clientX - vp.left + 10, vp.width - 270)) + 'px';
  tt.style.top = Math.max(4, Math.min(e.clientY - vp.top + 10, vp.height - 110)) + 'px';
}'''

SHOWTIP_NEW = u'''function showTooltip(e, ud) {
  // ★v6.4 全要素タイプで 寸法 (長さ・高さ・床からの高さ・位置) を出す。
  //   行の組み立ては tipRows() 側に集約 (ID検索 / デバッグAPI と共通化)。
  const tt = document.getElementById('tooltip');
  const a = nameOfInfo(ud);
  const raw = typeof ud.info === 'string' ? ud.info : (ud.info && ud.info.label) || '';
  const title = a
    ? (tipIcon(a) + ' 【' + esc(a.id) + '】' + esc(a.name || ''))
    : esc(tipClean(raw).split('(')[0].trim() || '要素');
  let rows = tipRows(a, ud).map(esc);
  if (!rows.length) rows = [esc(tipClean(raw) || raw)];
  // クリックしたのが 本体ではなく 付属部材 (三方枠・上レール・戸袋等) の時はそれも示す
  if (a && a.kind === 'opening' && raw && a.src && raw !== a.src.label) {
    rows.push(esc('クリック部材: ' + tipClean(raw).split('(')[0].trim()));
  }
  tt.innerHTML = '<div class="tt-title">' + title + '</div>' +
                 '<div class="tt-body">' + rows.join('<br>') + '</div>';
  tt.style.display = 'block';
  // ★v6.4 行数が増えたので 実サイズでクランプする (モバイルで下端が切れないように)
  const vp = document.getElementById('viewport').getBoundingClientRect();
  const tw = tt.offsetWidth || 260, th = tt.offsetHeight || 110;
  tt.style.left = Math.max(4, Math.min(e.clientX - vp.left + 10, vp.width - tw - 6)) + 'px';
  tt.style.top = Math.max(4, Math.min(e.clientY - vp.top + 10, vp.height - th - 6)) + 'px';
}'''

# 開口メッシュへの ID タグ付け + 窓/開口をクリック可能にするラッパ
WRAP_FN = u'''// ═══ ★v6.4 開口描画のラッパ ═══
//   ① buildOpeningPanel が作った全メッシュに opId を刻む → 三方枠・上レール・戸袋を押しても
//      どの建具 (D-06 等) の部材かが一意に引ける。
//   ② 窓 (WIN-) はガラスが pickables に入っていなかったので クリックできなかった → 登録する。
//   ③ 開口 (OP-) は建具が無くメッシュゼロ → クリック判定専用の不可視パネル (pickOnly) を立てる。
function buildOpeningPanelTagged(g, o, s, e, sill, top, horiz, wc, outSign, c) {
  const n0 = g.children.length;
  buildOpeningPanel(g, o, s, e, sill, top, horiz, wc, outSign, c);
  for (let i = n0; i < g.children.length; i++) {
    const m = g.children[i];
    if (!m || !m.userData) continue;
    if (!m.userData.opId) m.userData.opId = o.id;
    if (o.type === 'window' && m.isMesh && !m.userData.kind) {
      m.userData.kind = 'opening';
      m.userData.info = o.label || '窓';
      pickables.push(m);
    }
  }
  if (o.type === 'open') {
    const len = e - s, hgt = top - sill;
    if (len > 1 && hgt > 1) {
      const pm = new THREE.Mesh(
        new THREE.BoxGeometry(horiz ? len : 2, hgt, horiz ? 2 : len),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }));
      pm.position.set(horiz ? (s + e) / 2 : wc, sill + hgt / 2, horiz ? wc : (s + e) / 2);
      pm.userData.kind = 'opening';
      pm.userData.info = o.label || '開口';
      pm.userData.opId = o.id;
      pm.userData.pickOnly = true;   // setFocus の淡色化対象外 (不可視のままに保つ)
      g.add(pm);
      pickables.push(pm);
    }
  }
}
'''

DEBUG_TIP = u'''      // ★v6.4 検証用: 要素ID から ツールチップに出る行をそのまま取る
      tip: function (id) {
        const idx = ensureNameIndex();
        const a = idx.byId[String(id || '').trim().toUpperCase()];
        if (!a) return null;
        return { id: a.id, name: a.name, kind: a.kind, rows: tipRows(a, {}) };
      },
      tipAll: function (prefix) {
        const idx = ensureNameIndex();
        const p = String(prefix || '').trim().toUpperCase();
        return idx.anchors.filter(function (a) { return !p || a.id.indexOf(p) === 0; })
          .map(function (a) { return { id: a.id, name: a.name, kind: a.kind, rows: tipRows(a, {}) }; });
      },
'''

LIGHTS_INDEX = u'''  // ★v6.4 照明 L-: 3D には描画していない (天井ライト表現を v1.8 で削除) ので 直接クリックはできないが、
  //         ID検索 (【L-01】等) で 種類・位置・取付高さ を出せるよう索引には載せる。ラベルは出さない。
  (R.lights || []).forEach(function (l) {
    if (!l.id) return;
    add({ id: l.id, name: l.name || ('照明 ' + l.id), kind: 'light', cls: 'nl-out', room: l.room,
          pos: [l.pos[0], CH - 6, l.pos[1]], pri: 1, minor: true, noLabel: true, src: l,
          detail: (l.name || l.id) + ' / ' + (l.type === 'downlight' ? 'ダウンライト' : '引掛シーリング') });
  });
'''


# ───────────────────────── パッチ定義 ─────────────────────────
# (name, marker(既に入っていれば skip), old, new)
PATCHES = [
    (
        'P1 setFocus: pickOnly メッシュを淡色化対象外に',
        u"if (obj.userData.pickOnly) return;",
        u"      if (obj.userData.doorId) return;   // ★v2.2[4] ドア・引き戸パネルは淡色化 (半透明化) しない\n",
        u"      if (obj.userData.doorId) return;   // ★v2.2[4] ドア・引き戸パネルは淡色化 (半透明化) しない\n"
        u"      if (obj.userData.pickOnly) return;   // ★v6.4 クリック判定専用の不可視パネル (開口 OP-) は素材を触らない\n",
    ),
    (
        'P2 buildOpeningPanelTagged を定義',
        u"function buildOpeningPanelTagged(",
        u"function buildWalls(room) {\n",
        WRAP_FN + u"\nfunction buildWalls(room) {\n",
    ),
    (
        'P3a 呼び出し元① (buildWalls) をラッパへ',
        u"if (o.room === room.key) buildOpeningPanelTagged(",
        u"      if (o.room === room.key) buildOpeningPanel(g, o, s, e, sill, top, horiz, wc, outSign, c);",
        u"      if (o.room === room.key) buildOpeningPanelTagged(g, o, s, e, sill, top, horiz, wc, outSign, c);   // ★v6.4",
    ),
    (
        'P3b 呼び出し元② (buildStatic) をラッパへ',
        u"buildOpeningPanelTagged(group(o.room)",
        u"    buildOpeningPanel(group(o.room), o, r0.a, r0.b, o.sillH || 0,",
        u"    buildOpeningPanelTagged(group(o.room), o, r0.a, r0.b, o.sillH || 0,   // ★v6.4",
    ),
    (
        'P4 buildAircon: userData に acId を付与',
        u"acId: a.id",
        u"    { kind: 'fixture', info: 'エアコン ' + a.no + ' (' + a.label + ')' });",
        u"    { kind: 'fixture', info: 'エアコン ' + a.no + ' (' + a.label + ')', acId: a.id });   // ★v6.4 ID直結",
    ),
    (
        'P5 ツールチップ寸法モジュールを挿入 + showTooltip を差し替え',
        u"function tipRows(",
        SHOWTIP_OLD,
        TIP_MODULE + u"\n" + SHOWTIP_NEW,
    ),
    (
        'P6 handleClick: ドアは開閉 + 寸法ツールチップを同時に出す',
        u"showTooltip(e, info); return; }   // ★v2.2[8]",
        u"  if (info && info.doorId) { toggleDoor(info.doorId, info.panelIdx); return; }   // ★v2.2[8]",
        u"  if (info && info.doorId) { toggleDoor(info.doorId, info.panelIdx); showTooltip(e, info); return; }   // ★v2.2[8]",
    ),
    (
        'P7 buildNameIndex: add() が anchor を返す',
        u"byId[a.id] = a; return a; };",
        u"  const add = function (a) { anchors.push(a); byId[a.id] = a; };",
        u"  const add = function (a) { anchors.push(a); byId[a.id] = a; return a; };   // ★v6.4 byLabel も anchor 実体を指す",
    ),
    (
        'P8 開口 anchor に src を持たせ、byLabel も anchor を指す',
        u"pos: r0.horiz ? [mid, y, r0.c] : [r0.c, y, mid], pri: 4, src: o,",
        u"""    add({ id: o.id, name: o.name || nameShortJa(o.label, o.type), kind: 'opening', cls: cls, room: o.room,
          pos: r0.horiz ? [mid, y, r0.c] : [r0.c, y, mid], pri: 4,
          detail: (o.name || nameShortJa(o.label, o.type)) + ' / 幅' + o.width + 'cm' });
    if (o.label) byLabel[o.label] = { id: o.id, name: o.name || nameShortJa(o.label, o.type) };""",
        u"""    const oa = add({ id: o.id, name: o.name || nameShortJa(o.label, o.type), kind: 'opening', cls: cls, room: o.room,
          pos: r0.horiz ? [mid, y, r0.c] : [r0.c, y, mid], pri: 4, src: o,   // ★v6.4 src = ROOM_DATA の開口オブジェクト
          detail: (o.name || nameShortJa(o.label, o.type)) + ' / 幅' + o.width + 'cm' });
    if (o.label) byLabel[o.label] = oa;""",
    ),
    (
        'P9 設備 anchor に src を持たせ、byLabel も anchor を指す',
        u"minor: !!f.minor, src: f,",
        u"""    if (FIX_STYLE[f.type]) {
      add({ id: f.id, name: nm, kind: 'fixture', cls: 'nl-fix', room: f.room,
            pos: nameFixtureAnchor(f), pri: f.minor ? 1 : 2, minor: !!f.minor,
            detail: nm + (f.rect ? ' / ' + f.rect[2] + '×' + f.rect[3] + 'cm' : '') });
    }
    if (f.label) byLabel[f.label] = { id: f.id, name: nm };""",
        u"""    let fa = null;
    if (FIX_STYLE[f.type]) {
      fa = add({ id: f.id, name: nm, kind: 'fixture', cls: 'nl-fix', room: f.room,
            pos: nameFixtureAnchor(f), pri: f.minor ? 1 : 2, minor: !!f.minor, src: f,   // ★v6.4
            detail: nm + (f.rect ? ' / ' + f.rect[2] + '×' + f.rect[3] + 'cm' : '') });
    }
    if (f.label) byLabel[f.label] = fa || { id: f.id, name: nm, kind: 'fixture', room: f.room, src: f };""",
    ),
    (
        'P10 コンセント anchor に src',
        u"pri: 1, src: u,",
        u"    add({ id: u.id, name: u.name || ('コンセント No.' + u.no), kind: 'outlet', cls: 'nl-out', room: u.room,\n"
        u"          pos: [u.pos[0] + d[0] * 4, (u.h || 25) + 9, u.pos[1] + d[1] * 4], pri: 1,",
        u"    add({ id: u.id, name: u.name || ('コンセント No.' + u.no), kind: 'outlet', cls: 'nl-out', room: u.room,\n"
        u"          pos: [u.pos[0] + d[0] * 4, (u.h || 25) + 9, u.pos[1] + d[1] * 4], pri: 1, src: u,   // ★v6.4",
    ),
    (
        'P11 エアコン anchor に src + 照明 L- を索引に追加',
        u"pri: 2, src: a,",
        u"""    add({ id: a.id, name: a.name || ('エアコン ' + a.no), kind: 'aircon', cls: 'nl-out', room: a.room,
          pos: [a.pos[0] + d[0] * 13, a.bottomH ? a.bottomH + 13 : 218, a.pos[1] + d[1] * 13], pri: 2,
          detail: (a.name || ('エアコン ' + a.no)) });
  });
  return { anchors: anchors, byId: byId, byLabel: byLabel, walls: walls };""",
        u"""    add({ id: a.id, name: a.name || ('エアコン ' + a.no), kind: 'aircon', cls: 'nl-out', room: a.room,
          pos: [a.pos[0] + d[0] * 13, a.bottomH ? a.bottomH + 13 : 218, a.pos[1] + d[1] * 13], pri: 2, src: a,   // ★v6.4
          detail: (a.name || ('エアコン ' + a.no)) });
  });
""" + LIGHTS_INDEX + u"""  return { anchors: anchors, byId: byId, byLabel: byLabel, walls: walls };""",
    ),
    (
        'P12 nameOfInfo: opId / acId から直接引く',
        u"if (ud.opId && idx.byId[ud.opId])",
        u"  if (ud.nameId) return idx.byId[ud.nameId] || { id: ud.nameId, name: '' };   // 壁 (tagWallSegMeshes 済み)\n",
        u"  if (ud.nameId) return idx.byId[ud.nameId] || { id: ud.nameId, name: '' };   // 壁 (tagWallSegMeshes 済み)\n"
        u"  if (ud.opId && idx.byId[ud.opId]) return idx.byId[ud.opId];   // ★v6.4 ドア/窓/開口 (枠・レール・戸袋等の付属部材も本体に寄せる)\n"
        u"  if (ud.acId && idx.byId[ud.acId]) return idx.byId[ud.acId];   // ★v6.4 エアコン\n",
    ),
    (
        'P13 updateNameLabels: noLabel (照明) はラベルを出さない',
        u"if (a.noLabel && !isFocus) continue;",
        u"    const isFocus = nameFocusId === a.id;\n",
        u"    const isFocus = nameFocusId === a.id;\n"
        u"    if (a.noLabel && !isFocus) continue;   // ★v6.4 3D実体の無い要素 (照明 L-) は ID検索時のみ\n",
    ),
    (
        'P14 家具シートに 寸法サマリーを追加',
        u"itemDimSummaryHtml(selectedItemId, it)",
        u"    (fixedDims ? '<div class=\"dim-note\">📐 カタログ商品の正式寸法のためサイズは変更できません</div>' : '') +\n",
        u"    (fixedDims ? '<div class=\"dim-note\">📐 カタログ商品の正式寸法のためサイズは変更できません</div>' : '') +\n"
        u"    itemDimSummaryHtml(selectedItemId, it) +   // ★v6.4 W×D×H / 回転角 / 床からの高さ / 収納内・マウント状態\n",
    ),
    (
        'P15 __noza デバッグAPI: tip / tipAll',
        u"      tip: function (id) {",
        u"      // ★v6.2 検証用: オープン部 (ゴミ箱スペース) の内寸 / 収納内アイテム / スタック候補\n",
        DEBUG_TIP + u"      // ★v6.2 検証用: オープン部 (ゴミ箱スペース) の内寸 / 収納内アイテム / スタック候補\n",
    ),
    (
        # ROOM_DATA のラベルには改訂履歴 (例 WIN-01 「★v1.7 掃き出し→腰窓修正」) が残っており、
        # 形式ワードを素直に全部拾うと「掃き出し窓・腰窓」と矛盾表示になる。
        # 競合したら sillH (実データ) で決め、開閉方式ワード (FIX/すべり出し/引違い) を優先する。
        'P16 tipWindowKind: ラベルの改訂履歴による矛盾を sillH で解消',
        u"// ★v6.4-a 窓の種類",
        u"""// 窓の種類
function tipWindowKind(o) {
  const lb = (o.label || '') + ' ' + (o.name || ''), k = [];
  if (/FIX|はめ殺し/i.test(lb)) k.push('FIX (はめ殺し)');
  if (/すべり出し/.test(lb)) k.push((/縦すべり出し/.test(lb) ? '縦' : '') + 'すべり出し窓');
  if (/掛け出し/.test(lb)) k.push('掛け出し窓');
  if (/掃き出し/.test(lb)) k.push('掃き出し窓');
  if (/腰窓/.test(lb)) k.push('腰窓');
  if (/引違い/.test(lb)) k.push('引違い');
  if (!k.length) {
    const s = Number(o.sillH) || 0;
    k.push(s < 5 ? '掃き出し窓' : (s >= 140 ? '高所窓' : '腰窓'));
  }
  return k.join('・');
}""",
        u"""// ★v6.4-a 窓の種類
//   ROOM_DATA のラベルには改訂履歴 (例 WIN-01 「★v1.7 掃き出し→腰窓修正」) が残っているため、
//   形式ワードを素直に全部拾うと「掃き出し窓・腰窓」と矛盾する。競合時は sillH (実データ) で決める。
function tipWindowKind(o) {
  const lb = (o.label || '') + ' ' + (o.name || ''), k = [];
  const sill = Number(o.sillH) || 0;
  if (/FIX|はめ殺し/i.test(lb)) k.push('FIX (はめ殺し)');
  if (/すべり出し/.test(lb)) k.push((/縦すべり出し/.test(lb) ? '縦' : '') + 'すべり出し窓');
  if (/引違い/.test(lb)) k.push('引違い');
  if (!k.length) {
    const sweep = /掃き出し/.test(lb), koshi = /腰窓/.test(lb);
    if (sweep && koshi) k.push(sill < 5 ? '掃き出し窓' : '腰窓');
    else if (sweep) k.push('掃き出し窓');
    else if (koshi) k.push('腰窓');
    else k.push(sill < 5 ? '掃き出し窓' : (sill >= 140 ? '高所窓' : '腰窓'));
  }
  return k.join('・');
}""",
    ),
    (
        # rect = [x, y, dx, dy] なので W/D は「物のW/D」ではなく「平面 x/y 方向の寸法」。
        # 例: F-01 カウンターキッチン180x74.5 は rect[2]=74.5(x) / rect[3]=180(y) で
        #     ラベルの「幅180」と逆に見える → どちらの軸かを併記する。
        'P17 設備の W/D にどちらの平面軸かを明記',
        u"'幅W ' + tipN(bx.w) + '(x) × 奥行D '",
        u"""      rows.push('幅W ' + tipN(bx.w) + ' × 奥行D ' + tipN(bx.d) +
                ' × 高さH ' + tipN(Math.max(topH - botH, 0)) + 'cm' + (bx.poly ? ' (外接矩形)' : ''));""",
        u"""      // ★v6.4-a rect は [x, y, dx, dy] = 平面 x/y 方向の寸法。物の「幅」と一致しない向きもあるので軸を併記
      rows.push('幅W ' + tipN(bx.w) + '(x) × 奥行D ' + tipN(bx.d) + '(y)' +
                ' × 高さH ' + tipN(Math.max(topH - botH, 0)) + 'cm' + (bx.poly ? ' (外接矩形)' : ''));""",
    ),
    (
        # 開口の不可視パネルを 壁中心 wc に置くと、開口の裏に設備がある場合
        # (OP-02 ペット小部屋 開口 の裏の F-16) に設備が手前に来てクリックできない。
        # 開口を定義した部屋側の壁面のすぐ手前に置き、確実に最前面で拾えるようにする。
        'P18 開口 OP- のクリック用パネルを部屋側の壁面手前へ',
        u"// ★v6.4-a 開口の不可視パネルは 部屋側の壁面のすぐ手前",
        u"""      const pm = new THREE.Mesh(
        new THREE.BoxGeometry(horiz ? len : 2, hgt, horiz ? 2 : len),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }));
      pm.position.set(horiz ? (s + e) / 2 : wc, sill + hgt / 2, horiz ? wc : (s + e) / 2);""",
        u"""      // ★v6.4-a 開口の不可視パネルは 部屋側の壁面のすぐ手前 (壁中心 wc だと 開口の裏の設備が手前に来て拾えない)
      const face = (c === undefined || c === null) ? wc : c;
      const pc = face - outSign * 1.2;
      const pm = new THREE.Mesh(
        new THREE.BoxGeometry(horiz ? len : 1.6, hgt, horiz ? 1.6 : len),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }));
      pm.position.set(horiz ? (s + e) / 2 : pc, sill + hgt / 2, horiz ? pc : (s + e) / 2);""",
    ),
    (
        # 収納のオープン部は床まで抜けているので 中のアイテムも y=0。
        # そこに「(床置き)」と出ると 収納の外に置いてあるように読めるので、収納内・マウント中は付けない。
        'P19 家具サマリー: 収納内/マウント中は「(床置き)」を付けない',
        u"(y < 0.05 && !it.insideOf && !isMountedItem(it) ? ' (床置き)' : '')",
        u"  rows.push('回転: ' + rot + '° / 床から: ' + tipN(y) + 'cm' + (y < 0.05 ? ' (床置き)' : '') +",
        u"  rows.push('回転: ' + rot + '° / 床から: ' + tipN(y) + 'cm' +\n"
        u"            (y < 0.05 && !it.insideOf && !isMountedItem(it) ? ' (床置き)' : '') +   // ★v6.4-a 収納内は床まで抜けているので床置きとは書かない",
    ),
]


def main():
    dry = '--dry-run' in sys.argv
    with io.open(TARGET, encoding='utf-8', newline='') as f:
        text = f.read()
    assert '\r\n' not in text, 'unexpected CRLF in room.html'

    before = data_line_hashes(text)
    applied, skipped, failed = [], [], []

    for name, marker, old, new in PATCHES:
        if marker in text:
            skipped.append(name)
            continue
        n = text.count(old)
        if n != 1:
            failed.append('%s : anchor matched %d times (expected 1)' % (name, n))
            continue
        text = text.replace(old, new, 1)
        applied.append(name)

    after = data_line_hashes(text)
    for k in before:
        assert before[k] == after[k], 'DATA CHANGED: %s\n  before=%s\n  after =%s' % (k, before[k], after[k])

    print('ROOM_DATA sha256    : %s (unchanged)' % before['var ROOM_DATA ='])
    print('CATALOG_SEED sha256 : %s (unchanged)' % before['var CATALOG_SEED ='])
    print('')
    for n in applied:
        print('  [apply] %s' % n)
    for n in skipped:
        print('  [skip ] %s' % n)
    for n in failed:
        print('  [FAIL ] %s' % n)
    print('')
    print(u'適用 %d 件 / skip %d 件 / 失敗 %d 件' % (len(applied), len(skipped), len(failed)))

    if failed:
        print('\n!! 失敗があるので書き戻しません (並行編集でアンカーが変わった可能性)')
        return 1
    if dry:
        print('(dry-run: 書き込みなし)')
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

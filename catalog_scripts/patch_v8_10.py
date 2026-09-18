# -*- coding: utf-8 -*-
u"""v8.10: ① モニターアームの **リーチ (伸び縮み) + スイング (ポール回り)** を UI から調整できるようにする /
         ② モニター2機種 (MSI MAG 342CQR E2 / BenQ EX2710) の 3D 描画を公式実寸に合わせて是正する。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_10.py

冪等 (再実行で「適用0件 / skip 全件」)。 ROOM_DATA は一切変更しない (sha256 assert)。
CATALOG_SEED v2.13 → v2.14: 変更は モニター2点 + アーム1点 の specNote のみ (他34商品は バイト単位で不変を assert)。

━━ ① アームのリーチ / スイング ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
出典 = エルゴトロン 公式寸法図 DIM2-056 (rev.08/29/2024) (catalog\\商品公式資料\\Ergotron_45-241-224\\):
  ・ポール中心〜第1アーム軸 40 / 第1アーム 231 / 第2アーム 293 / モニターマウント 86 → 最大リーチ 650 (=40+231+293+86)
  ・上面図「14.2" (360mm)」= 折り畳み時の全長 (ベース後端〜VESAプレート)。 ポール中心基準の最小リーチとしては控えめな値
  ・p3 可動範囲: ベース回転 180° (= ±90°) / 肘 360° / 手首 360°
仕組み:
  ・保存フィールド `item.armReach` (cm、 null=既定=これまでどおりの折り畳み姿勢 fold=-70°) / `item.armSwing` (°、 null=0)
  ・armPose(): 高さ (vesaH) の解き方は **一切変えない** (第1アーム仰角 th1 + ポール上の取付高 hc)。
    その後 水平面で 2リンク (A = 40 + 231·cos th1, B = 293) の逆運動学 (余弦定理) で
    「手首がポール軸の真正面 (x=0)・距離 D = R − 86」 になる yaw1/yaw2 を解く。 armReach=null の時は
    従来の式 (yaw1=fold, yaw2=asin) をそのまま通すので 既存の呼び出しは bit 単位で同じ結果を返す (check_v8_10 で検証)。
  ・クランプ: 36 ≦ R ≦ min(65, A+B+8.6)。 第1アームを起こす (高さを上げる) ほど A が縮むので 最大値は vesaH に依存。
    届かない値はクランプしてトーストで知らせる。
  ・スイング: 水平面の全リンク角に φ を足し、 マウント (86) と VESAプレートも φ 方向へ。 マウント中モニターの rotY = アーム rotY − φ。
  ・伸ばした先の干渉: scanObstacle のレイキャスト (VESA面〜パネル前面 の奥行ぶん) で 壁・家具に当たれば警告トースト (ブロックはしない)。

━━ ② モニターの実寸 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MSI MAG 342CQR E2 (公式 datasheet PDF): 表示領域 797.22×333.72 / パネルのみ 808.60×119.67×363.95 / 1500R
    → 旧: 5分割の箱の厚み 12 + 弧の矢高 ≈ 5.5 = **奥行 17.5cm で描いていた** (公式 11.97 より 5.5cm 厚い)。
       画面は 各分割ごとに 0.6cm ずつ細く描いていたので 幅 77.9 (公式 79.7) + 縦の継ぎ目4本。
    → 新: 外形幅 80.9 が 弧の外側の角で決まる θ の 薄い曲面スラブ (縁の厚み 2.4 [est]) + 背面中央の膨らみ (奥行 4.2 =
       公式D 11.97 − 前端までの矢高分 [幾何計算]) で 外形 W80.9×D12.0×H36.4 を bbox で一致させる /
       スクリーンは 1枚の円筒面 (幅 79.7 × 高 33.4 = 公式表示領域) / 上ベゼル 0.7・下 2.3 [est: 公式正面写真の画素比率] /
       左右ベゼル 各 0.57 (= (80.86−79.72)/2 公式値の差分)。
  BenQ EX2710 (公式スペック表・Wayback): パネルのみ 614.1×64.1×382.2 / 表示領域は **公式非公表**
    → 27型 16:9 の計算値 597.9×336.3 [est] (旧描画は 59.0×35.0 = 縦が 1.4cm 高く 横が 0.8cm 狭い = 16:9 でなく 1.69:1)。
       上ベゼル 0.8 [est: 公式正面写真]・下 3.8 (= 38.2−33.6−0.8) / 左右 各 0.8 (計算差分)。
  両機種とも VESA 中心の位置は公式に記載なし → パネル中心と仮定 [est] (従来どおり)。
  スタンド昇降 (BenQ 130mm / MSI 90mm) は 家具シートの寸法欄に「最低〜最高」で表示 (3Dは従来どおり最低位置)。
"""
import hashlib
import io
import json
import re
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'
MARK = u'armReachRaw'   # 適用済み判定のマーカー (関数名)

# ═══ ① ARM 定数 ═══════════════════════════════════════════════════════════
OLD_ARM_TAIL = u"""  snapR: 32, holdR: 45                       // マウント吸着半径 / マウント解除半径 (ヒステリシス)
};
"""
NEW_ARM_TAIL = u"""  snapR: 32, holdR: 45,                      // マウント吸着半径 / マウント解除半径 (ヒステリシス)
  // ★v8.10 リーチ (ポール中心〜VESA面の水平距離) の可動範囲。 公式寸法図 DIM2-056:
  //   最大 650 (=40+231+293+86) / 上面図の折り畳み 360 (ベース後端〜VESA面の全長。 ポール中心基準としては控えめな下限)
  //   高さ (第1アームの仰角) を上げると 水平投影 231·cos(th1) が縮むので 実際の最大は vesaH に依存 (armPose().reachMax)
  reachMin: 36, reachMax: 65,
  swingMax: 90                               // ★v8.10 ポール回りのスイング ±90° (公式寸法図 p3 上面図: ベース回転 180°)
};
"""

# ═══ ② armPose の水平面 IK ═════════════════════════════════════════════════
OLD_POSE_HEAD = u"""function armVesaH(it) {
  const v = Number(it && it.vesaH);
  return Math.min(Math.max(isFinite(v) && v > 0 ? v : ARM.liftDef, ARM.liftMin), ARM.liftMax);
}
"""
NEW_POSE_HEAD = OLD_POSE_HEAD + u"""// ★v8.10 リーチの保存値 (cm)。 null = 既定 (折り畳み姿勢 = v4.1〜v8.9 と同じ armPose の解)
function armReachRaw(it) {
  if (!it || it.armReach === null || it.armReach === undefined || it.armReach === '') return null;
  const v = Number(it.armReach);
  return isFinite(v) && v > 0 ? v : null;
}
// ★v8.10 実効リーチ (ポール中心〜VESAプレート面の水平距離 cm・0.1刻み)
function armReach(it) { return Math.round(armPose(it).reach * 10) / 10; }
// ★v8.10 スイング (ポール回りの水平回転 °。 +で 右手方向)。 null/0 = 正面
function armSwing(it) {
  const v = Number(it && it.armSwing);
  return isFinite(v) ? Math.min(Math.max(v, -ARM.swingMax), ARM.swingMax) : 0;
}
"""
OLD_POSE_A = u"""  s = Math.min(Math.max(s, -0.75), 0.93);
  const th1 = Math.asin(s), yaw1 = ARM.fold * Math.PI / 180;
  const y1 = ARM.baseT + hc;                                     // 第1アーム回転軸の高さ
  const L1 = ARM.a1 * Math.cos(th1);                             // 第1アームの水平投影長
  const yaw2 = Math.asin(Math.min(Math.max(-Math.sin(yaw1) * (ARM.offs + L1) / ARM.a2, -0.98), 0.98));
  const p1x"""
NEW_POSE_A = u"""  s = Math.min(Math.max(s, -0.75), 0.93);
  const th1 = Math.asin(s);
  const y1 = ARM.baseT + hc;                                     // 第1アーム回転軸の高さ
  const L1 = ARM.a1 * Math.cos(th1);                             // 第1アームの水平投影長
  // ★v8.10 水平面の姿勢: リーチ指定なし (null) は従来どおり 折り畳み角 fold で決める (既存の解と bit 単位で同じ)。
  //   リーチ R が指定されていれば 2リンク (A = 40 + L1 / B = 293) の逆運動学で
  //   「手首がポール軸の真正面 (x=0)・ポール中心から D = R − マウント86」 になる yaw1 / yaw2 を余弦定理で解く。
  //   届かない R は [reachMin, A+B+mount] にクランプ (第1アームを起こすほど A が縮む = 高いと届く距離が短い、 実機と同じ)。
  const A = ARM.offs + L1, reachMax = A + ARM.a2 + ARM.mount;
  const R0 = armReachRaw(it), sw = armSwing(it) * Math.PI / 180;
  let yaw1, yaw2;
  if (R0 === null) {
    yaw1 = ARM.fold * Math.PI / 180;
    yaw2 = Math.asin(Math.min(Math.max(-Math.sin(yaw1) * (ARM.offs + L1) / ARM.a2, -0.98), 0.98));
  } else {
    const D = Math.min(Math.max(R0, ARM.reachMin), reachMax) - ARM.mount;
    const c = Math.min(Math.max((A * A + D * D - ARM.a2 * ARM.a2) / (2 * A * D), -1), 1);
    yaw1 = -Math.acos(c);                                        // 肘は従来と同じ側 (−x) へ出す
    yaw2 = Math.atan2(-A * Math.sin(yaw1), D - A * Math.cos(yaw1));
  }
  yaw1 += sw; yaw2 += sw;                                        // スイング = 水平面の全リンクを φ だけ回す
  const p1x"""
OLD_POSE_B = u"""  return { hc: hc, th1: th1, yaw1: yaw1, yaw2: yaw2, poleZ: poleZ, y1: y1, ey: ey,
           p1x: p1x, p1z: p1z, ex: ex, ez: ez, wx: wx, wz: wz,
           ax: wx, ay: ey, az: poleZ + wz + ARM.mount, vesaH: T };   // a* = VESAプレート面の中心 (取付点)
}"""
NEW_POSE_B = u"""  return { hc: hc, th1: th1, yaw1: yaw1, yaw2: yaw2, poleZ: poleZ, y1: y1, ey: ey,
           p1x: p1x, p1z: p1z, ex: ex, ez: ez, wx: wx, wz: wz, sw: sw,
           ax: wx + Math.sin(sw) * ARM.mount, ay: ey, az: poleZ + wz + Math.cos(sw) * ARM.mount, vesaH: T,   // a* = VESAプレート面の中心 (取付点)
           reach: Math.sqrt(wx * wx + wz * wz) + ARM.mount,          // ★v8.10 実効リーチ (ポール中心〜VESA面)
           reachMax: reachMax };                                      // ★v8.10 この高さで届く最大リーチ
}"""
OLD_ATTACH = u"""  return { x: arm.x + p.ax * ca + p.az * sa, y: (Number(arm.y) || 0) + p.ay,
           z: arm.z - p.ax * sa + p.az * ca,
           rotY: (((arm.rotY || 0) % 360) + 360) % 360, vesaH: p.vesaH };
}"""
NEW_ATTACH = u"""  return { x: arm.x + p.ax * ca + p.az * sa, y: (Number(arm.y) || 0) + p.ay,
           z: arm.z - p.ax * sa + p.az * ca,
           rotY: ((((arm.rotY || 0) - armSwing(arm)) % 360) + 360) % 360, vesaH: p.vesaH };   // ★v8.10 スイングぶん向きが変わる
}"""

# ═══ ③ アームの 3D (チルター / VESAプレート を スイング方向へ) ═══════════════
OLD_ARM_TIP = u"""    P(3.2, 2.8, ARM.mount - 2.4, AP.wx, AP.ey, AP.poleZ + AP.wz + (ARM.mount - 2.4) / 2, met);  // チルター (後70°/前5°)
    P(ARM.vesaW, ARM.vesaPlateH, 1.0, AP.ax, AP.ay, AP.az - 0.5, mdk);    // VESAプレート 幅156mm
    P(ARM.vesaW * 0.3, ARM.vesaPlateH * 0.3, 0.8, AP.ax, AP.ay, AP.az - 1.4, met);   // プレート裏のボス
"""
NEW_ARM_TIP = u"""    const sS = Math.sin(AP.sw), cS = Math.cos(AP.sw);                     // ★v8.10 マウント〜プレートは スイング方向 φ へ向く
    const tlt = P(3.2, 2.8, ARM.mount - 2.4, AP.wx + sS * (ARM.mount - 2.4) / 2, AP.ey,
                  AP.poleZ + AP.wz + cS * (ARM.mount - 2.4) / 2, met);   // チルター (後70°/前5°)
    tlt.rotation.y = AP.sw;
    const vpl = P(ARM.vesaW, ARM.vesaPlateH, 1.0, AP.ax - sS * 0.5, AP.ay, AP.az - cS * 0.5, mdk);    // VESAプレート 幅156mm
    vpl.rotation.y = AP.sw;
    const vbs = P(ARM.vesaW * 0.3, ARM.vesaPlateH * 0.3, 0.8, AP.ax - sS * 1.4, AP.ay, AP.az - cS * 1.4, met);   // プレート裏のボス
    vbs.rotation.y = AP.sw;
"""

# ═══ ④ 再構築キー / 保存 ═══════════════════════════════════════════════════
OLD_KEY = u"               it.mounted ? 'AM1' : 'AM0', it.vesaH || '',\n"
NEW_KEY = u"               it.mounted ? 'AM1' : 'AM0', it.vesaH || '', it.armReach || '', it.armSwing || '',   // ★v8.10 リーチ / スイング\n"
OLD_CLEAN = u"    vesaH: (it.vesaH === undefined || it.vesaH === null || it.vesaH === '') ? null : Number(it.vesaH),\n"
NEW_CLEAN = OLD_CLEAN + u"""    // ★v8.10 armReach=アームのリーチ (ポール中心〜VESA面 cm。null=既定の折り畳み姿勢) / armSwing=ポール回りのスイング ° (null=正面)
    armReach: (it.armReach === undefined || it.armReach === null || it.armReach === '') ? null : Number(it.armReach),
    armSwing: (it.armSwing === undefined || it.armSwing === null || it.armSwing === '' || Number(it.armSwing) === 0) ? null : Number(it.armSwing),
"""

# ═══ ⑤ UI (家具シート) + setter ═══════════════════════════════════════════
OLD_UI = u"""          : ' (モニターをドラッグして重ねるとマウントできます)') +
      '</div></div>';
  }
"""
NEW_UI = u"""          : ' (モニターをドラッグして重ねるとマウントできます)') +
      '</div></div>';
    vesaBlock += armReachBlockHtml(it);   // ★v8.10 リーチ (伸び縮み) + スイング
  }
"""
OLD_SETTER = u"""// ★v6.5 テレビスタンドの TV取付高さ (床〜ブラケット上端)。公式 120〜170cm の 11段階 (5cmピッチ)。
//        取り付け中のテレビも一緒に上下する。live=true (スライダー操作中) は数値ラベルだけ更新。
window.setStandH = function (v, live) {"""
NEW_SETTER = u"""// ★v8.10 モニターアームの リーチ (伸び縮み) と スイング の UI ブロック。 vesaH スライダーと同じ構成
//        (range + −/既定/＋ の floorh-seg・タップ領域 44px)。 既定 = これまでどおりの折り畳み姿勢 (armReach=null)。
function armReachBlockHtml(it) {
  const AP = armPose(it), R = Math.round(AP.reach * 10) / 10, mx = Math.floor(AP.reachMax * 2) / 2;
  const isDef = armReachRaw(it) === null, swv = armSwing(it), mc = mountedCountOf(selectedItemId);
  const mn = Math.min(ARM.reachMin, R);   // 既定 (折り畳み) は 低い vesaH で 36 を下回ることがあるので つまみが外へ出ないようにする
  return '<div class="form-group"><label class="form-label">アームのリーチ (ポール中心から画面背面まで): ' +
    '<b id="reachVal">' + R + '</b> cm' + (isDef ? ' <span style="opacity:.7;">(既定 = 折り畳み)</span>' : '') + '</label>' +
    '<input class="form-input" type="range" min="' + mn + '" max="' + mx + '" step="0.5" ' +
    'value="' + R + '" oninput="setArmReach(this.value, true)" onchange="setArmReach(this.value)" ' +
    'aria-label="アームのリーチ" style="padding:0;">' +
    '<div class="floorh-seg" style="margin-top:6px;">' +
    '<button class="floorh-btn" onclick="nudgeArmReach(-1)">− 1cm</button>' +
    '<button class="floorh-btn" onclick="setArmReach(null)">既定 (折り畳み)</button>' +
    '<button class="floorh-btn" onclick="nudgeArmReach(1)">＋ 1cm</button>' +
    '</div>' +
    '<div class="dim-note">📐 公式 折り畳み 360mm 〜 最大リーチ 650mm。VESA高さ ' + armVesaH(it) + 'cm では最大 ' + mx +
    'cm (第1アームを起こすほど届く距離は縮みます)' +
    (mc ? ' / マウント中のモニター ' + mc + '台も前後に追従します' : '') + '</div></div>' +
    '<div class="form-group"><label class="form-label">アームのスイング (ポール回りの向き): ' +
    '<b id="swingVal">' + swv + '</b>°</label>' +
    '<input class="form-input" type="range" min="' + (-ARM.swingMax) + '" max="' + ARM.swingMax + '" step="5" ' +
    'value="' + swv + '" oninput="setArmSwing(this.value, true)" onchange="setArmSwing(this.value)" ' +
    'aria-label="アームのスイング" style="padding:0;">' +
    '<div class="floorh-seg" style="margin-top:6px;">' +
    '<button class="floorh-btn" onclick="nudgeArmSwing(-5)">↶ 5°</button>' +
    '<button class="floorh-btn" onclick="setArmSwing(0)">正面 0°</button>' +
    '<button class="floorh-btn" onclick="nudgeArmSwing(5)">↷ 5°</button>' +
    '</div>' +
    '<div class="dim-note">📐 公式 ベース回転 180° (±' + ARM.swingMax + '°)。マウント中のモニターも一緒に向きが変わります</div></div>';
}
// ★v8.10 伸ばした先 (VESAプレート面 → マウント中モニターの前面) に 壁・家具が重なっていないかを
//        scanObstacle のレイキャストで見る。当たったら警告トースト (ブロックはしない = 実機でも当てられる)
function armReachObstacleWarn(armId) {
  const arm = workItems[armId], g = furnMeshes[armId];
  if (!arm || !g) return null;
  scene.updateMatrixWorld(true);   // 直前に動かしたモニター等の行列も更新してからレイを撃つ (描画前でも正しい位置)
  const AP = armPose(arm);
  const Wp = function (x, y, z) { return g.localToWorld(new THREE.Vector3(x, y, z)); };
  // ① アーム本体 (取付カラー → 肘 → 手首 → VESA面) が 壁・家具を貫いていないか (自分自身は除外)
  const pts = [Wp(AP.p1x, AP.y1, AP.poleZ + AP.p1z), Wp(AP.ex, AP.ey, AP.poleZ + AP.ez),
               Wp(AP.wx, AP.ey, AP.poleZ + AP.wz), Wp(AP.ax, AP.ay, AP.az)];
  const segNm = ['第1アーム', '第2アーム', 'マウント'];
  for (let i = 0; i < 3; i++) {
    const sv = pts[i + 1].clone().sub(pts[i]), len = sv.length();
    if (len < 1.2) continue;
    const rs = scanObstacle(g, [pts[i]], sv.normalize(), len - 0.6);
    if (rs.dist !== null) return '⚠ ' + segNm[i] + 'が「' + (rs.name || '障害物') + '」に当たります (' + (Math.round(rs.dist * 10) / 10) + 'cm 先)';
  }
  // ② VESA面の前 (マウント中モニターならパネルの奥行ぶん)
  const dir = new THREE.Vector3(Math.sin(AP.sw), 0, Math.cos(AP.sw)).applyQuaternion(g.quaternion).normalize();
  const rt = new THREE.Vector3(Math.cos(AP.sw), 0, -Math.sin(AP.sw)).applyQuaternion(g.quaternion).normalize();
  let selfG = g, far = 3.0, hw = ARM.vesaW / 2 - 1, hh = ARM.vesaPlateH / 2 - 1, what = 'VESAプレートの前';
  let moId = null;
  Object.keys(workItems).forEach(function (k) {
    const o = workItems[k];
    if (isMountedItem(o) && o.mountArm === armId && furnMeshes[k]) moId = k;
  });
  if (moId) {
    const mo = workItems[moId], pd = monitorPanelDims(mo);
    selfG = furnMeshes[moId]; far = (pd.depth || pd.panT) + 3.0;
    hw = Math.max((Number(mo.w) || 10) / 2 - 1, 1); hh = Math.max(pd.panH / 2 - 1, 1); what = 'モニターの前面';
  }
  const base = Wp(AP.ax, AP.ay, AP.az).addScaledVector(dir, 0.6);
  const origins = [[0, 0], [hw, hh], [-hw, hh], [hw, -hh], [-hw, -hh], [hw, 0], [-hw, 0]].map(function (o) {
    return base.clone().addScaledVector(rt, o[0]).add(new THREE.Vector3(0, o[1], 0));
  });
  const r = scanObstacle(selfG, origins, dir, far);
  if (r.dist === null) return null;
  return '⚠ 伸ばした先で「' + (r.name || '障害物') + '」に当たります (' + what + ' ' + (Math.round(r.dist * 10) / 10) + 'cm)';
}
// ★v8.10 アームのリーチ。 null/'' = 既定 (折り畳み姿勢) へ戻す。 届かない値は [36, この高さの最大] にクランプしてトースト
window.setArmReach = function (v, live) {
  const it = workItems[selectedItemId];
  if (!it || !isArmItem(it)) return;
  let note = '';
  if (v === null || v === undefined || v === '' || v === 'null') {
    it.armReach = null;
  } else {
    const want = Number(v), mx = Math.floor(armPose(it).reachMax * 2) / 2;
    const val = Math.round(Math.min(Math.max(isFinite(want) ? want : ARM.reachMin, ARM.reachMin), mx) * 2) / 2;
    if (isFinite(want) && Math.abs(val - want) >= 0.5) {
      note = want > val ? ' — VESA高さ ' + armVesaH(it) + 'cm では最大 ' + mx + 'cm までです (第1アームを起こしているぶん縮む)'
                        : ' — 公式の折り畳み 36cm が下限です';
    }
    it.armReach = val;
  }
  const m = furnMeshes[selectedItemId];
  if (m) syncItemMesh(m, it);
  syncMounts(selectedItemId);          // マウント中モニターも前後に追従
  markDirty();
  const lab = document.getElementById('reachVal');
  if (lab) lab.textContent = armReach(it);
  if (!live) {
    const mc = mountedCountOf(selectedItemId);
    toast((it.armReach === null ? 'アームを既定 (折り畳み) に戻しました: リーチ ' : 'アームのリーチを ') + armReach(it) + 'cm' +
          (it.armReach === null ? '' : ' にしました') + (mc ? ' (モニター' + mc + '台も追従)' : '') + note);
    const wobs = armReachObstacleWarn(selectedItemId);
    if (wobs) setTimeout(function () { toast(wobs); }, 1800);
  }
};
window.nudgeArmReach = function (d) {
  const it = workItems[selectedItemId];
  if (!it || !isArmItem(it)) return;
  window.setArmReach(armReach(it) + Number(d));
  openItemSheet();                     // スライダーのつまみ位置を反映
};
// ★v8.10 アームのスイング (ポール回りの向き °)。 ±swingMax にクランプ。 0 は null で保存 (既定)
window.setArmSwing = function (v, live) {
  const it = workItems[selectedItemId];
  if (!it || !isArmItem(it)) return;
  const n = Math.round(Number(v) || 0);
  const val = Math.min(Math.max(n, -ARM.swingMax), ARM.swingMax);
  it.armSwing = val === 0 ? null : val;
  const m = furnMeshes[selectedItemId];
  if (m) syncItemMesh(m, it);
  syncMounts(selectedItemId);          // マウント中モニターの位置と向きも追従
  markDirty();
  const lab = document.getElementById('swingVal');
  if (lab) lab.textContent = armSwing(it);
  if (!live) {
    const mc = mountedCountOf(selectedItemId);
    toast('アームのスイングを ' + armSwing(it) + '° にしました' + (mc ? ' (モニター' + mc + '台も追従)' : '') +
          (Math.abs(n) > ARM.swingMax ? ' — 公式 ベース回転 180° (±' + ARM.swingMax + '°) が上限です' : ''));
    const wobs = armReachObstacleWarn(selectedItemId);
    if (wobs) setTimeout(function () { toast(wobs); }, 1800);
  }
};
window.nudgeArmSwing = function (d) {
  const it = workItems[selectedItemId];
  if (!it || !isArmItem(it)) return;
  window.setArmSwing(armSwing(it) + Number(d));
  openItemSheet();
};
// ★v6.5 テレビスタンドの TV取付高さ (床〜ブラケット上端)。公式 120〜170cm の 11段階 (5cmピッチ)。
//        取り付け中のテレビも一緒に上下する。live=true (スライダー操作中) は数値ラベルだけ更新。
window.setStandH = function (v, live) {"""

# ═══ ⑥ デバッグフック ═══════════════════════════════════════════════════════
OLD_HOOK = u"""                     rotY: workItems[k].rotY || 0, vesaH: armVesaH(workItems[k]),
                     attach: { x: Math.round(ap.x * 10) / 10, y: Math.round(ap.y * 10) / 10, z: Math.round(ap.z * 10) / 10 },
                     mounted: mountedCountOf(k) };
          });
      },
      mounts: function () {"""
NEW_HOOK = u"""                     rotY: workItems[k].rotY || 0, vesaH: armVesaH(workItems[k]),
                     reach: armReach(workItems[k]), reachRaw: armReachRaw(workItems[k]),   // ★v8.10
                     reachMax: Math.round(armPose(workItems[k]).reachMax * 10) / 10, swing: armSwing(workItems[k]),
                     attach: { x: Math.round(ap.x * 10) / 10, y: Math.round(ap.y * 10) / 10, z: Math.round(ap.z * 10) / 10, rotY: ap.rotY },
                     mounted: mountedCountOf(k) };
          });
      },
      reach: function (armId, v) {   // ★v8.10 検証用: リーチを UI と同じ経路で設定 (null = 既定)
        const prev = selectedItemId;
        selectedItemId = armId;
        window.setArmReach(v);
        selectedItemId = prev;
        return { reach: armReach(workItems[armId]), reachRaw: armReachRaw(workItems[armId]),
                 attach: armAttachPoint(workItems[armId]), pose: armPose(workItems[armId]),
                 warn: armReachObstacleWarn(armId) };
      },
      swing: function (armId, v) {   // ★v8.10 検証用: スイングを UI と同じ経路で設定
        const prev = selectedItemId;
        selectedItemId = armId;
        window.setArmSwing(v);
        selectedItemId = prev;
        return { swing: armSwing(workItems[armId]), attach: armAttachPoint(workItems[armId]), warn: armReachObstacleWarn(armId) };
      },
      monDims: function (id) { return monitorPanelDims(workItems[id]); },   // ★v8.10 検証用
      mounts: function () {"""

# ═══ ⑦ モニターの実寸 (monitorPanelDims + 3D) ═══════════════════════════════
OLD_PDIMS = u"""function monitorPanelDims(it) {
  const nm = specTextOf(it);            // ★v5.3
  const d = Math.max(Number(it.d) || 10, 2), h = Math.max(Number(it.h) || 10, 2);
  const curve = /342CQR|1500R|曲面/.test(nm);
  return {
    panH: /EX2710/.test(nm) ? Math.min(38.2, h - 2) : (curve ? Math.min(36.4, h - 2) : Math.max(h * 0.68, 6)),
    panT: /EX2710/.test(nm) ? 6.4 : (curve ? Math.min(12, d * 0.5) : Math.min(6, d * 0.35)),
    curve: curve
  };
}"""
NEW_PDIMS = u"""//  ★v8.10 表示領域 (scrW×scrH) と 上ベゼル (bezTop) を機種別に持ち、 曲面は「弦 = 公式幅」の弧で描く。
//    depth = スタンド無しの公式奥行 (曲面は 縁の前角 〜 背面の膨らみ)。 AABB (mountedAabb) は depth を使う。
//    ・MSI MAG 342CQR E2: 表示領域 797.22×333.72 (公式 datasheet) / パネル 808.60×119.67×363.95 / 1500R。
//        上ベゼル 0.7・下 2.3 は公式非公表 → 公式正面写真の画素比率 [est]。 縁の厚み 2.4 [est] + 背面中央の膨らみで 公式奥行 11.97 を作る
//    ・BenQ EX2710: 表示領域は公式非公表 → 27型 16:9 の計算値 59.8×33.6 [est]。 上ベゼル 0.8 [est: 公式正面写真]・下 3.8 (差分)
//    ・VESA 中心の位置は 両機種とも公式に記載なし → パネル中心と仮定 [est]
function monitorPanelDims(it) {
  const nm = specTextOf(it);            // ★v5.3
  const w = Math.max(Number(it.w) || 10, 2), d = Math.max(Number(it.d) || 10, 2), h = Math.max(Number(it.h) || 10, 2);
  const msi = /342CQR/.test(nm), benq = /EX2710/.test(nm);
  const curve = msi || /1500R|曲面/.test(nm);
  const panH = benq ? Math.min(38.2, h - 2) : (curve ? Math.min(36.4, h - 2) : Math.max(h * 0.68, 6));
  let panT, depth, scrW, scrH, bezTop, curveR = 0, theta = 0, humpD = 0;
  if (benq) {
    panT = 6.4; depth = 6.4; scrW = 59.8; scrH = 33.6; bezTop = 0.8;
  } else if (curve) {
    // 曲面パネル = 薄い曲面スラブ (縁の厚み slabT [est]) + 背面中央の膨らみ (VESA/基板部)。
    //   外形幅 w は 弧の外側 (背面) の角で決まるので θ = 2·asin((w/2)/(R+slabT/2))。 矢高は θ から幾何で決まる。
    //   depth (公式のスタンド無し奥行) = 前端 (縁の前角) 〜 後端 (膨らみの背面) なので 膨らみの奥行 humpD はその残り。
    curveR = 150; panT = 2.4;                                                         // 縁の厚み 2.4 [est: 公式非公表]
    theta = 2 * Math.asin(Math.min((w / 2) / (curveR + panT / 2), 0.99));
    depth = Math.min(12, d * 0.5);                                                    // スタンド無しの奥行 (MSI 公式 119.67)
    const front = curveR - (curveR - panT / 2) * Math.cos(theta / 2);                 // スラブ中心弧の中央 → 縁の前角 (z)
    humpD = Math.max(depth - front - panT / 2, 0.5);                                  // 背面中央の膨らみの奥行 (12.0 → 4.2)
    scrW = msi ? 79.7 : w - 1.2; scrH = msi ? 33.4 : panH - 3.0; bezTop = 0.7;
  } else {
    panT = Math.min(6, d * 0.35); depth = panT;
    scrW = w - 2.4; scrH = panH - 3.2; bezTop = 1.0;                                   // 汎用 (v3.7 と同じ比率)
  }
  return {
    panH: panH, panT: panT, depth: depth, curve: curve, curveR: curveR, theta: theta, humpD: humpD,
    scrW: Math.min(scrW, w - 0.4), scrH: Math.min(scrH, panH - 0.4), bezTop: bezTop
  };
}"""
OLD_AABB = u"""  const w = Math.max(Number(it.w) || 10, 2), t = pd.panT + 2, y = Number(it.y) || 0;"""
NEW_AABB = u"""  const w = Math.max(Number(it.w) || 10, 2), t = (pd.depth || pd.panT) + 2, y = Number(it.y) || 0;   // ★v8.10 曲面は矢高込みの奥行"""
OLD_STAND = u"""    const zBk = armMt ? (1.0 + panT / 2) : (-d / 2 + panT / 2 + 1);       // パネル中心の z
    if (armMt) {
      P(12, 12, 1.0, 0, cy, 0.5, met);                                    // VESA 100×100 プレート (アーム側と接する面)
      P(3.4, 3.4, 1.4, 0, cy, 1.3, met);                                  // プレート〜パネル背面のボス
    } else {
      [-1, 1].forEach(function (s) {                                      // V字 (ブーメラン型) の低い板状ベース ×2
        const vf = P(w * 0.34, 1.6, d * 0.16, s * w * 0.13, 0.8, d * 0.14, met);
        vf.rotation.y = -s * 0.50;                                        // 前方 (+z) へ開く浅いV字
      });
      P(w * 0.13, 2.0, d * 0.16, 0, 1.0, d * 0.02, met);                  // V字の要 (支柱の足元)
      P(Math.max(w * 0.075, 4), standH, Math.min(6.5, d * 0.35), 0, standH / 2, d * 0.02, met);  // 角柱支柱
      P(Math.max(w * 0.10, 6), Math.min(10, panH * 0.3), 1.6, 0, standH + panH * 0.35, zBk - panT / 2 - 0.8, met); // VESA 100×100 マウント部
    }
"""
NEW_STAND = u"""    const humpD = pdm.humpD || 0;                                         // ★v8.10 曲面: 背面中央の膨らみ (平面は 0)
    const colD = Math.min(6.5, d * 0.3);                                  // ★v8.10 支柱の奥行 [est: 公式非公表・写真比率]
    // ★v8.10 床置きは 支柱を footprint の後端に立て、 その前面にパネル背面 (膨らみ) が付く = 支柱が画面より前に出ない
    //   (v8.9 までは 支柱を footprint 中央に置いていたので、 パネルを実厚にすると支柱が画面の前に出てしまう)。
    //   マウント時は 原点 = VESA面 (アームのプレート) → 膨らみ → スラブ。
    const zBack = armMt ? 1.0 : (-d / 2 + 0.5 + colD);                    // パネル最後端 (膨らみの背面) の z
    const zBk = zBack + humpD + panT / 2;                                 // パネル (スラブ) 中心の z
    const scrY = cy + panH / 2 - pdm.bezTop - pdm.scrH / 2;              // ★v8.10 表示領域の中心 (上ベゼル薄・下ベゼル厚)
    if (armMt) {
      P(12, 12, 1.0, 0, cy, 0.5, met);                                    // VESA 100×100 プレート (アーム側と接する面)
      P(3.4, 3.4, 1.4, 0, cy, 1.3, met);                                  // プレート〜パネル背面のボス
    } else {
      const zc = -d / 2 + 0.5 + colD / 2;                                 // 支柱の中心 z (footprint 後端)
      [-1, 1].forEach(function (s) {                                      // V字 (ブーメラン型) の低い板状ベース ×2 (支柱から前方へ開く)
        const vf = P(w * 0.34, 1.6, d * 0.16, s * w * 0.13, 0.8, zc + (d / 2 - zc) * 0.55, met);
        vf.rotation.y = -s * 0.50;                                        // 前方 (+z) へ開く浅いV字
      });
      P(w * 0.13, 2.0, colD, 0, 1.0, zc, met);                            // V字の要 (支柱の足元)
      P(Math.max(w * 0.075, 4), standH, colD, 0, standH / 2, zc, met);   // 角柱支柱
      P(Math.max(w * 0.10, 6), Math.min(10, panH * 0.3), 1.6, 0, standH + panH * 0.35, zBack - 0.8, met); // VESA マウント部 (支柱の中)
    }
"""
OLD_MON_SCR = u"""    if (isCurve) {                                                        // 1500R 曲面 (幅80.9cmで端が約5.5cm手前に来る)
      const seg = 5, R = 150, sw = w / seg;
      for (let ci = 0; ci < seg; ci++) {
        const ang = (ci - (seg - 1) / 2) * (sw / R);
        const pn = P(sw + 0.4, panH, panT, Math.sin(ang) * R, cy, zBk + (R - Math.cos(ang) * R), base);
        pn.rotation.y = -ang;
        const sc = P(sw - 0.6, panH - 3, 1, Math.sin(ang) * R, cy, zBk + (R - Math.cos(ang) * R) + panT / 2 + 0.6, 0x2c3542);
        sc.rotation.y = -ang;
      }
    } else {
      P(w, panH, panT, 0, cy, zBk, base);                                 // パネル (平面)
      P(w - 2.4, panH - 3.2, 1, 0, cy + 0.6, zBk + panT / 2 + 0.6, 0x2c3542);  // 画面 (下ベゼルのみ約2cm厚)
    }"""
NEW_MON_SCR = u"""    if (isCurve) {
      // ★v8.10 1500R 曲面: 外形幅 w が 弧の外側の角で決まる θ (monitorPanelDims.theta) の 薄いスラブ (縁 2.4 [est]) を
      //   7分割で並べ、 背面中央に 膨らみ (VESA/基板部・奥行 humpD) を足して 公式「スタンド無し D119.67」を作る。
      //   v3.7〜v8.9 は 弧長 = w・スラブ 12 で 奥行 17.5 (公式より 5.5 厚) + 画面を分割ごとに 0.6 細く描いていた。
      //   スクリーンは 1枚の円筒面 (幅 scrW × 高 scrH = 公式表示領域) にして 継ぎ目を無くす
      const R = pdm.curveR || 150, th = pdm.theta, seg = 7, sa = th / seg;
      for (let ci = 0; ci < seg; ci++) {
        const ang = (ci - (seg - 1) / 2) * sa;
        const pn = P(R * sa + 0.1, panH, panT, Math.sin(ang) * R, cy, zBk + (R - Math.cos(ang) * R), base);   // 分割の継ぎ目を 0.1 重ねる
        pn.rotation.y = -ang;
      }
      P(Math.min(w * 0.42, 34), Math.min(panH * 0.62, 22.5), humpD, 0, cy, zBk - panT / 2 - humpD / 2, met);   // 背面中央の膨らみ [est]
      const Rs = R - panT / 2 - 0.3, ha = (pdm.scrW / 2) / Rs;             // 画面 = パネル前面の 0.3cm 手前の円筒面
      const scr = new THREE.Mesh(new THREE.CylinderGeometry(Rs, Rs, pdm.scrH, 24, 1, true, Math.PI - ha, 2 * ha),
        new THREE.MeshLambertMaterial({ color: 0x2c3542, side: THREE.DoubleSide }));
      scr.position.set(0, scrY, zBk + R);
      g.add(scr);
    } else {
      P(w, panH, panT, 0, cy, zBk, base);                                 // パネル (平面)
      P(pdm.scrW, pdm.scrH, 0.4, 0, scrY, zBk + panT / 2 + 0.1, 0x2c3542);  // 画面 (表示領域。下ベゼルが厚い。前面から 0.3 出る)
    }"""

# ═══ ⑧ 家具シートの寸法欄 (昇降レンジ / パネルのみ寸法) ═══════════════════
OLD_DIMROWS = u"""      rows.push('マウント: 「' + (arm ? (arm.name || 'モニターアーム') : 'モニターアーム') +
                '」のアーム上 (画面中心 床から ' + tipN(y) + 'cm)');
    }
  }
  return '<div class="dim-note">📐 ' + rows.map(esc).join('<br>') + '</div>';
}"""
NEW_DIMROWS = u"""      rows.push('マウント: 「' + (arm ? (arm.name || 'モニターアーム') : 'モニターアーム') +
                '」のアーム上 (画面中心 床から ' + tipN(y) + 'cm)');
    }
  }
  if (isMonitorItem(it)) {   // ★v8.10 モニター: マウント中は パネルのみの公式寸法 / 床置きは スタンド昇降のレンジ
    const pdm = monitorPanelDims(it), lift = monitorLiftCm(it);
    const scr = ' / 表示領域 ' + tipN(pdm.scrW) + '×' + tipN(pdm.scrH) + 'cm' + (pdm.curve ? ' (1500R 曲面)' : '');
    if (isMountedItem(it)) {
      rows.push('パネルのみ: W' + tipN(it.w) + ' × D' + tipN(pdm.depth) + ' × H' + tipN(pdm.panH) +
                'cm (スタンドを外した公式値)' + scr);
    } else if (lift !== null) {
      rows.push('スタンド昇降: 高さ ' + tipN(h) + '〜' + tipN(h + lift) + 'cm (公式 ' + Math.round(lift * 10) +
                'mm) — 3Dは最低位置で表示' + scr);
    }
  }
  return '<div class="dim-note">📐 ' + rows.map(esc).join('<br>') + '</div>';
}
// ★v8.10 スタンドの昇降量 (cm)。 specNote の「昇降130mm」「昇降0-90mm」から拾う。無ければ null
function monitorLiftCm(it) {
  const m = specTextOf(it).match(/昇降\\s*(?:0\\s*[-〜~]\\s*)?(\\d{2,3})\\s*mm/);
  return m ? Math.round(parseInt(m[1], 10)) / 10 : null;
}"""

# ═══ ⑨ CATALOG_SEED (specNote 追記のみ) ═══════════════════════════════════
SEED_NOTES = {
    u'MAG 342CQR E2 (9S6-3DB64H-070)':
        u' ★v8.10 (2026-09-19): 表示領域 797.22(H)×333.72(V)mm (公式 datasheet)。 ベゼル 左右 各0.57cm (=(80.86−79.72)/2 公式値の差分) / '
        u'上 0.7・下 2.3cm [est: 公式正面写真の画素比率、 合計 3.0 は公式差分]。 1500R曲面の矢高 ≈5.5cm (幾何計算) '
        u'→ 3Dは 外形幅80.9 の弧 (7分割・縁の厚み2.4 [est]) + 背面中央の膨らみ (奥行4.2) + 円筒面スクリーンで 外形 W80.9×D12.0×H36.4 を作る (v8.9 までは 弧長=80.9・厚12 で 奥行17.5cm と 5.5cm 厚すぎた)。 '
        u'VESA 75×75 の中心位置は公式に記載なし → パネル中心と仮定 [est]。 昇降 0-90mm は床置き時の家具シートに レンジ表示。',
    u'EX2710':
        u' ★v8.10 (2026-09-19): 表示領域は公式非公表 → 27型 16:9 の計算値 597.9×336.3mm [est]。 ベゼル 左右 各0.8cm (計算差分) / '
        u'上 0.8 [est: 公式正面写真] ・下 3.8cm (=38.22−33.63−0.8)。 v8.9 までの3Dは 画面 59.0×35.0 (=1.69:1) で 縦が 1.4cm 高く 横が 0.8cm 狭かった。 '
        u'VESA 100×100 の中心位置は公式に記載なし → パネル中心と仮定 [est]。 昇降 130mm は床置き時の家具シートに 41〜54cm のレンジ表示。',
    u'45-241-224':
        u' ★v8.10 (2026-09-19): リーチ (ポール中心〜VESA面) を 36〜65cm・スイング ±90° で UI 調整可 (armReach / armSwing)。 '
        u'下限 36 = 公式上面図「折り畳み 360mm」(ベース後端〜VESA面の全長) を ポール中心基準に読んだ控えめな値。 '
        u'上限は 40+231·cos(第1アーム仰角)+293+86 なので VESA高さを上げるほど縮む (既定高 24cm で 約59.5cm)。 '
        u'スイング上限は 公式寸法図 p3 上面図の ベース回転 180°。 肘 360°/手首 360° は 手首が常にポール軸の真正面に来る解 (実機のパン関節相当) で消化。',
}
CMT_ADD = (u' ★v2.14 の変更点 (2026-09-19): **モニター2機種の 3D を公式実寸へ是正 + モニターアームの リーチ/スイング調整**。 '
           u'MSI MAG 342CQR E2 は 弧長=幅・スラブ12 で描いていたため スタンド無しの奥行が 17.5cm (公式 11.97) と 5.5cm 厚く、 '
           u'画面も 5分割で各0.6cm 細く (幅77.9 / 公式表示領域 79.7)・継ぎ目4本 → 外形幅80.9 の薄い弧 + 背面の膨らみ (奥行12.0) + 円筒面スクリーン 79.7×33.4 (公式 datasheet) へ。 '
           u'BenQ EX2710 は 画面 59.0×35.0 (1.69:1) → 27型16:9 の計算値 59.8×33.6 [est] へ。 上ベゼル/下ベゼルの配分は公式非公表のため公式正面写真の比率 [est]。 '
           u'エルゴトロン LX は `armReach` (36〜65cm、 null=従来の折り畳み姿勢) と `armSwing` (±90°) を追加、 2関節の逆運動学で姿勢を解き マウント中モニターが追従する。 '
           u'寸法 (w/d/h) は3商品とも不変、 specNote への追記のみ ★アプリ v8.10')


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def rep1(src, old, new, what):
    assert src.count(old) == 1, u'%s の置換元が %d 箇所 (1でない)' % (what, src.count(old))
    return src.replace(old, new, 1)


def main():
    src = io.open(P, encoding='utf-8').read()
    rd_before = sha(RD_PAT, src)
    m0 = re.search(CS_PAT, src, re.S)
    cs = json.loads(m0.group(1))
    raw_before = m0.group(1)

    if cs['version'] == '2.14' and MARK in src:
        print(u'適用0件 / skip 全件 (既に CATALOG_SEED v2.14 + armReachRaw = 適用済み)')
        return 0
    assert cs['version'] == '2.13', u'CATALOG_SEED が v2.13 でない: %s' % cs['version']
    assert len(cs['items']) == 37, u'商品が 37件でない: %d' % len(cs['items'])
    assert MARK not in src

    # ① ARM 定数
    src = rep1(src, OLD_ARM_TAIL, NEW_ARM_TAIL, u'① ARM 定数 (reachMin/reachMax/swingMax)')
    # ② armPose
    src = rep1(src, OLD_POSE_HEAD, NEW_POSE_HEAD, u'② armReachRaw / armReach / armSwing')
    src = rep1(src, OLD_POSE_A, NEW_POSE_A, u'② armPose 水平面 IK')
    src = rep1(src, OLD_POSE_B, NEW_POSE_B, u'② armPose 戻り値 (sw / reach / reachMax)')
    src = rep1(src, OLD_ATTACH, NEW_ATTACH, u'② armAttachPoint の rotY にスイング')
    # ③ 3D
    src = rep1(src, OLD_ARM_TIP, NEW_ARM_TIP, u'③ チルター/VESAプレートをスイング方向へ')
    # ④ key / cleanItem
    src = rep1(src, OLD_KEY, NEW_KEY, u'④ syncItemMesh の buildKey')
    src = rep1(src, OLD_CLEAN, NEW_CLEAN, u'④ cleanItem に armReach / armSwing')
    # ⑤ UI
    src = rep1(src, OLD_UI, NEW_UI, u'⑤ 家具シートに リーチ/スイング ブロック')
    src = rep1(src, OLD_SETTER, NEW_SETTER, u'⑤ setArmReach / setArmSwing / 干渉警告')
    # ⑥ hooks
    src = rep1(src, OLD_HOOK, NEW_HOOK, u'⑥ __noza.arms / reach / swing / monDims')
    # ⑦ モニター実寸
    src = rep1(src, OLD_PDIMS, NEW_PDIMS, u'⑦ monitorPanelDims (表示領域・ベゼル・矢高)')
    src = rep1(src, OLD_AABB, NEW_AABB, u'⑦ mountedAabb の奥行')
    src = rep1(src, OLD_STAND, NEW_STAND, u'⑦ 3D スタンド (支柱を後端へ) / 膨らみ / scrY')
    src = rep1(src, OLD_MON_SCR, NEW_MON_SCR, u'⑦ 3D 曲面/平面スクリーン')
    # ⑧ 家具シートの寸法欄
    src = rep1(src, OLD_DIMROWS, NEW_DIMROWS, u'⑧ 寸法欄 (昇降レンジ / パネルのみ)')

    # ⑨ CATALOG_SEED (specNote 追記のみ)
    hits = {}
    for it in cs['items']:
        if it.get('model') in SEED_NOTES:
            hits[it['model']] = it
    assert len(hits) == 3, u'対象3商品が見つからない: %s' % list(hits.keys())
    others = [i for i in cs['items'] if i.get('model') not in SEED_NOTES]
    assert len(others) == 34
    others_raw = [json.dumps(i, ensure_ascii=False, separators=(',', ':')) for i in others]
    for r in others_raw:
        assert r in raw_before, u'他商品の元の直列化が room.html の生テキストに無い (シードの書式が変わっている?)'
    dims_before = dict((k, (v['w'], v['d'], v['h'])) for k, v in hits.items())
    for k, it in hits.items():
        assert SEED_NOTES[k] not in it['specNote']
        it['specNote'] = it['specNote'] + SEED_NOTES[k]
    for k, it in hits.items():
        assert (it['w'], it['d'], it['h']) == dims_before[k], u'寸法が変わった'
    cs['version'] = '2.14'
    cs['updatedAt'] = '2026-09-19'
    cs['_comment'] += CMT_ADD

    m = re.search(CS_PAT, src, re.S)
    new_raw = json.dumps(cs, ensure_ascii=False, separators=(',', ':'))
    for r in others_raw:
        assert r in new_raw, u'他商品がバイト単位で不変でない'
    src = src[:m.start()] + 'var CATALOG_SEED = ' + new_raw + ';\n' + src[m.end():]

    assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用9件')
    print(u'  ① ARM: reachMin 36 / reachMax 65 / swingMax 90 (公式寸法図 DIM2-056)')
    print(u'  ② armPose: 水平面 2リンク IK (armReach) + スイング (armSwing)。 null は従来の解と同一')
    print(u'  ③ 3D: チルター/VESAプレートをスイング方向へ')
    print(u'  ④ buildKey / cleanItem に armReach・armSwing')
    print(u'  ⑤ UI: リーチ/スイング スライダー + −/既定/＋ ボタン + 干渉警告 (scanObstacle)')
    print(u'  ⑥ __noza.arms に reach/swing、 __noza.reach / swing / monDims フック')
    print(u'  ⑦ monitorPanelDims: 表示領域・ベゼル・曲面 (薄い弧+背面の膨らみ)。 MSI 奥行 17.5→12.0 / 画面 77.9×33.4→79.7×33.4 / BenQ 59.0×35.0→59.8×33.6')
    print(u'  ⑧ 家具シート: 床置きは スタンド昇降レンジ / マウント中は パネルのみ寸法+表示領域')
    print(u'  ⑨ CATALOG_SEED v2.13 → v2.14: MSI / BenQ / エルゴトロン の specNote 追記のみ (他34商品 バイト単位不変)')
    print(u'ROOM_DATA sha256 %s (不変)' % rd_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

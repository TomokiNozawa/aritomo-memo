# -*- coding: utf-8 -*-
u"""v8.6: LOWYA アユリナ 2点 (ドレッサーデスク幅120+正方形ミラー / ハイチェスト幅80) を 洋室4.5帖 に追加。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_6.py

冪等 (再実行で「適用0件 / skip 全件」)。 ROOM_DATA は **一切変更しない** (sha256 前後一致を assert)。
CATALOG_SEED v2.9 → v2.10 (35 → 37商品)。

━━ 追加する商品 (寸法はすべて LOWYA 公式。 推定は est と明記) ━━━━━━━━━━━━━━━━━━━━
 ① アユリナ / ドレッサーデスク (幅120) 「ドレッサー+正方形ミラーセット / ウォルナット」
    商品番号 MLT4G_SB24MM / ¥69,980 税込 / 本体 120×48×71 + ミラー 60×60×2.5
 ② アユリナ / チェスト (幅80/120) 「ウォルナット(ハイチェスト)」
    商品番号 F501_05002_100HU1 / ¥49,990 税込 / 80×42×99.5

━━ 3Dモデル: 商品ごとに if を足さず CABINET_MODELS へデータ化 ━━━━━━━━━━━━━━━━━━━
FRIDGE_MODELS (v7.5) / BED_MODELS (v8.1) と同じ流儀で、 **脚付き引き出し家具の構成だけを
データで持ち、 描画は共通コード1本** にする。 次のチェスト/サイドボード/ドレッサーは
CABINET_MODELS に 1エントリ足すだけで描ける (ローチェスト幅120 も 行の割付を変えるだけ)。
引き出しの開閉は 既存の itemDrawerSet (リガーレ・エトナ・収納ベッドと同じ) に そのまま乗せ、
真鍮つまみは アザン3 の手掛けと同じ hideOpen で 開いた時に隠す。

★公式値だけで幾何が閉じることを確認済み (詳細は Box の README):
   天板厚 = 71 − 58.5(チェスト高) − 10(引き出し前板) = 2.5
   チェスト天面 58.5 = デスク引き出し部の下端 = 脚の長さ58 + アジャスター
   チェスト 58.5 = 天板2.0(est) + 12 + 19.5 + 19.5 + 台輪5.5(est)
   ハイチェスト 99.5 = 脚15 + 前板14 + 22×3 + 天板2.5(est) + 最下部の帯2.0(est)
   ミラーの後傾 = 公式の設置例「全高124cm」から逆算 acos((124−71)/60) ≒ 27.9°
⚠ 公式サイズ図 右上の「8」(デスク天板 右端の小さな水平寸法) は 起点が読めず **未解釈**。
   数値を捏ねず モデルには入れていない (README にも記録)。
"""
import hashlib
import io
import json
import os
import re
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'

SRC = u'出典 = LOWYA 公式商品ページ (2026-09-06 取得)。 LOWYA は Vue の CSR で curl では取れず ' \
      u'api.low-ya.com は 403 のため、 **実ブラウザ (catalog_scripts/fetch_lowya.py) で ' \
      u'買う予定のバリエーションを実際にクリックしてから** 取得している ' \
      u'(既定選択のまま読むと 別バリエーションの寸法を掴む)。 一次資料は ' \
      u'catalog\\商品公式資料\\LOWYA_アユリナ_*\\ に README 付きで保存。'

WN = u'#835845'      # ウォルナット (公式 白背景スタジオ撮影 07.jpg の前板 n=53,500 の中央値)
SN = u'#a77144'      # シャビーナチュラル (公式 白背景 12.jpg の側板 n=66,250 の中央値)

DRESSER = {
    "name": u"LOWYA アユリナ ドレッサーデスク 幅120 + 正方形ミラー (ウォルナット)",
    "model": u"アユリナ / ドレッサーデスク (幅120) ドレッサー+正方形ミラーセット ウォルナット / 商品番号 MLT4G_SB24MM",
    "room": "west45",
    "w": 120, "d": 48, "h": 71,
    "color": WN,
    "colors": [
        {"name": u"ウォルナット (MLT4G_SB24MM)", "hex": WN},
        {"name": u"シャビーナチュラル (MLT4G_7TZ6KT)", "hex": SN},
    ],
    "type": "cabinet",
    "url": "https://www.low-ya.com/goods/MLT4G",
    "install": {
        "openKind": "drawer",
        "doorFront": 34,
        "doorFrontFrom": u"本体前面",
        "doorNote": u"[est] 公式は引き出しの有効内寸 (デスク 奥行34 / チェスト 奥行28.5) までしか"
                    u"書いておらず、 引き切った時の張り出し量の記載が無い。 深い方の34をそのまま採用",
        "note": u"半完成品 (取っ手と脚の取り付けのみ)。 壁からのすきま・上方のすきまは公式に指定なし",
    },
    "specNote": (
        u"LOWYA アユリナ / ドレッサーデスク (幅120)「[幅120] ドレッサーデスク 収納一体型」 の "
        u"**ドレッサー+正方形ミラーセット / ウォルナット** (商品番号 **MLT4G_SB24MM**) / "
        u"**¥69,980 (税込) 送料無料** / 日本製 / あんしん1年保証 / 複数梱包商品 / "
        u"半完成品 (取っ手と脚の取り付けのみ)。 " + SRC + u"\n"
        u"★公式サイズ: **ミラー 幅60×奥行60×高さ2.5 / 本体 幅120×奥行48×高さ71**。 "
        u"重量 ミラー約4kg・本体約36kg。 耐荷重 デスク天板 約10kg / チェスト天板 約8kg / 引出すべて 約5kg。 "
        u"素材 天板:強化紙 / 本体:プリント / 脚部:ラバー無垢 / つまみ:真鍮。 "
        u"梱包 62×62×5(6.5kg) + 38×51×62(20kg) + 124×51×13(25kg)。\n"
        u"★公式サイズ図の実数: デスク天板 幅100 / デスク引き出し 前板高さ10・幅 ①49.5 ②49.5 / "
        u"チェスト部 幅40×奥行41.6×高さ58.5 で **右へ20はみ出す** (100+20=120) / "
        u"チェスト引き出し 前板高さ ③12・④19.5・⑤19.5 / 脚の長さ58 / 脚の足元は前後 約37.5 / "
        u"脚の足元〜チェスト左面 約80 / 天板裏のレール幅 95.8。 "
        u"引き出し有効内寸 ①②幅40×奥行34×高さ5 / ③幅23×奥行28.5×高さ8 / ④⑤幅23×奥行28.5×高さ12.5。\n"
        u"★公式値だけで幾何が閉じる (推定を足していない): 天板厚 = 71−58.5−10 = **2.5** / "
        u"チェスト天面58.5 = デスク引き出し部の下端 = 脚58 + アジャスター / "
        u"チェスト58.5 = 天板2.0[est] + 12 + 19.5 + 19.5 + 台輪5.5[est]。\n"
        u"★ミラー: 鏡面 57.8×57.8 (枠は四周1.1)。 背面は平らでスタンドが無い = **天板に立てかけて使う**。 "
        u"公式の設置例の全高は **正方形124cm / 長方形(60×80)138cm** で、 3Dモデルの後傾角は "
        u"acos((124−71)/60) ≒ **27.9°** として この124を再現している (角度そのものは公式に記載なし)。 "
        u"⚠ ウォルナットに 長方形ミラーセットの設定は無い (選択不可)。\n"
        u"⚠ **公式サイズ図の右上にある「8」** (デスク天板 右端の小さな水平寸法) は 起点が読めず未解釈。 "
        u"数値を捏ねないため 3Dモデルには反映していない (要確認)。\n"
        u"⚠ 公式に記載が無い項目 (est を置いた分): チェストの天板厚2.0・台輪5.5・デスク引き出し部の奥行44・"
        u"脚の太さ (上φ4.4→下φ2.6)・脚の傾き・つまみの寸法。 引き切った時の張り出し量も公式には無い。\n"
        u"⚠ 販売状況 (2026-09-06 時点): **ウォルナットは「販売準備中」** (シャビーナチュラルは在庫あり)。\n"
        u"★カラーの16進は **公式製品画像からの画素実測** (推定色は使っていない): "
        u"ウォルナット #835845 = 白背景スタジオ撮影 07.jpg の デスク前板 + チェスト前板 n=53,500 の中央値 "
        u"(sd≈20〜26 はウォルナットの木目そのもの) / シャビーナチュラル #a77144 = 白背景 12.jpg の側板 "
        u"n=66,250 の中央値 (sd≈14)。 ⚠ 室内カットからは #c2976d と明るく出る (照明込みなので albedo に使わない)。\n"
        u"★3Dモデル: CABINET_MODELS の1エントリ (デスクユニット + チェストユニット + 脚2本 + 立てかけミラー)。 "
        u"引き出しの開閉は 既存の itemDrawerSet、 真鍮つまみは 開けると隠れる (アザン3 の手掛けと同じ hideOpen)。"
    ),
    "memo": "",
}

CHEST = {
    "name": u"LOWYA アユリナ ハイチェスト 幅80 (ウォルナット)",
    "model": u"アユリナ / チェスト (幅80/120) ウォルナット(ハイチェスト) / 商品番号 F501_05002_100HU1",
    "room": "west45",
    "w": 80, "d": 42, "h": 99.5,
    "color": WN,
    "colors": [
        {"name": u"ウォルナット (F501_05002_100HU1)", "hex": WN},
        {"name": u"シャビーナチュラル (F501_05002_100H21)", "hex": SN},
    ],
    "type": "cabinet",
    "url": "https://www.low-ya.com/goods/F501_05002",
    "install": {
        "openKind": "drawer",
        "doorFront": 34,
        "doorFrontFrom": u"本体前面",
        "doorNote": u"[est] 公式は引き出しの有効内寸 奥行34 までしか書いておらず、"
                    u"引き切った時の張り出し量の記載が無いので 34 をそのまま採用",
        "note": u"半完成品 (取っ手と脚の取り付けのみ)。 "
                u"⚠公式注意書き「引き出しを同時に引き出すと チェストが前倒れする恐れ」あり",
    },
    "specNote": (
        u"LOWYA アユリナ / チェスト (幅80/120)「[幅80/120] 日本製 チェスト 真鍮 選べる2サイズ」 の "
        u"**ウォルナット(ハイチェスト)** (商品番号 **F501_05002_100HU1**) / "
        u"**¥49,990 (税込) 送料無料** / 日本製 / AR対応 / あんしん1年保証 / "
        u"半完成品 (取っ手と脚の取り付けのみ)。 " + SRC + u"\n"
        u"★公式サイズ: **幅80×奥行42×高さ99.5** (ローチェストは 幅120×奥行42×高さ74.5)。 重量 34kg。 "
        u"耐荷重 天板 約20kg / 引き出し 約6kg。 素材 本体:プリント紙化粧繊維板 / 前板:強化紙化粧繊維板 / "
        u"脚部:ラバー無垢材 / つまみ:真鍮。 梱包 84×46×63 (約37kg)。\n"
        u"★公式サイズ図 + 公式の引き出し表: ハイチェストは **引き出し 計5杯** "
        u"(1段目に小引出2杯 + 2〜4段目が全幅1杯ずつ)。 脚15 / 1段目 前板高さ14 (幅39.5×2) / "
        u"2〜4段目 前板高さ 各22。 引き出し有効内寸 = 1段目 幅32.5×奥行34×高さ12 (2杯とも) / "
        u"**2・3段目 幅70.5×奥行34×高さ17.7** / 4段目 幅70.5×奥行34×高さ16.2。 "
        u"(サイズ図だけでは3段目がどちらか読めないが、 公式画像の引き出し表が「引き出し(2・3段目)」と"
        u"明記していて確定した)\n"
        u"⚠ 15 + 14 + 22×3 = 95 と 全高99.5 の差 4.5 の内訳は公式に無く、 天板厚2.5[est] + "
        u"最下部の帯2.0[est] と置いている。 引き切った時の張り出し量・脚の太さ・つまみの寸法も公式には無い。\n"
        u"⚠ 販売状況 (2026-09-06 時点): **ウォルナット(ハイチェスト)は「販売準備中」** "
        u"(シャビーナチュラル(ハイチェスト)=予約受付中 / ウォルナット(ローチェスト)=残り4点)。\n"
        u"★カラーの16進は 同シリーズのドレッサーデスクと同じ公式実測値 (ウォルナット #835845 / "
        u"シャビーナチュラル #a77144)。 ⚠ ウォルナット(ハイチェスト)の白背景スタジオ写真は公式に無く "
        u"室内カットしか無い (室内カットからは #704834〜#5b3628 と暗く出る = 照明込みなので albedo に使わない)。\n"
        u"★3Dモデル: CABINET_MODELS の1エントリ (本体1ユニット + 丸テーパー脚4本)。 "
        u"ローチェスト(幅120・7杯)も 行の割付を足すだけで描ける。"
    ),
    "memo": "",
}

# ═══ JS ①: CABINET_MODELS レジストリ (共通ロジック) ═══════════════════════════════
JS_REGISTRY = u"""// ═══ ★v8.6 脚付き引き出し家具 (type 'cabinet') の構成レジストリ ═══
//   チェスト / ドレッサーデスク / サイドボードは 「箱 + 引き出しの段 + 脚」 の組み合わせでできている。
//   商品ごとに if を足すと 1台を直しても他へ伝わらないので、 FRIDGE_MODELS (v7.5) /
//   BED_MODELS (v8.1) と同じ流儀で **構成だけをデータで持ち、 描画は共通コード1本** にする。
//   新商品は CABINET_MODELS に 1エントリ足すだけ (ローチェスト幅120 も 行の割付を変えるだけ)。
//
//   test  … specTextOf (商品名+specNote+memo) への正規表現。 **商品番号で当てる** (品名の部分一致は
//           他商品の specNote にも出るので当たり事故のもと。 例: ドレッサーの説明にも「チェスト」が出る)
//   w/d/h … 公式外寸。 アイテムの寸法を変えた時は この比で全パーツをスケールする
//   units … 箱の集合 (上から下ではなく 部位ごと)。 x0/z0 = 中心からのオフセット [cm]
//     y0/h … 下端の高さ / 高さ、 topT = 天板の厚み、 plinth = 台輪 (0 = 無し)
//     rows … **上から順の** 引き出しの段 { fh:前板の高さ, n:横に並ぶ杯数, inner:{w,d,h} 有効内寸, label }
//   legs  … [{ x, z, h, dTop, dBot, sx, sz }] … x/z=取付位置 (上端)、 sx/sz=足元のずれ (開き)
//   knob  … つまみ { r:半径, len:出, col } — 開けると隠れる (アザン3 の手掛けと同じ hideOpen)
//   set   … セット品。 kind:'mirror' = 天板に立てかける鏡 { w,h,t,glassW,glassH,onUnit,totalH }
//           totalH = 公式の設置例の全高。 **後傾角はここから逆算する** (角度は公式に無い)
const CABINET_MODELS = [
  {
    // LOWYA アユリナ / ドレッサーデスク (幅120) 「ドレッサー+正方形ミラーセット」 MLT4G_SB24MM
    test: /MLT4G|アユリナ ドレッサーデスク/,
    label: 'ドレッサーデスク + 立てかけミラー (アユリナ 幅120)',
    w: 120, d: 48, h: 71,
    knob: { r: 0.85, len: 2.2, col: 0xb08d57 },        // 真鍮つまみ (公式: つまみ 真鍮)
    adjuster: true,                                     // 脚先のアジャスター (公式画像で確認)
    units: [
      { key: 'desk', x0: -10, z0: 0, w: 100, d: 48, y0: 58.5, h: 12.5, topT: 2.5, plinth: 0,
        rows: [{ fh: 10, n: 2, inner: { w: 40, d: 34, h: 5 }, label: 'デスク引き出し' }] },
      // チェスト部: 幅40 のうち 20 がデスク天板の下・20 が右へはみ出す。 背面はデスクと揃う
      { key: 'chest', x0: 40, z0: -3.2, w: 40, d: 41.6, y0: 0, h: 58.5, topT: 2.0, plinth: 5.5,
        rows: [{ fh: 12,   n: 1, inner: { w: 23, d: 28.5, h: 8 },    label: 'チェスト1段目' },
               { fh: 19.5, n: 1, inner: { w: 23, d: 28.5, h: 12.5 }, label: 'チェスト2段目' },
               { fh: 19.5, n: 1, inner: { w: 23, d: 28.5, h: 12.5 }, label: 'チェスト3段目' }] }
    ],
    // 脚は左端の2本だけ (右はチェストが支える)。 足元は前後 約37.5 に開く (公式値)
    legs: [{ x: -54, z: -13, h: 58.5, dTop: 4.4, dBot: 2.6, sx: -4, sz: -5.75 },
           { x: -54, z: 13,  h: 58.5, dTop: 4.4, dBot: 2.6, sx: -4, sz: 5.75 }],
    set: { kind: 'mirror', onUnit: 'desk', w: 60, h: 60, t: 2.5, glassW: 57.8, glassH: 57.8,
           totalH: 124, label: '正方形ミラー' }
  },
  {
    // LOWYA アユリナ / チェスト (幅80/120) 「ウォルナット(ハイチェスト)」 F501_05002_100HU1
    test: /F501_05002|アユリナ ハイチェスト/,
    label: 'ハイチェスト 5杯 (アユリナ 幅80)',
    w: 80, d: 42, h: 99.5,
    knob: { r: 0.85, len: 2.2, col: 0xb08d57 },
    adjuster: false,
    units: [
      { key: 'body', x0: 0, z0: 0, w: 80, d: 42, y0: 15, h: 84.5, topT: 2.5, plinth: 0,
        rows: [{ fh: 14, n: 2, inner: { w: 32.5, d: 34, h: 12 },   label: '1段目 小引出' },
               { fh: 22, n: 1, inner: { w: 70.5, d: 34, h: 17.7 }, label: '2段目' },
               { fh: 22, n: 1, inner: { w: 70.5, d: 34, h: 17.7 }, label: '3段目' },
               { fh: 22, n: 1, inner: { w: 70.5, d: 34, h: 16.2 }, label: '4段目' }] }
    ],
    legs: [{ x: -34, z: -15, h: 15, dTop: 4.0, dBot: 2.8, sx: -1.2, sz: -1.2 },
           { x: 34,  z: -15, h: 15, dTop: 4.0, dBot: 2.8, sx: 1.2,  sz: -1.2 },
           { x: -34, z: 15,  h: 15, dTop: 4.0, dBot: 2.8, sx: -1.2, sz: 1.2 },
           { x: 34,  z: 15,  h: 15, dTop: 4.0, dBot: 2.8, sx: 1.2,  sz: 1.2 }],
    set: null
  }
];
function cabinetModelOf(nm) {
  for (let i = 0; i < CABINET_MODELS.length; i++) {
    if (CABINET_MODELS[i].test.test(nm)) return CABINET_MODELS[i];
  }
  return null;
}

"""

# ═══ JS ②: buildItemParts に type 'cabinet' の共通描画を追加 ═══════════════════════
JS_BRANCH = u"""  } else if (type === 'cabinet' && cabinetModelOf(nm)) {
    // ★v8.6 脚付き引き出し家具 (CABINET_MODELS のデータ + この共通コード1本だけで描く)。
    //   ユニット (箱) → 台輪 → 天板 → 引き出しの段 (itemDrawerSet で開閉登録) → 脚 → セット品。
    //   商品固有の分岐はここに書かない。 追加は CABINET_MODELS に 1エントリだけ。
    const CM = cabinetModelOf(nm);
    const kx = w / CM.w, kz = d / CM.d, ky = h / CM.h;        // 公式外寸からの倍率 (寸法変更でも比率維持)
    const brass = new THREE.Color((CM.knob && CM.knob.col) || 0xb08d57);
    const silver = new THREE.Color(0xa8abae);
    const seam = dark.clone().lerp(base, 0.45);
    const legCol = base.clone().lerp(lite, 0.10);
    const KN = CM.knob || { r: 0.85, len: 2.2 };
    CM.units.forEach(function (U) {
      const uw = U.w * kx, ud = U.d * kz, uh = U.h * ky, uy = U.y0 * ky;
      const ux = U.x0 * kx, uz = U.z0 * kz;
      const topT = (U.topT || 0) * ky, pl = (U.plinth || 0) * ky;
      const uf = uz + ud / 2;                                 // このユニットの前面 (ローカル z)
      if (pl > 0) {                                           // 台輪 (床際が少し引っ込む)
        P(uw - 3, pl, ud - 3, ux, uy + pl / 2, uz, seam);
      }
      P(uw, uh - pl - topT, ud, ux, uy + pl + (uh - pl - topT) / 2, uz, base);      // 本体
      if (topT > 0) {
        P(uw, topT, ud, ux, uy + uh - topT / 2, uz, base.clone().lerp(lite, 0.18)); // 天板
      }
      const defs = [];
      let y = uy + uh - topT;                                 // 引き出しの段は 天板の下から 上→下へ
      U.rows.forEach(function (R, ri) {
        const fh = R.fh * ky, n = R.n || 1, gp = 0.7;
        const fw = (uw - gp * (n + 1)) / n;
        for (let i = 0; i < n; i++) {
          const cx = ux - uw / 2 + gp * (i + 1) + fw * (i + 0.5);
          // 真鍮の丸つまみ (前板の中央)。 開けると hideOpen で隠れる = アザン3 の手掛けと同じ流儀
          const kb = CYL(KN.r, KN.len, cx, y - fh / 2, uf + KN.len / 2, brass);
          kb.rotation.x = Math.PI / 2;
          defs.push({ key: U.key + (ri + 1) + (n > 1 ? '_' + (i + 1) : ''), kind: 'drawer',
                      handle: 'none', hideOpen: [kb],
                      label: R.label + (n > 1 ? ' ' + (i + 1) + '杯目' : '') +
                             ' (内寸 ' + R.inner.w + '×' + R.inner.d + '×' + R.inner.h + 'cm)',
                      x0: cx, bw: fw, y0: y - fh + 0.4, rh: fh - 0.8, depth: R.inner.d * kz });
        }
        y -= fh;
      });
      // ctx.d には **このユニットの前面 ×2** を渡す = 前面が本体と違う位置のユニット
      // (ドレッサーのチェスト部は 奥行41.6 でデスク48 より手前が引っ込む) でも面が合う
      itemDrawerSet(g, it, defs, { w: w, d: uf * 2, base: base, dark: dark, lite: lite, silver: silver });
    });
    (CM.legs || []).forEach(function (L) {                    // 丸テーパー脚 (ラバー無垢材)
      const lh = L.h * ky, sx = (L.sx || 0) * kx, sz = (L.sz || 0) * kz;
      const lx = L.x * kx, lz = L.z * kz;
      const lg = new THREE.Mesh(new THREE.CylinderGeometry(L.dTop / 2, L.dBot / 2, Math.max(lh, 1), 12),
        new THREE.MeshLambertMaterial({ color: legCol }));
      // 傾けると 円筒の下端の縁が床へ潜るので、 合成した傾きから 接地する中心高さを出す
      // (脚を傾ける商品はこれから何点も来るので、 商品ごとに数値で逃げず 式で持つ)
      const th = Math.atan2(Math.hypot(sx, sz), lh);
      lg.position.set(lx + sx / 2, (lh / 2) * Math.cos(th) + (L.dBot / 2) * Math.sin(th), lz + sz / 2);
      lg.rotation.z = Math.atan2(sx, lh);                     // 足元が外へ開く (公式: 前後 約37.5)
      lg.rotation.x = -Math.atan2(sz, lh);
      g.add(lg);
      if (CM.adjuster) CYL(L.dBot / 2 + 0.35, 0.6, lx + sx, 0.3, lz + sz, silver);
    });
    if (CM.set && CM.set.kind === 'mirror') {
      // セット品のミラー: 背面が平らでスタンドが無い = 天板に **立てかける**。
      //   後傾角は 公式の設置例の全高 (totalH) から逆算する = 角度を勝手に決めない。
      const S = CM.set;
      let host = CM.units[0];
      CM.units.forEach(function (u2) { if (u2.key === S.onUnit) host = u2; });
      const topY = (host.y0 + host.h) * ky;                   // 立てかける面 (デスク天板の上面)
      const mw = S.w * kx, mh = S.h * ky, mt = S.t * kz;
      const lean = Math.acos(Math.min(Math.max((S.totalH * ky - topY) / Math.max(mh, 1), 0), 1));
      const mg = new THREE.Group();
      mg.position.set(host.x0 * kx, topY, -d / 2 + mh * Math.sin(lean) + mt);   // 上端が背面に来る位置
      mg.rotation.x = -lean;
      g.add(mg);
      const addTo = function (sx, sy, sz, px, py, pz, col) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(Math.max(sx, 0.3), Math.max(sy, 0.3), Math.max(sz, 0.3)),
          new THREE.MeshLambertMaterial({ color: col }));
        m.position.set(px, py, pz);
        mg.add(m);
        return m;
      };
      addTo(mw, mh, mt, 0, mh / 2, 0, base);                                     // 木枠
      addTo(S.glassW * kx, S.glassH * ky, 0.4, 0, mh / 2, mt / 2 + 0.2, 0xdbe6ea);  // 鏡面
    }
"""


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def rep1(src, old, new, what):
    assert src.count(old) == 1, u'%s の置換元が %d 箇所 (1でない)' % (what, src.count(old))
    return src.replace(old, new, 1)


def main():
    src = io.open(P, encoding='utf-8').read()
    rd_before = sha(RD_PAT, src)
    cs = json.loads(re.search(CS_PAT, src, re.S).group(1))

    if cs['version'] == '2.10' and 'CABINET_MODELS' in src:
        print(u'適用0件 / skip 全件 (既に CATALOG_SEED v2.10 + CABINET_MODELS = 適用済み)')
        return 0
    assert cs['version'] == '2.9', u'CATALOG_SEED が v2.9 でない: %s' % cs['version']
    assert len(cs['items']) == 35, u'既存商品が 35件でない: %d' % len(cs['items'])
    assert 'CABINET_MODELS' not in src, u'CABINET_MODELS が既にある'
    names = set(i['name'] for i in cs['items'])
    for it in (DRESSER, CHEST):
        assert it['name'] not in names, u'同名の商品が既にある: %s' % it['name']

    # ── test 正規表現が 自分の商品にだけ当たることを機械 assert (当たり事故の予防) ──
    #    specTextOf = name + specNote + memo と同じ文字列で照合する。
    tests = [(u'MLT4G|アユリナ ドレッサーデスク', DRESSER), (u'F501_05002|アユリナ ハイチェスト', CHEST)]
    for pat, owner in tests:
        rx = re.compile(pat)
        for it in cs['items'] + [DRESSER, CHEST]:
            txt = it['name'] + u' ' + it.get('specNote', '') + u' ' + it.get('memo', '')
            hit = bool(rx.search(txt))
            assert hit == (it['name'] == owner['name']), \
                u'CABINET_MODELS の test /%s/ が別商品に当たる (or 当たらない): %s' % (pat, it['name'])
    print(u'  機械照合: CABINET_MODELS の test 2本は それぞれ自分の商品にだけ当たる (37件で確認)')

    # ── CATALOG_SEED へ 2件追加 (既存 35件は触らない) ──
    before = json.dumps(cs['items'], ensure_ascii=False, sort_keys=True)
    cs['items'].append(DRESSER)
    cs['items'].append(CHEST)
    assert json.dumps(cs['items'][:-2], ensure_ascii=False, sort_keys=True) == before, u'既存商品が変化した'
    cs['version'] = '2.10'
    cs['updatedAt'] = '2026-09-06'
    cs['_comment'] += (
        u' ★v2.10 の変更点 (2026-09-06): **LOWYA アユリナ 2点を 洋室4.5帖 (room=west45) に追加** — '
        u'①ドレッサーデスク 幅120 + 正方形ミラーセット / ウォルナット (MLT4G_SB24MM / 本体 120×48×71 + '
        u'ミラー 60×60×2.5 / ¥69,980) ②ハイチェスト 幅80 / ウォルナット (F501_05002_100HU1 / 80×42×99.5 / '
        u'¥49,990)。 寸法・耐荷重・素材・引き出しの有効内寸は すべて LOWYA 公式商品ページと公式サイズ図が出典 '
        u'(LOWYA は CSR なので curl では取れない → catalog_scripts/fetch_lowya.py で 実ブラウザで '
        u'**買うバリエーションをクリックしてから** 取得。 既定選択のまま読むと別バリエーションの寸法を掴む)。 '
        u'カラーの16進は 公式製品画像からの画素実測 (ウォルナット #835845 = 白背景スタジオ撮影の前板 n=53,500 の中央値)。 '
        u'一次資料は catalog\\商品公式資料\\LOWYA_アユリナ_ドレッサーデスク120\\ と '
        u'\\LOWYA_アユリナ_チェスト80\\ に README 付きで保存。 '
        u'3Dモデルは 商品ごとの if を足さず **CABINET_MODELS (脚付き引き出し家具の構成レジストリ) を新設** し、 '
        u'描画は共通コード1本に集約した (FRIDGE_MODELS / BED_MODELS と同じ流儀。 次のチェスト・サイドボード・'
        u'ローチェスト幅120 は 1エントリ足すだけ)。 引き出しの開閉は 既存の itemDrawerSet に乗せ '
        u'(ctx.d にユニットの前面×2 を渡すことで 奥行の違うユニットでも面が合う)、 真鍮つまみは '
        u'開けると隠れる (アザン3 の手掛けと同じ hideOpen)。 セットのミラーは 背面が平らでスタンドが無いため '
        u'天板に立てかける描画にし、 後傾角は 公式の設置例「全高124cm」から逆算している ★アプリ v8.6')

    src = (src[:re.search(CS_PAT, src, re.S).start()] + 'var CATALOG_SEED = '
           + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n'
           + src[re.search(CS_PAT, src, re.S).end():])

    # ── JS: レジストリ + 描画ブランチ ──
    src = rep1(src, u'function buildItemParts(g, it) {', JS_REGISTRY + u'function buildItemParts(g, it) {',
               u'JS① CABINET_MODELS の追加')
    src = rep1(src, u"  } else if (type === 'chair' && /オフィス|サリダ|C300|COFO|ゲーミング/.test(nm)) {",
               JS_BRANCH + u"  } else if (type === 'chair' && /オフィス|サリダ|C300|COFO|ゲーミング/.test(nm)) {",
               u'JS② type cabinet の描画ブランチ')

    assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)

    after = json.loads(re.search(CS_PAT, io.open(P, encoding='utf-8').read(), re.S).group(1))
    assert after['version'] == '2.10' and len(after['items']) == 37
    print(u'適用4件')
    print(u'  ① CATALOG_SEED: LOWYA アユリナ ドレッサーデスク 幅120 + 正方形ミラー (ウォルナット) を west45 へ追加')
    print(u'  ② CATALOG_SEED: LOWYA アユリナ ハイチェスト 幅80 (ウォルナット) を west45 へ追加')
    print(u'  ③ JS: CABINET_MODELS レジストリ + cabinetModelOf() を新設')
    print(u'  ④ JS: buildItemParts に type \'cabinet\' の共通描画を追加 (商品ごとの if は無し)')
    print(u'CATALOG_SEED v2.9 → v2.10 / 商品 35 → 37 / ROOM_DATA sha256 %s (不変)' % rd_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

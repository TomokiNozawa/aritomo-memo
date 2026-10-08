# -*- coding: utf-8 -*-
u"""v8.11: ケユカ 両開きダストボックス **LL (42L)** を キッチン (ldk / zone=kitchen) に追加。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_11.py

冪等 (再実行で「適用0件 / skip 全件」)。 ROOM_DATA は **一切変更しない** (sha256 前後一致を assert)。
CATALOG_SEED v2.14 → v2.15 (37 → 38商品)。 既存37商品は バイト単位で不変を assert。

━━ 公式値 (catalog\\商品公式資料\\KEYUCA_両開きダストボックスLL42L\\ に README 付きで保存) ━━
  商品ページ pid=3301142: W27 × D42 × H60.7 (開口時 H72.7)・42L (45L袋対応)・税込¥5,280・日本製
  公式 SIZE 画像 (sub07): 天面 27 / 奥行 42 / 高さ 60.7 / 開口時 72.7 / 全開時の上端スパン 27 / **底の幅 22.4**
  取説 p2 製品図: 42 / 60.7 / 72.7 / 開いたフタ上端 27 / 2台並べ 53 / 1台 26.5
  ⚠ 公式内の食い違い: 取説 p4 は「W26.5」、 商品ページと SIZE 画像は「W27」。 天面プレート (最大外形) の
    27 を w に採用 (設置検討は大きい側で見る。 L 版の 22/24 と同じ考え方)。

━━ 3Dモデル: L/LL で if を分けず DUSTBOX_MODELS へデータ化 ━━━━━━━━━━━━━━━━━━━━━━━━━
v5.3〜v8.10 の両開きゴミ箱は L (H50/W22) 専用の数値が描画コードに直書きされていて、
LL を足すと kY = h/50 の比例縮尺で 天面プレート厚・キャスター・ペダル・フタ開き寸法が全部ずれる。
FRIDGE_MODELS / BED_MODELS / CABINET_MODELS と同じ流儀で 寸法構成だけをデータで持ち、
描画は既存の1本のコードのまま にする (次の M/S サイズも 1エントリ足すだけ)。
  - L エントリは v8.10 の直書き値をそのまま転記 = L の見た目は不変 (フタ角の式も L は旧式のまま)。
  - LL のフタ: ヒンジ間 22 (製品図の実測) から 上端スパン 27 へ外へ倒れる。 L の式
    (asin(上昇量/フタ長)) は LL だと 12/11 > 1 で垂直に張り付きスパンが 22 になるので、
    スパン基準の式 (π/2 + asin((外端−ヒンジ)/フタ長)) を使う。 L では2式の差は 0.13° だが
    L の出力を変えないため L は旧式のまま (rise < Ll の時だけ旧式)。
"""
import hashlib
import io
import json
import re
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'
MARK = u'DUSTBOX_MODELS'

# ── ① レジストリ (buildItemParts の直前に挿入) ──
ANCHOR_REG = u'function buildItemParts(g, it) {\n'
NEW_REG = u"""// ═══ ★v8.11 両開きダストボックスの構成レジストリ (type 'trash' の ケユカ両開き) ═══
//   v5.3〜v8.10 は L (H50/W22) の数値が描画コードに直書きで、 LL を足すと kY=h/50 の比例縮尺で
//   天面プレート厚・キャスター・ペダル・フタの開き寸法が全部ずれる。 冷蔵庫/ベッド/引き出し家具と同じく
//   寸法構成だけをデータで持ち、 描画は1本のコードにする (M/S サイズも 1エントリ足すだけ)。
//   test   … specTextOf (名前+specNote+memo) への正規表現。 null = 既定 (L)
//   H/W/D  … 公式外形 (この値と商品の h/w/d の比で全体を伸縮)
//   yBody  … 本体上端 (= 天面プレート下端) / top・bot … 本体の上面・底面 [幅, 奥行] (四角錐台)
//   finger … 正面の指掛けくぼみ [幅, 高さ, 中心y] / pedal … [幅, 厚み, 突出, 中心y, 前面からのz]
//   caster … [半径, 背面からのz, 厚み] / open … フタ全開時 { h: 高さ, span: 上端の左右スパン, hinge: 中心〜ヒンジ }
const DUSTBOX_MODELS = [
  {
    // ケユカ 両開きダストボックス LL 42L (品番3301142)。★v8.11 追加
    //   公式: W27×D42×H60.7 / 開口時 H72.7 / 全開時の上端スパン27 / 底の幅22.4 (公式SIZE画像)。
    //   内訳 (取説 p2 製品図を 600dpi で実測・正面図の縮尺 9.09px/cm、 側面図は横に引き伸ばされた schematic なので
    //   奥行は比率で読む): 天面プレート厚 2.2 [est] / 本体上面 24.3×37.5 [実測] / 底 22.4 [公式]×36.0 [実測] /
    //   ペダル 幅14.5×厚1.9・前へ3.9・中心高5.2 [実測] / 後輪 半径3.5 [実測±0.5] / ヒンジ 中心から11.0 [実測]。
    //   catalog/商品公式資料/KEYUCA_両開きダストボックスLL42L/README.md 参照。
    test: /3301142|LL ?[（(]?42L/,
    label: 'ケユカ 両開き LL 42L',
    H: 60.7, W: 27, D: 42, yBody: 58.5, top: [24.3, 37.5], bot: [22.4, 36.0],
    finger: [17.5, 1.5, 57.25], pedal: [14.5, 1.9, 3.9, 5.2, 1.7], caster: [3.5, 4.5, 2.0],
    open: { h: 72.7, span: 27, hinge: 11.0 }
  },
  {
    // ケユカ 両開きダストボックス L 27L (品番3301207)。v5.3〜v8.10 の直書き値をそのまま転記 (見た目は不変)
    test: null,
    label: 'ケユカ 両開き L 27L',
    H: 50, W: 22, D: 41, yBody: 48.5, top: [20.5, 36.0], bot: [18.8, 34.7],
    finger: [14.3, 1.5, 47.25], pedal: [9.5, 1.3, 3.2, 2.2, 1.4], caster: [2.5, 4.0, 1.6],
    open: { h: 60, span: 24, hinge: 10.17 }
  }
];
function dustboxModelOf(nm) {
  for (let i = 0; i < DUSTBOX_MODELS.length; i++) {
    const t = DUSTBOX_MODELS[i].test;
    if (!t || t.test(nm)) return DUSTBOX_MODELS[i];
  }
  return DUSTBOX_MODELS[DUSTBOX_MODELS.length - 1];
}

"""

# ── ② 本体の描画 (kY 行 〜 ★v6.2 コメント直前) を置換。 旧ブロックは sha256 で完全一致を確認 ──
OLD_A_HEAD = u'    const kY = h / 50, kX = w / 22, kZ = d / 41;\n'
OLD_A_TAIL = u'    // ★v6.2 観音開きフタの クリック開閉'
OLD_A_SHA = u'5da49b6489af05a851176fb6f35f2e4b55668a860663b4491cc845b2149d6cd3'
NEW_A = u"""    // ★v8.11 寸法構成は DUSTBOX_MODELS から (L は v8.10 までの直書き値と同じ = 見た目不変 / LL 42L を追加)
    const DM = dustboxModelOf(nm);
    const kY = h / DM.H, kX = w / DM.W, kZ = d / DM.D;
    const yBody = DM.yBody * kY, plT = (DM.H - DM.yBody) * kY;
    // 本体: 四角錐台 (下すぼまり)。上面 DM.top / 底面 DM.bot を4面の台形で作る
    const tw = DM.top[0] * kX, td = DM.top[1] * kZ, bw = DM.bot[0] * kX, bd = DM.bot[1] * kZ;
    // BoxGeometry の頂点を直接動かして四角錐台にする (角のRは小さいのでシャープな四角で近似)
    const bodyGeo = new THREE.BoxGeometry(1, yBody, 1);
    const bpos = bodyGeo.attributes.position;
    for (let vi = 0; vi < bpos.count; vi++) {
      const up = bpos.getY(vi) > 0;
      bpos.setX(vi, bpos.getX(vi) * (up ? tw : bw));
      bpos.setZ(vi, bpos.getZ(vi) * (up ? td : bd));
    }
    bodyGeo.computeVertexNormals();
    const bodyM = new THREE.Mesh(bodyGeo, new THREE.MeshLambertMaterial({ color: base }));
    bodyM.position.set(0, yBody / 2, 0);
    g.add(bodyM);
    P(DM.finger[0] * kX, DM.finger[1] * kY, 0.6, 0, DM.finger[2] * kY, td / 2 + 0.1, base.clone().multiplyScalar(0.90));   // 正面の指掛けくぼみ
    // 天面プレート (本体より一回り大きい傘状) + 観音開きのフタ2枚 (幅を中央で2分割・分割線は奥行方向)
    const lidL = P(w / 2 - 0.2, plT, d, -(w / 4 + 0.1), yBody + plT / 2, 0, lite);
    const lidR = P(w / 2 - 0.2, plT, d, (w / 4 + 0.1), yBody + plT / 2, 0, lite);
    const lidSeam = P(0.35, plT * 1.04, d, 0, yBody + plT / 2, 0, base.clone().multiplyScalar(0.78));   // 中央の分割線 (観音開き)
    // 背面: 縦チャンネル2本 + スチールリンクロッド2本 (下部中央でU字に繋がる)
    P(2.4 * kX, yBody * 0.95, 1.2, -w * 0.26, yBody * 0.5, -td / 2 - 0.4, base.clone().multiplyScalar(0.92));
    P(2.4 * kX, yBody * 0.95, 1.2, w * 0.26, yBody * 0.5, -td / 2 - 0.4, base.clone().multiplyScalar(0.92));
    P(0.7 * kX, yBody * 0.82, 0.7, -w * 0.26, yBody * 0.45, -td / 2 - 1.1, 0xb9bcc0);
    P(0.7 * kX, yBody * 0.82, 0.7, w * 0.26, yBody * 0.45, -td / 2 - 1.1, 0xb9bcc0);
    P(w * 0.52, 0.7, 0.7, 0, 4.5 * kY, -td / 2 - 1.1, 0xb9bcc0);
    // 正面のペダル (下端から前方へ突出する平板タブ) + 後輪キャスター2個 (背面側だけ・固定ホイール)
    P(DM.pedal[0] * kX, DM.pedal[1] * kY, DM.pedal[2] * kZ, 0, DM.pedal[3] * kY, td / 2 + DM.pedal[4] * kZ, base.clone().multiplyScalar(0.86));
    const cr = DM.caster[0] * kY, cT = DM.caster[2];
    [-1, 1].forEach(function (sx) {
      const wh = CYL(cr, cT * kX, sx * (bw / 2 + 0.7 * kX), cr, -bd / 2 + DM.caster[1] * kZ, 0x8f9296);
      wh.rotation.z = Math.PI / 2;                                    // 側面直付けの固定ホイール (自在ではない)
      const hub = CYL(cr * 0.45, (cT + 0.15) * kX, sx * (bw / 2 + 0.7 * kX), cr, -bd / 2 + DM.caster[1] * kZ, base);
      hub.rotation.z = Math.PI / 2;
    });
"""

# ── ③ フタの開き寸法 ──
OLD_B = u"""      const LID_H = 60, LID_HINGE = 10.17, LID_OUT = 12;          // 公式値 (外形 H50 / W22 基準の cm)
      const hingeX = LID_HINGE * kX, yTopP = yBody + plT, Ll = LID_HINGE * kX;
      const rise = (LID_H - 50) * kY;
      const phi = Math.PI - Math.asin(Math.min(rise / Math.max(Ll, 0.1), 1));
"""
NEW_B = u"""      const LID_H = DM.open.h, LID_HINGE = DM.open.hinge, LID_OUT = DM.open.span / 2;   // ★v8.11 DUSTBOX_MODELS の公式値
      const hingeX = LID_HINGE * kX, yTopP = yBody + plT, Ll = LID_HINGE * kX;
      const rise = (LID_H - DM.H) * kY;
      // ★v8.11 L は 上昇量 < フタ長 なので従来式 (見た目不変)。 LL は 12 > 11 で従来式だと垂直に張り付き
      //   上端スパンが ヒンジ間22 になる → 公式の上端スパン27 に合わせて外へ倒す式を使う。
      const phi = rise < Ll
        ? Math.PI - Math.asin(rise / Math.max(Ll, 0.1))
        : Math.PI / 2 + Math.asin(Math.min(Math.max((LID_OUT - LID_HINGE) * kX, 0) / Math.max(Ll, 0.1), 1));
"""

# ── ④ 分岐の見出しコメント ──
OLD_C = u"""  } else if (type === 'trash') {
    // ★v5.3 ケユカ 両開きダストボックス L 27L (品番3301207 ホワイト / 旧名 arrots ダストボックスIII_L)。
"""
NEW_C = u"""  } else if (type === 'trash') {
    // ★v8.11 L 27L / LL 42L の2サイズ。 寸法構成は DUSTBOX_MODELS (下のコメントは L の内訳)。
    // ★v5.3 ケユカ 両開きダストボックス L 27L (品番3301207 ホワイト / 旧名 arrots ダストボックスIII_L)。
"""

LL = {
    "name": u"ダストボックス ケユカ 両開き LL 42L",
    "model": u"3301142 (旧名 KEYUCA両開きダストボックスⅡ_LL_WH / 黒は旧品番3301143)",
    "room": "ldk",
    "zone": "kitchen",
    "w": 27, "d": 42, "h": 60.7,
    "color": "#e3e3dd",
    "type": "trash",
    "url": "https://www.keyuca.com/Form/Product/ProductDetail.aspx?shop=0&pid=3301142",
    "memo": "",
    "specNote": (
        u"ケユカ 両開きダストボックス LL 42L (ペダル式・ソフトクローズ・後輪キャスター付・日本製・税込¥5,280)。"
        u"★公式値 (商品ページ / 公式SIZE画像 / 取扱説明書PDF): 外形 W27 × D42 × H60.7cm・容量42L (45L袋対応)。"
        u"★フタ全開時 H72.7cm・全開時の上端スパン 27cm (= 天面プレート幅と同じで、L 27L と違い左右へははみ出さない)。"
        u"★底の幅 22.4cm (公式SIZE画像) = 下すぼまりの四角錐台。"
        u"⚠公式内で食い違い1件: 取説p4 は W26.5、商品ページ・SIZE画像は W27 → 天面プレート (最大外形) の 27 を採用。"
        u"★外観 (取説p2 製品図を600dpiで実測。正面図は縮尺 9.09px/cm、側面図は横に引き伸ばされた schematic のため奥行は比率で読む): "
        u"本体上面 24.3×37.5 / 底 22.4×36.0 / 天面プレート厚 約2.2 [est] / ペダル 幅14.5×厚1.9・前へ3.9・中心高5.2 / "
        u"後輪キャスター2個 半径約3.5 / フタのヒンジは中心から11.0 (ヒンジ間22 → 全開で外へ倒れて上端27)。"
        u"★材質: 本体・フタ・ペダル・キャスター・ポケット=PP(耐熱110℃) / キャスター外周=熱可塑性エラストマー / リンク・袋留め=スチール(クロームめっき)。"
        u"★カラー4色 (ライトグレー・ダークグレーは WEB限定 2025.9〜): ホワイト #E3E3DD・ブラック #3A3633 は 同シリーズ L 27L と同じ値を流用 / "
        u"ライトグレー #C5BFB9・ダークグレー #565455 は 公式カラーバリエーション画像 (sub10) の正面を実測し、同画像のホワイト正面と L のホワイトの比で明るさ補正 [est]。"
        u"⚠エトナ60OP の下段 (天 69.3cm) に入れると フタ全開 72.7cm が当たる (L 27L の 60cm は入る)。奥行42 も下段の奥行 約37〜41 を超える。"
        u"※2025年9月に商品名変更 (KEYUCA両開きダストボックスⅡ_LL_WH → KEYUCA両開きダストボックス LL（42L）)、仕様変更なしと公式明記。"
        u"※公式非公表: 質量・JAN・内寸・各部詳細寸法。"
        u"★一次資料は catalog\\商品公式資料\\KEYUCA_両開きダストボックスLL42L\\ (README.md + 公式画像23点 + 公式取説PDF + 取説ページPNG + 製品図600dpi)。"
    ),
    "colors": [
        {"name": u"ホワイト", "hex": "#e3e3dd"},
        {"name": u"ライトグレー (WEB限定)", "hex": "#c5bfb9"},
        {"name": u"ダークグレー (WEB限定)", "hex": "#565455"},
        {"name": u"ブラック", "hex": "#3a3633"},
    ],
}

# ── ⑥ 段2 (v8.11 の撮影で発見): 開いた時の投入口 (黒) が 本体上面と同じ高さ = z-fighting で、
#    L は 上面のグレーが勝って投入口が見えず、 LL は 黒とグレーが斑に出ていた (v6.2 からの既存不具合)。
#    投入口の上面を 0.1cm だけ上げる (天面プレートは開いた時に非表示なので干渉しない)。
#    あわせて ラベルの「フタ全開60cm OK」 直書きを LID_H に (LL は 72.7)。
OLD_D = u"      const mouth = P(tw - 2.4 * kX, 1.2 * kY, td - 2.4 * kZ, 0, yBody - 0.6 * kY, 0, 0x1a1a1c);   // 開時に見える投入口\n"
NEW_D = u"      const mouth = P(tw - 2.4 * kX, 1.2 * kY, td - 2.4 * kZ, 0, yBody - 0.6 * kY + 0.1, 0, 0x1a1a1c);   // 開時に見える投入口 (★v8.11 本体上面と z-fighting しないよう 0.1 上げ)\n"
OLD_E = u"            label: ok ? (marg === null ? 'フタ全開60cm OK' : 'フタ開OK 余裕' + marg + 'cm')\n"
NEW_E = u"            label: ok ? (marg === null ? 'フタ全開' + LID_H + 'cm OK' : 'フタ開OK 余裕' + marg + 'cm')   // ★v8.11 60 直書きを LID_H に\n"


def stage2(src):
    if NEW_D in src and NEW_E in src:
        return src, 0
    src = rep1(src, OLD_D, NEW_D, u'⑥ 投入口の z-fighting')
    src = rep1(src, OLD_E, NEW_E, u'⑥ ラベルの 60 直書き')
    return src, 2


CMT_ADD = (u" ★v2.15 の変更点 (2026-10-08): **ケユカ 両開きダストボックス LL 42L を1点追加** "
           u"(room=ldk / zone=kitchen / type='trash' / W27×D42×H60.7・全開時H72.7)。 既存の L 27L は変更なし。 "
           u"3Dは 両開きゴミ箱の寸法構成を DUSTBOX_MODELS レジストリへデータ化 (L は従来の値をそのまま転記) ★アプリ v8.11")


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

    if cs['version'] == '2.15' and MARK in src:
        src, n2 = stage2(src)
        if not n2:
            print(u'適用0件 / skip 全件 (既に CATALOG_SEED v2.15 + DUSTBOX_MODELS + 段2 = 適用済み)')
            return 0
        assert sha(RD_PAT, src) == rd_before and re.search(CS_PAT, src, re.S).group(1) == raw_before
        io.open(P, 'w', encoding='utf-8', newline='').write(src)
        print(u'適用2件 (段2のみ: 投入口 z-fighting / ラベル LID_H)。 CATALOG_SEED 不変')
        return 0
    assert cs['version'] == '2.14', u'CATALOG_SEED が v2.14 でない: %s' % cs['version']
    assert len(cs['items']) == 37, u'商品が 37件でない: %d' % len(cs['items'])
    assert MARK not in src
    keys = set(i.get('model') or i['name'] for i in cs['items'])
    names = set(i['name'] for i in cs['items'])
    assert LL['name'] not in names and LL['model'] not in keys, u'同じ商品が既にある'

    # test 正規表現が LL にだけ当たることを機械 assert (specTextOf と同じ 名前+specNote+memo で照合)
    rx = re.compile(u'3301142|LL ?[（(]?42L')
    for it in cs['items'] + [LL]:
        txt = it['name'] + u' ' + it.get('specNote', '') + u' ' + it.get('memo', '')
        assert bool(rx.search(txt)) == (it is LL), u'DUSTBOX_MODELS の LL test が別商品に当たる (or 当たらない): %s' % it['name']
    print(u'  機械照合: DUSTBOX_MODELS の LL test は LL にだけ当たる (38件で確認)')

    # ① レジストリ
    src = rep1(src, ANCHOR_REG, NEW_REG + ANCHOR_REG, u'① DUSTBOX_MODELS')
    # ② 本体描画
    assert src.count(OLD_A_HEAD) == 1
    a = src.index(OLD_A_HEAD)
    b = src.index(OLD_A_TAIL, a)
    assert hashlib.sha256(src[a:b].encode()).hexdigest() == OLD_A_SHA, u'② 旧ブロックが想定と違う (並行編集?)'
    src = src[:a] + NEW_A + src[b:]
    # ③ フタ
    src = rep1(src, OLD_B, NEW_B, u'③ フタの開き寸法')
    # ④ 見出し
    src = rep1(src, OLD_C, NEW_C, u'④ 分岐の見出しコメント')
    src, _ = stage2(src)

    # ⑤ CATALOG_SEED へ1件追加 (既存37件はバイト単位不変)
    others_raw = [json.dumps(i, ensure_ascii=False, separators=(',', ':')) for i in cs['items']]
    for r in others_raw:
        assert r in raw_before, u'既存商品の直列化が生テキストと一致しない (シードの書式が変わっている?)'
    cs['items'].append(LL)
    cs['version'] = '2.15'
    cs['updatedAt'] = '2026-10-08'
    cs['_comment'] += CMT_ADD
    m = re.search(CS_PAT, src, re.S)
    new_raw = json.dumps(cs, ensure_ascii=False, separators=(',', ':'))
    for r in others_raw:
        assert r in new_raw, u'既存商品がバイト単位で不変でない'
    src = src[:m.start()] + 'var CATALOG_SEED = ' + new_raw + ';\n' + src[m.end():]

    assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用5件')
    print(u'  ① DUSTBOX_MODELS / dustboxModelOf (LL 42L + 既定 L 27L)')
    print(u'  ② 両開きゴミ箱の本体描画を レジストリ参照へ (L は同値)')
    print(u'  ③ フタの開き寸法 (L は従来式 / LL は上端スパン基準)')
    print(u'  ④ 見出しコメント')
    print(u'  ⑥ 開いた時の投入口の z-fighting / ラベルの 60 直書き')
    print(u'  ⑤ CATALOG_SEED v2.14 → v2.15: LL 42L を追加 (既存37商品 バイト単位不変)')
    print(u'ROOM_DATA sha256 %s (不変)' % rd_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

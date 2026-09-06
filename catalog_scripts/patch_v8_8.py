# -*- coding: utf-8 -*-
u"""v8.8: デスク天板の後ろにある **ミラー差し込み溝** をモデル化し、 ミラーをそこへ挿す。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_8.py

冪等。 ROOM_DATA は一切変更しない。 CATALOG_SEED v2.11 → v2.12 (商品37件は不変)。

━━ 何がまちがっていたか (野沢さん指摘) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
「横から見た図の右上の部分が鏡をはめる隙間。 そこにはめ、 壁にもたれかけさせるイメージ」。
v8.6/8.7 は **天板の上に直置きして30°倒す** モデルで、 溝の存在を見落としていた
(公式の側面カットに写っているのに読み落とした)。 実物は 天板後方の溝に差し込むので
ミラーは ほぼ垂直 (7.7°) に立つ。 室内カット (公式画像 05.jpg / 10.jpg) の見た目とも、
こちらの方が合う。 v8.7 が「写真実測 30.5°」としたのは **カメラの俯角による縦の圧縮** を
傾きと取り違えたもので、 誤りだった (天板が見えている = 見下ろしのカット)。

━━ 溝の実測 (公式 SIDE カット img/dresser/09.jpg の画素実測) ━━━━━━━━━━━━━━
デスク部の側面 (奥行48cm) が 175px → 3.65 px/cm。 これで測ると:
  ・天板 (板が残っている部分) = 前から 約40cm
  ・溝 = そこから背面まで **約7〜8cm** (溝の手前の縁が 背面から 8.2cm)
  ・溝の奥に 厚さ **約1.5cm** の背板が 天板と同じ高さまで立つ
  ・溝の底は 天板面から 6.4〜8.3cm 下 (暗くて底か奥壁か判別しきれない = 幅を持つ)
⇒ モデルは 溝幅 **8**・背板 **1.5**・溝の底 **64.2** (天板71 から 6.8 下) とした。
   溝の底だけは 公式の設置例の全高 124 から逆算している (枠の厚みぶんの出っぱりも入れた最高点で合わせる):
     124 − (60·cos7.66° + 2.5·sin7.66°) = 124 − 59.80 = **64.2**  (写真実測 6.4〜8.3cm の範囲内)
   → **溝の幾何 (公式写真) と 全高124 (公式) が 独立に整合する** ので、この置き方が正しいと判断した。

⚠ 溝の寸法そのものは 公式サイズ図・仕様表に記載が無い (組立説明書の公開も無し) = **est**。
⚠ 公式サイズ図の未解釈の「8」が この溝の幅である可能性はあるが、 矢印が幅方向に見えるため断定しない。
⚠ 長方形ミラー (60×80) の設置例 138cm は この置き方では 143.7 になり 約6cm 合わない。
   正方形の 124 は合うので、 138 側は 立てかけ方が違う (もっと手前に倒している) と見ている。
"""
import hashlib
import io
import json
import re
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'

# ═══ ① ユニットに slot を持たせる (データ) ═══════════════════════════════════
OLD_UNIT = (u"      { key: 'desk', x0: -10, z0: 0, w: 100, d: 48, y0: 58.5, h: 12.5, topT: 2.5, plinth: 0,\n"
            u"        rows: [{ fh: 10, n: 2, inner: { w: 40, d: 34, h: 5 }, label: 'デスク引き出し' }] },")
NEW_UNIT = (u"      // slot = 天板の後ろにある **ミラー差し込み溝** (公式 SIDE カットの画素実測 [est])。\n"
            u"      //   back:溝の幅(奥行方向) / rail:溝の奥に立つ背板の厚み / floor:溝の底の高さ\n"
            u"      { key: 'desk', x0: -10, z0: 0, w: 100, d: 48, y0: 58.5, h: 12.5, topT: 2.5, plinth: 0,\n"
            u"        slot: { back: 8, rail: 1.5, floor: 64.2 },\n"
            u"        rows: [{ fh: 10, n: 2, inner: { w: 40, d: 34, h: 5 }, label: 'デスク引き出し' }] },")

# set 側: 天板に置くのではなく 溝に挿す
OLD_SET = (u"    set: { kind: 'mirror', onUnit: 'desk', w: 60, h: 60, t: 2.5, glassW: 57.8, glassH: 57.8,\n"
           u"           totalH: 124, label: '正方形ミラー' }")
NEW_SET = (u"    // seat:'slot' = ホストの溝に差し込む (天板に直置きではない)。 傾きは溝の幅から決まる\n"
           u"    set: { kind: 'mirror', onUnit: 'desk', seat: 'slot', w: 60, h: 60, t: 2.5,\n"
           u"           glassW: 57.8, glassH: 57.8, totalH: 124, label: '正方形ミラー' }")

# ═══ ② ユニットの描画: 溝を作る ═══════════════════════════════════════════════
OLD_BODY = u"""      P(uw, uh - pl - topT, ud, ux, uy + pl + (uh - pl - topT) / 2, uz, base);      // 本体
      if (topT > 0) {
        P(uw, topT, ud, ux, uy + uh - topT / 2, uz, base.clone().lerp(lite, 0.18)); // 天板
      }"""
NEW_BODY = u"""      // ★v8.8 slot = 天板の後ろの ミラー差し込み溝。 天板を前側だけにし、 溝の底板と背板を足す。
      //   専用コードにせず ユニット共通の任意フィールドにしてあるので、 同じ作りの
      //   ドレッサー・鏡付きチェストは data に slot を1行足すだけで同じ溝ができる。
      const SL = U.slot || null;
      const solidD = SL ? ud - SL.back * kz : ud;                      // 板が残っている奥行 (前側)
      const solidZ = uz + (ud - solidD) / 2;                           // その中心 z (前へ寄る)
      P(uw, uh - pl - topT, solidD, ux, uy + pl + (uh - pl - topT) / 2, solidZ, base);   // 本体
      if (topT > 0) {
        P(uw, topT, solidD, ux, uy + uh - topT / 2, solidZ, base.clone().lerp(lite, 0.18)); // 天板
      }
      if (SL) {
        const sBack = SL.back * kz, sRail = SL.rail * kz, sFloor = SL.floor * ky;
        const zBackFace = uz - ud / 2;                                 // ユニットの背面
        P(uw, sFloor - uy, sBack, ux, (uy + sFloor) / 2, zBackFace + sBack / 2, base);    // 溝の下の躯体
        P(uw, 1.2, sBack, ux, sFloor - 0.6, zBackFace + sBack / 2,
          dark.clone().lerp(base, 0.55));                                                 // 溝の底板
        P(uw, uy + uh - sFloor, sRail, ux, (sFloor + uy + uh) / 2, zBackFace + sRail / 2, base); // 背板
      }"""

# ═══ ③ ミラーの座り方: 溝に挿す ═══════════════════════════════════════════════
OLD_MIRROR = u"""      const topY = (host.y0 + host.h) * ky;                   // 立てかける面 (デスク天板の上面)
      const mw = S.w * kx, mh = S.h * ky, mt = S.t * kz;
      // ★v8.7 傾きの軸は **後ろ下端の稜線** (後ろへ倒した板が実際に接する線)。
      //   角度は 板の厚みを含めた全高の式から解く: mh·cosθ + mt·sinθ = totalH − 天板高
      //   (最高点 = 上前角)。 → 最下点が天板の上面ちょうど / 最高点が公式の設置例ちょうどになる。
      //   v8.6 は 下端の中央を軸にし 厚みを無視した acos((totalH−topY)/mh) だったので、
      //   枠の後ろ下角が天板へ 0.6cm めり込み 最高点も 0.6cm 高かった (公式写真の実測とも 2.5° ズレ)。
      const need = Math.min(Math.max(S.totalH * ky - topY, 0), Math.hypot(mh, mt));
      const lean = Math.acos(need / Math.hypot(mh, mt)) + Math.atan2(mt, mh);
      const mg = new THREE.Group();
      mg.position.set(host.x0 * kx, topY, -d / 2 + mh * Math.sin(lean));   // 上端(背面側)が壁に付く位置
      mg.rotation.x = -lean;"""
NEW_MIRROR = u"""      // ★v8.8 seat:'slot' … 天板の後ろの溝に **差し込んで** 壁にもたれかけさせる (実物の使い方)。
      //   ・下端は 溝の底 (slot.floor) に載る
      //   ・下端の後ろ角は 溝の手前の壁 = 背面から slot.back の位置
      //   ・そこから後ろへ倒して 上端が背面 (= 壁) に当たる → 傾きは asin(slot.back / 高さ) で決まる
      //   → 溝の幾何だけで角度が決まる (角度を勝手に決めない)。 公式の設置例の全高 124 とも一致する。
      //   v8.6/8.7 は 溝を見落として天板に直置きし 30° 倒していた (実物はほぼ垂直)。
      const SLm = (S.seat === 'slot') ? host.slot : null;
      const mw = S.w * kx, mh = S.h * ky, mt = S.t * kz;
      const topY = SLm ? SLm.floor * ky : (host.y0 + host.h) * ky;   // 立てかける面 (溝の底 or 天板の上面)
      let lean, baseZ;
      if (SLm) {
        lean = Math.asin(Math.min(SLm.back * kz / Math.max(mh, 1), 1));
        baseZ = -d / 2 + SLm.back * kz;                              // 溝の手前の壁ぎわに下端の後ろ角
      } else {
        const need = Math.min(Math.max(S.totalH * ky - topY, 0), Math.hypot(mh, mt));
        lean = Math.acos(need / Math.hypot(mh, mt)) + Math.atan2(mt, mh);
        baseZ = -d / 2 + mh * Math.sin(lean);
      }
      const mg = new THREE.Group();
      mg.position.set(host.x0 * kx, topY, baseZ);
      mg.rotation.x = -lean;"""

OLD_NOTE = (u'公式の設置例の全高は **正方形124cm / 長方形(60×80)138cm**。 3Dモデルは '
            u'**後ろ下端の稜線を軸に** 立てかけ、 後傾角は 枠の厚みを含めた全高の式 '
            u'60cosθ + 2.5sinθ = 124−71 から **θ = 30.4°** として この124をちょうど再現している '
            u'(最下点=天板の上面 / 最高点=124.0)。 ★裏取り: 公式の設置例の写真を画素実測すると '
            u'床→ミラー上端 168px = 124cm に対し 見かけの高さ 70px = 51.7cm (見かけの幅は58.3 ≒ 実寸60 = '
            u'横には倒れていない) で cosθ = 51.7/60 → **θ ≒ 30.5°**、 式から出た 30.4° と一致する。 '
            u'⚠角度そのものは公式に記載が無く 立てかけ方で変わる (モデルは公式の設置例どおり壁に立てかけた状態)。 '
            u'⚠v8.6 は 下端中央を軸にし厚みを無視した 27.9° で、 枠の後ろ下角が天板に0.6cmめり込んでいた (v8.7で是正)。')
NEW_NOTE = (u'★**ミラーは天板の上に直置きではなく、 天板の後ろにある溝に差し込んで 壁にもたれかけさせる** '
            u'(野沢さん指摘 2026-09-06 + 公式 SIDE カットに溝が写っている)。 溝は公式サイズ図・仕様表に'
            u'寸法の記載が無いので 公式 SIDE カット (09.jpg) の画素実測 [est]: 天板の側面 48cm = 175px '
            u'(3.65px/cm) で測ると **板が残っているのは前から約40cm / 溝の幅 約7〜8cm / 奥に厚さ約1.5cmの背板 / '
            u'溝の底は天板面から 6.4〜8.3cm 下**。 モデルは 溝幅8・背板1.5・**溝の底 64.2** (天板71 から6.8下) '
            u'とした。 傾きは 溝の幾何から決まる = 下端の後ろ角が背面から8cm の位置で 上端が壁に当たる → '
            u'asin(8/60) = **7.7°** (ほぼ垂直) で、 全高は 64.2 + 60cos7.7° + 2.5sin7.7° = **124.0** = '
            u'公式の設置例 124cm と一致する (溝の実測と 公式の全高が 独立に整合した)。 '
            u'⚠長方形(60×80)の設置例138は この置き方だと143.7になり6cm合わない → 138側は もっと手前に倒した'
            u'立てかけ方と見ている。 ⚠v8.6/8.7 は **溝を見落として天板に直置きし 27.9°/30.4° 倒していた**。 '
            u'室内カットの見かけの縦圧縮を「傾き」と読んだのが誤りで、 実際はカメラの俯角によるもの (v8.8で是正)。')


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def rep1(src, old, new, what):
    assert src.count(old) == 1, u'%s の置換元が %d 箇所 (1でない)' % (what, src.count(old))
    return src.replace(old, new, 1)


def main():
    src = io.open(P, encoding='utf-8').read()
    rd_before = sha(RD_PAT, src)
    cs = json.loads(re.search(CS_PAT, src, re.S).group(1))

    if cs['version'] == '2.12' and u"seat: 'slot'" in src:
        print(u'適用0件 / skip 全件 (既に CATALOG_SEED v2.12 + 溝モデル = 適用済み)')
        return 0
    assert cs['version'] == '2.11', u'CATALOG_SEED が v2.11 でない: %s' % cs['version']
    assert len(cs['items']) == 37, u'商品が 37件でない: %d' % len(cs['items'])

    src = rep1(src, OLD_UNIT, NEW_UNIT, u'① デスクユニットへ slot を追加')
    src = rep1(src, OLD_SET, NEW_SET, u'① set に seat:slot を追加')
    src = rep1(src, OLD_BODY, NEW_BODY, u'② ユニット描画に 溝 (底板・背板) を追加')
    src = rep1(src, OLD_MIRROR, NEW_MIRROR, u'③ ミラーを溝に挿す座り方へ')

    hit = [i for i in cs['items'] if OLD_NOTE in i.get('specNote', '')]
    assert len(hit) == 1, u'specNote の置換対象が %d件 (1でない)' % len(hit)
    others = json.dumps([i for i in cs['items'] if i is not hit[0]], ensure_ascii=False, sort_keys=True)
    hit[0]['specNote'] = hit[0]['specNote'].replace(OLD_NOTE, NEW_NOTE)
    assert json.dumps([i for i in cs['items'] if i is not hit[0]], ensure_ascii=False,
                      sort_keys=True) == others, u'他の商品が変化した'
    cs['version'] = '2.12'
    cs['updatedAt'] = '2026-09-06'
    cs['_comment'] += (
        u' ★v2.12 の変更点 (2026-09-06): **ミラーの置き方を「天板の後ろの溝に差し込む」へ是正** — '
        u'野沢さん指摘「横から見た図の右上が鏡をはめる隙間。そこにはめ、壁にもたれかけさせるイメージ」。 '
        u'v2.10/2.11 は 溝を見落として 天板に直置きし 27.9°/30.4° 倒していた '
        u'(室内カットの見かけの縦圧縮を傾きと誤読。 実際はカメラの俯角)。 溝は 公式 SIDE カットの画素実測で '
        u'幅約7〜8cm・奥に厚さ約1.5cmの背板・底は天板面から6.4〜8.3cm下 [est]。 モデルは 溝幅8/背板1.5/底64.2 とし、 '
        u'傾きは **溝の幾何から** asin(8/60)=7.7° (ほぼ垂直) で決まる。 全高は 64.2+60cos7.7°+2.5sin7.7°=124.0 で '
        u'公式の設置例124cmと一致 (溝の実測と公式の全高が独立に整合)。 ユニットの `slot` は共通フィールドなので '
        u'同じ作りのドレッサーは data に1行足すだけで同じ溝になる ★アプリ v8.8')

    m = re.search(CS_PAT, src, re.S)
    src = (src[:m.start()] + 'var CATALOG_SEED = '
           + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n' + src[m.end():])

    assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用5件')
    print(u'  ① CABINET_MODELS: デスクユニットに slot {back:8, rail:1.5, floor:64.2} を追加')
    print(u'  ② set に seat:\'slot\' を追加 (天板直置き → 溝へ差し込み)')
    print(u'  ③ JS: ユニット描画に 溝 (天板を前40だけに / 底板 / 背板) を追加 (共通フィールド)')
    print(u'  ④ JS: ミラーの座り方 = 溝の底に載せ 溝の幅から傾きを決める (asin(8/60)=7.7°)')
    print(u'  ⑤ CATALOG_SEED: specNote のミラーの説明を差し替え')
    print(u'CATALOG_SEED v2.11 → v2.12 / 商品 37件 (不変) / ROOM_DATA sha256 %s (不変)' % rd_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

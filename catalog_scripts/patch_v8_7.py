# -*- coding: utf-8 -*-
u"""v8.7: 立てかけミラーの **傾きの軸と角度** を是正する (アユリナ ドレッサーデスク)。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_7.py

冪等。 ROOM_DATA は一切変更しない (sha256 前後一致を assert)。 CATALOG_SEED v2.10 → v2.11
(商品は 37件のまま。 ドレッサーの specNote の「後傾角」の説明だけ差し替える)。

━━ 何がまちがっていたか ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v8.6 は 板を **下端の中央** を軸に倒していた。 後ろへ倒す板が実際に接するのは
**後ろ下端の稜線** なので、
  ・枠の後ろ下角が 天板に 0.6cm めり込む
  ・最高点が 124.6cm になり 公式の設置例 124 とズレる
  ・角度も (124−71)/60 の逆余弦 = 27.9° と、 枠の厚み 2.5 を無視した値になっていた

━━ 是正 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
軸を **後ろ下端の稜線** にし、 角度は 厚みを含めた全高の式から解く:
    mh·cosθ + mt·sinθ = totalH − 天板高   (最高点 = 上前角)
  → 60cosθ + 2.5sinθ = 124 − 71 = 53   → **θ = 30.4°**
  これで 最下点 = 天板の上面ちょうど / 最高点 = **124.0cm ちょうど** になる。

★独立した裏取り: 公式の設置例の写真 (公式サイズ図の下段カット) を画素実測すると
  床→ミラー上端 168px = 124cm (1.355 px/cm) に対し ミラーの見かけの高さ 70px = 51.7cm、
  見かけの幅 79px = 58.3cm (実寸60 とほぼ一致 = 横は倒れていない)。
  cosθ = 51.7 / 60 → **θ ≒ 30.5°** で、 上の式から出た 30.4° と一致する。
  (v8.6 の 27.9° は この写真実測と 2.5° 合わなかった = まちがいだったことの裏付け)

⚠ 傾き自体は公式に数値の記載が無く、 立てかけ方でユーザーが変えられる。
   モデルは 「公式の設置例どおりに壁へ立てかけた状態」 を再現している。
"""
import hashlib
import io
import json
import re
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'

OLD_JS = u"""      const topY = (host.y0 + host.h) * ky;                   // 立てかける面 (デスク天板の上面)
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
"""

NEW_JS = u"""      const topY = (host.y0 + host.h) * ky;                   // 立てかける面 (デスク天板の上面)
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
      mg.rotation.x = -lean;
      g.add(mg);
      const addTo = function (sx, sy, sz, px, py, pz, col) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(Math.max(sx, 0.3), Math.max(sy, 0.3), Math.max(sz, 0.3)),
          new THREE.MeshLambertMaterial({ color: col }));
        m.position.set(px, py, pz);
        mg.add(m);
        return m;
      };
      addTo(mw, mh, mt, 0, mh / 2, mt / 2, base);                                  // 木枠 (軸=後ろ下端)
      addTo(S.glassW * kx, S.glassH * ky, 0.4, 0, mh / 2, mt + 0.2, 0xdbe6ea);      // 鏡面 (前面側)
"""

OLD_NOTE = (u'公式の設置例の全高は **正方形124cm / 長方形(60×80)138cm** で、 3Dモデルの後傾角は '
            u'acos((124−71)/60) ≒ **27.9°** として この124を再現している (角度そのものは公式に記載なし)。')
NEW_NOTE = (u'公式の設置例の全高は **正方形124cm / 長方形(60×80)138cm**。 3Dモデルは '
            u'**後ろ下端の稜線を軸に** 立てかけ、 後傾角は 枠の厚みを含めた全高の式 '
            u'60cosθ + 2.5sinθ = 124−71 から **θ = 30.4°** として この124をちょうど再現している '
            u'(最下点=天板の上面 / 最高点=124.0)。 ★裏取り: 公式の設置例の写真を画素実測すると '
            u'床→ミラー上端 168px = 124cm に対し 見かけの高さ 70px = 51.7cm (見かけの幅は58.3 ≒ 実寸60 = '
            u'横には倒れていない) で cosθ = 51.7/60 → **θ ≒ 30.5°**、 式から出た 30.4° と一致する。 '
            u'⚠角度そのものは公式に記載が無く 立てかけ方で変わる (モデルは公式の設置例どおり壁に立てかけた状態)。 '
            u'⚠v8.6 は 下端中央を軸にし厚みを無視した 27.9° で、 枠の後ろ下角が天板に0.6cmめり込んでいた (v8.7で是正)。')


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def rep1(src, old, new, what):
    assert src.count(old) == 1, u'%s の置換元が %d 箇所 (1でない)' % (what, src.count(old))
    return src.replace(old, new, 1)


def main():
    src = io.open(P, encoding='utf-8').read()
    rd_before = sha(RD_PAT, src)
    cs = json.loads(re.search(CS_PAT, src, re.S).group(1))

    if cs['version'] == '2.11' and u'後ろ下端の稜線' in src:
        print(u'適用0件 / skip 全件 (既に CATALOG_SEED v2.11 + 後ろ下端の稜線を軸 = 適用済み)')
        return 0
    assert cs['version'] == '2.10', u'CATALOG_SEED が v2.10 でない: %s' % cs['version']
    assert len(cs['items']) == 37, u'商品が 37件でない: %d' % len(cs['items'])

    src = rep1(src, OLD_JS, NEW_JS, u'JS ミラーの立てかけブロック')

    hit = [i for i in cs['items'] if OLD_NOTE in i.get('specNote', '')]
    assert len(hit) == 1, u'specNote の置換対象が %d件 (1でない)' % len(hit)
    before = json.dumps([i for i in cs['items'] if i is not hit[0]], ensure_ascii=False, sort_keys=True)
    hit[0]['specNote'] = hit[0]['specNote'].replace(OLD_NOTE, NEW_NOTE)
    assert json.dumps([i for i in cs['items'] if i is not hit[0]], ensure_ascii=False,
                      sort_keys=True) == before, u'他の商品が変化した'
    cs['version'] = '2.11'
    cs['updatedAt'] = '2026-09-06'
    cs['_comment'] += (
        u' ★v2.11 の変更点 (2026-09-06): **立てかけミラーの傾きの軸と角度を是正** — 後ろへ倒した板が'
        u'実際に接するのは後ろ下端の稜線なので 軸をそこへ移し、 角度は枠の厚みを含めた全高の式 '
        u'mh·cosθ + mt·sinθ = 全高−天板高 から解くようにした (60cosθ+2.5sinθ=53 → θ=30.4°)。 '
        u'v2.10 は 下端中央を軸に acos((124−71)/60)=27.9° としていたため 枠の後ろ下角が天板に0.6cm'
        u'めり込み 最高点も124.6cmだった。 是正後は 最下点=天板の上面ちょうど / 最高点=公式の設置例'
        u'124.0cm ちょうど。 公式の設置例写真の画素実測 (見かけの高さ51.7/実寸60 → 30.5°) とも一致する ★アプリ v8.7')

    m = re.search(CS_PAT, src, re.S)
    src = (src[:m.start()] + 'var CATALOG_SEED = '
           + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n' + src[m.end():])

    assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用2件')
    print(u'  ① JS: ミラーの傾きの軸を 後ろ下端の稜線へ / 角度を 厚み込みの式で解く (27.9° → 30.4°)')
    print(u'  ② CATALOG_SEED: ドレッサーの specNote の後傾角の説明を差し替え (写真実測での裏取りを追記)')
    print(u'CATALOG_SEED v2.10 → v2.11 / 商品 37件 (不変) / ROOM_DATA sha256 %s (不変)' % rd_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

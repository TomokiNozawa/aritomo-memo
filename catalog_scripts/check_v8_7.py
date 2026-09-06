# -*- coding: utf-8 -*-
u"""v8.7 の検証: 立てかけミラーが 公式の設置例どおりに載っているかを 実頂点で機械照合する。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_7.py

見るもの (すべて ミラーのメッシュ2個 = 木枠 + 鏡面 の **実頂点** から):
  ① 最下点 = デスク天板の上面 71.0cm ちょうど (めり込まない・浮かない)
  ② 最高点 = 公式の設置例の全高 **124.0cm** ちょうど
  ③ 後傾角 = 30.4° (= 60cosθ + 2.5sinθ = 53 の解。 公式写真の画素実測 30.5° と一致)
  ④ 上端が 本体の背面 (壁側) に接している = 壁に立てかけた状態
  ⑤ 左右方向は デスク部 (幅100) の中央 = 公式の設置例と同じ

⚠ Box3 は既定だと「ジオメトリのAABBの8隅を変換」なので 傾いた板では誤差が出る。
   precise=true (実頂点) で測る。
"""
import json
import math
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:8777/room.html?debug=1"
NG = []


def ck(cond, msg):
    print((u'  [OK ] ' if cond else u'  [NG ] ') + msg)
    if not cond:
        NG.append(msg)


def main():
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1100, "height": 780})
        errs = []
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
        pg.wait_for_timeout(900)

        def mjs(code):
            return pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + code + "})()") + ")")

        mjs("switchRoom('west45'); return 1;")
        cid = mjs("var c=__noza.catFull().filter(function(c){return /ドレッサーデスク/.test(c.name);});"
                  " return c.length===1 ? c[0].id : null;")
        ck(cid is not None, u'ドレッサーデスクがカタログに1件ある')
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(cid))
        pg.wait_for_timeout(700)
        # ミラーは Group の子 (木枠 + 鏡面)。 y が 60cm より上にある板 2枚を拾う
        r = mjs("""
          var ks=Object.keys(workItems), k=ks[ks.length-1], g=furnMeshes[k]; deselect(); g.updateMatrixWorld();
          var res=null;
          g.children.forEach(function(o){ if(o.isGroup){
            var b=new THREE.Box3().setFromObject(o, true);
            res={ lo:b.min.y, hi:b.max.y, zBack:b.min.z, zFront:b.max.z,
                  xMin:b.min.x, xMax:b.max.x, rotX:o.rotation.x }; }});
          var bb=new THREE.Box3().setFromObject(g, true);
          var it=workItems[k];
          return { m:res, ix:it.x, iz:it.z, rotY:it.rotY||0, all:{lo:bb.min.y, hi:bb.max.y} };""")
        M = r['m']
        ck(M is not None, u'ミラーのグループが1つある')
        lean = -M['rotX'] * 180 / math.pi
        print(u'  実測: 最下点 %.2f / 最高点 %.2f / 後傾 %.2f° / 奥行 %.1f〜%.1f / 左右 %.1f〜%.1f'
              % (M['lo'], M['hi'], lean, M['zBack'], M['zFront'], M['xMin'], M['xMax']))
        ck(abs(M['lo'] - 71.0) < 0.05, u'① 最下点 = デスク天板 71.0 (ずれ %.2fcm)' % (M['lo'] - 71.0))
        ck(abs(M['hi'] - 124.0) < 0.05, u'② 最高点 = 公式の設置例 124.0 (ずれ %.2fcm)' % (M['hi'] - 124.0))
        ck(abs(lean - 30.4) < 0.2, u'③ 後傾角 = 30.4° (公式写真の実測 30.5° と一致) / 実際 %.2f°' % lean)
        # Box3 は **ワールド座標** なので アイテムの設置位置を引いてローカルに直す (回転0の個体で検証)
        ck(abs(r['rotY']) < 1e-6, u'  検証個体は回転0 (rotY=%s)' % r['rotY'])
        zb = M['zBack'] - r['iz']
        xc = (M['xMin'] + M['xMax']) / 2 - r['ix']
        ck(abs(zb - (-24.0)) < 0.6,
           u'④ 上端が本体背面 z=-24.0 に接する (壁に立てかけ) / 実際 %.2f' % zb)
        ck(abs(xc - (-10.0)) < 0.3,
           u'⑤ 左右は デスク部(幅100)の中央 x=-10 / 実際 %.2f' % xc)
        mjs("__noza.studio(true); return 1;")
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip,#drawerLabels{display:none !important;}")
        it = mjs("var ks=Object.keys(workItems), k=ks[ks.length-1], it=workItems[k];"
                 " return {x:it.x,z:it.z};")
        for tag, cam in (('side', (it['x'] + 210, 75, it['z'] + 40)), ('front', (it['x'], 75, it['z'] + 230))):
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (cam[0], cam[1], cam[2], it['x'], 60, it['z']))
            pg.wait_for_timeout(700)
            pg.screenshot(path=os.path.join(HERE, '_v8_7_mirror_%s.png' % tag))
            print(u'      -> _v8_7_mirror_%s.png' % tag)
        br.close()
    ck(not errs, u'ページエラー 0件 (実際 %d件)' % len(errs))
    print(u'\n════ 結果: NG %d 件 ════' % len(NG))
    return 1 if NG else 0


if __name__ == '__main__':
    sys.exit(main())

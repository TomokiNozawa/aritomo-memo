# -*- coding: utf-8 -*-
u"""カタログ商品を studio モード (無地背景) で 正面・斜めから撮る (type 指定の汎用版)。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/shot_item_studio.py <type> <tag> [room]

  例) ... shot_item_studio.py cabinet after west45

★shot_bed_studio.py は type='bed' 決め打ちだったので、 商品を足すたびに撮影スクリプトを
  コピーしないよう **type と部屋を引数にした汎用版** を用意した (案件ごとに作り込まない)。
  引き出しは 3D 上でクリックして開くので、 --open を付けると全部開けた状態でも撮る。

出力: catalog_scripts/_shot_<type>_<tag>_<n><a|b>.png
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:8777/room.html?debug=1"


def main():
    typ = sys.argv[1] if len(sys.argv) > 1 else 'cabinet'
    tag = sys.argv[2] if len(sys.argv) > 2 else 'after'
    room = sys.argv[3] if len(sys.argv) > 3 else 'west45'
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

        mjs("switchRoom(%s); return 1;" % json.dumps(room))
        pg.wait_for_timeout(400)
        cats = mjs("return __noza.catFull().filter(function(c){return c.type===%s;})"
                   ".map(function(c){return {id:c.id,name:c.name,w:c.w,d:c.d,h:c.h};});" % json.dumps(typ))
        print(u'  type=%s の商品 %d 件' % (typ, len(cats)))
        mjs("__noza.studio(true); return 1;")
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip,#drawerLabels{display:none !important;}")
        for n, c in enumerate(cats):
            pg.evaluate("window.addFromCatalog(%s);" % json.dumps(c['id']))
            pg.wait_for_timeout(600)
            pos = mjs("var ks=Object.keys(workItems); var k=ks[ks.length-1]; var it=workItems[k];"
                      " deselect(); return {x:it.x,z:it.z,w:it.w,d:it.d,h:it.h};")
            pg.wait_for_timeout(250)
            cx, cz = pos['x'], pos['z']
            span = max(pos['w'], pos['d'], pos['h'])
            for vn, (dx, dy, dz) in enumerate([(0, pos['h'] * 0.8, span * 2.2),
                                               (span * 1.7, pos['h'] * 1.5, span * 1.8)]):
                mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;"
                    % (cx + dx, dy, cz + dz, cx, pos['h'] * 0.45, cz))
                pg.wait_for_timeout(700)
                path = os.path.join(HERE, '_shot_%s_%s_%d%s.png' % (typ, tag, n, 'ab'[vn]))
                pg.screenshot(path=path)
                print(u'  %-52s -> %s' % (c['name'] if vn == 0 else '', os.path.basename(path)))
            # 次の商品と重ならないよう、撮り終えた個体はメッシュだけ隠す (データは触らない)
            mjs("var ks=Object.keys(workItems); var k=ks[ks.length-1];"
                " if(furnMeshes[k]) furnMeshes[k].visible=false; return 1;")
            pg.wait_for_timeout(200)
        br.close()
    for e in errs[:6]:
        print(u'  ' + e)
    return 0


if __name__ == '__main__':
    sys.exit(main())

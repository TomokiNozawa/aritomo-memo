# -*- coding: utf-8 -*-
u"""ベッド商品を studio モード (無地背景) で正面・斜めから撮る。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/shot_bed_studio.py before
  (パッチ後) ... shot_bed_studio.py after

出力: catalog_scripts/_bedshot_<tag>_<n>.png
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:8777/room.html?debug=1"
TAG = (sys.argv[1] if len(sys.argv) > 1 else 'before')


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
            return pg.evaluate("window.__noza.run("
                               + json.dumps("(function(){" + code + "})()") + ")")

        mjs("switchRoom('east62'); return 1;")
        pg.wait_for_timeout(400)
        cats = mjs("return __noza.catFull().filter(function(c){return c.type==='bed';})"
                   ".map(function(c){return {id:c.id,name:c.name};});")
        mjs("__noza.studio(true); return 1;")
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip,#drawerLabels{display:none !important;}")
        for n, c in enumerate(cats):
            pg.evaluate("window.addFromCatalog(%s);" % json.dumps(c['id']))
            pg.wait_for_timeout(500)
            pos = mjs("var ks=Object.keys(workItems); var k=ks[ks.length-1]; var it=workItems[k];"
                      " deselect(); return {x:it.x,z:it.z,w:it.w,d:it.d,h:it.h};")
            pg.wait_for_timeout(250)
            cx, cz = pos['x'], pos['z']
            for vn, (dx, dy, dz) in enumerate([(0, 90, 300), (230, 190, 240)]):
                mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;"
                    % (cx + dx, dy, cz + dz, cx, 35, cz))
                pg.wait_for_timeout(700)
                path = os.path.join(HERE, '_bedshot_%s_%d%s.png' % (TAG, n, 'ab'[vn]))
                pg.screenshot(path=path)
                print(u'  %-46s -> %s' % (c['name'] if vn == 0 else '', os.path.basename(path)))
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

# -*- coding: utf-8 -*-
import json, math, os
from playwright.sync_api import sync_playwright
HERE = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
NG = []
def ck(c, m):
    print((u'  [OK ] ' if c else u'  [NG ] ') + m)
    if not c: NG.append(m)
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width":1100,"height":780})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8777/room.html?debug=1")
    pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000); pg.wait_for_timeout(900)
    mjs = lambda c: pg.evaluate("window.__noza.run(" + json.dumps("(function(){"+c+"})()") + ")")
    mjs("switchRoom('west45'); return 1;")
    cid = mjs("return __noza.catFull().filter(function(c){return /ドレッサーデスク/.test(c.name);})[0].id;")
    pg.evaluate("window.addFromCatalog(%s);" % json.dumps(cid)); pg.wait_for_timeout(800)
    r = mjs("""var ks=Object.keys(workItems),k=ks[ks.length-1],g=furnMeshes[k],it=workItems[k];
      deselect(); g.updateMatrixWorld();
      var m=null; g.children.forEach(function(o){if(o.isGroup){var b=new THREE.Box3().setFromObject(o,true);
        m={lo:b.min.y,hi:b.max.y,zb:b.min.z,rot:o.rotation.x,px:o.position.x,py:o.position.y,pz:o.position.z};}});
      var bb=new THREE.Box3().setFromObject(g,true);
      return {m:m, ix:it.x, iz:it.z, allHi:bb.max.y};""")
    M = r['m']; lean = -M['rot']*180/math.pi
    baseZ = M['pz']   # ミラーの下端(後ろ角)。 Group.position は **ローカル** (家具の中心基準)
    print(u'  実測: 下端 %.2f / 上端 %.2f / 傾き %.2f° / 下端後ろ角 z=%.2f (背面-24から %.2fcm) / 最奥 z=%.2f'
          % (M['lo'], M['hi'], lean, baseZ, baseZ + 24, M['zb'] - r['iz']))
    ck(abs(M['lo'] - 64.2) < 0.05, u'① 下端 = 溝の底 64.2 (ずれ %.2f)' % (M['lo']-64.2))
    ck(abs(M['hi'] - 124.0) < 0.06, u'② 最高点 = 公式の設置例 124.0 (実際 %.2f)' % M['hi'])
    ck(abs(lean - 7.66) < 0.15, u'③ 傾き = asin(8/60) = 7.66° = ほぼ垂直 (実際 %.2f°)' % lean)
    ck(abs((baseZ + 24) - 8.0) < 0.05, u'④ 下端の後ろ角 = 溝の手前ぎわ (背面から 8.0cm / 実際 %.2f)' % (baseZ+24))
    ck(abs((M['zb'] - r['iz']) + 24) < 0.05, u'⑤ 上端が背面 z=-24 (壁) に接する (実際 %.2f)' % (M['zb']-r['iz']))
    ck(abs(r['allHi'] - 124.0) < 0.06, u'⑥ 家具全体の最高点も 124.0 (実際 %.2f)' % r['allHi'])
    mjs("__noza.studio(true); return 1;")
    pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip,#drawerLabels{display:none !important;}")
    for tag, cam in (('side', (r['ix']+215, 80, r['iz']+30)), ('front', (r['ix'], 80, r['iz']+230)),
                     ('slot', (r['ix']+60, 105, r['iz']+95))):
        mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (cam[0],cam[1],cam[2], r['ix'], 62, r['iz']))
        pg.wait_for_timeout(700)
        pg.screenshot(path=os.path.join(HERE, '_v8_8_%s.png' % tag)); print(u'      -> _v8_8_%s.png' % tag)
    br.close()
ck(not errs, u'ページエラー 0件 (実際 %d件)' % len(errs))
print(u'\n════ 結果: NG %d 件 ════' % len(NG))

# -*- coding: utf-8 -*-
u"""v8.9 検証: リガーレの下台が 左40 (炊飯器スライドテーブル) + 右60 (引出し4段) になっているか。
  前提: python -m http.server 8777 を aritomo-memo 直下で起動しておく。
  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_9.py
"""
import json, os
from playwright.sync_api import sync_playwright
HERE = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
NG = []
def ck(c, m):
    print((u'  [OK ] ' if c else u'  [NG ] ') + m)
    if not c: NG.append(m)
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1100, "height": 780})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("" + os.environ.get("NOZA_URL", "http://127.0.0.1:8777/room.html") + "?debug=1")
    pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000); pg.wait_for_timeout(900)
    mjs = lambda c: pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + c + "})()") + ")")
    mjs("switchRoom('ldk'); return 1;")
    cat = mjs("return __noza.catFull().filter(function(c){return /リガーレ/.test(c.name);});")
    ck(len(cat) == 1, u'⓪ カタログにリガーレが1件だけ (二重登録なし / 実際 %d件)' % len(cat))
    ck(u'左40+右60' in cat[0]['name'], u'① 商品名が 左40+右60 (%s)' % cat[0]['name'])
    pg.evaluate("window.addFromCatalog(%s);" % json.dumps(cat[0]['id'])); pg.wait_for_timeout(800)
    r = mjs("""var ks=Object.keys(workItems),k=ks[ks.length-1],it=workItems[k];
      it.rotY=0; itemMeshBuild(k,it); deselect();
      var out={ix:it.x,iz:it.z,name:it.name,dr:[]};
      Object.keys(drawers).forEach(function(id){ if(id.indexOf(k)<0) return; var d=drawers[id];
        var b=new THREE.Box3(); d.boxes.forEach(function(m){var v=m.visible;m.visible=true;m.updateWorldMatrix(true,false);
          b.union(new THREE.Box3().setFromObject(m));m.visible=v;});
        out.dr.push({id:id,label:d.label,cx:(b.min.x+b.max.x)/2-it.x}); });
      return out;""")
    for d in r['dr']:
        print(u'      %s  中心x=%+.1f  %s' % (d['id'].split('_')[-1] if '_' in d['id'] else d['id'], d['cx'], d['label']))
    tbl = [d for d in r['dr'] if u'スライドテーブル' in d['label']]
    ddr = [d for d in r['dr'] if u'深引出し' in d['label']]
    d60 = [d for d in r['dr'] if u'60cm' in d['label']]
    ck(len(tbl) == 1 and abs(tbl[0]['cx'] + 30) < 1.0 and u'左40cm' in tbl[0]['label'],
       u'② スライドテーブル(炊飯器) が左 x=-30 (実際 %+.1f)' % (tbl[0]['cx'] if tbl else 999))
    ck(len(ddr) == 1 and abs(ddr[0]['cx'] + 30) < 1.0, u'③ 深引出しも左 x=-30 (実際 %+.1f)' % (ddr[0]['cx'] if ddr else 999))
    ck(len(d60) == 4 and all(abs(d['cx'] - 20) < 1.0 and u'右60cm' in d['label'] for d in d60),
       u'④ 引出し4段が右 x=+20 (実際 %s)' % [round(d['cx'], 1) for d in d60])
    mjs("__noza.studio(true); return 1;")
    pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip{display:none !important;}")
    mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (r['ix'] + 40, 130, r['iz'] + 290, r['ix'], 100, r['iz']))
    pg.wait_for_timeout(700)
    pg.screenshot(path=os.path.join(HERE, '_v8_9_front_closed.png')); print(u'      -> _v8_9_front_closed.png')
    for d in r['dr']:
        mjs("__noza.drawer(%s); return 1;" % json.dumps(d['id']))
    mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (r['ix'] + 150, 190, r['iz'] + 260, r['ix'], 70, r['iz']))
    pg.wait_for_timeout(900)
    pg.screenshot(path=os.path.join(HERE, '_v8_9_open_all.png')); print(u'      -> _v8_9_open_all.png')
    br.close()
ck(not errs, u'ページエラー 0件 (実際 %d件) %s' % (len(errs), errs[:2]))
print(u'\n════ 結果: NG %d 件 ════' % len(NG))

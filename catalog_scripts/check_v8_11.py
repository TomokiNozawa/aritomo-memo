# -*- coding: utf-8 -*-
u"""v8.11 検証: ① L 27L のメッシュが v8.10 とビット同一 (投入口 +0.1 を除く) ② LL 42L の外形/フタ全開の寸法が公式値どおり ③ ページエラー0。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_11.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働。 v8.10 比較用に room_before_tmp.html (git show HEAD:room.html) を置く。
"""
import json, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8777/"
DUMP = u"""
var ks=Object.keys(workItems); var k=ks[ks.length-1]; var g=null;
scene.traverse(function(o){ if(!g && o.userData && o.userData.itemId===k) g=o; });
g.updateMatrixWorld(true);
var out=[]; g.traverse(function(m){ if(!m.isMesh) return;
  var p=m.geometry.attributes.position, s=0; for(var i=0;i<p.count;i++){ s+=p.getX(i)*1.3+p.getY(i)*1.7+p.getZ(i)*2.1; }
  out.push([m.geometry.type, Math.round(s*1000)/1000, +m.position.x.toFixed(4), +m.position.y.toFixed(4), +m.position.z.toFixed(4),
            +m.rotation.z.toFixed(5), m.visible]); });
function bb(vis){ var b=new THREE.Box3(); g.traverse(function(m){ if(m.isMesh && (vis? m.visible : true)) b.expandByObject(m); }); return b; }
var b=bb(true);
return {k:k, meshes:out, size:[+(b.max.x-b.min.x).toFixed(2), +(b.max.y-b.min.y).toFixed(2), +(b.max.z-b.min.z).toFixed(2)]};
"""


def run(pg, page, names):
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE + page + "?debug=1")
    pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
    pg.wait_for_timeout(800)
    mjs = lambda c: pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + c + "})()") + ")")
    mjs("switchRoom('ldk'); return 1;")
    cats = mjs("return __noza.catFull().map(function(c){return {id:c.id,name:c.name};});")
    res = {}
    for nm in names:
        c = [x for x in cats if x['name'] == nm]
        if not c:
            res[nm] = None
            continue
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(c[0]['id']))
        pg.wait_for_timeout(500)
        closed = mjs(DUMP)
        did = 'i_' + closed['k'] + '_lid'
        mjs("__noza.drawer(%s); return 1;" % json.dumps(did))
        pg.wait_for_timeout(300)
        opened = mjs(DUMP)
        mjs("__noza.drawer(%s); return 1;" % json.dumps(did))
        res[nm] = {'closed': closed, 'open': opened}
    return res, errs


def main():
    L, LL = u'ダストボックス ケユカ 両開き L 27L', u'ダストボックス ケユカ 両開き LL 42L'
    ng = 0
    with sync_playwright() as p:
        br = p.chromium.launch()
        b4, e1 = run(br.new_page(viewport={"width": 1100, "height": 780}), 'room_before_tmp.html', [L])
        af, e2 = run(br.new_page(viewport={"width": 1100, "height": 780}), 'room.html', [L, LL])
        br.close()
    for tag, errs in (('v8.10', e1), ('v8.11', e2)):
        print(u'  ページエラー %s: %d %s' % (tag, len(errs), errs[:2]))
        ng += len(errs)
    # 段2 で 投入口 (開時のみ表示) だけを +0.1cm 上げた (z-fighting 解消)。 それ以外は v8.10 とビット同一であること
    diffs = []
    for st in ('closed', 'open'):
        for x, y in zip(b4[L][st]['meshes'], af[L][st]['meshes']):
            if x != y:
                diffs.append((st, x, y))
    mouth_only = len(b4[L]['open']['meshes']) == len(af[L]['open']['meshes']) and all(
        abs(y[3] - x[3] - 0.1) < 1e-3 and x[:3] == y[:3] and x[4:] == y[4:] for _, x, y in diffs) and len(diffs) == 2
    same = mouth_only
    print(u'  ① L 27L メッシュ v8.10 と同一 (閉/開、 投入口の +0.1 のみ差分): %s  (%d メッシュ / 差分 %d)'
          % (same, len(af[L]['closed']['meshes']), len(diffs)))
    ng += 0 if same else 1
    for nm in (L, LL):
        c, o = af[nm]['closed']['size'], af[nm]['open']['size']
        print(u'  %s 閉: 幅%.1f 高%.1f 奥%.1f / 全開: 幅%.1f 高%.1f' % (nm, c[0], c[1], c[2], o[0], o[1]))
    c, o = af[LL]['closed']['size'], af[LL]['open']['size']
    ok = abs(c[1] - 60.7) < 0.3 and abs(c[0] - 27) < 0.6 and abs(o[0] - (27 + 2.2)) < 0.5 and abs(o[1] - 72.7) < 1.6
    print(u'  ② LL 公式値 (H60.7 / W27 / 全開スパン27 (+フタ厚2.2 = bbox) / 全開H72.7 ±1.5。 L も bbox は 24+1.5=25.5) : %s' % ok)
    ng += 0 if ok else 1
    print(u'結果: NG %d 件' % ng)
    return 1 if ng else 0


if __name__ == '__main__':
    sys.exit(main())

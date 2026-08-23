# -*- coding: utf-8 -*-
u"""冷蔵庫 3Dモデルの メッシュ台帳スナップショット。

v7.5 の「fridge 描画をデータ駆動へ共通化」で **既存の日立 R-HZC54Y XH の見た目が
1メッシュも変わっていない** ことを機械証明するために使う。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/snap_fridge_mesh.py before
  (パッチ後) ... snap_fridge_mesh.py after   → 自動で before と diff

出力: catalog_scripts/_fridge_mesh_<tag>.json
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:8777/room.html?debug=1"

TAG = (sys.argv[1] if len(sys.argv) > 1 else 'before')

# type=fridge の商品を全部 LDK に置き、その Group 配下の全メッシュを
# (幾何タイプ, スケール, 位置, 色) で丸ごと台帳化する
JS = r"""
const cats = __noza.catFull().filter(function(c){ return c.type === 'fridge'; });
const items = __noza.state().items;
const out = [];
cats.forEach(function (c) {
  const id = Object.keys(items).find(function (k) { return items[k].catalogId === c.id; });
  const g = furnMeshes[id];
  const parts = [];
  g.traverse(function (o) {
    if (!o.isMesh) return;
    const gm = o.geometry, pr = (gm && gm.parameters) || {};
    parts.push({
      geo: gm ? gm.type : null,
      p: [r3(o.position.x), r3(o.position.y), r3(o.position.z)],
      s: [r3(pr.width), r3(pr.height), r3(pr.depth),
          r3(pr.radiusTop), r3(pr.radiusBottom)],
      col: o.material && o.material.color ? o.material.color.getHexString() : null,
      op: o.material ? (o.material.opacity === undefined ? 1 : r3(o.material.opacity)) : null,
      tex: !!(o.material && o.material.map)
    });
  });
  out.push({ name: c.name, model: c.model, w: c.w, d: c.d, h: c.h,
             color: c.color, itemId: id, nParts: parts.length, parts: parts });
});
function r3(v) { return (v === undefined || v === null) ? null : Math.round(v * 1000) / 1000; }
return out;
"""


def main():
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 940})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
        pg.wait_for_timeout(900)

        def mjs(code):
            return pg.evaluate("window.__noza.run("
                               + json.dumps("(function(){" + code + "})()") + ")")

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)
        cids = mjs("return __noza.catFull().filter(function(c){return c.type==='fridge';})"
                   ".map(function(c){return c.id;});")
        for cid in cids:
            pg.evaluate("window.addFromCatalog(%s);" % json.dumps(cid))
            pg.wait_for_timeout(400)
        data = mjs(JS)
        br.close()
    if errs:
        print(u'⚠ console error:')
        for e in errs[:10]:
            print(u'   ' + e)
    path = os.path.join(HERE, '_fridge_mesh_%s.json' % TAG)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    for d in data:
        print(u'  %-40s %s  メッシュ %d 個' % (d['name'], d['model'], d['nParts']))
    print(u'  -> ' + path)

    # after なら before と自動 diff
    if TAG != 'before':
        bp = os.path.join(HERE, '_fridge_mesh_before.json')
        if not os.path.exists(bp):
            print(u'  (before スナップショットが無いので diff はスキップ)')
            return 0
        before = json.load(open(bp, encoding='utf-8'))
        bmap = {b['model']: b for b in before}
        bad = 0
        for d in data:
            b = bmap.get(d['model'])
            if not b:
                print(u'  [NEW ] %s (before に無い = 新規商品)' % d['model'])
                continue
            if json.dumps(b['parts'], sort_keys=True) == json.dumps(d['parts'], sort_keys=True):
                print(u'  [SAME] %s のメッシュ台帳は完全一致 (%d 個)' % (d['model'], d['nParts']))
            else:
                bad += 1
                print(u'  [DIFF] %s のメッシュが変わった!' % d['model'])
                for i, (x, y) in enumerate(zip(b['parts'], d['parts'])):
                    if x != y:
                        print(u'     #%d before=%s' % (i, json.dumps(x, ensure_ascii=False)))
                        print(u'        after =%s' % json.dumps(y, ensure_ascii=False))
                if len(b['parts']) != len(d['parts']):
                    print(u'     個数 %d → %d' % (len(b['parts']), len(d['parts'])))
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())

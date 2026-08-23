# -*- coding: utf-8 -*-
u"""★v7.6 検証 — 三菱 MR-MD45N を 左開き (MR-MD45NL) で既定登録

  ① 機械検証: CATALOG_SEED の name/model/install.doorSide / 日立が無変更で残っている /
     hinge が描画に効いている (吊元を左右に振ると 見切り線の x が反転する) /
     ツールチップに「扉の開き: 左開き」が出る
  ② スクリーンショット:
     00 三菱 左開き 正面 (自由端の見切り線が左に出る)
     01 参考: 吊元を左にした場合 (見切り線が右) — 描画が効いていることの対比
     02 家具シート (扉の開き / 据付必要すきま)
     03 モバイル 375x812 家具シート

出力: catalog_scripts\\v7_6_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_6.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
"""
import json
import os
import shutil

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/room.html?debug=1"
HERE = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM', '確認用切り出し')

fails = []
shots = []


def chk(cond, label, got=None):
    print(u'  [%s] %s%s' % ('OK  ' if cond else 'FAIL', label,
                            '' if got is None else (u'  -> %s' % (got,))))
    if not cond:
        fails.append(label)


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

        def shot(tag):
            path = os.path.join(HERE, "v7_6_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-24s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)

        cats = mjs("return Object.keys(catalogData).map(function(id){var c=catalogData[id];"
                   "return {id:id,name:c.name,model:c.model||null,w:c.w,d:c.d,h:c.h,"
                   "type:c.type||null,install:c.install||null};})"
                   ".filter(function(c){return c.type==='fridge';});")
        mit = next((c for c in cats if 'MD45N' in (c.get('model') or '')), None)
        hit = next((c for c in cats if 'HZC' in (c.get('model') or '')), None)
        chk(len(cats) == 2, u'① 冷蔵庫は 2機種のまま', len(cats))
        chk(mit is not None and mit['model'] == 'MR-MD45NL',
            u'① 三菱の形名が 左開き MR-MD45NL', mit and mit['model'])
        chk(mit is not None and u'左開き' in (mit['name'] or ''),
            u'① 商品名に (左開き) が入っている', mit and mit['name'])
        chk(mit is not None and (mit['install'] or {}).get('doorSide') == 'left',
            u'① install.doorSide = left', mit and (mit['install'] or {}).get('doorSide'))
        chk(mit is not None and mit['w'] == 60 and mit['d'] == 69.9 and mit['h'] == 182.6,
            u'① 寸法は公式のまま W60 × D69.9 × H182.6',
            mit and '%sx%sx%s' % (mit['w'], mit['d'], mit['h']))
        chk(hit is not None and (hit['install'] or {}).get('doorSide') is None,
            u'① 日立には doorSide を足していない (無変更)',
            hit and (hit['install'] or {}).get('doorSide'))
        if not mit:
            br.close()
            return 1

        # ── 配置して 3D を確認 ──
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(mit['id']))
        pg.wait_for_timeout(500)
        MID = mjs("var s=__noza.state().items;"
                  "return Object.keys(s).find(function(k){return s[k].catalogId===%s;});"
                  % json.dumps(mit['id']))
        chk(bool(MID), u'② LDK に配置できた', MID)

        # 自由端の見切り線の x を読む (hinge が描画に効いているかの実証)
        def free_edge_x():
            return mjs(
                "var gs=[]; scene.traverse(function(o){if(o.userData&&o.userData.itemId===%s)gs.push(o);});"
                "if(!gs.length) return null;"
                "var g=gs[gs.length-1];"   # 再構築後は最後に積まれたものが現物
                "var best=null;"
                "g.traverse(function(o){ if(!o.geometry||!o.geometry.parameters) return;"
                "  var q=o.geometry.parameters;"
                "  if(Math.abs(q.width-0.9)<0.01 && q.height>80){"
                "    if(best===null || Math.abs(o.position.x)>Math.abs(best)) best=o.position.x; } });"
                "return best;" % json.dumps(MID))

        x_left = free_edge_x()
        chk(x_left is not None and x_left < -20,
            u'② 左開き = 自由端の見切り線が【左】(x<0) に出る', x_left)

        # 吊元を左に振ると反転すること = hinge が本当に効いている
        mjs("var M=FRIDGE_MODELS.filter(function(m){return m.test.test('MR-MD45NL');})[0];"
            "M.rows[M.rows.length-1].hinge='l';"
            "rebuildFurniture(); return 1;")
        pg.wait_for_timeout(400)
        x_right = free_edge_x()
        chk(x_right is not None and x_right > 20,
            u'② 吊元を左にすると 見切り線が【右】へ反転する (hinge が描画に効いている)', x_right)
        shot('01_ref_hinge_left')
        # 元に戻す
        mjs("var M=FRIDGE_MODELS.filter(function(m){return m.test.test('MR-MD45NL');})[0];"
            "M.rows[M.rows.length-1].hinge='r';"
            "rebuildFurniture(); return 1;")
        pg.wait_for_timeout(400)

        # 正面カメラ
        mjs("var it=__noza.state().items[%s];"
            "__noza.cam(it.x, 95, it.z - 190, it.x, 92, it.z); return 1;" % json.dumps(MID))
        pg.wait_for_timeout(700)
        shot('00_left_hinge_front')

        # ── ツールチップ / 家具シート ──
        tip = mjs("return itemDimSummaryHtml(%s, __noza.state().items[%s])"
                  ".replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();" % (json.dumps(MID), json.dumps(MID)))
        print(u'  tip: %s' % tip)
        chk(u'左開き' in tip, u'③ 寸法サマリーに「左開き」が出る')
        chk(u'吊元=右' in tip, u'③ 吊元が右であることが出る')
        chk(u'左へ 41.1cm' in tip, u'③ 扉の開きに必要な側方寸法が出る')
        chk(u'60 × 奥行D 69.9 × 高さH 182.6' in tip, u'③ 寸法が公式値のまま出る')

        pg.evaluate("window.__noza.selectItem(%s);" % json.dumps(MID))
        pg.wait_for_timeout(600)
        shot('02_item_sheet')

        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        pg.evaluate("window.__noza.selectItem(%s);" % json.dumps(MID))
        pg.wait_for_timeout(600)
        shot('03_mobile_item_sheet')

        chk(not errs, u'④ console エラーなし', errs[:3])
        br.close()

    if os.path.isdir(BOX):
        for s in shots:
            shutil.copy2(s, os.path.join(BOX, os.path.basename(s)))
        print(u'  Box へコピー: %d枚' % len(shots))

    print(u'\n════ 結果: FAIL %d件 ════' % len(fails))
    for f in fails:
        print(u'   - %s' % f)
    return 1 if fails else 0


raise SystemExit(main())

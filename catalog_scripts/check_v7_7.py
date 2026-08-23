# -*- coding: utf-8 -*-
u"""★v7.7 検証 — リガーレを ユーザー確定構成 (左60+右40 / 上台109+下台93 / ブラック+セラミック天板) へ

  ① 機械検証: CATALOG_SEED (name/色/天板色/寸法) / openCavityOf が左60cmへ移った /
     引き出し3つのラベルが左右入れ替わっている / 他32商品が無変更
  ② ゴミ箱収納機構: ケユカ27L を 新しい左のオープン部へドロップ → insideOf が付き、
     矢印キーでキャビティ内を動かせること (v6.2〜v6.3 の機構が壊れていないこと)
  ③ 引き出し開閉: 3つとも開閉でき、開いた時に前へ出ること
  ④ スクリーンショット: 正面 / 斜め / 引き出しオープン / ゴミ箱イン / 家具シート / モバイル
  ⑤ console エラーなし

出力: catalog_scripts\\v7_7_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_7.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
⚠カメラは部屋ポリゴンの内側に置く (LDK は x103..790 / y208.5..553.5、x<364 では y283.5 が北壁)
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
            path = os.path.join(HERE, "v7_7_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-26s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)

        # ── ① カタログ ──
        cats = mjs("return Object.keys(catalogData).map(function(id){var c=catalogData[id];"
                   "return {id:id,name:c.name,model:c.model||null,w:c.w,d:c.d,h:c.h,type:c.type||null,"
                   "color:c.color||null,topColor:c.topColor||null,"
                   "colors:(c.colors||[]).map(function(q){return q.name+':'+q.hex;}),"
                   "spec:c.specNote||''};});")
        rig = next((c for c in cats if u'リガーレ' in (c['name'] or '')), None)
        trash27 = next((c for c in cats if u'27L' in (c['name'] or '')), None)
        chk(rig is not None, u'① リガーレがカタログに1件ある')
        if not rig or not trash27:
            br.close()
            return 1
        chk(rig['w'] == 101 and rig['d'] == 51 and rig['h'] == 202,
            u'① 外寸は 101×51×202 のまま', '%sx%sx%s' % (rig['w'], rig['d'], rig['h']))
        chk(u'左60' in rig['name'] and u'右40' in rig['name'],
            u'① 商品名に 左60+右40 が入っている', rig['name'])
        chk(rig['topColor'] is not None, u'① セラミック天板 topColor が入っている', rig['topColor'])
        chk(rig['color'] != rig['topColor'], u'① 本体色と天板色が別色', '%s / %s' % (rig['color'], rig['topColor']))
        blk = [q for q in rig['colors'] if q.split(':')[1].lower() == (rig['color'] or '').lower()]
        chk(bool(blk), u'① 既定色が swatch に存在する (色名が出る)', blk)
        chk(any(q.startswith(u'グレー') for q in rig['colors']),
            u'① 既存の「グレー」スウォッチが残っている', rig['colors'])
        chk(u'167,000' in rig['spec'], u'① specNote に 167,000円 が記録されている')
        chk(u'109' in rig['spec'] and u'93' in rig['spec'], u'① specNote に 上台109/下台93 が記録されている')

        # ── ② 配置 ──
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(rig['id']))
        pg.wait_for_timeout(500)
        RID = mjs("var s=__noza.state().items;"
                  "return Object.keys(s).find(function(k){return s[k].catalogId===%s;});" % json.dumps(rig['id']))
        chk(bool(RID), u'② LDK に配置できた', RID)

        # 壁際に据える (LDK 北壁 y=208.5 に背を付ける。奥行51 → 中心 z=234。x=470 は北壁が 208.5 の帯)
        mjs("__noza.drop(%s, 470, 234); "
            "workItems[%s].rotY=0; syncItemMesh(furnMeshes[%s], workItems[%s]); return 1;"
            % (json.dumps(RID), json.dumps(RID), json.dumps(RID), json.dumps(RID)))
        pg.wait_for_timeout(400)
        pos = mjs("var it=__noza.state().items[%s]; return {x:it.x,z:it.z,rotY:it.rotY};" % json.dumps(RID))
        print(u'  リガーレ位置: %s' % pos)

        # ── ② オープン部が【左】へ移ったか ──
        cav = mjs("var h=__noza.state().items[%s]; var c=openCavityOf(h);"
                  "return c && {label:c.label,x0:Math.round(c.x0*10)/10,x1:Math.round(c.x1*10)/10,"
                  "y1:Math.round(c.y1*10)/10,z0:Math.round(c.z0*10)/10};" % json.dumps(RID))
        print(u'  cavity: %s' % cav)
        chk(cav is not None, u'② openCavityOf がオープン部を返す')
        chk(cav and u'左60' in cav['label'], u'② ラベルが「左60cm」になった', cav and cav['label'])
        chk(cav and cav['x0'] < 0 and cav['x1'] < 12,
            u'② オープン部が本体の【左】側にある (x0<0)', cav and (cav['x0'], cav['x1']))
        chk(cav and abs((cav['x1'] - cav['x0']) - 55) < 0.6, u'② 内寸幅 55cm', cav and round(cav['x1'] - cav['x0'], 1))
        chk(cav and abs(cav['y1'] - 73) < 0.6, u'② 内寸高さ 73cm (下台単品SKU 4709148 の公式値)', cav and cav['y1'])

        # ── ② ゴミ箱を入れて動かす ──
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(trash27['id']))
        pg.wait_for_timeout(500)
        TID = mjs("var s=__noza.state().items;var ks=Object.keys(s).filter(function(k){return s[k].catalogId===%s;});"
                  "return ks[ks.length-1];" % json.dumps(trash27['id']))
        wc = mjs("var h=__noza.state().items[%s];var c=openCavityOf(h);var w=cavityWorld(h,c);"
                 "return {cx:(w.minX+w.maxX)/2, cz:(w.minZ+w.maxZ)/2};" % json.dumps(RID))
        mjs("__noza.drop(%s, %f, %f); return 1;" % (json.dumps(TID), wc['cx'], wc['cz']))
        pg.wait_for_timeout(500)
        ins = mjs("return __noza.insides().filter(function(q){return q.id===%s;})[0];" % json.dumps(TID))
        print(u'  inside: %s' % json.dumps(ins, ensure_ascii=False))
        chk(ins and ins['insideOf'] == RID, u'② ケユカ27L が新しい左オープン部に収まった', ins and ins['insideOf'])
        chk(ins and ins['fit'] and ins['fit'].get('ok') is not False,
            u'② 内寸に収まっている (fit)', ins and ins['fit'])
        before = ins['x'] if ins else None
        mv = mjs("return __noza.insideNudge(%s,'ArrowLeft',3);" % json.dumps(TID))
        chk(mv and mv['insideOf'] == RID and abs(mv['x'] - before) > 0.5,
            u'② 収納内で矢印キー移動できる (キャビティ内クランプ)', (before, mv and mv['x']))
        mjs("__noza.insideNudge(%s,'ArrowRight',3); return 1;" % json.dumps(TID))
        pg.wait_for_timeout(300)

        # ── ③ 引き出し ──
        drs = mjs("return __noza.drawers().filter(function(q){return q.id.indexOf(%s)>=0;});"
                  % json.dumps('i_' + RID + '_'))
        labs = [q['label'] for q in drs]
        print(u'  drawers: %s' % json.dumps(labs, ensure_ascii=False))
        chk(len(drs) == 3, u'③ 引き出し/スライドテーブルが3つ', len(drs))
        chk(any(u'薄引出し(左60cm' in l for l in labs), u'③ 薄引出しが「左60cm」', labs)
        chk(any(u'深引出し(右40cm' in l for l in labs), u'③ 深引出しが「右40cm」', labs)
        chk(any(u'スライドテーブル(右40cm' in l for l in labs), u'③ スライドテーブルが「右40cm」', labs)
        for q in drs:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        pg.wait_for_timeout(400)
        opened = mjs("return __noza.drawers().filter(function(q){return q.id.indexOf(%s)>=0;})"
                     ".map(function(q){return q.open;});" % json.dumps('i_' + RID + '_'))
        chk(all(opened), u'③ 3つとも開いた', opened)

        # ── ④ スクリーンショット ── (家具シートが3Dを覆うので必ず deselect してから撮る)
        it = mjs("var i=__noza.state().items[%s]; return {x:i.x,y:i.y,z:i.z};" % json.dumps(RID))

        def cam(px, py, pz, ty=100, wait=2600):
            mjs("__noza.sel(); return 1;")              # deselect (家具シートを閉じる)
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, it['x'], ty, it['z']))
            pg.wait_for_timeout(wait)                   # ★トーストが消えるまで待つ (下端に被って足元が見えなくなる)

        cam(it['x'], 118, it['z'] + 300, 96)          # 正面 (南から北を見る)
        shot('00_front_drawers_open')
        for q in drs:                                   # 閉じる
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        pg.wait_for_timeout(400)
        cam(it['x'], 118, it['z'] + 300, 96)
        shot('01_front_closed')
        cam(it['x'] - 215, 155, it['z'] + 265, 100)      # 斜め (★右にキッチン本体があるので左から)
        shot('02_iso')
        cam(it['x'] - 40, 60, it['z'] + 145, 42)        # 下段オープン + ゴミ箱 寄り
        shot('03_trash_inside_closeup')
        cam(it['x'] + 10, 160, it['z'] + 165, 160)      # 上台 引き戸 寄り
        shot('04_upper_sliding_doors')
        cam(it['x'] + 30, 95, it['z'] + 135, 78)        # 下台の段 (見切りラインが潰れていないか)
        shot('08_lower_seams_closeup')

        tip = mjs("return itemDimSummaryHtml(%s, __noza.state().items[%s])"
                  ".replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();" % (json.dumps(RID), json.dumps(RID)))
        print(u'  tip(リガーレ): %s' % tip)
        chk(u'101 × 奥行D 51 × 高さH 202' in tip, u'④ 寸法サマリーが公式外寸のまま')
        tipt = mjs("return itemDimSummaryHtml(%s, __noza.state().items[%s])"
                   ".replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();" % (json.dumps(TID), json.dumps(TID)))
        print(u'  tip(ゴミ箱): %s' % tipt)
        chk(u'左60' in tipt, u'④ ゴミ箱側の寸法サマリーに「左60cm」の収納名が出る')

        pg.evaluate("window.__noza.sel(%s);" % json.dumps(RID))
        pg.wait_for_timeout(700)
        shot('05_item_sheet')

        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        cam(it['x'], 118, it['z'] + 300, 96)
        shot('06_mobile_front')
        pg.evaluate("window.__noza.sel(%s);" % json.dumps(RID))
        pg.wait_for_timeout(700)
        shot('07_mobile_item_sheet')

        chk(not errs, u'⑤ console エラーなし', errs[:3])
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

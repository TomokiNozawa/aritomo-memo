# -*- coding: utf-8 -*-
u"""★v7.9 検証 — リガーレ 下台60 を H50-60C (引出し4段) へ是正

  ① 機械検証: CATALOG_SEED v2.7 / model・specNote が引出し4段になった / 外寸は不変
  ② openCavityOf からリガーレが消えた (__noza.cavities() にリガーレが出ない) / エトナは残っている
  ③ 引き出し 6つ (左60 の4段 + 右40 深引出し + スライドテーブル)。4段とも開閉できる
  ④ 🔴後始末-1: ゴミ箱をリガーレへ近づけても 中に入らない (insideOf が付かない)
  ⑤ 🔴後始末-2: 既に insideOf=リガーレ で保存済みのゴミ箱が rebuildFurniture で床へ戻る
     (insideOf=null / y=0 / 宙に浮かない / 消えない / リガーレと重ならない / console エラー無し)
  ⑥ エトナ60OP のゴミ箱スペースは健在 (別商品なので触っていない)
  ⑦ スクショ: 正面 (添付画像と並べて見比べる画角) / 4段オープン / ゴミ箱を近づけた図 /
     床へ戻った図 / エトナ / 家具シート / モバイル 375x812

出力: catalog_scripts\\v7_9_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_9.py
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
            path = os.path.join(HERE, "v7_9_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-26s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)

        # ══ ① カタログ ══
        ver = mjs("return {v: CATALOG_SEED.version, n: CATALOG_SEED.items.length};")
        chk(ver['v'] == '2.7', u'① CATALOG_SEED v2.7', ver['v'])
        chk(ver['n'] == 34, u'① 商品 34件のまま', ver['n'])
        cats = mjs("return Object.keys(catalogData).map(function(id){var c=catalogData[id];"
                   "return {id:id,name:c.name,model:c.model||null,w:c.w,d:c.d,h:c.h,type:c.type||null,"
                   "spec:c.specNote||''};});")
        rig = next((c for c in cats if u'リガーレ' in (c['name'] or '')), None)
        eto = next((c for c in cats if u'エトナ' in (c['name'] or '')), None)
        t27 = next((c for c in cats if u'27L' in (c['name'] or '')), None)
        chk(rig is not None and eto is not None and t27 is not None,
            u'① リガーレ / エトナ / ケユカ27L がカタログにある')
        if not (rig and eto and t27):
            br.close()
            return 1
        chk(rig['w'] == 101 and rig['d'] == 51 and rig['h'] == 202,
            u'① リガーレ 外寸は 101×51×202 のまま', '%sx%sx%s' % (rig['w'], rig['d'], rig['h']))
        chk(u'H50-60C' in (rig['model'] or ''), u'① model に H50-60C が入った', rig['model'])
        chk(u'H50-40J' in (rig['model'] or ''), u'① model に H50-40J が入った')
        chk(u'60OP' not in (rig['model'] or ''), u'① model から 60OP が消えた')
        chk(u'引出し4段' in rig['spec'], u'① specNote に 引出し4段')
        chk(u'最上段51.5×43.5×11' in rig['spec'], u'① specNote に 公式内寸 (最上段11)')
        chk(u'最下段51.5×43.5×24.5' in rig['spec'], u'① specNote に 公式内寸 (最下段24.5)')
        chk(u'167,000' in rig['spec'] and u'4717309' in rig['spec'],
            u'① specNote に 合計167,000円 と SKU 4717309')
        chk(u'未確定・要ユーザー確認' not in rig['spec'],
            u'① v7.7 の「未確定・要ユーザー確認」ブロックが消えた')
        chk(u'ゴミ箱置き場' not in rig['spec'], u'① specNote から リガーレのゴミ箱置き場 記述が消えた')

        # ══ ② 配置 + キャビティ ══
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(rig['id']))
        pg.wait_for_timeout(500)
        RID = mjs("var s=__noza.state().items;"
                  "return Object.keys(s).find(function(k){return s[k].catalogId===%s;});" % json.dumps(rig['id']))
        mjs("__noza.drop(%s, 470, 234); workItems[%s].rotY=0;"
            "syncItemMesh(furnMeshes[%s], workItems[%s]); return 1;"
            % (json.dumps(RID), json.dumps(RID), json.dumps(RID), json.dumps(RID)))
        pg.wait_for_timeout(400)
        cav = mjs("return openCavityOf(__noza.state().items[%s]);" % json.dumps(RID))
        chk(cav is None, u'② openCavityOf(リガーレ) が null (ゴミ箱オープン削除)', cav)
        cavs = mjs("return __noza.cavities().map(function(q){return q.name+' | '+q.label;});")
        chk(not any(u'リガーレ' in c for c in cavs), u'② cavities() にリガーレが出ない', cavs)

        # ══ ③ 引き出し 6つ ══
        drs = mjs("return __noza.drawers().filter(function(q){return q.id.indexOf(%s)>=0;});"
                  % json.dumps('i_' + RID + '_'))
        labs = [q['label'] for q in drs]
        print(u'  drawers(%d):' % len(drs))
        for l in labs:
            print(u'    - %s' % l)
        chk(len(drs) == 6, u'③ 引き出し/スライドテーブルが6つ (4段+深+テーブル)', len(drs))
        for seg, inner in ((u'最上段', u'11'), (u'2段目', u'13.5'), (u'3段目', u'13.5'), (u'最下段', u'24.5')):
            chk(any((u'引出し' + seg) in l and (u'×' + inner + ')') in l for l in labs),
                u'③ 左60 %s のラベル (内寸 %s)' % (seg, inner), [l for l in labs if seg in l])
        chk(not any(u'薄引出し' in l for l in labs), u'③ 旧「薄引出し」ラベルが消えた')
        chk(any(u'深引出し(右40cm' in l for l in labs), u'③ 右40 深引出しは健在')
        chk(any(u'スライドテーブル(右40cm' in l for l in labs), u'③ 右40 スライドテーブルは健在')
        d60 = [q for q in drs if u'左60cm' in q['label']]
        chk(len(d60) == 4, u'③ 左60 の引き出しは4段', len(d60))
        for q in drs:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        pg.wait_for_timeout(400)
        opened = mjs("return __noza.drawers().filter(function(q){return q.id.indexOf(%s)>=0;})"
                     ".map(function(q){return q.open;});" % json.dumps('i_' + RID + '_'))
        chk(all(opened) and len(opened) == 6, u'③ 6つとも開いた', opened)

        it = mjs("var i=__noza.state().items[%s]; return {x:i.x,y:i.y,z:i.z};" % json.dumps(RID))

        def cam(px, py, pz, ty=100, wait=2600):
            mjs("__noza.sel(); return 1;")
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, it['x'], ty, it['z']))
            pg.wait_for_timeout(wait)

        cam(it['x'], 112, it['z'] + 300, 85)
        shot('00_drawers_open')
        for q in drs:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        pg.wait_for_timeout(400)
        cam(it['x'], 112, it['z'] + 300, 85)
        shot('01_front_closed')                      # ★添付画像と並べて見比べる画角
        cam(it['x'] - 30, 95, it['z'] + 130, 60)
        shot('02_lower60_closeup')                   # 下台60 の4段 寄り
        cam(it['x'] - 215, 155, it['z'] + 265, 100)
        shot('03_iso')

        # ══ ④ ゴミ箱を近づけても 中に入らない ══
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(t27['id']))
        pg.wait_for_timeout(500)
        TID = mjs("var s=__noza.state().items;"
                  "var ks=Object.keys(s).filter(function(k){return s[k].catalogId===%s;});"
                  "return ks[ks.length-1];" % json.dumps(t27['id']))
        # 旧オープン部の中心 (左60cm ユニットの内寸中心 = ローカル x-20 / 前寄り) へ落とす
        drp = mjs("var h=__noza.state().items[%s];"
                  "return __noza.drop(%s, h.x - 20, h.z + 8);" % (json.dumps(RID), json.dumps(TID)))
        pg.wait_for_timeout(500)
        ins = mjs("return __noza.insides().filter(function(q){return q.id===%s;})[0];" % json.dumps(TID))
        print(u'  drop結果: %s / inside: %s' % (drp, json.dumps(ins, ensure_ascii=False)))
        chk(ins and ins['insideOf'] is None,
            u'④ ゴミ箱をリガーレへ近づけても 中に入らない (insideOf=null)', ins and ins['insideOf'])
        chk(ins and abs(ins['y']) < 0.05, u'④ 床置きのまま (y=0)', ins and ins['y'])
        ovl = mjs("return pairCollides(__noza.state().items[%s], __noza.state().items[%s]);"
                  % (json.dumps(RID), json.dumps(TID)))
        chk(ovl is False, u'④ リガーレ本体と重なっていない (押し出された)', ovl)
        cam(it['x'] - 20, 70, it['z'] + 150, 45)
        shot('04_trash_not_inside')

        # ══ ⑤ 既に中に入れて保存済みのゴミ箱が 床へ戻ること ══
        #    v7.8 以前のデータを再現: insideOf=リガーレ / insideX,insideZ / y=0 を手で書き込む
        mjs("var t=workItems[%s], h=workItems[%s];"
            "t.insideOf=%s; t.insideX=-20; t.insideZ=3; t.y=0;"
            "t.x=h.x-20; t.z=h.z+3;"
            "syncItemMesh(furnMeshes[%s], t); return 1;"
            % (json.dumps(TID), json.dumps(RID), json.dumps(RID), json.dumps(TID)))
        pg.wait_for_timeout(200)
        pre = mjs("var t=__noza.state().items[%s]; return {insideOf:t.insideOf, x:t.x, y:t.y, z:t.z};"
                  % json.dumps(TID))
        print(u'  仕込み (v7.8以前のデータ相当): %s' % pre)
        chk(pre['insideOf'] == RID, u'⑤ 仕込み完了 (insideOf=リガーレ)', pre['insideOf'])
        errs_before = len(errs)
        n = mjs("rebuildFurniture(); return syncInsidesAll();")   # 読み込みと同じ経路 → 追加分は0
        pg.wait_for_timeout(600)
        post = mjs("var t=__noza.state().items[%s];"
                   "return {exists: !!t, insideOf: t && (t.insideOf||null), x:t&&t.x, y:t&&t.y, z:t&&t.z,"
                   " mesh: !!furnMeshes[%s], meshY: furnMeshes[%s] ? Math.round(furnMeshes[%s].position.y*10)/10 : null};"
                   % (json.dumps(TID), json.dumps(TID), json.dumps(TID), json.dumps(TID)))
        print(u'  後始末後: %s (2回目の syncInsidesAll で追加ドロップ %s件)' % (post, n))
        chk(post['exists'] is True, u'⑤ ゴミ箱が消えていない', post['exists'])
        chk(post['mesh'] is True, u'⑤ 3Dメッシュが残っている', post['mesh'])
        chk(post['insideOf'] is None, u'⑤ insideOf がクリアされた', post['insideOf'])
        chk(abs(post['y']) < 0.05, u'⑤ 床へ戻った (y=0・宙に浮いていない)', post['y'])
        chk(n == 0, u'⑤ rebuildFurniture の中で既に処理済み (2回目は0件) = 冪等', n)
        ovl2 = mjs("return pairCollides(__noza.state().items[%s], __noza.state().items[%s]);"
                   % (json.dumps(RID), json.dumps(TID)))
        chk(ovl2 is False, u'⑤ リガーレと重なっていない (findFreeSpot で逃げた)', ovl2)
        chk(len(errs) == errs_before, u'⑤ 後始末で console エラーが出ていない', errs[errs_before:])
        cam(it['x'] - 20, 80, it['z'] + 170, 45)
        shot('05_trash_dropped_to_floor')

        # ══ ⑥ エトナ側のゴミ箱スペースは健在 ══
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(eto['id']))
        pg.wait_for_timeout(500)
        EID = mjs("var s=__noza.state().items;"
                  "return Object.keys(s).find(function(k){return s[k].catalogId===%s;});" % json.dumps(eto['id']))
        mjs("__noza.drop(%s, 620, 235); workItems[%s].rotY=0;"
            "syncItemMesh(furnMeshes[%s], workItems[%s]); return 1;"
            % (json.dumps(EID), json.dumps(EID), json.dumps(EID), json.dumps(EID)))
        pg.wait_for_timeout(400)
        ecav = mjs("var c=openCavityOf(__noza.state().items[%s]); return c && c.label;" % json.dumps(EID))
        chk(bool(ecav) and u'エトナ' in (ecav or ''), u'⑥ エトナ60OP のゴミ箱スペースは残っている', ecav)
        ewc = mjs("var h=__noza.state().items[%s];var c=openCavityOf(h);var w=cavityWorld(h,c);"
                  "return {cx:(w.minX+w.maxX)/2, cz:(w.minZ+w.maxZ)/2};" % json.dumps(EID))
        mjs("__noza.drop(%s, %f, %f); return 1;" % (json.dumps(TID), ewc['cx'], ewc['cz']))
        pg.wait_for_timeout(500)
        eins = mjs("return __noza.insides().filter(function(q){return q.id===%s;})[0];" % json.dumps(TID))
        chk(eins and eins['insideOf'] == EID, u'⑥ ケユカ27L が エトナへ収まる (機構は健在)',
            eins and eins['insideOf'])

        # ⑥-b 27L が **2個** 入り、**両方のフタ** が開くこと (ユーザー確定: リガーレ廃止分はエトナへ集約)
        #     1個目を左寄せ → 2個目を追加して右寄せ (実操作と同じ __noza.drop 経路)
        mjs("__noza.drop(%s, %f, %f); return 1;" % (json.dumps(TID), ewc['cx'] - 13, ewc['cz']))
        pg.wait_for_timeout(400)
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(t27['id']))
        pg.wait_for_timeout(500)
        T2 = mjs("var s=__noza.state().items;"
                 "var ks=Object.keys(s).filter(function(k){return s[k].catalogId===%s;});"
                 "return ks[ks.length-1];" % json.dumps(t27['id']))
        mjs("__noza.drop(%s, %f, %f); return 1;" % (json.dumps(T2), ewc['cx'] + 13, ewc['cz']))
        pg.wait_for_timeout(500)
        eall = mjs("return __noza.insides().filter(function(q){return q.insideOf===%s;});" % json.dumps(EID))
        chk(len(eall) == 2, u'⑥ エトナ下段に ケユカ27L が2個入った', len(eall))
        for q in eall:
            print(u'    27L: %s local=%s 残り幅=%scm' % (q['id'], q['local'], q['remain'] and q['remain']['gap']))
        lids = mjs("return __noza.drawers().filter(function(q){return /_lid$/.test(q.id) && !q.open;});")
        for q in lids:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        pg.wait_for_timeout(700)
        elid = mjs("var want=%s;"
                   "return __noza.drawers().filter(function(q){return want.indexOf(q.id)>=0;})"
                   ".map(function(q){return {id:q.id, open:q.open, remain:q.remain};});"
                   % json.dumps(['i_' + i + '_lid' for i in [TID, T2] if i]))
        print(u'  エトナ内 27L のフタ: %s' % json.dumps(elid, ensure_ascii=False))
        chk(len(elid) == 2 and all(q['open'] for q in elid),
            u'⑥ エトナ下段の 27L 2個とも フタが開く', elid)
        chk(all(q['remain'] is None or q['remain'] >= 0 for q in elid),
            u'⑥ フタ全開のクリアランスが 2個とも足りている (remain >= 0cm)',
            [q['remain'] for q in elid])

        ei = mjs("var i=__noza.state().items[%s]; return {x:i.x,z:i.z};" % json.dumps(EID))
        mjs("__noza.sel(); return 1;")
        mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (ei['x'], 75, ei['z'] + 150, ei['x'], 45, ei['z']))
        pg.wait_for_timeout(2600)
        shot('06_etona_two_trash_lids_open')

        # ══ ⑦ 家具シート / ツールチップ / モバイル ══
        tip = mjs("return itemDimSummaryHtml(%s, __noza.state().items[%s])"
                  ".replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();" % (json.dumps(RID), json.dumps(RID)))
        print(u'  tip(リガーレ): %s' % tip)
        chk(u'101 × 奥行D 51 × 高さH 202' in tip, u'⑦ 寸法サマリーは公式外寸のまま')
        pg.evaluate("window.__noza.sel(%s);" % json.dumps(RID))
        pg.wait_for_timeout(700)
        shot('07_item_sheet')

        # ⑦-b スタジオ撮影 (床・壁・設備を非表示) = 野沢さんの組み合わせ選択画面の画像と1対1で見比べる画角
        mjs("__noza.sel(); __noza.studio(true); return 1;")
        mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (it['x'], 101, it['z'] + 340, it['x'], 101, it['z']))
        pg.wait_for_timeout(1200)
        shot('09_studio_front')
        mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (it['x'] - 20, 48, it['z'] + 175, it['x'] - 20, 48, it['z']))
        pg.wait_for_timeout(900)
        shot('10_studio_lower60')
        for q in [d for d in drs if u'左60cm' in d['label']]:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        pg.wait_for_timeout(500)
        mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (it['x'] - 60, 120, it['z'] + 260, it['x'] - 10, 60, it['z']))
        pg.wait_for_timeout(900)
        shot('11_studio_4drawers_open')
        for q in [d for d in drs if u'左60cm' in d['label']]:     # 閉じてからモバイルを撮る
            mjs("__noza.drawer(%s); return 1;" % json.dumps(q['id']))
        mjs("__noza.studio(false); return 1;")
        pg.wait_for_timeout(400)

        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        cam(it['x'], 112, it['z'] + 300, 85)
        shot('08_mobile_front')

        chk(not errs, u'⑦ console エラーなし (通し)', errs[:3])
        br.close()

    if os.path.isdir(BOX):
        for s in shots:
            shutil.copy2(s, os.path.join(BOX, os.path.basename(s)))
        print(u'  Box へコピー: %d枚 -> %s' % (len(shots), BOX))

    print(u'\n════ 結果: FAIL %d件 ════' % len(fails))
    for f in fails:
        print(u'   - %s' % f)
    return 1 if fails else 0


raise SystemExit(main())

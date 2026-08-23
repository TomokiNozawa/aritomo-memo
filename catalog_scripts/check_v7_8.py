# -*- coding: utf-8 -*-
u"""★v7.8 検証 — 丸型の壁掛け時計 (セイコークロック KX397A) の追加と 壁掛け対応

  ① 機械検証: CATALOG_SEED (name/model/寸法/type/shape/colors+variant/specNote) / 既存33商品が無変更
  ② 壁掛け機構: WALL_HANG_TYPES に clock を足しただけで
     吸着する / 掛ける高さスライダーが効く / 矢印キーで壁沿いに動く / 壁から外すと床に戻る
  ③ 丸型対応: 寸法表記が「直径32cm × 厚み4.6cm」/ 一覧が φ32×厚4.6 /
     当たり判定 (AABB) が直径基準 / 壁区画の左右クランプが直径基準
  ④ 3Dモデル: メッシュ数 5個 (円は CylinderGeometry。Box の寄せ集めではない)
  ⑤ スクリーンショット: 壁掛け正面 / 文字盤寄り / LDK全景 / スライダー / 床に戻した所 /
     濃茶(KX397B)バリアント / モバイル
  ⑥ console エラーなし

出力: catalog_scripts\\v7_8_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_8.py
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
            path = os.path.join(HERE, "v7_8_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-26s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)

        # ══ ① カタログ ══
        cats = mjs("return Object.keys(catalogData).map(function(id){var c=catalogData[id];"
                   "return {id:id,name:c.name,model:c.model||null,w:c.w,d:c.d,h:c.h,type:c.type||null,"
                   "shape:c.shape||null,room:c.room||null,url:c.url||null,memo:c.memo,"
                   "colors:(c.colors||[]).map(function(q){return q.name+'|'+q.hex+'|'+(q.variant||'');}),"
                   "spec:c.specNote||''};});")
        chk(len(cats) == 34, u'① カタログ 34件 (33 + 時計1)', len(cats))
        ck = next((c for c in cats if c['type'] == 'clock'), None)
        chk(ck is not None, u'① type=clock の商品が1件ある')
        if not ck:
            br.close()
            return 1
        chk(ck['name'] == u'壁掛け時計 セイコー 電波 φ32', u'① 商品名', ck['name'])
        chk(ck['model'] == 'KX397A', u'① 型番 KX397A', ck['model'])
        chk(ck['w'] == 32 and ck['h'] == 32 and abs(ck['d'] - 4.6) < 0.001,
            u'① 寸法 w32 / h32 / d4.6 (公式 直径320×厚み46mm)', (ck['w'], ck['d'], ck['h']))
        chk(ck['shape'] == 'round', u'① shape=round (丸型フラグ)', ck['shape'])
        chk(ck['room'] == 'ldk', u'① room=ldk', ck['room'])
        chk(ck['url'] == 'https://www.seiko-clock.co.jp/product-personal/wall_clock/standard/kx397a.html',
            u'① url が公式製品ページ', ck['url'])
        chk(ck['memo'] in (None, '', 'null'), u'① memo は空 (ユーザーの自由入力欄)', repr(ck['memo']))
        chk(len(ck['colors']) == 2, u'① カラースウォッチ 2色', ck['colors'])
        chk(any(v.startswith(u'アイボリー') and 'KX397A' in v for v in ck['colors']),
            u'① アイボリー(KX397A) スウォッチ', ck['colors'])
        chk(any(v.startswith(u'濃茶') and 'KX397B' in v for v in ck['colors']),
            u'① 濃茶(KX397B) スウォッチ', ck['colors'])
        defcol = mjs("var c=catalogData[%s]; return c.color;" % json.dumps(ck['id']))
        chk((defcol or '').upper() == '#DAD8CC', u'① 既定色 = アイボリー #DAD8CC (実測)', defcol)
        for kw in [u'直径320x46mm', u'970g', u'プラスチック枠', u'アイボリー塗装', u'前面 ガラス',
                   u'電波修正機能', u'40kHz/60kHz', u'ステップセコンド', u'おやすみ秒針', u'11,000円',
                   u'KX397B', u'KX398A', u'木ねじ', u'AKX-070W']:
            chk(kw in ck['spec'], u'① specNote に「%s」' % kw)
        seed = mjs("return {ver:CATALOG_SEED.version, n:CATALOG_SEED.items.length};")
        chk(seed['ver'] == '2.6' and seed['n'] == 34, u'① CATALOG_SEED v2.6 / 34件', seed)

        # ══ ② 配置 → 壁に掛かるか ══
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(ck['id']))
        pg.wait_for_timeout(500)
        CID = mjs("var s=__noza.state().items;"
                  "return Object.keys(s).find(function(k){return s[k].catalogId===%s;});" % json.dumps(ck['id']))
        chk(bool(CID), u'② LDK に配置できた', CID)
        Q = json.dumps(CID)

        meshN = mjs("return furnMeshes[%s].children.length;" % Q)
        chk(meshN == 5, u'④ メッシュ数 5個 (側面/裏板/文字盤/ガラス/銀ツメ4個を1メッシュ)', meshN)
        geos = mjs("return furnMeshes[%s].children.map(function(m){return m.geometry.type;});" % Q)
        chk('CylinderGeometry' in geos and geos.count('CircleGeometry') >= 3,
            u'④ 円は CylinderGeometry + CircleGeometry (Box の寄せ集めではない)', geos)

        walls = mjs("return __noza.walls();")
        north = [w for w in walls if w['dir'] == 'N' and (w['to'] - w['from']) > 120]
        print(u'  LDK 北壁の候補: %s' % json.dumps(north, ensure_ascii=False))
        chk(bool(north), u'② 掛けられる長さの壁区画がある', len(north))
        WL = max(north, key=lambda w: w['to'] - w['from'])
        # レンジフード (黒い箱) を正面カメラに入れないよう、区画の中心から 70cm 右へずらして掛ける
        wx = min((WL['from'] + WL['to']) / 2.0 + 70, WL['to'] - 20)
        wz = WL['c'] - WL['outSign'] * 4.0            # 室内側へ 4cm 浮かせて落とす (reach 30cm 以内)
        mjs("__noza.drop(%s, %f, %f); return 1;" % (Q, wx, wz))
        pg.wait_for_timeout(500)
        hg = mjs("return __noza.hangs().filter(function(q){return q.id===%s;})[0];" % Q)
        print(u'  hang: %s' % json.dumps(hg, ensure_ascii=False))
        chk(hg and hg['hung'], u'② 壁に掛かった (WALL_HANG_TYPES に clock を足しただけ)', hg and hg['wallName'])
        chk(hg and hg['wallId'] == WL['id'], u'② 掛かった壁区画が狙いどおり', hg and hg['wallId'])
        chk(hg and abs(hg['top'] - 175) < 0.6, u'② 既定の上端高さ 175cm', hg and hg['top'])
        chk(hg and abs(hg['y'] - 143) < 0.6, u'② 下端 143cm (175 − 直径32)', hg and hg['y'])
        chk(hg and abs(hg['rotY'] - WL['faceRotY']) < 0.1, u'② 室内を向いている', hg and hg['rotY'])
        ab = hg['aabb'] if hg else None
        chk(ab and abs((ab['maxX'] - ab['minX']) - 32) < 0.6,
            u'③ 当たり判定の幅が直径32cm', ab and round(ab['maxX'] - ab['minX'], 2))
        chk(ab and abs((ab['maxZ'] - ab['minZ']) - 4.6) < 0.3,
            u'③ 当たり判定の奥行が厚み4.6cm', ab and round(ab['maxZ'] - ab['minZ'], 2))

        # ── 掛ける高さスライダー ──
        hh = mjs("return __noza.hangh(%s, 150);" % Q)
        chk(hh and abs(hh['top'] - 150) < 0.6 and abs(hh['y'] - 118) < 0.6,
            u'② 高さスライダー: 上端150 → 下端118', hh)
        hh2 = mjs("return __noza.hangh(%s, 999);" % Q)     # 天井クランプ
        chk(hh2 and hh2['top'] <= 235.1, u'② 上限クランプ (天井クリアランス)', hh2 and hh2['top'])
        mjs("__noza.hangh(%s, 175); return 1;" % Q)

        # ── 矢印キーで壁沿い移動 (丸型でもクランプが直径基準か) ──
        pg.evaluate("window.__noza.sel(%s);" % Q)
        pg.wait_for_timeout(300)
        bx = mjs("return __noza.state().items[%s].x;" % Q)
        for _ in range(5):
            pg.keyboard.press('ArrowLeft')
        pg.wait_for_timeout(300)
        ax = mjs("return __noza.state().items[%s].x;" % Q)
        st = mjs("var h=__noza.hangs().filter(function(q){return q.id===%s;})[0];return h&&h.hung;" % Q)
        chk(abs(ax - bx) > 2 and st, u'② 矢印キーで壁沿いに動く (掛かったまま)', (bx, ax))
        # 端まで押し込んでも壁区画からはみ出さない (クランプは直径基準)
        for _ in range(25):                                   # Shift = 10cm ステップ → 250cm 押し切る
            pg.keyboard.press('Shift+ArrowLeft')
        pg.wait_for_timeout(400)
        ex = mjs("return __noza.state().items[%s].x;" % Q)
        chk(abs(ex - (WL['from'] + 16)) < 0.6,
            u'③ 左端クランプが直径基準 (from + 半径16cm ちょうどで止まる)',
            (round(ex, 1), WL['from'] + 16))
        still = mjs("return __noza.hangs().filter(function(q){return q.id===%s;})[0].hung;" % Q)
        chk(still, u'③ 端まで寄せても掛かったまま (壁区画からはみ出さない)')
        mjs("__noza.drop(%s, %f, %f); return 1;" % (Q, wx, wz))
        pg.wait_for_timeout(400)

        # ══ ③ 寸法表記 (丸型) ══
        tip = mjs("return itemDimSummaryHtml(%s, __noza.state().items[%s])"
                  ".replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();" % (Q, Q))
        print(u'  📐 サマリー: %s' % tip)
        chk(u'直径 32cm × 厚み 4.6cm' in tip, u'③ 「直径 32cm × 厚み 4.6cm」表記', tip[:60])
        chk(u'幅W' not in tip and u'奥行D' not in tip, u'③ 直方体表記 (W×D×H) は出ない')
        chk(u'壁掛け' in tip and u'上端' in tip and u'下端' in tip,
            u'③ 掛けた高さ (上端/下端) が出る')
        wn = (hg or {}).get('wallName') or ''
        chk(wn and wn in tip, u'③ 掛かっている壁の名前が出る', wn)
        short = mjs("return itemDimsShort(catalogData[%s]);" % json.dumps(ck['id']))
        chk(short == u'φ32×厚4.6', u'③ 一覧の短い表記 φ32×厚4.6', short)
        rect = mjs("var s=__noza.state().items; var k=Object.keys(s).filter(function(q){"
                   "return itemTypeOf(s[q])!=='clock';})[0];"
                   "return k?itemDimsText(s[k]):'(配置済みが時計だけ)';")
        print(u'  参考 (直方体商品の表記): %s' % rect)

        # ══ ⑤ スクリーンショット ══
        it = mjs("var i=__noza.state().items[%s]; return {x:i.x,y:i.y,z:i.z};" % Q)
        insign = -WL['outSign']

        def cam(dx, dy, dz, ty=None, wait=2500):
            mjs("__noza.sel(); return 1;")
            tgt = it['y'] + 16 if ty is None else ty
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;"
                % (it['x'] + dx, dy, it['z'] + insign * dz, it['x'], tgt, it['z']))
            pg.wait_for_timeout(wait)

        cam(0, 168, 130)
        shot('00_hung_front')
        cam(0, 166, 46)                      # 文字盤 寄り
        shot('01_face_closeup')
        cam(70, 150, 90)                     # 斜め (厚み46mm と ガラスの奥の文字盤が見える)
        shot('02_iso_thickness')
        cam(-60, 205, 340, 150)              # LDK 全景 (壁に掛かっている位置関係)
        shot('03_ldk_overview')

        pg.evaluate("window.__noza.sel(%s);" % Q)
        pg.wait_for_timeout(700)
        lab3d = pg.evaluate("document.getElementById('dimLabel').textContent")
        chk(lab3d == u'φ32 × 厚4.6', u'③ 3D上の寸法ラベルも丸型表記 (φ32 × 厚4.6)', lab3d)
        sheet = pg.evaluate("document.getElementById('itemSheet').innerText")
        chk(u'掛ける高さ (床〜上端): 175 cm' in sheet, u'② 家具シートに掛ける高さスライダーが出る')
        chk(u'アイボリー (KX397A)' in sheet, u'① カラー名が出る (アイボリー (KX397A))')
        shot('04_item_sheet_slider')

        # ── 濃茶 (KX397B) バリアント ──
        mjs("window.setItemColor('%s','%s'); return 1;" % ('#373632', u'濃茶 (KX397B)'))
        pg.wait_for_timeout(600)
        vcol = mjs("var i=__noza.state().items[%s];return {color:i.color,name:i.colorName,"
                   "mesh:furnMeshes[%s].children.length};" % (Q, Q))
        chk((vcol['color'] or '').lower() == '#373632' and vcol['mesh'] == 5,
            u'⑤ 濃茶バリアントに切替 (メッシュ数は据え置き)', vcol)
        cam(0, 168, 55)
        shot('05_variant_kx397b')
        mjs("window.__noza.sel(%s); window.setItemColor('%s','%s'); return 1;"
            % (Q, '#DAD8CC', u'アイボリー (KX397A)'))
        pg.wait_for_timeout(500)

        # ── 壁から外すと床に戻る ──
        off = mjs("return __noza.unhang(%s);" % Q)
        pg.wait_for_timeout(500)
        chk(off and off['wallId'] is None and abs(off['y']) < 0.05,
            u'② 壁から外すと床に戻る (y=0)', off)
        cam(0, 60, 120, 20)
        shot('06_unhung_floor')
        mjs("__noza.drop(%s, %f, %f); return 1;" % (Q, wx, wz))
        pg.wait_for_timeout(500)
        rehung = mjs("return __noza.hangs().filter(function(q){return q.id===%s;})[0].hung;" % Q)
        chk(rehung, u'② もう一度 壁に掛け直せる')

        # ── 別の壁区画でも同じように掛かるか (レジストリが汎用に効いている証拠) ──
        others = [w for w in north if w['id'] != WL['id']]
        if others:
            W2 = others[0]
            mjs("__noza.drop(%s, %f, %f); return 1;"
                % (Q, (W2['from'] + W2['to']) / 2.0, W2['c'] - W2['outSign'] * 4.0))
            pg.wait_for_timeout(500)
            h2 = mjs("return __noza.hangs().filter(function(q){return q.id===%s;})[0];" % Q)
            chk(h2 and h2['hung'] and h2['wallId'] == W2['id'],
                u'② 別の壁区画 (%s) でも同じように掛かる' % W2['id'], h2 and h2['wallId'])
            i2 = mjs("var i=__noza.state().items[%s]; return {x:i.x,y:i.y,z:i.z};" % Q)
            # ⚠カメラは部屋ポリゴンの内側 (LDK は y208.5..553.5)。N1 は c=283.5 なので +160 まで
            mjs("__noza.sel(); __noza.cam(%f,%f,%f,%f,%f,%f); return 1;"
                % (i2['x'] - 30, 180, i2['z'] + 160, i2['x'], 158, i2['z']))
            pg.wait_for_timeout(2500)
            shot('09_other_wall')
            mjs("__noza.drop(%s, %f, %f); return 1;" % (Q, wx, wz))
            pg.wait_for_timeout(500)

        # ── モバイル 375×812 ──
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        cam(0, 175, 150)
        shot('07_mobile_hung')
        pg.evaluate("window.__noza.sel(%s);" % Q)
        pg.wait_for_timeout(700)
        shot('08_mobile_item_sheet')

        chk(not errs, u'⑥ console エラーなし', errs[:3])
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

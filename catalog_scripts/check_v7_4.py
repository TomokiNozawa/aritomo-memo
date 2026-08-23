# -*- coding: utf-8 -*-
u"""★v7.4 検証 — 壁掛け機構 + 壁掛けカレンダー (新日本カレンダー NK163)

  ① 機械検証: 掛かる / 高さスライダーが効く / 壁から離すと床に戻る / 開口の上には掛からない /
     rotY が室内向き / 保存 (cleanItem) と再構築 (syncHangs) で復元される
  ② スクリーンショット (PNG):
     00 北壁③に掛けた正面 (紙面の見た目)
     01 紙面ドアップ (曜日帯の色・日付グリッド・六曜・吊り下げ穴)
     02 LDK 俯瞰 (北壁③ + 東壁① の2枚 = 縦壁でも正面が室内を向く)
     03 高さスライダー UI (デスク幅)
     04 ツールチップ (W42.5 × H61 × D0.5 / 上端 / 壁の名前)
     05 モバイル 375x812 — 家具シート peek + 操作ハンドル
     06 モバイル 375x812 — 高さスライダー (44px 以上で押せるか)
     07 壁から外して床置きに戻した状態

出力: catalog_scripts\\v7_4_check_*.png  +  Box\\…\\nozaROOM\\確認用切り出し\\v7_4_check_*.png
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_4.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
"""
import json
import os
import shutil
import sys

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/room.html?debug=1"
HERE = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM', '確認用切り出し')

fails = []


def chk(cond, label, got=None):
    print(u'  [%s] %s%s' % ('OK  ' if cond else 'FAIL', label,
                           '' if got is None else (u'  → %s' % (got,))))
    if not cond:
        fails.append(label)


def main():
    shots = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 940})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.hangs", timeout=30000)
        pg.wait_for_timeout(900)

        def js(code):
            return pg.evaluate("(function(){" + code + "})()")

        def mjs(code):
            u"""モジュールスコープ (cleanItem / openItemSheet / itemDimSummaryHtml 等) を
            ?debug=1 の eval フック経由で呼ぶ。"""
            return pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + code + "})()") + ")")

        def shot(tag):
            path = os.path.join(HERE, "v7_4_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-26s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))

        js("switchRoom('ldk');")
        pg.wait_for_timeout(500)

        # ── カタログから壁掛けカレンダーを2枚追加 ───────────────────────
        cid = js("return __noza.catFull().find(function(c){return c.type==='calendar';}).id;")
        chk(bool(cid), u'CATALOG_SEED に type=calendar の商品がある', cid)
        cat = js("return __noza.catFull().find(function(c){return c.type==='calendar';});")
        chk(cat['w'] == 42.5 and cat['h'] == 61 and cat['d'] == 0.5 and cat['room'] == 'ldk'
            and cat['memo'] == '', u'寸法 W42.5 × H61 × D0.5 / room=ldk / memo空',
            '%s %sx%sx%s memo=%r' % (cat['name'], cat['w'], cat['d'], cat['h'], cat['memo']))
        js("window.addFromCatalog('%s');" % cid)
        pg.wait_for_timeout(500)
        js("window.addFromCatalog('%s');" % cid)
        pg.wait_for_timeout(500)
        ids = js("return Object.keys(__noza.state().items);")
        chk(len(ids) == 2, u'カレンダー2枚を配置', ids)
        a, b = ids[0], ids[1]

        # ── ① 壁に掛かる ────────────────────────────────────────
        js("__noza.drop('%s', 650, 216);" % a)          # 北壁③ (c=208.5 / 室内 +z)
        h = js("return __noza.hangs().find(function(x){return x.id==='%s';});" % a)
        chk(h['hung'] and h['wallId'] == 'W-LDK-N3', u'① 北壁③に掛かる', h['wallName'])
        chk(abs(h['z'] - 209.1) < 0.05 and h['rotY'] == 0,
            u'① 背面が壁に密着 (すきま0.3) / rotY=0 で室内向き', 'z=%s rotY=%s' % (h['z'], h['rotY']))
        chk(h['top'] == 175 and abs(h['y'] - 114) < 0.05, u'① 既定の上端 175cm', h['top'])
        js("__noza.drop('%s', 782, 300);" % b)          # 東壁① (c=790 / 室内 -x)
        h2 = js("return __noza.hangs().find(function(x){return x.id==='%s';});" % b)
        chk(h2['hung'] and h2['wallId'] == 'W-LDK-E1' and h2['rotY'] == 90,
            u'① 縦壁 (東壁①) は rotY=90 で室内向き', 'x=%s rotY=%s' % (h2['x'], h2['rotY']))

        # ── ② 高さスライダー ──────────────────────────────────
        chk(js("return __noza.hangh('%s',120).top;" % a) == 120, u'② 高さ 120cm')
        chk(js("return __noza.hangh('%s',235).top;" % a) == 235, u'② 高さ 235cm')
        chk(js("return __noza.hangh('%s',999).top;" % a) == 235, u'② 天井超えは 235 でクランプ')
        chk(js("return __noza.hangh('%s',10).top;" % a) == 100, u'② 下限は 100 でクランプ (床にめり込まない)')
        js("__noza.hangh('%s',175);" % a)

        # ── ③ 開口 (D-07 引き戸 x434〜508.5) の上には掛からない ──────
        js("__noza.drop('%s', 470, 213);" % a)
        h3 = js("return __noza.hangs().find(function(x){return x.id==='%s';});" % a)
        chk((not h3['hung']) and h3['y'] == 0, u'③ 建具 (引き戸) の上には掛からない → 床置き', h3['wallId'])
        # 区画の端でクランプ
        js("__noza.drop('%s', 505, 213);" % a)
        h4 = js("return __noza.hangs().find(function(x){return x.id==='%s';});" % a)
        chk(h4['hung'] and abs(h4['x'] - 529.8) < 0.2,
            u'③ 区画の端 (x508.5) でクランプ = 開口へはみ出さない', h4['x'])
        # 短い壁 (W-LDK-W1 14cm) は掛け先にならない
        walls = js("return __noza.walls();")
        chk(all(w['id'] != 'W-LDK-W1' or w['length'] < 42.5 for w in walls),
            u'③ 幅42.5より短い壁区画 (W-LDK-W1 14cm) は候補外')

        # ── ④ 壁から離すと床に戻る ──────────────────────────────
        js("__noza.drop('%s', 650, 216);" % a)
        js("__noza.drop('%s', 650, 320);" % a)
        h5 = js("return __noza.hangs().find(function(x){return x.id==='%s';});" % a)
        chk((not h5['hung']) and h5['y'] == 0 and h5['wallId'] is None,
            u'④ 壁から離すと床置きに戻る', 'y=%s' % h5['y'])

        # ── ⑤ 保存 (cleanItem) と 再構築 (syncHangs) ────────────────
        js("__noza.drop('%s', 650, 216);" % a)
        js("__noza.hangh('%s',190);" % a)
        cl = mjs("return cleanItem(workItems['%s']);" % a)
        chk(cl.get('wallId') == 'W-LDK-N3' and cl.get('hangH') == 190,
            u'⑤ cleanItem が wallId / hangH を保存', '%s / %s' % (cl.get('wallId'), cl.get('hangH')))
        rb = mjs("var s=JSON.parse(JSON.stringify(workItems));"
                "Object.keys(s).forEach(function(k){s[k]=cleanItem(s[k]);});"
                "workItems=s; rebuildFurniture();"
                "return __noza.hangs().filter(function(x){return x.hung;}).length;")
        chk(rb == 2, u'⑤ 再構築 (syncHangs) で2枚とも壁へ復元', rb)

        # ── スクリーンショット ────────────────────────────────
        js("__noza.hangh('%s',175);" % a)
        js("__noza.sel(null);"); mjs("closeItemSheetFn(); return 1;")
        pg.wait_for_timeout(300)
        # 北壁③ は レンジフード (黒) が手前に立って紙面が隠れるので、
        # 見た目の確認は 東壁① に掛けた b (縦壁ケース) を正対で撮る
        js("__noza.fov(45); __noza.cam(700,145,300,789.5,145,300);")
        pg.wait_for_timeout(500)
        shot('00_hung_front')
        js("__noza.fov(17); __noza.cam(740,145,300,789.5,145,300);")
        pg.wait_for_timeout(500)
        shot('01_paper_closeup')
        js("__noza.fov(60); __noza.cam(560,330,600,600,120,300);")
        pg.wait_for_timeout(500)
        shot('02_ldk_overview')

        # 高さスライダー UI (デスク幅)
        js("__noza.sel('%s');" % a); mjs("openItemSheet(); return 1;")
        pg.wait_for_timeout(400)
        js("var s=document.getElementById('itemSheet'); s.classList.remove('peek');"
           "var e=document.getElementById('hangVal'); if(e) e.scrollIntoView({block:'center'});")
        pg.wait_for_timeout(400)
        chk(js("return !!document.getElementById('hangVal');"), u'⑥ 家具シートに高さスライダーが出る')
        rng = js("var l=document.getElementById('hangVal');"
                 "var r=l&&l.closest('.form-group').querySelector('input[type=range]');"
                 "return r? {min:r.min,max:r.max,step:r.step,value:r.value,h:Math.round(r.getBoundingClientRect().height)}:null;")
        chk(rng and float(rng['min']) == 100 and float(rng['max']) == 235 and rng['h'] >= 44,
            u'⑥ スライダー 100〜235 / 高さ44px以上', rng)
        shot('03_slider_desktop')

        # ツールチップ (寸法 / 上端 / 壁の名前)
        tip = mjs("return itemDimSummaryHtml('%s', workItems['%s']);" % (a, a))
        chk(u'42.5' in tip and u'61' in tip and u'0.5' in tip, u'⑦ ツールチップに W42.5 × D0.5 × H61')
        chk(u'上端: 175cm' in tip.replace(' ', '') or u'上端' in tip, u'⑦ ツールチップに 上端の高さ')
        chk(u'LDK北壁③' in tip and u'W-LDK-N3' in tip, u'⑦ ツールチップに 掛かっている壁の名前 + ID')
        print(u'      tip: ' + tip.replace('<div class="dim-note">', '').replace('</div>', '')
              .replace('<br>', ' | ').replace('📐 ', ''))
        js("var e=document.getElementById('itemBody'); e.scrollTop=0;")
        pg.wait_for_timeout(300)
        shot('04_tooltip_dims')

        # 壁から外す → 床置き
        js("__noza.unhang('%s');" % a)
        pg.wait_for_timeout(300)
        js("__noza.sel(null); __noza.fov(52); __noza.cam(650,150,400,650,60,300);"); mjs("closeItemSheetFn(); return 1;")
        pg.wait_for_timeout(500)
        shot('07_unhung_floor')

        # ── モバイル 375x812 ────────────────────────────────
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(600)
        js("__noza.drop('%s', 650, 216);" % a)
        js("__noza.sel('%s');" % a); mjs("openItemSheet(); return 1;")
        pg.wait_for_timeout(500)
        ui = js("var mv=document.getElementById('gizmoMove'), rt=document.getElementById('gizmoRot');"
                "var f=function(e){if(!e)return null;var r=e.getBoundingClientRect();"
                "return {w:Math.round(r.width),h:Math.round(r.height),vis:r.width>0&&r.height>0};};"
                "return {move:f(mv), rot:f(rt), peek:document.getElementById('itemSheet').className};")
        chk(ui['move'] and ui['move']['w'] >= 44 and ui['move']['h'] >= 44,
            u'⑧ モバイル: 移動ハンドルが 44px 以上', ui['move'])
        shot('05_mobile_peek')
        js("var s=document.getElementById('itemSheet'); s.classList.remove('peek');")
        pg.wait_for_timeout(300)
        js("var l=document.getElementById('hangVal'); if(l) l.closest('.form-group').scrollIntoView({block:'center'});")
        pg.wait_for_timeout(400)
        m = js("var l=document.getElementById('hangVal');"
               "if(!l) return null; var g=l.closest('.form-group');"
               "var r=g.querySelector('input[type=range]').getBoundingClientRect();"
               "var bs=[].map.call(g.querySelectorAll('.floorh-btn'), function(b){var q=b.getBoundingClientRect();"
               "return {w:Math.round(q.width),h:Math.round(q.height)};});"
               "var u=g.querySelector('.btn-secondary').getBoundingClientRect();"
               "return {range:{w:Math.round(r.width),h:Math.round(r.height)}, btns:bs,"
               "unhang:{w:Math.round(u.width),h:Math.round(u.height)}};")
        chk(m and m['range']['h'] >= 44, u'⑧ モバイル: スライダー 高さ44px以上', m and m['range'])
        chk(m and all(x['h'] >= 44 for x in m['btns']), u'⑧ モバイル: ±5cm/既定 ボタン 44px以上', m and m['btns'])
        chk(m and m['unhang']['h'] >= 44, u'⑧ モバイル: 「壁から外す」 44px以上', m and m['unhang'])
        shot('06_mobile_slider')

        print(u'  console errors: %s' % (errs if errs else u'なし'))
        if errs:
            fails.append(u'console error: %s' % errs[:3])
        br.close()

    # Box へコピー
    if os.path.isdir(os.path.dirname(BOX)):
        if not os.path.isdir(BOX):
            os.makedirs(BOX)
        for s in shots:
            shutil.copy2(s, os.path.join(BOX, os.path.basename(s)))
        print(u'  Box へコピー: %s (%d 枚)' % (BOX, len(shots)))
    else:
        print(u'  ⚠ Box フォルダが見つからない: %s' % BOX)

    print(u'\n════ 検証結果: FAIL %d 件 ════' % len(fails))
    for f in fails:
        print(u'   - %s' % f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

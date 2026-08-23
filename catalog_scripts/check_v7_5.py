# -*- coding: utf-8 -*-
u"""★v7.5 検証 — 冷蔵庫 三菱 MR-MD45N の追加 + 冷蔵庫3Dモデルのデータ駆動共通化

  ① 機械検証: CATALOG_SEED の値 (寸法・room・zone・memo空) / 既存の日立が残っている /
     FRIDGE_MODELS のデータ駆動描画で 2機種が別メッシュ構成になる /
     寸法ラベル・寸法サマリー (据付必要すきま込み) が出る
  ② スクリーンショット (PNG):
     00 新旧2機種を並べた正面 (見分けがつくか)
     01 三菱 MR-MD45N 単体 ドアップ (5ドア・真ん中野菜室・1枚扉)
     02 日立 R-HZC54Y XH 単体 ドアップ (フレンチ6ドア = v7.4 と同じ見た目)
     03 LDK 俯瞰 (冷蔵庫置き場 有効幅169cm に置いた状態)
     04 寸法サマリー (W60 × D69.9 × H182.6 + 据付必要すきま) の家具シート
     05 寸法ラベル (3D上の W60 × D69.9 × H182.6)
     06 モバイル 375x812 — 2機種並べた表示
     07 モバイル 375x812 — 家具シート (寸法サマリー)

出力: catalog_scripts\\v7_5_check_*.png  +  Box\\…\\nozaROOM\\確認用切り出し\\v7_5_check_*.png
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_5.py
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
        pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
        pg.wait_for_timeout(900)

        def js(code):
            return pg.evaluate("(function(){" + code + "})()")

        def mjs(code):
            return pg.evaluate("window.__noza.run("
                               + json.dumps("(function(){" + code + "})()") + ")")

        def shot(tag):
            path = os.path.join(HERE, "v7_5_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-26s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)

        # ── ① CATALOG_SEED の値 ───────────────────────────────
        # __noza.catFull() は url / install を返さないので catalogData を直接読む
        cats = mjs("return Object.keys(catalogData).map(function(id){var c=catalogData[id];"
                   "return {id:id, name:c.name, model:c.model||null, w:c.w, d:c.d, h:c.h,"
                   "type:c.type||null, room:c.room||null, zone:c.zone||null, color:c.color||null,"
                   "memo:c.memo===undefined?null:c.memo, url:c.url||null,"
                   "install:c.install||null, colors:c.colors||null};})"
                   ".filter(function(c){return c.type==='fridge';});")
        chk(len(cats) == 2, u'① 冷蔵庫が 2機種 (日立 + 三菱) カタログにある', len(cats))
        mit = next((c for c in cats if 'MD45N' in (c.get('model') or '')), None)
        hit = next((c for c in cats if 'HZC' in (c.get('model') or '')), None)
        chk(hit is not None, u'① 既存の 日立 R-HZC54Y XH が削除されずに残っている',
            hit and hit['name'])
        chk(mit is not None, u'① 三菱 MR-MD45N が追加されている', mit and mit['name'])
        if not (mit and hit):
            br.close()
            return 1
        chk(mit['w'] == 60 and mit['d'] == 69.9 and mit['h'] == 182.6,
            u'① 三菱 寸法 W60 × D69.9 × H182.6 (公式 600×699×1826mm)',
            '%sx%sx%s' % (mit['w'], mit['d'], mit['h']))
        chk(mit['room'] == 'ldk' and mit.get('zone') == 'kitchen',
            u'① 三菱 room=ldk / zone=kitchen', '%s/%s' % (mit['room'], mit.get('zone')))
        chk(mit.get('memo') == '', u'① 三菱 memo は空 (ユーザーの自由入力欄)',
            repr(mit.get('memo')))
        chk('mitsubishielectric.co.jp' in (mit.get('url') or ''),
            u'① 三菱 url が公式製品ページ', mit.get('url'))
        chk(bool(mit.get('install')), u'① 三菱 install (据付必要すきま) を持つ', mit.get('install'))
        chk(bool(hit.get('install')), u'① 日立 install (据付必要すきま) を持つ', hit.get('install'))

        # ── ② 3Dモデル: データ駆動で 2機種が別構成になる ─────────────
        for c in (hit, mit):
            pg.evaluate("window.addFromCatalog(%s);" % json.dumps(c['id']))
            pg.wait_for_timeout(450)
        ids = mjs("var s=__noza.state().items;"
                  "return {hit:Object.keys(s).find(function(k){return s[k].catalogId===%s;}),"
                  "mit:Object.keys(s).find(function(k){return s[k].catalogId===%s;})};"
                  % (json.dumps(hit['id']), json.dumps(mit['id'])))
        HID, MID = ids['hit'], ids['mit']
        chk(bool(HID) and bool(MID), u'② 2機種とも LDK に配置できた', ids)

        models = mjs("return FRIDGE_MODELS.map(function(m){return "
                     "{label:m.label, rows:m.rows.map(function(r){return "
                     "{key:r.key, top:r.top, front:r.front, "
                     "split:(r.split===undefined?null:r.split), "
                     "handles:(r.handles||[]).length, panels:(r.panels||[]).length};})};});")
        chk(len(models) == 2, u'② FRIDGE_MODELS に 2機種ぶんのデータがある', len(models))
        print(u'      ' + json.dumps(models, ensure_ascii=False))
        hm = mjs("return fridgeModelOf(%s).label;" % json.dumps(hit['name'] + ' ' + hit['model']))
        mm = mjs("return fridgeModelOf(%s).label;" % json.dumps(mit['name'] + ' ' + mit['model']))
        chk(hm != mm, u'② 型番から別の扉構成データが引ける', '%s ⇔ %s' % (hm, mm))

        def parts(iid):
            return mjs("var g=furnMeshes[%s], a=[];"
                       "g.traverse(function(o){if(!o.isMesh)return;var pr=o.geometry.parameters||{};"
                       "a.push([Math.round((pr.width||0)*100)/100,Math.round((pr.height||0)*100)/100,"
                       "Math.round(o.position.x*100)/100,Math.round(o.position.y*100)/100]);});"
                       "return a;" % json.dumps(iid))

        hp, mp = parts(HID), parts(MID)
        chk(len(hp) > 0 and len(mp) > 0, u'② 2機種とも詳細モデルで描かれている',
            u'日立 %d メッシュ / 三菱 %d メッシュ' % (len(hp), len(mp)))
        chk(hp != mp, u'② 2機種のメッシュ構成が違う = 見分けがつく')
        chk(len(hp) == 13, u'② 日立は v7.4 と同じ 13 メッシュ (見た目不変)', len(hp))
        # 縦長ハンドル (幅2.2cm) の本数 = 日立フレンチ観音2本 / 三菱フラット扉0本
        hbar = [q for q in hp if q[0] == 2.2]
        mbar = [q for q in mp if q[0] == 2.2]
        chk(len(hbar) == 2, u'② 日立はフレンチ観音 = 縦長ハンドル2本', len(hbar))
        chk(len(mbar) == 0, u'② 三菱はフラット扉 = 縦ハンドル0本 (公式写真どおり)', len(mbar))
        # 三菱の冷蔵室扉は 下端の全幅グリップ (段の境界 0.531h の 2.8cm 上)
        gy = round(182.6 * 0.531 + 2.8, 1)
        grip = [q for q in mp if abs(q[1] - 1.6) < 0.01 and abs(q[3] - gy) < 0.15]
        chk(len(grip) == 1, u'② 三菱 冷蔵室扉に 下端の全幅グリップがある (床から %.1fcm)' % gy,
            grip)
        # 段の境界: 三菱は 冷蔵室扉下端 = 公式 969mm
        chk(abs(mjs("return FRIDGE_MODELS.find(function(m){return /MD/.test(m.label);})"
                    ".rows[2].top;") * 1826 - 969) < 3,
            u'② 三菱 冷蔵室扉の下端 = 床から969mm (公式据付必要寸法図)')

        # ── ③ 寸法ラベル / 寸法サマリー (据付必要すきま込み) ────────────
        mjs("__noza.sel(%s); return 1;" % json.dumps(MID))
        pg.wait_for_timeout(400)
        lab = js("var e=document.getElementById('dimLabel');"
                 "return {txt:e.textContent, show:e.style.display};")
        chk(lab['txt'] == 'W60 × D69.9 × H182.6',
            u'③ 3D上の寸法ラベルが W60 × D69.9 × H182.6', lab)
        tip = mjs("return itemDimSummaryHtml(%s, workItems[%s]);"
                  % (json.dumps(MID), json.dumps(MID)))
        flat = tip.replace('<div class="dim-note">', '').replace('</div>', '') \
                  .replace('<br>', ' | ').replace('📐 ', '')
        print(u'      三菱 tip: ' + flat)
        chk(u'60' in tip and u'69.9' in tip and u'182.6' in tip,
            u'③ 寸法サマリーに 幅W 60 × 奥行D 69.9 × 高さH 182.6cm')
        chk(u'据付必要すきま' in tip, u'③ 寸法サマリーに 据付必要すきま が出る')
        htip = mjs("return itemDimSummaryHtml(%s, workItems[%s]);"
                   % (json.dumps(HID), json.dumps(HID)))
        print(u'      日立 tip: ' + htip.replace('<div class="dim-note">', '')
              .replace('</div>', '').replace('<br>', ' | ').replace('📐 ', ''))
        chk(u'据付必要すきま' in htip, u'③ 日立にも 据付必要すきま が出る (汎用フィールド)')

        # ── ④ スクリーンショット ────────────────────────────────
        mjs("__noza.sel(null); closeItemSheetFn(); return 1;")
        # 2機種を並べて正対 (rotY=0 = 正面が +z 向き → カメラは南 (z大) から北を見る)。
        # 見比べ用は studio モード (床・壁・建具を非表示にして無地背景) で撮る
        mjs("__noza.drop(%s, 480, 300); __noza.drop(%s, 620, 300); return 1;"
            % (json.dumps(HID), json.dumps(MID)))
        pg.wait_for_timeout(400)
        pos = mjs("var s=__noza.state().items;"
                  "return [[s[%s].x,s[%s].z],[s[%s].x,s[%s].z]];"
                  % (json.dumps(HID), json.dumps(HID), json.dumps(MID), json.dumps(MID)))
        print(u'      配置: 日立 %s / 三菱 %s' % (pos[0], pos[1]))
        hx, hz = pos[0]
        mx, mz = pos[1]
        mid = (hx + mx) / 2.0
        span = abs(hx - mx) + 80
        dist = max(340.0, span * 1.9)

        def cam(cx, cy, cz, tx, ty, tz, fov):
            mjs("__noza.fov(%s); __noza.cam(%s,%s,%s,%s,%s,%s); return 1;"
                % (fov, cx, cy, cz, tx, ty, tz))

        mjs("__noza.studio(true); return 1;")
        cam(mid, 175, hz + dist, mid, 92, hz, 40)
        pg.wait_for_timeout(700)
        shot('00_two_fridges_front')
        cam(mx, 175, mz + 420, mx, 92, mz, 40)
        pg.wait_for_timeout(500)
        shot('01_mitsubishi_closeup')
        cam(hx, 175, hz + 420, hx, 92, hz, 40)
        pg.wait_for_timeout(500)
        shot('02_hitachi_closeup')
        # 冷蔵庫置き場 (E壁 有効幅169cm / x724..790 z208.5..377.5) に三菱を入れてみる
        mjs("__noza.studio(false); return 1;")
        mjs("__noza.drop(%s, 200, 480); return 1;" % json.dumps(HID))   # 日立はリビング側へ退避
        mjs("__noza.drop(%s, 757, 250); return 1;" % json.dumps(MID))
        pg.wait_for_timeout(400)
        nook = mjs("var s=__noza.state().items; var m=s[%s];"
                   "return {x:m.x, z:m.z, rotY:m.rotY||0,"
                   "x0:Math.round((m.x-m.w/2)*10)/10, x1:Math.round((m.x+m.w/2)*10)/10,"
                   "z0:Math.round((m.z-m.d/2)*10)/10, z1:Math.round((m.z+m.d/2)*10)/10};"
                   % json.dumps(MID))
        print(u'      冷蔵庫置き場に置いた三菱: %s' % nook)
        # 冷蔵庫置き場 = x724..790 / z208.5..377.5 (有効幅169cm) に収まっているか
        chk(nook['x0'] >= 723.5 and nook['x1'] <= 790.5 and nook['z0'] >= 208.0,
            u'④ 三菱が LDK東壁の冷蔵庫置き場 (x724..790 / 有効幅169cm) に収まる', nook)
        cam(560, 190, 470, 757, 95, 270, 58)
        pg.wait_for_timeout(700)
        shot('03_ldk_fridge_nook')

        # 家具シート (寸法サマリー)
        mjs("__noza.sel(%s); openItemSheet(); return 1;" % json.dumps(MID))
        pg.wait_for_timeout(500)
        js("var s=document.getElementById('itemSheet'); s.classList.remove('peek');"
           "var e=document.getElementById('itemBody'); if(e) e.scrollTop=0;")
        pg.wait_for_timeout(400)
        shot('04_item_sheet_dims')
        mjs("closeItemSheetFn(); return 1;")
        mjs("__noza.drop(%s, %s, %s); return 1;" % (json.dumps(MID), mx, mz))
        mjs("__noza.sel(%s); return 1;" % json.dumps(MID))
        cam(mx + 150, 200, mz + 230, mx, 110, mz, 50)   # LDK の内側 (z<553.5) に収める
        pg.wait_for_timeout(700)
        shot('05_dim_label')

        # ── ⑤ モバイル 375x812 ────────────────────────────────
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        mjs("__noza.sel(null); closeItemSheetFn(); __noza.studio(true); return 1;")
        mjs("__noza.drop(%s, %s, %s); __noza.drop(%s, %s, %s); return 1;"
            % (json.dumps(HID), hx, hz, json.dumps(MID), mx, mz))
        pg.wait_for_timeout(500)
        cam(mid, 175, hz + max(dist, 420), mid, 92, hz, 46)
        pg.wait_for_timeout(700)
        shot('06_mobile_two_fridges')
        mjs("__noza.studio(false); return 1;")
        mjs("__noza.sel(%s); openItemSheet(); return 1;" % json.dumps(MID))
        pg.wait_for_timeout(500)
        js("var s=document.getElementById('itemSheet'); s.classList.remove('peek');"
           "var e=document.getElementById('itemBody'); if(e) e.scrollTop=0;")
        pg.wait_for_timeout(400)
        note = js("var e=document.querySelector('.dim-note');"
                  "if(!e) return null; var r=e.getBoundingClientRect();"
                  "return {w:Math.round(r.width), h:Math.round(r.height),"
                  "inview: r.left>=0 && r.right<=window.innerWidth+1};")
        chk(note and note['inview'],
            u'⑤ モバイル375: 寸法サマリーが横にはみ出さない', note)
        shot('07_mobile_item_sheet')

        print(u'  console errors: %s' % (errs if errs else u'なし'))
        if errs:
            fails.append(u'console error: %s' % errs[:3])
        br.close()

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

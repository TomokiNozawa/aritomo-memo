# -*- coding: utf-8 -*-
u"""v8.6 の検証: LOWYA アユリナ 2点 (CABINET_MODELS) が 公式値どおりに描けているかを機械照合する。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_6.py

前提: python -m http.server 8777 が ~/aritomo-memo で稼働
見るもの:
  ① ページエラーが出ないこと
  ② カタログ2点が west45 (洋室4.5帖) にいて 寸法が公式値ちょうどであること
  ③ 引き出しの登録数 (ドレッサー 5杯 / ハイチェスト 5杯 = 公式の杯数) と ラベルの内寸表記
  ④ 引き出しを全部開いても 例外が出ないこと + 開いた状態のスクリーンショット
  ⑤ メッシュの高さ方向の要所 (デスク天板71 / チェスト天面58.5 / ミラー上端124) が公式値と一致
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:8777/room.html?debug=1"
NG = []


def ck(cond, msg):
    print((u'  [OK ] ' if cond else u'  [NG ] ') + msg)
    if not cond:
        NG.append(msg)


def main():
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1100, "height": 780})
        errs = []
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
        pg.wait_for_timeout(900)

        def mjs(code):
            return pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + code + "})()") + ")")

        mjs("switchRoom('west45'); return 1;")
        cats = mjs("return __noza.catFull().filter(function(c){return c.type==='cabinet';})"
                   ".map(function(c){return {id:c.id,name:c.name,room:c.room,w:c.w,d:c.d,h:c.h,color:c.color};});")
        ck(len(cats) == 2, u'type=cabinet の商品が2件 (実際 %d件)' % len(cats))
        want = {u'LOWYA アユリナ ドレッサーデスク 幅120 + 正方形ミラー (ウォルナット)': (120, 48, 71),
                u'LOWYA アユリナ ハイチェスト 幅80 (ウォルナット)': (80, 42, 99.5)}
        for c in cats:
            ck(c['name'] in want, u'商品名: %s' % c['name'])
            if c['name'] in want:
                ck((c['w'], c['d'], c['h']) == want[c['name']],
                   u'  公式寸法どおり %s×%s×%s' % (c['w'], c['d'], c['h']))
            ck(c['room'] == 'west45', u'  配置予定部屋 = west45 (洋室4.5帖) / 実際 %s' % c['room'])
            ck(str(c['color']).lower() == '#835845', u'  カラー = ウォルナット #835845 / 実際 %s' % c['color'])

        mjs("__noza.studio(true); return 1;")
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip{display:none !important;}")
        for n, c in enumerate(cats):
            pg.evaluate("window.addFromCatalog(%s);" % json.dumps(c['id']))
            pg.wait_for_timeout(600)
            info = mjs("var ks=Object.keys(workItems); var k=ks[ks.length-1]; var it=workItems[k];"
                       " deselect();"
                       " var g=furnMeshes[k]; g.updateMatrixWorld();"
                       # ⚠ precise=true が要る: 既定の Box3 は「ジオメトリのAABBの8隅を変換」なので、
                       #   傾けた丸脚だと 実物より 1〜2mm 下に出て 接地判定を誤る (実頂点で測る)
                       " var bb=new THREE.Box3().setFromObject(g, true);"
                       " return {id:k,x:it.x,z:it.z,w:it.w,d:it.d,h:it.h,"
                       "         top:Math.round((bb.max.y)*100)/100, bot:Math.round(bb.min.y*100)/100,"
                       "         bw:Math.round((bb.max.x-bb.min.x)*10)/10,"
                       "         bd:Math.round((bb.max.z-bb.min.z)*10)/10};")
            drs = mjs("return __noza.drawers();")
            mine = [d for d in drs if d['id'].startswith('i_' + info['id'] + '_')]
            print(u'  ── %s' % c['name'])
            ck(len(mine) == 5, u'  引き出し 5杯 (公式の杯数) / 実際 %d杯' % len(mine))
            for d in mine:
                print(u'      %s  %s' % (d['id'], d['label']))
            # 高さ方向の要所
            if '120' in c['name']:
                ck(abs(info['top'] - 124.0) < 0.15,
                   u'  ミラー上端 = 公式の設置例 124cm ちょうど / 実際 %.2f' % info['top'])
                ck(abs(info['bw'] - 120) < 0.6, u'  外形幅 120 / 実際 %.1f' % info['bw'])
            else:
                ck(abs(info['top'] - 99.5) < 0.3, u'  天面 = 99.5 / 実際 %.1f' % info['top'])
                ck(abs(info['bw'] - 80) < 0.6, u'  外形幅 80 / 実際 %.1f' % info['bw'])
            ck(abs(info['bot']) < 0.06, u'  脚がちょうど接地 (床からのずれ %.2f cm)' % info['bot'])
            # 全部開ける
            for d in mine:
                mjs("__noza.drawer(%s); return 1;" % json.dumps(d['id']))
            pg.wait_for_timeout(900)
            opened = [d for d in mjs("return __noza.drawers();") if d['id'].startswith('i_' + info['id'] + '_')]
            ck(all(d['open'] for d in opened), u'  5杯すべて開いた')
            span = max(info['w'], info['d'], info['h'])
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;"
                % (info['x'] + span * 1.5, info['h'] * 1.3, info['z'] + span * 1.9,
                   info['x'], info['h'] * 0.45, info['z']))
            pg.wait_for_timeout(700)
            pg.screenshot(path=os.path.join(HERE, '_v8_6_open_%d.png' % n))
            print(u'      -> _v8_6_open_%d.png (全部開けた状態)' % n)
            for d in mine:
                mjs("__noza.drawer(%s); return 1;" % json.dumps(d['id']))
            mjs("var ks=Object.keys(workItems); var k=ks[ks.length-1];"
                " if(furnMeshes[k]) furnMeshes[k].visible=false; return 1;")
            pg.wait_for_timeout(200)
        br.close()
    ck(not errs, u'ページエラー 0件 (実際 %d件)' % len(errs))
    for e in errs[:6]:
        print(u'      ' + e)
    print(u'\n════ 結果: NG %d 件 ════' % len(NG))
    return 1 if NG else 0


if __name__ == '__main__':
    sys.exit(main())

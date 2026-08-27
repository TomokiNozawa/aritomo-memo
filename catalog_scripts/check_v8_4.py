# -*- coding: utf-8 -*-
u"""★v8.4 検証 — 野沢さん 2026-08-24 追加実測の反映

  ① 機械検証: ROOM_DATA v6.11 / CATALOG_SEED 不変 / 各要素の値 / 東壁チェーンの閉合
  ② 汎用機構: install.doorFront が 4室 + キッチン の 5要素に載り、
     建具・設備 どちらのツールチップにも 同じ1行として出る (4室バラバラの実装になっていない)
  ③ 3D スクショ: 4室のクローゼット (3室は扉を開いた状態 / LDK は F-24 本体) /
     6.2帖の小窓と空気口 / キッチンのコンロ引き出しを開けた状態 / モバイル375x812

出力: catalog_scripts\\v8_4_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_4.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
⚠カメラは必ず部屋ポリゴンの内側に置くこと
"""
import json
import os
import shutil
import sys

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/room.html?debug=1"
HERE = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   u'野沢用', 'claude', 'nozaROOM', u'確認用切り出し')

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
        pg.add_style_tag(content="#vpHint{display:none !important;}")

        def mjs(code):
            return pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + code + "})()") + ")")

        def shot(tag):
            path = os.path.join(HERE, "v8_4_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-28s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))
            return path

        def cam(px, py, pz, tx, ty, tz, wait=1100):
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, tx, ty, tz))
            pg.wait_for_timeout(wait)

        # ══════════════ ① データ ══════════════
        print(u'\n■ ① ROOM_DATA / CATALOG_SEED')
        meta = mjs("return {v: R.meta.version, nf: R.fixtures.length, no: R.openings.length,"
                   " cs: CATALOG_SEED.version, n: CATALOG_SEED.items.length};")
        chk(meta['v'] == '6.11', u'ROOM_DATA v6.11', meta['v'])
        # F-16 はリタイア済み ID (欠番) なので 件数は 最大番号 -1
        chk(meta['nf'] == 54, u'fixtures 54件 (53 + 空気口 F-55 / F-16 は欠番)', meta['nf'])
        chk(meta['no'] == 19, u'openings 19件 (増減なし)', meta['no'])
        chk(meta['cs'] == '2.9' and meta['n'] == 35, u'CATALOG_SEED v2.9 / 35商品 (不変)',
            '%s / %s' % (meta['cs'], meta['n']))

        g = mjs("var f=function(i){return (R.fixtures.concat(R.openings)).filter("
                "function(e){return e.id===i;})[0];};"
                "return {w6:f('WIN-06'), w7:f('WIN-07'), f51:f('F-51'), f24:f('F-24'),"
                " f55:f('F-55'), f01:f('F-01'), f02:f('F-02'),"
                " d02:f('D-02'), d04:f('D-04'), d11:f('D-11')};")

        print(u'\n■ ② 洋室6.2帖 高所小窓 (実測が正)')
        for k, y0 in (('w6', 196.0), ('w7', 257.0)):
            o = g[k]
            chk(o['sillH'] == 152.0 and o['height'] == 49.0,
                u'%s 床上152.0〜201.0 (高さ49.0)' % o['id'],
                u'sill%s h%s' % (o['sillH'], o['height']))
            chk(abs(o['wallFrom'][1] - y0) < 0.01, u'%s y=%.1f' % (o['id'], y0), o['wallFrom'][1])
        gap = g['w7']['wallFrom'][1] - g['w6']['wallTo'][1]
        chk(abs(gap - 17.0) < 0.01, u'2窓の離隔 17.0 (実測)', gap)
        chain = [g['w6']['wallFrom'][1] - 107.0,
                 g['w6']['wallTo'][1] - g['w6']['wallFrom'][1], gap,
                 g['w7']['wallTo'][1] - g['w7']['wallFrom'][1], 418.0 - g['w7']['wallTo'][1]]
        chk(abs(sum(chain) - 311.0) < 0.01,
            u'東壁チェーン 311 = %s' % ' + '.join('%.1f' % c for c in chain), sum(chain))
        chk(abs(chain[0] - 89.0) < 0.01 and abs(chain[4] - 117.0) < 0.01,
            u'  入隅→小窓1 = 89.0 (実測) / 小窓2→入隅 = 117.0 (差の吸収先)',
            '%.1f / %.1f' % (chain[0], chain[4]))

        print(u'\n■ ③ カーテンレール F-51 / 空気口 F-55')
        chk(g['f51']['bottomH'] == 208.8 and g['f51']['rect'][1] == 183.5,
            u'F-51 下端208.8 (中心210.0 = 天井から30) / y183.5', g['f51']['rect'])
        chk(g['f55']['rect'] == [1051.0, 375.0, 4.0, 21.0]
            and g['f55']['bottomH'] == 24.0 and g['f55']['h'] == 45.0,
            u'F-55 東壁 x1051〜1055 / y375〜396 / 床上24〜45 (21×21)', g['f55']['rect'])
        chk(g['f55']['type'] == 'vent', u'F-55 は 4.8帖 F-22 と同じ type=vent (専用実装なし)',
            g['f55']['type'])
        chk(abs((418.0 - g['f55']['rect'][1]) - 43.0) < 0.01,
            u'WIC側の壁面 y418 → 空気口の北(左)端 = 43.0 (実測)', 418.0 - g['f55']['rect'][1])

        print(u'\n■ ④ LDK 左収納 F-24 (実測 横65 × 奥行66)')
        chk(g['f24']['rect'] == [103.0, 283.5, 65.0, 66.0],
            u'F-24 幅(x)65.0 × 奥行(y)66.0', g['f24']['rect'])
        chk(abs((364.0 - (103.0 + 65.0)) + 65.0 - 261.0) < 0.01,
            u'LDK北壁チェーン 261 = 収納65.0 + 壁196.0 (実測204 とは -9 の差 / 報告済み)')
        chk(abs(66.0 + (385.0 - (283.5 + 66.0)) + 165.0 + 3.5 - 270.0) < 0.01,
            u'LDK西壁チェーン 270 = 収納66.0 + 壁35.5 + 窓165 + 3.5 (窓は動かしていない)')
        win2 = mjs("return R.openings.filter(function(o){return o.id==='WIN-02';})[0];")
        chk(win2['wallFrom'][1] == 385.0 and win2['wallTo'][1] == 550.0,
            u'WIN-02 掃き出し窓は y385〜550 のまま (対象外は不動)', win2['wallFrom'])

        print(u'\n■ ⑤ 汎用機構 install.doorFront (4室 + キッチンが同じ1フィールド)')
        for k, cm in (('d02', 36.0), ('d04', 35.0), ('d11', 32.0), ('f24', 38.0), ('f01', 26.5)):
            e = g[k]
            chk(e.get('install', {}).get('doorFront') == cm,
                u'%s install.doorFront = %s' % (e['id'], cm), e.get('install'))
        chk(g['f01']['install']['openKind'] == 'drawer',
            u'F-01 だけ openKind=drawer (表示が「引き出しの開放」になる)')
        # ツールチップに 同じ1行として出るか (建具側 / 設備側 の両方)
        for eid, word in (('D-02', u'扉の開放'), ('D-04', u'扉の開放'), ('D-11', u'扉の開放'),
                          ('F-24', u'扉の開放'), ('F-01', u'引き出しの開放')):
            rows = mjs("var t=__noza.tip(%s); return t ? t.rows.join(' | ') : '';" % json.dumps(eid))
            chk(word in (rows or ''), u'%s のツールチップに「%s」行が出る' % (eid, word),
                [r for r in (rows or '').split(' | ') if u'開放' in r])
        # キッチン引き出しの張り出しが data 駆動になっているか
        kd = mjs("return Object.keys(drawers).filter(function(k){"
                 "return /キッチン/.test(drawers[k].label);}).map(function(k){"
                 "return {label: drawers[k].label, depth: drawers[k].depth};});")
        chk(len(kd) == 4 and all(abs(d['depth'] - 26.5) < 0.01 for d in kd),
            u'キッチン引き出し4杯の depth が install.doorFront (26.5) から来ている',
            [(d['label'], d['depth']) for d in kd])

        # ══════════════ ⑥ スクショ ══════════════
        print(u'\n■ ⑥ スクショ')
        doors = mjs("return __noza.doors().map(function(d){return d.id||d.label;});")
        print(u'   doors: %s' % doors)

        # (a) 洋室4.5 クローゼット D-02 を開く  (部屋 x103..354 / y18..273.5)
        mjs("switchRoom('west4_5'); return 1;")
        pg.wait_for_timeout(500)
        mjs("__noza.doors().forEach(function(d){ if(/4.5→クローゼット/.test(d.label||''))"
            " __noza.door(d.id); }); return 1;")
        pg.wait_for_timeout(700)
        cam(150, 165, 245, 352, 110, 100, 1300)
        shot('01_cl_r45_open')

        # (b) 洋室4.8 クローゼット D-04 を開く  (部屋 x103..414.5 / y563.5..819.5)
        mjs("switchRoom('west48'); return 1;") if False else None
        mjs("switchRoom('west4_8'); return 1;")
        pg.wait_for_timeout(500)
        mjs("__noza.doors().forEach(function(d){ if(/4.8→クローゼット/.test(d.label||''))"
            " __noza.door(d.id); }); return 1;")
        pg.wait_for_timeout(700)
        cam(400, 170, 615, 162, 110, 735, 1300)
        shot('02_cl_r48_open')

        # (c) 6.2帖 WIC 扉 D-11 を開く  (部屋 x800..1055 / y107..418)
        mjs("switchRoom('east62'); return 1;")
        pg.wait_for_timeout(500)
        mjs("__noza.doors().forEach(function(d){ if(/WIC/.test(d.label||''))"
            " __noza.door(d.id); }); return 1;")
        pg.wait_for_timeout(700)
        cam(858, 175, 175, 985, 100, 420, 1300)
        shot('03_cl_wic_open')

        # (d) LDK 左収納 F-24 (扉は建具として未モデル化 = 本体と 65×66 の見付けを確認)
        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(500)
        cam(620, 195, 505, 150, 110, 320, 1400)
        shot('04_ldk_f24')
        # 65×66 の見付け・奥行は 真上ビューが いちばん確認しやすい (カメラは部屋の上空)
        mjs("__noza.fov(34); return 1;")
        cam(205, 620, 350, 200, 0, 345, 1500)
        shot('04b_ldk_f24_top')
        mjs("__noza.fov(55); return 1;")

        # (e) 6.2帖 小窓 + 空気口 (東壁 x1055 を室内から見る)
        mjs("switchRoom('east62'); return 1;")
        pg.wait_for_timeout(500)
        # ⚠WIC扉 (D-11) を開けたままだと 90°振れた戸が 東壁の空気口の前に立ち塞がる → 閉じてから撮る
        mjs("__noza.doors().forEach(function(d){ if(/WIC/.test(d.label||'') && d.open)"
            " __noza.door(d.id); }); return 1;")
        pg.wait_for_timeout(700)
        cam(828, 105, 330, 1053, 178, 249, 1400)
        shot('05_r62_small_windows')
        cam(900, 60, 386, 1053, 34, 386, 1400)       # 東壁に正対 (空気口の真正面)
        shot('06_r62_vent')
        cam(862, 125, 300, 1053, 55, 390, 1400)      # 床・入隅ごと入れた引き
        shot('06b_r62_vent_wide')

        # (f) キッチン コンロ引き出しを開ける (北列 = コンロ側)
        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(500)
        opened = mjs("var r=[]; Object.keys(drawers).forEach(function(k){"
                     " if(/キッチン引き出し 北列/.test(drawers[k].label)){ toggleDrawer(k);"
                     " r.push({label: drawers[k].label, open: drawers[k].open, remain: drawers[k].remain}); }});"
                     " return r;")
        print(u'   コンロ側 (北列) を開いた: %s' % opened)
        chk(len(opened) == 2 and all(o['open'] for o in opened),
            u'コンロ側 (北列) の引き出し2杯が開く', opened)
        rem = [o['remain'] for o in opened if o['remain'] is not None]
        chk(bool(rem) and all(abs(r - 117) <= 2 for r in rem),
            u'開いた引き出しの先端 → 逆の壁 (LDK東壁) の残りが 実測117 と一致', rem)
        pg.wait_for_timeout(700)
        cam(752, 125, 340, 664, 62, 253, 1400)
        shot('07_kitchen_drawer_open')
        cam(730, 205, 430, 668, 55, 262, 1400)
        shot('07b_kitchen_drawer_open_high')

        # (g) モバイル 375x812
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        mjs("switchRoom('east62'); return 1;")
        pg.wait_for_timeout(500)
        # 真上ビューだと 床だけの絵になるので、 今回の主題 (東壁の小窓2つ + 空気口) を室内から見る
        mjs("__noza.fov(58); return 1;")
        cam(818, 120, 292, 1053, 112, 292, 1600)
        shot('08_mobile_375x812')
        mjs("__noza.fov(55); return 1;")
        pg.set_viewport_size({"width": 1280, "height": 940})

        br.close()

    if errs:
        print(u'\n⚠ console error:')
        for e in errs[:10]:
            print(u'   ' + e)
        fails.append(u'console error')

    if os.path.isdir(BOX):
        for s in shots:
            shutil.copy2(s, os.path.join(BOX, os.path.basename(s)))
        print(u'\n  Box へコピー: %s (%d枚)' % (BOX, len(shots)))
    else:
        print(u'\n  ⚠ Box フォルダが見つからない: %s' % BOX)

    print(u'\n════ 結果: FAIL %d 件 / スクショ %d 枚 ════' % (len(fails), len(shots)))
    for f in fails:
        print(u'   ✗ ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

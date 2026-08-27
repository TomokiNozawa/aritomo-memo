# -*- coding: utf-8 -*-
u"""★v8.5 検証 — 野沢さん 2026-08-24 回答4件の反映

  ① 機械検証: ROOM_DATA v6.12 / CATALOG_SEED 不変 / fold データ / F-24 の復帰 / 各チェーンの閉合
  ② 折れ戸の実挙動: 3室とも **閉=壁面上に一列 / 開=畳まれて側方へ寄る** を 3D の実座標で測り、
     「柱から戸先までの出」 が パネル1枚幅 (+建具厚) になっているかを 実測値と突合する
  ③ ツールチップ: 種類=折れ戸 / 「扉の開放: 柱(枠)の面から先端まで …(最大まで開いた状態)」 が
     建具・設備 どちらにも 同じ1行として出る (3室バラバラの実装になっていない)
  ④ スクショ: 3室の折れ戸 (閉/最大開) / LDK F-24 の片開き / 6.2帖のWICまわり / モバイル375x812

出力: catalog_scripts\\v8_5_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_5.py
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
            path = os.path.join(HERE, "v8_5_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-28s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))
            return path

        def cam(px, py, pz, tx, ty, tz, wait=1100):
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, tx, ty, tz))
            pg.wait_for_timeout(wait)

        def door_id(pat):
            r = mjs("var a=__noza.doors().filter(function(d){return /%s/.test(d.label||'');});"
                    "return a.length ? a[0].id : null;" % pat)
            return r

        def bbox(did):
            return mjs("var d=doors[%s]; var b=new THREE.Box3();"
                       "d.parts.forEach(function(p){p.mesh.updateMatrixWorld(true); b.expandByObject(p.mesh);});"
                       "return {x0:b.min.x, x1:b.max.x, z0:b.min.z, z1:b.max.z, open:d.open};"
                       % json.dumps(did))

        # ══════════════ ① データ ══════════════
        print(u'\n■ ① ROOM_DATA / CATALOG_SEED')
        meta = mjs("return {v: R.meta.version, nf: R.fixtures.length, no: R.openings.length,"
                   " cs: CATALOG_SEED.version, n: CATALOG_SEED.items.length};")
        chk(meta['v'] == '6.12', u'ROOM_DATA v6.12', meta['v'])
        chk(meta['nf'] == 54 and meta['no'] == 19, u'fixtures 54 / openings 19 (増減なし)',
            '%s / %s' % (meta['nf'], meta['no']))
        chk(meta['cs'] == '2.9' and meta['n'] == 35, u'CATALOG_SEED v2.9 / 35商品 (不変)',
            '%s / %s' % (meta['cs'], meta['n']))

        g = mjs("var f=function(i){return (R.fixtures.concat(R.openings)).filter("
                "function(e){return e.id===i;})[0];};"
                "return {d02:f('D-02'), d04:f('D-04'), d11:f('D-11'), f24:f('F-24'), f01:f('F-01'),"
                " f55:f('F-55'), win02:f('WIN-02')};")

        print(u'\n■ ② 折れ戸 (3室共通の fold データ / F-24 は片開きのまま)')
        for k, sets, panels, hinge in (('d02', 2, 2, 'outer'), ('d04', 2, 2, 'outer'), ('d11', 1, 2, 'e')):
            fo = g[k].get('fold')
            chk(bool(fo) and fo['sets'] == sets and fo['panels'] == panels and fo['hinge'] == hinge,
                u'%s fold = %d枚折れ×%d組 / 吊元 %s' % (g[k]['id'], panels, sets, hinge), fo)
        chk('leaves' not in g['d04'], u'D-04 の旧 leaves:4 は削除 (二重の真実を残さない)',
            g['d04'].get('leaves'))
        chk(not g['f24'].get('fold'), u'F-24 (LDK) は折れ戸にしない = 片開き1枚のまま', g['f24'].get('fold'))

        print(u'\n■ ③ F-24 を v8.4 以前へ戻す')
        chk(g['f24']['rect'] == [103.0, 283.5, 57.0, 70.5],
            u'F-24 rect = [103, 283.5, 57.0, 70.5] (奥行57 × 幅70.5)', g['f24']['rect'])
        chk(g['f24']['est'] is True, u'F-24 est を true へ戻す', g['f24']['est'])
        chk(g['f24']['install']['doorFront'] == 38.0, u'F-24 install.doorFront = 38 は維持',
            g['f24']['install'])
        e_face, s_face = 103.0 + 57.0, 283.5 + 70.5
        chk(abs((364.0 - e_face) - 204.0) < 0.01,
            u'LDK北壁 実測204 が再び閉じる (収納東面 x160 → 北壁内隅 x364)', 364.0 - e_face)
        chk(abs((553.5 - s_face) - 199.5) < 0.01,
            u'LDK南壁 実測199.5 が再び閉じる (収納南面 y354 → 南壁 y553.5)', 553.5 - s_face)
        chk(abs(57.0 + (364.0 - e_face) - 261.0) < 0.01,
            u'北壁チェーン 261 = 収納57 + 204', 57.0 + (364.0 - e_face))
        chk(abs(70.5 + (385.0 - s_face) + 165.0 + 3.5 - 270.0) < 0.01,
            u'西壁チェーン 270 = 収納70.5 + 壁31 + 窓165 + 3.5', 70.5 + (385.0 - s_face) + 165.0 + 3.5)
        chk(g['win02']['wallFrom'][1] == 385.0 and g['win02']['wallTo'][1] == 550.0,
            u'WIN-02 は y385〜550 のまま (対象外は不動)', g['win02']['wallFrom'])

        print(u'\n■ ④ 空気口の壁 → WIC の壁 44 (終点 = 壁)')
        chk(g['d11']['wallTo'][0] == 1011.0 and g['d11']['wallFrom'][0] == 953.0,
            u'D-11 開口 x953〜1011 (東端だけ 2cm 西へ)', [g['d11']['wallFrom'], g['d11']['wallTo']])
        chk(g['d11']['width'] == 58, u'D-11 幅 60 → 58 (ラベルの「間取り図実測≈58」と一致)',
            g['d11']['width'])
        w = mjs("var o={}; R.walls.forEach(function(w){o[w.id]=Math.round(w.length*10)/10;}); return o;")
        chk(abs(w['W-R62-S3'] - 44.0) < 0.01, u'W-R62-S3 (東壁→WICの壁) = 44.0 (実測)', w['W-R62-S3'])
        chk(abs(w['W-WIC-N2'] - 44.0) < 0.01, u'W-WIC-N2 も 44.0 (同じ壁)', w['W-WIC-N2'])
        chk(abs(w['W-R62-S2'] - 81.0) < 0.01, u'W-R62-S2 は 81.0 のまま (西端は動かしていない)',
            w['W-R62-S2'])
        chk(abs(w['W-R62-S2'] + 58.0 + w['W-R62-S3'] - 183.0) < 0.01,
            u'6.2帖 南壁チェーン 183 = 81 + 58 + 44')
        e1, e2, e3 = w['W-R62-E1'], w['W-R62-E2'], w['W-R62-E3']
        chk(abs(e1 + 44.0 + e2 + 44.0 + e3 - 311.0) < 0.01,
            u'東壁チェーン 311 = 89 + 44 + 17 + 44 + 117 が不変 (44cm 反映で壊れていない)',
            '%.1f + 44 + %.1f + 44 + %.1f' % (e1, e2, e3))
        chk(g['f55']['rect'] == [1051.0, 375.0, 4.0, 21.0], u'空気口 F-55 は不動', g['f55']['rect'])

        # ══════════════ ⑤ 折れ戸の実挙動 (3D の実座標) ══════════════
        print(u'\n■ ⑤ 折れ戸の畳み込み (3D 実測) — 柱面からの出 ≒ パネル1枚の幅')
        # (面, 開く向き, 実測はみ出し, 開口幅, 総枚数)
        SPEC = [(u'4.5帖 D-02', u'4.5→クローゼット', 'x', 354.0, -1, 36.0, 145.0, 4),
                (u'4.8帖 D-04', u'4.8→クローゼット', 'x', 160.5, +1, 35.0, 160.0, 4),
                (u'WIC D-11', u'WIC', 'z', 426.0, -1, 32.0, 58.0, 2)]
        geom = []
        for name, pat, ax, face, sgn, meas, span, n in SPEC:
            did = door_id(pat)
            b0 = bbox(did)
            out0 = (b0['x1'] - face) if (ax == 'x' and sgn > 0) else \
                   (face - b0['x0']) if ax == 'x' else \
                   (b0['z1'] - face) if sgn > 0 else (face - b0['z0'])
            mjs("__noza.door(%s); return 1;" % json.dumps(did))
            pg.wait_for_timeout(300)
            b1 = bbox(did)
            out1 = (b1['x1'] - face) if (ax == 'x' and sgn > 0) else \
                   (face - b1['x0']) if ax == 'x' else \
                   (b1['z1'] - face) if sgn > 0 else (face - b1['z0'])
            pw = span / n
            geom.append((name, out0, out1, pw, meas))
            # 閉: 部屋側の壁面から出るのは 「建具パネルの面が壁心にある ぶん (±2.5)」 + 「取っ手の出 (3.5)」
            #     = 高々 7cm。 これは v8.5 以前からの描画の約束事 (パネルは壁心 wc に置く) で折れ戸とは無関係。
            chk(out0 < 7.0, u'%s 閉: 壁面から %.1fcm (取っ手+パネル面の壁心オフセットのみ・一列に収まる)'
                % (name, out0), out0)
            # 開: 畳まれて側方へ寄るので 出 ≒ パネル1枚幅 (±2.5 = 上のパネル面オフセット)
            chk(abs(out1 - pw) <= 3.5,
                u'%s 開: 壁面から %.1fcm ≒ パネル1枚 %.2fcm (折れ戸として畳まれている)' % (name, out1, pw),
                out1)
            chk(out1 - out0 > pw * 0.7,
                u'%s 開いた時に 閉より %.1fcm 手前へ出る (90°回転の開き戸ではなく畳み込み)' % (name, out1 - out0))
            mjs("__noza.door(%s); return 1;" % json.dumps(did))     # 閉じ直す
            pg.wait_for_timeout(200)
        print(u'\n  ── 実測との突合 (捏ねずに差を出す) ──')
        for name, out0, out1, pw, meas in geom:
            d = out1 - meas
            print(u'   %-12s 幾何(パネル1枚)=%5.2f / 3D実測=%5.2f / 野沢さん実測=%4.1f → 差 %+.2f cm%s'
                  % (name, pw, out1, meas, d, u'  ⚠要確認' if abs(d) > 2.5 else u''))

        # ══════════════ ⑥ ツールチップ ══════════════
        print(u'\n■ ⑥ ツールチップ (同じ1行を 建具・設備が共有)')
        tips = {}
        for eid in ('D-02', 'D-04', 'D-11', 'F-24', 'F-01'):
            tips[eid] = mjs("var t=__noza.tip(%s); return t ? t.rows : [];" % json.dumps(eid))
        for eid in ('D-02', 'D-04', 'D-11'):
            row = [r for r in tips[eid] if u'種類' in r]
            chk(bool(row) and u'折れ戸' in row[0], u'%s の種類が「折れ戸」' % eid, row)
        row = [r for r in tips['D-11'] if u'種類' in r]
        chk(bool(row) and u'2枚折れ' in row[0] and u'=2枚' in row[0],
            u'D-11 は 2枚折れ×1組 = 2枚 と出る', row)
        for eid, word in (('D-02', u'扉の開放'), ('D-04', u'扉の開放'), ('D-11', u'扉の開放'),
                          ('F-24', u'扉の開放'), ('F-01', u'引き出しの開放')):
            row = [r for r in tips[eid] if u'の開放' in r]
            ok = bool(row) and word in row[0] and u'先端まで' in row[0] and u'最大まで開いた状態' in row[0]
            chk(ok, u'%s に「%s: …から先端まで N cm (最大まで開いた状態)」 が出る' % (eid, word), row)
        for eid in ('D-02', 'D-04', 'D-11', 'F-24'):
            row = [r for r in tips[eid] if u'の開放' in r]
            chk(bool(row) and u'柱(枠)の面から' in row[0], u'%s の起点が「柱(枠)の面」' % eid, row)
        row = [r for r in tips['F-01'] if u'の開放' in r]
        chk(bool(row) and u'本体前面 (カウンター東面)から' in row[0],
            u'F-01 の起点は「本体前面 (カウンター東面)」 (要素ごとの起点をデータで持つ)', row)

        # ══════════════ ⑦ スクショ ══════════════
        print(u'\n■ ⑦ スクショ')

        def open_door(pat):
            mjs("__noza.doors().forEach(function(d){ if(/%s/.test(d.label||'') && !d.open)"
                " __noza.door(d.id); }); return 1;" % pat)
            pg.wait_for_timeout(600)

        def close_door(pat):
            mjs("__noza.doors().forEach(function(d){ if(/%s/.test(d.label||'') && d.open)"
                " __noza.door(d.id); }); return 1;" % pat)
            pg.wait_for_timeout(600)

        # (a) 洋室4.5 D-02  (部屋 x103..354 / y18..273.5)
        mjs("switchRoom('west4_5'); return 1;")
        pg.wait_for_timeout(500)
        close_door(u'4.5→クローゼット')
        cam(150, 165, 245, 352, 110, 100, 1300)
        shot('01_fold_r45_closed')
        open_door(u'4.5→クローゼット')
        cam(150, 165, 245, 352, 110, 100, 1300)
        shot('02_fold_r45_open')
        # 畳まれ方 (2組が両端で側方へ寄る) が いちばん分かるのは 部屋の内側から見た 広角の俯瞰
        mjs("__noza.fov(72); return 1;")
        cam(150, 300, 240, 330, 60, 100, 1400)
        shot('02b_fold_r45_open_wide')
        mjs("__noza.fov(55); return 1;")
        close_door(u'4.5→クローゼット')

        # (b) 洋室4.8 D-04  (部屋 x103..414.5 / y563.5..819.5)
        mjs("switchRoom('west4_8'); return 1;")
        pg.wait_for_timeout(500)
        cam(400, 170, 615, 162, 110, 735, 1300)
        shot('03_fold_r48_closed')
        open_door(u'4.8→クローゼット')
        cam(400, 170, 615, 162, 110, 735, 1300)
        shot('04_fold_r48_open')
        mjs("__noza.fov(72); return 1;")
        cam(390, 300, 620, 160, 60, 740, 1400)
        shot('04b_fold_r48_open_wide')
        mjs("__noza.fov(55); return 1;")
        close_door(u'4.8→クローゼット')

        # (c) 6.2帖 WIC D-11  (部屋 x800..1055 / y107..418)
        mjs("switchRoom('east62'); return 1;")
        pg.wait_for_timeout(500)
        cam(858, 175, 175, 985, 100, 420, 1300)
        shot('05_fold_wic_closed')
        open_door('WIC')
        cam(858, 175, 175, 985, 100, 420, 1300)
        shot('06_fold_wic_open')
        mjs("__noza.fov(72); return 1;")
        cam(850, 300, 180, 1000, 60, 420, 1400)
        shot('06b_fold_wic_open_wide')
        mjs("__noza.fov(55); return 1;")
        close_door('WIC')
        # WIC まわり (東壁の空気口 → WICの壁 44 の位置関係)
        cam(880, 130, 250, 1040, 60, 415, 1400)
        shot('07_r62_wic_wall44')

        # (d) LDK 左収納 F-24 (57×70.5 に戻した見付け・片開きのまま)
        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(500)
        mjs("__noza.fov(72); return 1;")
        cam(430, 300, 500, 140, 40, 320, 1400)
        shot('08_ldk_f24')
        mjs("__noza.fov(50); return 1;")                  # 57×70.5 の footprint は 真上ビューで見る
        cam(260, 540, 430, 170, 0, 330, 1500)
        shot('08b_ldk_f24_top')
        mjs("__noza.fov(55); return 1;")

        # (e) モバイル 375x812 (折れ戸を開けた 4.5帖)
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        mjs("switchRoom('west4_5'); return 1;")
        pg.wait_for_timeout(500)
        open_door(u'4.5→クローゼット')
        mjs("__noza.fov(78); return 1;")
        cam(150, 300, 240, 330, 60, 100, 1600)
        shot('09_mobile_375x812')
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

# -*- coding: utf-8 -*-
u"""v8.10 の検証: モニターアームの リーチ/スイング + モニター2機種の実寸 を 実機ブラウザで機械照合する。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_10.py [--no-shot]

前提: python -m http.server 8777 が ~/aritomo-memo で稼働 (NOZA_URL 環境変数で差し替え可)
見るもの:
  ① ページエラー 0
  ② 回帰: armReach=null の armPose() が **v8.9 (git HEAD) の armPose と bit 単位で同じ** (vesaH 2〜35 を 0.5 刻み)
  ③ 4.8帖に デスク80 + アーム + MSI/BenQ を置き、 リーチ 最小/既定/最大 で 取付点の水平距離 = リーチ、
     マウント中モニターが取付点に追従、 届かない値のクランプ、 高さ変更でリーチが保たれる
  ④ 2アーム×2モニター (両方追従) / スイング ±90 で モニターの rotY が追従 / 干渉警告 (壁へ伸ばす)
  ⑤ モニター寸法: 床置き bbox = 公式スタンド込み、 マウント時 bbox = 公式パネルのみ (MSI 奥行 12.0 / BenQ 6.4)
  ⑥ デスク幅との比 (MSI 80.9 / デスク 80・90)
  ⑦ 回帰: TVスタンド×TV マウント (standh / 追従) が従来どおり
  ⑧ スクショ: catalog_scripts/v8_10_check_*.png (デスクトップ + モバイル 375×812)
"""
import json
import os
import re
import subprocess
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
URL = os.environ.get('NOZA_URL', "http://127.0.0.1:8777/room.html") + "?debug=1"
NG = []
SHOT = '--no-shot' not in sys.argv


def ck(cond, msg):
    print((u'  [OK ] ' if cond else u'  [NG ] ') + msg)
    if not cond:
        NG.append(msg)


def old_armpose_src():
    u"""git HEAD (= v8.9) の room.html から armPose 関数のソースを抜く (回帰の比較用)"""
    src = subprocess.check_output(['git', 'show', 'HEAD:room.html'], cwd=REPO).decode('utf-8')
    a = src.index('function armPose(it) {')
    b = src.index('\n}\n', a) + 3
    return src[a:b]


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

        def shot(name):
            if not SHOT:
                return
            pg.wait_for_timeout(500)
            path = os.path.join(HERE, 'v8_10_check_%s.png' % name)
            pg.screenshot(path=path)
            print(u'      📷 %s' % os.path.basename(path))

        # ── ② armPose 回帰 (v8.9 の関数を armPoseOld として注入し 全キー === 比較) ──
        old = old_armpose_src()
        assert 'armReachRaw' not in old, u'git HEAD が既に v8.10 (回帰比較の基準にならない)'
        mjs("window.__armPoseOld = " + old.replace('function armPose(it)', 'function (it)', 1) + "; return 1;")
        reg = mjs("""
          var bad = [], n = 0;
          for (var T = 2; T <= 35.0001; T += 0.5) {
            var o = window.__armPoseOld({vesaH: T}), q = armPose({vesaH: T}); n++;
            Object.keys(o).forEach(function (k) { if (o[k] !== q[k]) bad.push(T + ':' + k + ' ' + o[k] + ' vs ' + q[k]); });
            // 旧 armPose に無い新キーの整合: reach = sqrt(ax^2 + (az-poleZ)^2)
            var r2 = Math.sqrt(q.ax * q.ax + (q.az - q.poleZ) * (q.az - q.poleZ));
            if (Math.abs(r2 - q.reach) > 1e-9) bad.push(T + ':reach ' + q.reach + ' vs ' + r2);
          }
          return { n: n, bad: bad.slice(0, 8), nbad: bad.length };""")
        ck(reg['nbad'] == 0, u'② 回帰: armReach=null の armPose は v8.9 と全キー === (%d 高さ / 不一致 %d) %s'
           % (reg['n'], reg['nbad'], reg['bad']))

        # ── ③ 4.8帖 にセットアップ ──
        mjs("switchRoom('south48'); return 1;")
        pg.wait_for_timeout(400)
        cats = mjs("return __noza.catFull().map(function(c){return {id:c.id,name:c.name,type:c.type,w:c.w,d:c.d,h:c.h};});")
        by = {}
        for c in cats:
            if c['type'] in ('desk', 'monitor', 'monitorarm', 'tvstand', 'tv'):
                by.setdefault(c['type'], []).append(c)
        desk80 = [c for c in by['desk'] if c['w'] == 80][0]
        desk90 = [c for c in by['desk'] if c['w'] == 90][0]
        arm = by['monitorarm'][0]
        msi = [c for c in by['monitor'] if '342CQR' in c['name']][0]
        benq = [c for c in by['monitor'] if 'EX2710' in c['name']][0]
        ck(len(by['monitorarm']) == 1 and len(by['monitor']) == 2, u'③ カタログ: アーム1 / モニター2')

        def add(cid, x, z, rot=0):
            return mjs("var c=catalogData[%s]; var id=__noza.add({name:c.name,w:c.w,d:c.d,h:c.h,color:c.color,"
                       " type:c.type,specNote:c.specNote,catalogId:%s,x:%f,z:%f,rotY:%d,y:0});"
                       " return id;" % (json.dumps(cid), json.dumps(cid), x, z, rot))

        # 部屋 4.8帖 = x 103〜414.5 / z 563.5〜819.5 (ROOM_DATA poly)。 北壁の引き戸 (x103〜185) と
        # 南西のクローゼット (x103〜160.5 / z650.5〜) を避け、 デスク80 を x245・デスク90 を x360 に北壁から 12cm 離して置く
        dk = add(desk80['id'], 245, 610)
        dk2 = add(desk90['id'], 360, 610)
        # まず床置き (スタンドあり) のモニターをデスクの上に載せて撮る → ⑤ (bbox は公式スタンド込み)
        mo1 = add(msi['id'], 245, 760)
        mo2 = add(benq['id'], 360, 760)
        mjs("return __noza.drop(%s, 245, 612);" % json.dumps(mo1))
        mjs("return __noza.drop(%s, 360, 612);" % json.dumps(mo2))
        pg.wait_for_timeout(300)
        ys = dict((m['id'], m['y']) for m in mjs("return __noza.mounts();"))
        ck(abs(ys[mo1] - 70) < 0.6 and abs(ys[mo2] - 70) < 0.6, u'③ 床置きモニター2台がデスク天板 (70cm) に載った: %s' % ys)

        def bbox(iid):
            return mjs("var g=furnMeshes[%s]; g.updateMatrixWorld(); var bb=new THREE.Box3().setFromObject(g,true);"
                       " return {w:Math.round((bb.max.x-bb.min.x)*100)/100, d:Math.round((bb.max.z-bb.min.z)*100)/100,"
                       " h:Math.round((bb.max.y-bb.min.y)*100)/100, y0:Math.round(bb.min.y*100)/100, y1:Math.round(bb.max.y*100)/100};"
                       % json.dumps(iid))
        b1, b2 = bbox(mo1), bbox(mo2)
        print(u'      床置き bbox MSI %s / BenQ %s' % (b1, b2))
        ck(abs(b1['w'] - 80.9) < 0.3 and abs(b1['h'] - 51.4) < 0.3 and b1['d'] <= 27.01,
           u'⑤ MSI 床置き bbox ≈ 公式 W80.9×D≤27×H51.4 (実際 %s×%s×%s)' % (b1['w'], b1['d'], b1['h']))
        ck(abs(b2['w'] - 61.4) < 0.3 and abs(b2['h'] - 41.0) < 0.3 and b2['d'] <= 21.71,
           u'⑤ BenQ 床置き bbox ≈ 公式 W61.4×D≤21.7×H41.0 (実際 %s×%s×%s)' % (b2['w'], b2['d'], b2['h']))
        pd1 = mjs("return __noza.monDims(%s);" % json.dumps(mo1))
        pd2 = mjs("return __noza.monDims(%s);" % json.dumps(mo2))
        print(u'      monitorPanelDims MSI %s' % pd1)
        print(u'      monitorPanelDims BenQ %s' % pd2)
        ck(abs(pd1['depth'] - 12.0) < 0.05 and 3.5 < pd1['humpD'] < 5.0,
           u'⑤ MSI パネル奥行 12.0 (公式 119.67mm) = 縁 %.1f [est] + 矢高 + 背面の膨らみ %.2f' % (pd1['panT'], pd1['humpD']))
        ck(abs(pd1['scrW'] - 79.7) < 0.05 and abs(pd1['scrH'] - 33.4) < 0.05, u'⑤ MSI 表示領域 79.7×33.4 (公式 797.22×333.72)')
        ck(abs(pd2['scrW'] - 59.8) < 0.05 and abs(pd2['scrH'] - 33.6) < 0.05 and abs(pd2['scrW'] / pd2['scrH'] - 16 / 9.0) < 0.01,
           u'⑤ BenQ 表示領域 59.8×33.6 = 16:9 (計算値 est)')
        ck(abs(pd2['panT'] - 6.4) < 0.01 and abs(pd2['panH'] - 38.2) < 0.01, u'⑤ BenQ パネルのみ D6.4×H38.2 (公式)')
        # 家具シートの寸法欄 (床置き = 昇降レンジ)
        mjs("select(%s); return 1;" % json.dumps(mo2))
        pg.wait_for_timeout(300)
        sheet = pg.evaluate("document.getElementById('itemSheet') ? document.getElementById('itemSheet').innerText : document.body.innerText")
        ck(u'41〜54cm' in sheet and u'130mm' in sheet, u'④ BenQ 床置きの家具シートに「スタンド昇降: 高さ 41〜54cm (公式 130mm)」')
        mjs("select(%s); return 1;" % json.dumps(mo1))
        pg.wait_for_timeout(300)
        sheet = pg.evaluate("document.body.innerText")
        ck(u'51.4〜60.4cm' in sheet and u'90mm' in sheet, u'④ MSI 床置きの家具シートに「スタンド昇降: 高さ 51.4〜60.4cm (公式 90mm)」')
        ck(u'79.7×33.4cm' in sheet, u'④ MSI 家具シートに 表示領域 79.7×33.4cm')
        mjs("deselect(); return 1;")

        # カメラ: 部屋の内側 (南寄り) から北壁側のデスクを見る
        def cam(px, py, pz, tx, ty, tz):
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, tx, ty, tz))
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip,#drawerLabels{display:none !important;}")
        mjs("__noza.fov(60); return 1;")
        cam(300, 160, 805, 300, 85, 600)
        shot('00_floor_standing_two_monitors_on_desks')
        cam(140, 130, 640, 300, 85, 600)
        shot('00b_floor_standing_side_view')
        # モニターを床へ下ろしてから アームを置く (デスク上に立っていると アームの投入が AABB でブロックされる)
        mjs("return __noza.drop(%s, 245, 760);" % json.dumps(mo1))
        mjs("return __noza.drop(%s, 360, 760);" % json.dumps(mo2))
        armId = add(arm['id'], 245, 585)
        mjs("return __noza.drop(%s, 245, 585);" % json.dumps(armId))
        a0 = [a for a in mjs("return __noza.arms();") if a['mounted'] == 0][0]
        ck(abs(a0['y'] - 70) < 0.6, u'③ アームはデスク天板 (70cm) の上に載った: y=%s' % a0['y'])
        ck(a0['reachRaw'] is None and abs(a0['reach'] - 37.0) < 1.0,
           u'③ 既定 (armReach=null) のリーチ ≈ 37cm (折り畳み) / 実際 %s' % a0['reach'])

        # ── MSI をアームへマウント (実ドラッグ経路) ──
        ap = mjs("return __noza.arms()[0].attach;")
        mjs("return __noza.drop(%s, %f, %f);" % (json.dumps(mo1), ap['x'], ap['z']))
        pg.wait_for_timeout(300)
        mnt = [m for m in mjs("return __noza.mounts();") if m['id'] == mo1][0]
        ck(mnt['mounted'] and mnt['mountArm'] == armId, u'③ MSI をアームにマウントできた')
        arms = mjs("return __noza.arms();")[0]
        ck(abs(mnt['x'] - arms['attach']['x']) < 0.06 and abs(mnt['z'] - arms['attach']['z']) < 0.06 and abs(mnt['y'] - arms['attach']['y']) < 0.06,
           u'③ マウント中モニターの原点 = アーム取付点 (%s vs %s)' % ((mnt['x'], mnt['y'], mnt['z']), arms['attach']))
        bm = bbox(mo1)
        print(u'      マウント中 MSI bbox %s' % bm)
        ck(abs(bm['w'] - 80.9) < 0.3 and abs(bm['h'] - 36.4) < 0.3 and 12.0 - 0.1 <= bm['d'] <= 12.0 + 1.4,
           u'⑤ マウント中 MSI bbox ≈ パネルのみ W80.9×D12.0(+背面VESAプレート1・画面0.3)×H36.4 (実際 %s×%s×%s)' % (bm['w'], bm['d'], bm['h']))
        sheet = mjs("select(%s); return document.body.innerText;" % json.dumps(mo1))
        ck(u'パネルのみ: W80.9 × D12 × H36.4cm' in sheet, u'④ マウント中の家具シートに「パネルのみ: W80.9 × D12 × H36.4cm」')
        mjs("deselect(); return 1;")

        # ── リーチ 既定 → 最小 → 最大 → クランプ ──
        def pole_dist(a):
            u"""取付点 と ポール中心 の水平距離 (= リーチ)。 ポール中心はアーム原点から poleZ だけ後ろ"""
            pz = a['pose']['poleZ']
            ax, az = a['pose']['ax'], a['pose']['az'] - pz
            return (ax * ax + az * az) ** 0.5

        cam(245, 150, 805, 245, 80, 600)
        shot('01_reach_default_mounted_front')
        cam(135, 125, 645, 245, 88, 612)      # 西側から (リーチの前後差が見える 3/4 ビュー。 x<160.5・z>650.5 はクローゼットの中なので避ける)
        shot('01b_reach_default_side')
        r_min = mjs("return __noza.reach(%s, 36);" % json.dumps(armId))
        ck(abs(r_min['reach'] - 36) < 0.05 and abs(pole_dist(r_min) - 36) < 0.05, u'③ リーチ 36 (最小) → 取付点の水平距離 %.2f' % pole_dist(r_min))
        ck(abs(r_min['pose']['ax']) < 1e-6, u'③ IK: 手首はポール軸の真正面 (ax=%.2e)' % r_min['pose']['ax'])
        m1 = [m for m in mjs("return __noza.mounts();") if m['id'] == mo1][0]
        ck(abs(m1['x'] - r_min['attach']['x']) < 0.06 and abs(m1['z'] - r_min['attach']['z']) < 0.06, u'③ 最小リーチでモニターが追従')
        shot('02_reach_min_36_side')
        r_max = mjs("return __noza.reach(%s, 99);" % json.dumps(armId))
        rmx = mjs("return __noza.arms()[0].reachMax;")
        ck(r_max['reach'] <= rmx + 0.01 and r_max['reach'] >= rmx - 0.5 and r_max['reach'] < 65.01,
           u'③ リーチ 99 → この高さの最大 %.1f にクランプ (65 以下)' % r_max['reach'])
        ck(abs(pole_dist(r_max) - r_max['reach']) < 0.05, u'③ 最大リーチでも 取付点の水平距離 = リーチ')
        m1 = [m for m in mjs("return __noza.mounts();") if m['id'] == mo1][0]
        ck(abs(m1['x'] - r_max['attach']['x']) < 0.06 and abs(m1['z'] - r_max['attach']['z']) < 0.06, u'③ 最大リーチでモニターが追従')
        shot('03_reach_max_side')
        r_lo = mjs("return __noza.reach(%s, 10);" % json.dumps(armId))
        ck(abs(r_lo['reach'] - 36) < 0.05, u'③ リーチ 10 → 下限 36 にクランプ')
        # 高さ変更でもリーチ保持 (明示値 50)
        mjs("return __noza.reach(%s, 50);" % json.dumps(armId))
        v1 = mjs("return __noza.vesa(%s, 34);" % json.dumps(armId))
        a_hi = mjs("return __noza.arms()[0];")
        ck(abs(a_hi['reach'] - 50) < 0.05 and abs(a_hi['vesaH'] - 34) < 0.01,
           u'③ VESA高さ 34 に変更してもリーチ 50 を保持 (実際 reach=%s vesaH=%s)' % (a_hi['reach'], a_hi['vesaH']))
        m1 = [m for m in mjs("return __noza.mounts();") if m['id'] == mo1][0]
        ck(abs(m1['y'] - a_hi['attach']['y']) < 0.06 and abs(m1['z'] - a_hi['attach']['z']) < 0.06, u'③ 高さ変更でもモニターが追従')
        # 高さを上げると最大が縮む (実機どおり)
        mx_hi = mjs("return __noza.arms()[0].reachMax;")
        ck(mx_hi < rmx, u'③ VESA高さ 24→34 で 最大リーチ %.1f → %.1f に縮む (第1アームの仰角)' % (rmx, mx_hi))
        shot('04_reach50_vesa34_side')
        mjs("return __noza.vesa(%s, 24);" % json.dumps(armId))
        # 最大リーチ時は 65 ちょうど (第1アーム水平) になる高さがある = 65 に届く高さを探す
        best = mjs("""var b=0; for (var T=2; T<=35; T+=0.5) { var q=armPose({vesaH:T}); if (q.reachMax>b) b=q.reachMax; } return b;""")
        ck(abs(best - 65.0) < 0.6, u'③ 第1アームが水平になる高さでは 最大リーチ ≈ 65.0 (公式 650mm) / 実際 %.2f' % best)
        # 既定に戻す
        r_def = mjs("return __noza.reach(%s, null);" % json.dumps(armId))
        ck(r_def['reachRaw'] is None and abs(r_def['reach'] - a0['reach']) < 0.05, u'③ 既定に戻すと reach=%s (最初と同じ)' % r_def['reach'])

        # ── ④ 2アーム × 2モニター ──
        arm2 = add(arm['id'], 360, 585)
        mjs("return __noza.drop(%s, 360, 585);" % json.dumps(arm2))
        a2y = [a for a in mjs("return __noza.arms();") if a['id'] == arm2][0]['y']
        ck(abs(a2y - 70) < 0.6, u'④ 2台目のアームも デスク90 の天板 (70cm) の上: y=%s' % a2y)
        pg.wait_for_timeout(200)
        ap2 = [a for a in mjs("return __noza.arms();") if a['id'] == arm2][0]['attach']
        mjs("return __noza.drop(%s, %f, %f);" % (json.dumps(mo2), ap2['x'], ap2['z']))
        pg.wait_for_timeout(300)
        ms = dict((m['id'], m) for m in mjs("return __noza.mounts();"))
        ck(ms[mo1]['mounted'] and ms[mo1]['mountArm'] == armId and ms[mo2]['mounted'] and ms[mo2]['mountArm'] == arm2,
           u'④ 2アームに MSI / BenQ をそれぞれマウント')
        mjs("return __noza.reach(%s, 45);" % json.dumps(armId))
        mjs("return __noza.reach(%s, 55);" % json.dumps(arm2))
        arms = dict((a['id'], a) for a in mjs("return __noza.arms();"))
        ms = dict((m['id'], m) for m in mjs("return __noza.mounts();"))
        ok2 = all(abs(ms[m]['x'] - arms[a]['attach']['x']) < 0.06 and abs(ms[m]['z'] - arms[a]['attach']['z']) < 0.06
                  for m, a in ((mo1, armId), (mo2, arm2)))
        ck(ok2 and abs(arms[armId]['reach'] - 45) < 0.05 and abs(arms[arm2]['reach'] - 55) < 0.05,
           u'④ アーム1=45 / アーム2=55 で 両モニターがそれぞれ追従')
        b1m, b2m = bbox(mo1), bbox(mo2)
        ck(abs(b2m['w'] - 61.4) < 0.3 and abs(b2m['h'] - 38.2) < 0.3 and 6.4 - 0.1 <= b2m['d'] <= 6.4 + 1.4,
           u'⑤ マウント中 BenQ bbox ≈ パネルのみ W61.4×D6.4(+背面VESAプレート1・画面0.3)×H38.2 (実際 %s×%s×%s)' % (b2m['w'], b2m['d'], b2m['h']))
        cam(300, 150, 805, 300, 82, 600)
        shot('05_two_arms_two_monitors')
        cam(140, 130, 640, 300, 88, 600)
        shot('06_two_arms_side_view')

        # ── ④ スイング ──
        sw = mjs("return __noza.swing(%s, 30);" % json.dumps(arm2))
        ms = dict((m['id'], m) for m in mjs("return __noza.mounts();"))
        ck(sw['swing'] == 30 and abs(((ms[mo2]['rotY'] - sw['attach']['rotY']) % 360)) < 0.01 and abs((sw['attach']['rotY'] - 330) % 360) < 0.01,
           u'④ スイング +30° → 取付点 rotY=%s / モニター rotY=%s (アーム rotY 0 − 30 = 330)' % (sw['attach']['rotY'], ms[mo2]['rotY']))
        ck(abs(ms[mo2]['x'] - sw['attach']['x']) < 0.06 and abs(ms[mo2]['z'] - sw['attach']['z']) < 0.06, u'④ スイングでモニター位置が追従')
        sw2 = mjs("return __noza.swing(%s, 200);" % json.dumps(arm2))
        ck(sw2['swing'] == 90, u'④ スイング 200 → ±90 にクランプ (実際 %s)' % sw2['swing'])
        mjs("return __noza.swing(%s, -25);" % json.dumps(arm2))
        cam(360, 200, 790, 360, 80, 600)
        shot('07_swing_minus25')
        mjs("return __noza.swing(%s, 0);" % json.dumps(arm2))
        # スイング 0 は null で保存される (cleanItem)
        ck(mjs("return cleanItem(workItems[%s]).armSwing;" % json.dumps(arm2)) is None, u'④ スイング 0 → cleanItem で null')
        ck(mjs("return cleanItem(workItems[%s]).armReach;" % json.dumps(arm2)) == 55, u'④ cleanItem で armReach=55 が保存される')

        # ── ④ 干渉警告: アーム2 をデスク中央 (z=600) へ移し 180° 回して北壁 (z=563.5) へ向ける。
        #      リーチ 36 → VESA面 z≈566・パネル 12cm が壁 (553.5〜563.5) に入る = パネル前面のレイが壁を拾う。
        #      リーチ 55 → アームが壁を貫いて モニターが壁の向こう = アーム本体のレイ (第2アーム/マウント) が壁を拾う
        mjs("return __noza.drop(%s, 360, 600);" % json.dumps(arm2))
        mjs("workItems[%s].rotY = 180; syncItemMesh(furnMeshes[%s], workItems[%s]); syncMounts(%s); return 1;"
            % ((json.dumps(arm2),) * 4))
        pg.wait_for_timeout(200)
        wv = mjs("return __noza.reach(%s, 36);" % json.dumps(arm2))
        ck(wv['warn'] is not None and u'当たります' in (wv['warn'] or ''), u'④ 北壁へ 36cm: パネルが壁に入る → 警告: %s' % wv['warn'])
        wv2 = mjs("return __noza.reach(%s, 55);" % json.dumps(arm2))
        ck(wv2['warn'] is not None and u'当たります' in (wv2['warn'] or ''), u'④ 北壁へ 55cm: アームが壁を貫く → 警告: %s' % wv2['warn'])
        cam(360, 160, 770, 360, 85, 580)
        shot('07b_reach_into_wall_warn')
        mjs("workItems[%s].rotY = 0; syncItemMesh(furnMeshes[%s], workItems[%s]); syncMounts(%s); return 1;"
            % ((json.dumps(arm2),) * 4))
        wv0 = mjs("return __noza.reach(%s, 55);" % json.dumps(arm2))
        ck(wv0['warn'] is None, u'④ 正面 (南) 向きに戻すと警告なし (%s)' % wv0['warn'])
        mjs("return __noza.drop(%s, 360, 585);" % json.dumps(arm2))

        # ── ⑥ デスク幅との比 ──
        for dsk in (desk80, desk90):
            print(u'      ⑥ MSI 80.9 / %s = %.1f%%  |  BenQ 61.4 / %s = %.1f%%'
                  % (dsk['name'], 80.9 / dsk['w'] * 100, dsk['name'], 61.4 / dsk['w'] * 100))
        bd = bbox(dk)
        print(u'      ⑥ 3D bbox: MSI %.2f / デスク80 %.2f' % (b1m['w'], bd['w']))
        ck(abs(b1m['w'] / bd['w'] - 80.9 / 80.0) < 0.02,
           u'⑥ 3D 上の幅比 MSI bbox / デスク80 bbox (キャスター込み 81.5) = %.3f ≈ 公式比 80.9/80 = %.3f — 実物どおりモニターが天板より 0.9cm 広い' % (b1m['w'] / bd['w'], 80.9 / 80.0))

        # ── UI: アームの家具シートに リーチ/スイング ブロック ──
        mjs("select(%s); return 1;" % json.dumps(armId))
        pg.wait_for_timeout(300)
        ui = pg.evaluate("document.body.innerText")
        ck(u'アームのリーチ' in ui and u'アームのスイング' in ui and u'既定 (折り畳み)' in ui, u'⑤ 家具シートに リーチ/スイング ブロック')
        nb = pg.evaluate("Array.from(document.querySelectorAll('.floorh-btn')).filter(function(b){return b.offsetParent!==null && b.getBoundingClientRect().height>=44;}).length")
        nball = pg.evaluate("Array.from(document.querySelectorAll('.floorh-btn')).filter(function(b){return b.offsetParent!==null;}).length")
        ck(nb == nball and nball >= 9, u'⑤ 表示中の floorh-btn %d 個すべて 高さ ≥44px' % nball)
        ck(pg.evaluate("!!document.querySelector('input[aria-label=\"アームのリーチ\"]') && !!document.querySelector('input[aria-label=\"アームのスイング\"]')"),
           u'⑤ range スライダー (aria-label) が2本')
        pg.evaluate("var el=document.getElementById('reachVal'); if(el) el.scrollIntoView({block:'start'});")
        pg.wait_for_timeout(300)
        shot('08_item_sheet_arm_sliders')
        # + ボタンの実クリック
        before = mjs("return armReach(workItems[%s]);" % json.dumps(armId))
        pg.evaluate("Array.from(document.querySelectorAll('.floorh-btn')).filter(function(b){return b.textContent.indexOf('＋ 1cm')>=0;}).slice(-1)[0].click()")
        pg.wait_for_timeout(300)
        after = mjs("return armReach(workItems[%s]);" % json.dumps(armId))
        ck(abs(after - before - 1) < 0.05, u'⑤ ＋1cm ボタンで %s → %s' % (before, after))
        mjs("deselect(); return 1;")

        # ── ⑦ TVスタンド × TV 回帰 (debug モードの switchRoom は workItems を持ち越すので ページを読み直してから) ──
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
        pg.wait_for_timeout(700)
        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(400)
        st = [c for c in cats if c['type'] == 'tvstand'][0]
        tv = [c for c in cats if c['type'] == 'tv'][0]
        stId = add(st['id'], 600, 400)
        tvId = add(tv['id'], 700, 480)
        pg.wait_for_timeout(200)
        sap = [s for s in mjs("return __noza.stands();") if s['id'] == stId][0]['attach']
        dr = mjs("return __noza.drop(%s, %f, %f);" % (json.dumps(tvId), sap['x'], sap['z']))
        pg.wait_for_timeout(300)
        tvs = [t for t in mjs("return __noza.tvs();") if t['id'] == tvId][0]
        print(u'      ⑦ stand attach %s / drop → %s' % (sap, dr))
        ck(tvs['mounted'] and tvs['mountArm'] == stId, u'⑦ TV をテレビスタンドに取り付け (回帰)')
        sh = mjs("return __noza.standh(%s, 160);" % json.dumps(stId))
        tvs = [t for t in mjs("return __noza.tvs();") if t['id'] == tvId][0]
        ck(sh['standH'] == 160 and abs(tvs['y'] - sh['attach']['y']) < 0.06, u'⑦ 取付高さ 160 で TV が追従 (回帰)')

        # ── ⑧ モバイル 375×812 (デスク + アーム + MSI を置き直す) ──
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.catFull", timeout=30000)
        pg.wait_for_timeout(700)
        mjs("switchRoom('south48'); return 1;")
        pg.wait_for_timeout(400)
        add(desk80['id'], 245, 610)
        armId = add(arm['id'], 245, 585)
        mjs("return __noza.drop(%s, 245, 585);" % json.dumps(armId))
        mo1 = add(msi['id'], 245, 760)
        apm = mjs("return __noza.arms()[0].attach;")
        mjs("return __noza.drop(%s, %f, %f);" % (json.dumps(mo1), apm['x'], apm['z']))
        mjs("return __noza.reach(%s, 50);" % json.dumps(armId))
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip,#drawerLabels{display:none !important;}")
        mjs("__noza.fov(60); return 1;")
        pg.wait_for_timeout(300)
        cam(245, 175, 805, 245, 80, 600)
        mjs("select(%s); return 1;" % json.dumps(armId))
        pg.wait_for_timeout(400)
        # リーチのブロックまでスクロール
        pg.evaluate("var el=document.getElementById('reachVal'); if(el) el.scrollIntoView({block:'center'});")
        pg.wait_for_timeout(300)
        shot('09_mobile_375x812_arm_sheet')
        pg.evaluate("var el=document.getElementById('swingVal'); if(el) el.scrollIntoView({block:'start'});")
        pg.wait_for_timeout(300)
        shot('09b_mobile_375x812_swing_block')
        nbm = pg.evaluate("Array.from(document.querySelectorAll('.floorh-btn')).filter(function(b){return b.offsetParent!==null && b.getBoundingClientRect().height>=44 && b.getBoundingClientRect().width>=44;}).length")
        ck(nbm >= 9, u'⑧ モバイルでも floorh-btn %d 個が 44×44 以上' % nbm)
        mjs("deselect(); return 1;")
        pg.wait_for_timeout(300)
        shot('10_mobile_375x812_view')

        br.close()
    ck(not errs, u'① ページエラー 0 件 (%s)' % (errs[:3] if errs else ''))
    print(u'\n════ 結果: NG %d 件 ════' % len(NG))
    for n in NG:
        print(u'  - ' + n)
    return 1 if NG else 0


if __name__ == '__main__':
    sys.exit(main())

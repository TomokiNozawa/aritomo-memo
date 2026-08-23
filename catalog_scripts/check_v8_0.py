# -*- coding: utf-8 -*-
u"""★v8.0 検証 — キッチン シンク周りの実測是正

  ① 機械検証: ROOM_DATA v6.10 / F-02・F-03・F-04・F-05・F-06 の rect / F-54 の新設 /
     長辺方向 15+59+43+55+8=180 と 奥行方向 2+16.5+50.5+5.5=74.5・27+38+9.5=74.5 が閉じる
  ② 3D: シンクが 「天板に空いた開口 + 角R + 下すぼまり + 排水口」 になっている
     (sink の描画メッシュが 3個以上 / 天板が 4本の帯 / 水栓のメッシュが立っている)
  ③ ツールチップ: F-02 に 「開口: 横55 × 奥行38」 と 「ボウル深さ」、 F-54 に 「シングルレバー」
  ④ **真上ビューの逆算 (オーバーレイ相当)**: 天板を真上から撮り、 画素から cm へ戻して
     ROOM_DATA と 写真実測 の両方に対する残差を cm で出す
  ⑤ スクショ: 写真38/39 と同じ画角 (東=作業側から) / 写真34 (南から) / 写真29/33 (西から) /
     写真35 (玄関から) / シンク寄り / 真上 / ツールチップ / モバイル 375x812
  ⑥ 写真 と レンダリング の 並べ比較画像 (photo | render) を 3画角ぶん生成

出力: catalog_scripts\\v8_0_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_0.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
⚠カメラは部屋ポリゴンの内側に (LDK は x103..790 / y208.5..553.5、 x<364 では y283.5 が北壁)
"""
import glob
import json
import os
import shutil

from PIL import Image, ImageOps, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/room.html?debug=1"
HERE = os.path.dirname(os.path.abspath(__file__))
BOXR = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                    u'野沢用', 'claude', 'nozaROOM')
BOX = os.path.join(BOXR, u'確認用切り出し')
DK = os.path.join(BOXR, u'間取り図等', u'03_キッチン')

# 期待値 (ROOM_DATA v6.10)
CX0, CX1 = 572.0, 646.5          # 天板 西面 / 東面
CY0, CY1 = 208.5, 388.5          # 天板 北端 (壁) / 南端
SINK = [599.0, 325.5, 38, 55]
STOVE = [590.5, 223.5, 50.5, 59]


def jpfont(sz):
    u"""日本語が出るフォント (無ければ既定フォント)"""
    for f in (r'C:\Windows\Fonts\meiryo.ttc', r'C:\Windows\Fonts\YuGothM.ttc',
              r'C:\Windows\Fonts\msgothic.ttc'):
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, sz)
            except Exception:
                pass
    return ImageFont.load_default()

fails = []
shots = []


def chk(cond, label, got=None):
    print(u'  [%s] %s%s' % ('OK  ' if cond else 'FAIL', label,
                            '' if got is None else (u'  -> %s' % (got,))))
    if not cond:
        fails.append(label)


def photo(n):
    g = glob.glob(os.path.join(DK, '*_%s.jpg' % n))
    return ImageOps.exif_transpose(Image.open(g[0])).convert('RGB')


def side_by_side(tag, photo_no, render_path, note):
    u"""写真 (EXIF 正立) と レンダリングを 同じ高さで横に並べる"""
    a = photo(photo_no)
    b = Image.open(render_path).convert('RGB')
    H = 720
    a = a.resize((int(a.width * H / a.height), H), Image.LANCZOS)
    b = b.resize((int(b.width * H / b.height), H), Image.LANCZOS)
    out = Image.new('RGB', (a.width + b.width + 12, H + 40), (20, 20, 24))
    out.paste(a, (0, 40)); out.paste(b, (a.width + 12, 40))
    d = ImageDraw.Draw(out)
    d.text((8, 10), u'写真%s   |   nozaROOM v8.0 レンダリング   —  %s' % (photo_no, note),
           fill=(235, 235, 240), font=jpfont(20))
    p = os.path.join(HERE, 'v8_0_check_%s.png' % tag)
    out.save(p); shots.append(p)
    print(u'  cmp  %-24s -> %s (%d KB)' % (tag, os.path.basename(p), os.path.getsize(p) // 1024))


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
            return pg.evaluate("window.__noza.run(" + json.dumps("(function(){" + code + "})()") + ")")

        def shot(tag):
            path = os.path.join(HERE, "v8_0_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-24s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))
            return path

        def cam(px, py, pz, tx, ty, tz, wait=1500):
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, tx, ty, tz))
            pg.wait_for_timeout(wait)

        mjs("switchRoom('ldk'); return 1;")
        pg.wait_for_timeout(500)

        # ══════════════ ① ROOM_DATA ══════════════
        print(u'\n■ ① ROOM_DATA v6.10')
        meta = mjs("return {v: R.meta.version, n: R.fixtures.length};")
        chk(meta['v'] == '6.10', u'① ROOM_DATA v6.10', meta['v'])
        chk(meta['n'] == 53, u'① fixtures 53件 (52 + F-54)', meta['n'])
        F = mjs("var o={}; R.fixtures.forEach(function(f){o[f.id]={t:f.type,r:f.rect,h:f.h,b:f.bottomH||0,"
                "lab:f.label,cr:f.cornerR||null,dr:f.drain||null};}); return o;")
        chk(F['F-02']['r'] == SINK, u'① F-02 シンク rect = [599.0,325.5,38,55]', F['F-02']['r'])
        chk(F['F-02']['h'] == 85 and F['F-02']['b'] == 66, u'① F-02 h85 / bottomH66 (ボウル深さ19)')
        chk(F['F-03']['r'] == STOVE, u'① F-03 コンロ rect = [590.5,223.5,50.5,59]', F['F-03']['r'])
        chk(F['F-03']['b'] == 85, u'① F-03 は天板天面85に載る', F['F-03']['b'])
        chk(F['F-04']['r'][0] == 572.0, u'① F-04 オイルガードが天板の上 (x572)', F['F-04']['r'])
        chk(F['F-05']['r'][0] == 588.0 and F['F-06']['r'][0] == 583.0, u'① F-05/F-06 をコンロ中心へ')
        chk(F.get('F-54') and F['F-54']['t'] == 'kitchen_faucet', u'① F-54 キッチン水栓 新設')
        # 新規は「最大値+1」。 F-16 はリタイア済み ID なので 欠番のまま埋めない。
        chk('F-16' not in F, u'① F-16 は欠番のまま (リタイア済み ID を再利用していない)')
        chk('F-53' in F and F['F-53']['t'] != 'kitchen_faucet',
            u'① 既存の F-53 (カーテンレール等) はそのまま = ID の繰り上げをしていない',
            F.get('F-53', {}).get('t'))

        print(u'\n■ ① 寸法チェーンが閉じるか')
        s = STOVE, SINK
        wall_stove = STOVE[1] - CY0
        stove_len = STOVE[3]
        gap = SINK[1] - (STOVE[1] + STOVE[3])
        sink_len = SINK[3]
        tail = CY1 - (SINK[1] + SINK[3])
        tot = wall_stove + stove_len + gap + sink_len + tail
        print(u'    長辺: 壁→コンロ %.1f + コンロ %.1f + 間 %.1f + シンク %.1f + 余り %.1f = %.1f'
              % (wall_stove, stove_len, gap, sink_len, tail, tot))
        chk(abs(wall_stove - 15) < .01, u'① コンロ〜北壁 = 15', wall_stove)
        chk(abs(gap - 43) < .01, u'① コンロ〜シンクの間 = 43 (v6.9 は 28.5 だった)', gap)
        chk(abs(sink_len - 55) < .01, u'① シンク 長手 = 55', sink_len)
        chk(abs(tail - 8) < .01, u'① 南端の余り = 8', tail)
        chk(abs(tot - 180) < .01, u'① 合計 = 天板 180', tot)
        st_back, st_front = STOVE[0] - CX0, CX1 - (STOVE[0] + STOVE[2])
        sk_back, sk_front = SINK[0] - CX0, CX1 - (SINK[0] + SINK[2])
        print(u'    奥行: コンロ 西%.1f + 50.5 + 東%.1f = %.1f / シンク 西%.1f + 38 + 東%.1f = %.1f'
              % (st_back, st_front, st_back + 50.5 + st_front, sk_back, sk_front, sk_back + 38 + sk_front))
        chk(abs(st_back + STOVE[2] + st_front - 74.5) < .01, u'① コンロの奥行チェーン = 74.5')
        chk(abs(sk_back + SINK[2] + sk_front - 74.5) < .01, u'① シンクの奥行チェーン = 74.5')
        chk(abs(st_back - 18.5) < .01, u'① コンロ西面 = ガラス東面574 + 16.5', st_back)

        # ══════════════ ② 3D メッシュ ══════════════
        print(u'\n■ ② 3D メッシュ')
        cnt = mjs("var lab=%s, n=0, tri=0; scene.traverse(function(m){ if(m.isMesh && m.userData &&"
                  " m.userData.info===lab){ n++; var g=m.geometry;"
                  " tri += (g.index? g.index.count : (g.attributes.position? g.attributes.position.count:0))/3; }});"
                  " return {n:n, tri:Math.round(tri)};" % json.dumps(F['F-02']['lab']))
        chk(cnt['n'] >= 3, u'② シンクは 3メッシュ以上 (側面帯 + 底板 + 目皿)', cnt)
        chk(cnt['tri'] > 60, u'② シンク側面が 角R付きの帯になっている (三角形数)', cnt['tri'])
        fc = mjs("var lab=%s, n=0; scene.traverse(function(m){ if(m.isMesh && m.userData &&"
                 " m.userData.info===lab) n++; }); return n;" % json.dumps(F['F-54']['lab']))
        chk(fc >= 10, u'② 水栓は 台座+支柱+グースネック8+吐水口+レバー', fc)
        # 天板 (黒 0x2c2c30) が 4本の帯になっているか
        tops = mjs("var n=0; scene.traverse(function(m){ if(m.isMesh && m.material && m.material.color &&"
                   " m.material.color.getHex()===0x2c2c30) n++; }); return n;")
        chk(tops == 4, u'② 黒天板が シンク開口を避けた 4本の帯', tops)
        # ボウル底 66 / リム 85 が 実際のワールド座標で出ているか
        bb = mjs("var lab=%s, lo=1e9, hi=-1e9; scene.traverse(function(m){ if(m.isMesh && m.userData &&"
                 " m.userData.info===lab){ m.geometry.computeBoundingBox(); var b=m.geometry.boundingBox.clone();"
                 " b.applyMatrix4(m.matrixWorld); lo=Math.min(lo,b.min.y); hi=Math.max(hi,b.max.y);} });"
                 " return {lo:Math.round(lo*10)/10, hi:Math.round(hi*10)/10};" % json.dumps(F['F-02']['lab']))
        chk(abs(bb['lo'] - 66) < 1.2 and abs(bb['hi'] - 85) < 0.6,
            u'② シンクの実体が 床上 66〜85 にある (= 天板天面から19 凹む)', bb)

        # ══════════════ ③ ツールチップ ══════════════
        print(u'\n■ ③ ツールチップ')
        tip = mjs("var f=R.fixtures.filter(function(q){return q.id==='F-02';})[0];"
                  " return tipFixInner(f);")
        chk(u'横 55' in (tip or '') and u'奥行 38' in (tip or ''), u'③ F-02 に 「横55 × 奥行38」', tip)
        chk(u'深さ 19' in (tip or ''), u'③ F-02 に ボウル深さ 19cm')
        tip2 = mjs("var f=R.fixtures.filter(function(q){return q.id==='F-54';})[0];"
                   " return tipFixInner(f);")
        chk(u'シングルレバー' in (tip2 or ''), u'③ F-54 に 形式', tip2)

        # ══════════════ ④ 真上ビューの逆算 (オーバーレイ相当) ══════════════
        print(u'\n■ ④ 真上ビューから cm を逆算 (レンダリング残差)')
        # 天板の真上にあって視線を塞ぐもの (レンジフード F-05 / ダクト F-06 / 水栓 F-54 /
        # オイルガード F-04) を一時的に隠してから 真上を撮る。
        hide_labels = [F[i]['lab'] for i in ('F-04', 'F-05', 'F-06', 'F-54')]
        mjs("var L=%s, n=0; window.__v80hid=[]; scene.traverse(function(m){"
            " if((m.isMesh||m.isLineSegments) && m.userData && L.indexOf(m.userData.info)>=0 && m.visible){"
            " m.visible=false; window.__v80hid.push(m); n++; }}); return n;" % json.dumps(hide_labels))
        # 画面下のヒントバー等の UI は 天板の南端に重なるので 解析中だけ隠す
        pg.add_style_tag(content="#vpHint,#nameLabels,#tooltip{display:none !important;}")
        mjs("__noza.fov(24); return 1;")
        cam((CX0 + CX1) / 2, 760, (CY0 + CY1) / 2 + 0.4, (CX0 + CX1) / 2, 85, (CY0 + CY1) / 2, 1800)
        # 天板4隅の画面座標 → 解析はこの矩形の中だけで行う (他室・他設備を拾わない)
        box = mjs("camera.updateMatrixWorld();"
                  "var P=[[%f,%f],[%f,%f],[%f,%f],[%f,%f]], xs=[], ys=[];"
                  "var W=renderer.domElement.clientWidth, H=renderer.domElement.clientHeight;"
                  "var rc=renderer.domElement.getBoundingClientRect();"
                  "P.forEach(function(p){ var v=new THREE.Vector3(p[0],85,p[1]).project(camera);"
                  " xs.push(rc.left+(v.x+1)/2*W); ys.push(rc.top+(-v.y+1)/2*H); });"
                  "return {x0:Math.min.apply(null,xs), x1:Math.max.apply(null,xs),"
                  " y0:Math.min.apply(null,ys), y1:Math.max.apply(null,ys)};"
                  % (CX0, CY0, CX1, CY0, CX1, CY1, CX0, CY1))
        top = shot('06_top_ortho')
        mjs("__noza.fov(55); (window.__v80hid||[]).forEach(function(m){m.visible=true;});"
            " window.__v80hid=[]; return 1;")
        res = measure_top(top, box)
        for k, got, exp in res:
            chk(abs(got - exp) < 1.5, u'④ %s = %.1f cm (期待 %.1f)' % (k, got, exp), '%+.2f cm' % (got - exp))

        # ══════════════ ⑤ スクショ ══════════════
        print(u'\n■ ⑤ スクリーンショット')
        # 写真38/39 = 東 (作業側) から西を見る。 左=南(シンク) 右=北(コンロ)
        cam(785, 148, 302, 604, 86, 298)
        s_east = shot('00_east_worktop')
        # 写真34 = 南から北を見る (手前=シンク / 奥=コンロ+フード)
        cam(628, 128, 470, 612, 92, 260)
        s_south = shot('01_south_along')
        # 写真29/33 = 西 (通路/LDK) から北東を見る
        cam(470, 150, 430, 615, 88, 270)
        s_west = shot('02_west_face')
        # 写真35/36 = 玄関のほうから北を見る (引き) — LDK内に収める
        cam(706, 168, 508, 612, 96, 262)
        shot('03_from_entrance')
        # シンク寄り (角R・下すぼまり・排水口・水栓)
        cam(672, 118, 352, 618, 78, 352)
        shot('04_sink_closeup')
        # コンロ寄り (オイルガードが天板に載ったか)
        cam(730, 142, 336, 612, 92, 252)
        shot('05_stove_oilguard')
        # ツールチップ (ID 検索で F-02 にフォーカス)
        mjs("if (typeof focusNameId==='function') focusNameId('F-02'); return 1;")
        cam(690, 125, 350, 615, 85, 350)
        shot('07_names')

        # ══════════════ ⑥ 並べ比較 ══════════════
        print(u'\n■ ⑥ 写真 と レンダリングの並べ比較')
        side_by_side('10_cmp_photo38_east', '38', s_east, u'作業側(東)から: 左=南シンク / 右=北コンロ')
        side_by_side('11_cmp_photo34_south', '34', s_south, u'南から: 手前=シンク / 奥=コンロ+フード')
        side_by_side('12_cmp_photo33_west', '33', s_west, u'西(通路)から: 左=北コンロ / 右=南シンク')

        # ══════════════ モバイル ══════════════
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(400)
        # モバイルは視野が狭いので 引いた画角で キッチン全体が入るようにする
        cam(752, 175, 452, 608, 92, 288)
        shot('20_mobile_375x812')
        cam(682, 122, 356, 616, 80, 352)
        shot('21_mobile_sink')

        chk(not errs, u'console エラー無し', errs[:3])
        br.close()

    os.makedirs(BOX, exist_ok=True)
    for s in shots:
        shutil.copy2(s, os.path.join(BOX, os.path.basename(s)))
    print(u'\n  → Box にコピー: %s (%d 枚)' % (BOX, len(shots)))
    print(u'\n════ 結果: FAIL %d 件 ════' % len(fails))
    for f in fails:
        print(u'   ✗ %s' % f)
    return 1 if fails else 0


def measure_top(path, box):
    u"""真上ビューの PNG から 天板 / コンロ / シンク の境界を画素で拾い、
       天板の 180 と 74.5 をスケール基準にして cm へ戻す。
       box = 天板4隅の画面座標の外接矩形 (この中だけを見る)。"""
    im0 = Image.open(path).convert('RGB')
    M = 26
    crop = (max(0, int(box['x0'] - M)), max(0, int(box['y0'] - M)),
            min(im0.width, int(box['x1'] + M)), min(im0.height, int(box['y1'] + M)))
    im = im0.crop(crop)
    im.save(path.replace('06_top_ortho', '06b_top_crop'))
    W, H = im.size
    px = im.load()

    # 実測した描画色 (真上・Lambert): 黒天板 (33,33,36) / コンロ (18,19,21) /
    # シンク (189,185,178)〜(156,154,148) / 床 (158,132,102) は 彩度で外れる
    def dark(c):        # 黒天板
        return 27 <= c[0] <= 45 and 27 <= c[1] <= 46 and 28 <= c[2] <= 50

    def stove(c):       # コンロ (天板より暗い)
        return c[0] <= 26 and c[1] <= 27 and c[2] <= 30

    def sinkc(c):       # シンク (明るく低彩度)
        return c[0] >= 130 and c[1] >= 125 and abs(c[0] - c[2]) < 25 and abs(c[0] - c[1]) < 12

    # スケールは 「天板4隅を camera.project した画面座標」 を使う (真上・ほぼ正投影)。
    #   → 色セグメンテーションの誤差がスケールに乗らない。 縦=部屋y(長辺180) / 横=部屋x(奥行74.5)。
    x0, y0 = M, M
    x1, y1 = M + (box['x1'] - box['x0']), M + (box['y1'] - box['y0'])
    sc_y = 180.0 / (y1 - y0)
    sc_x = 74.5 / (x1 - x0)
    # 天板の内側だけを見る (北端は壁・南端は室内が接するので 2px 内側へ寄せる)
    IN = 8            # 天板の縁 (小口のハイライト) を拾わないよう 内側へ寄せる幅 [px] ≒ 2.7cm
    sx_lo, sx_hi = int(x0 + IN), int(x1 - IN)
    sy_lo, sy_hi = int(y0 + IN), int(y1 - IN)
    dbg = im.copy(); dp = dbg.load()

    def band(pred, axis):
        u"""行 (or 列) ごとの一致画素数を数え、 12px 以上一致した行だけを採用する。
           天板の縁の アンチエイリアス 1〜2px を コンロ/シンク と誤検出しないための足切り。"""
        cnt = {}
        for yy in range(max(0, sy_lo), min(H, sy_hi)):
            for xx in range(max(0, sx_lo), min(W, sx_hi)):
                if pred(px[xx, yy]):
                    k = yy if axis == 'y' else xx
                    cnt[k] = cnt.get(k, 0) + 1
                    if axis == 'y':
                        dp[xx, yy] = (255, 0, 255)
        hits = [k for k, v in cnt.items() if v >= 12]
        return (min(hits), max(hits)) if hits else (0, 0)

    sy0, sy1 = band(stove, 'y'); sx0, sx1 = band(stove, 'x')

    ky0, ky1 = band(sinkc, 'y'); kx0, kx1 = band(sinkc, 'x')
    dbg.save(path.replace('06_top_ortho', '06c_top_mask'))
    print(u'    [dbg] box px x %d..%d / y %d..%d  stove y %d..%d x %d..%d  sink y %d..%d x %d..%d'
          % (x0, x1, y0, y1, sy0, sy1, sx0, sx1, ky0, ky1, kx0, kx1))
    out = [
        (u'コンロ〜北壁',     (sy0 - y0) * sc_y, 15.0),
        (u'コンロ 長手',       (sy1 - sy0) * sc_y, 59.0),
        (u'コンロ〜シンク 間', (ky0 - sy1) * sc_y, 43.0),
        (u'シンク 長手',       (ky1 - ky0) * sc_y, 55.0),
        (u'南端の余り',        (y1 - ky1) * sc_y, 8.0),
        (u'コンロ 奥行',       (sx1 - sx0) * sc_x, 50.5),
        (u'シンク 奥行',       (kx1 - kx0) * sc_x, 38.0),
        (u'シンク 西の余白',   (kx0 - x0) * sc_x, 27.0),
        (u'シンク 東の余白',   (x1 - kx1) * sc_x, 9.5),
    ]
    print(u'    (真上ビュー スケール: 長手 %.4f cm/px / 奥行 %.4f cm/px)' % (sc_y, sc_x))
    return out


if __name__ == '__main__':
    raise SystemExit(main())

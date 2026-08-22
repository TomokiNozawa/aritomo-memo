# -*- coding: utf-8 -*-
u"""v7.0 検証: 新しい2枚の写真 (小窓写真 / 大窓写真) と **同画角のレンダリング** を並べる。

three.js は主点をキャンバス中心にしか置けないので、
  ・主点を中心に持つ一回り大きいキャンバス (2A × 2B) を描画し
  ・そのうち 写真に対応する矩形だけを切り出す
という手順で 同画角にする (諸元は measure_v7_0.py が _v7_0_cams.json に書き出す)。

出力 (Box\\確認用切り出し):
  v7_0_check_01_small_vs_render.jpg   小窓写真 ↔ レンダ (共通の高さガイド線つき)
  v7_0_check_02_small_overlay.jpg     小窓写真に ROOM_DATA を重ねたもの
  v7_0_check_03_big_vs_render.jpg     大窓写真 ↔ レンダ
  v7_0_check_04_big_overlay.jpg       大窓写真に ROOM_DATA を重ねたもの
  v7_0_check_05_rail_closeup.jpg      レール部の拡大 (写真 / レンダ 上下)
  v7_0_check_06_hanger.jpg            室内物干しの拡大
  v7_0_check_10/11_render_raw.jpg     レンダ生画像

前提: serve_room.py (or verify_server_v6_4.py) が :8712 で room.html を配信していること。
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v7_0.py
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM')
OUT = os.path.join(BOX, '確認用切り出し')
D62 = os.path.join(BOX, '間取り図等', '04_6.2帖')
URL = 'http://localhost:8712/room.html?debug=1'
CAMS = json.load(io.open(os.path.join(HERE, '_v7_0_cams.json'), encoding='utf-8'))


def font(sz):
    try:
        return ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', sz)
    except Exception:
        return ImageFont.load_default()


def shoot():
    from playwright.sync_api import sync_playwright
    res = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for key in ('small', 'big'):
            c = CAMS[key]
            target = (2 * c['A']) / (2 * c['B'])          # 幅/高さ
            pg = br.new_page(viewport={'width': 760, 'height': 1200})
            errs = []
            pg.on('pageerror', lambda e: errs.append('PAGEERROR: ' + str(e)))
            pg.goto(URL)
            pg.wait_for_function('window.__noza && window.__noza.state', timeout=30000)
            pg.evaluate("switchRoom('all');")
            pg.wait_for_timeout(400)
            # D-06 (内部id d1) = LDK→洋室6.2 引違い2枚。 小窓写真のカメラは LDK 側 (戸口の外) に
            # あるので、 北側パネルを開けて 戸口越しに室内が見えるようにする。
            if key == 'small':
                pg.evaluate("window.__noza.door('d1', 0)")
                pg.wait_for_timeout(400)
            pg.wait_for_timeout(600)
            # キャンバスのアスペクトを 目標に合わせる (viewport の高さを二分法で調整)
            for _ in range(24):
                cw = pg.evaluate('document.querySelector("canvas").clientWidth')
                ch = pg.evaluate('document.querySelector("canvas").clientHeight')
                cur = float(cw) / float(ch)
                if abs(cur - target) < 0.002:
                    break
                vh = pg.viewport_size['height']
                need = int(round(vh + (cw / target - ch)))
                if need < 300 or need > 4000 or need == vh:
                    break
                pg.set_viewport_size({'width': pg.viewport_size['width'], 'height': need})
                pg.wait_for_timeout(160)
            cw = pg.evaluate('document.querySelector("canvas").clientWidth')
            ch = pg.evaluate('document.querySelector("canvas").clientHeight')
            print(u'  %s: canvas %dx%d (比 %.4f / 目標 %.4f)' % (key, cw, ch, float(cw) / ch, target))
            pg.evaluate('window.__noza.fov(%f)' % c['fov'])
            pg.evaluate('window.__noza.cam(%f,%f,%f,%f,%f,%f)'
                        % (c['cam'][0], c['cam'][2], c['cam'][1],
                           c['tgt'][0], c['tgt'][2], c['tgt'][1]))
            pg.wait_for_timeout(400)
            url = pg.evaluate('window.__noza.shot(1200)')
            raw = base64.b64decode(url.split(',', 1)[1])
            path = os.path.join(OUT, 'v7_0_check_%s_render_raw.jpg' % ('10_small' if key == 'small' else '11_big'))
            io.open(path, 'wb').write(raw)
            res[key] = path
            info = pg.evaluate('JSON.stringify(window.__noza.win62())')
            io.open(os.path.join(HERE, '_v7_0_win62_%s.json' % key), 'w', encoding='utf-8').write(info)
            if errs:
                print(u'  ⚠ page errors: %s' % errs[:3])
            pg.close()
        br.close()
    return res


def build(key, render_path, tag, guides, label_ph, label_rn):
    c = CAMS[key]
    rn = Image.open(render_path).convert('RGB')
    RW, RH = rn.size
    s = float(RW) / (2 * c['A'])                         # レンダ px / 写真 px
    # 写真に対応する レンダ内の矩形
    box = (int(round(-c['ox'] * s)), int(round(-c['oy'] * s)),
           int(round((-c['ox'] + c['W']) * s)), int(round((-c['oy'] + c['H']) * s)))
    crop = rn.crop(box)
    ph = ImageOps.exif_transpose(Image.open(os.path.join(D62, c['name']))).convert('RGB')
    ph = ph.resize(crop.size, Image.LANCZOS)
    ph = ImageEnhance.Contrast(ImageEnhance.Brightness(ph).enhance(1.55)).enhance(1.05)

    sc = float(crop.size[0]) / c['W']                    # 写真px → 出力px
    f, px, py = c['f'] * sc, (c['px']) * sc, (c['py']) * sc
    CX, CY, CZ = c['cam']

    def proj(P):
        u"""部屋座標 → 出力画像座標 (measure_v7_0 と同じ内部標定・姿勢)"""
        w = (P[0] - CX, P[1] - CY, P[2] - CZ)
        ex, ey, ez = c['ex'], c['ey'], c['ez']
        X = w[0] * ex[0] + w[1] * ey[0] + w[2] * ez[0]
        Y = w[0] * ex[1] + w[1] * ey[1] + w[2] * ez[1]
        Z = w[0] * ex[2] + w[1] * ey[2] + w[2] * ez[2]
        if Z <= 1e-6:
            return None
        return (px + f * X / Z, py + f * Y / Z)

    F1 = font(max(13, int(crop.size[0] / 55)))
    TOP = int(F1.size * 2.4)
    cv = Image.new('RGB', (crop.size[0] * 2 + 16, crop.size[1] + TOP), (20, 20, 24))
    cv.paste(ph, (0, TOP))
    cv.paste(crop, (crop.size[0] + 16, TOP))
    d = ImageDraw.Draw(cv)
    d.text((8, 6), label_ph, fill=(255, 255, 255), font=F1)
    d.text((crop.size[0] + 24, 6), label_rn, fill=(255, 255, 255), font=F1)
    for P0, P1, col, lab in guides:
        a, b = proj(P0), proj(P1)
        if not a or not b:
            continue
        for dx in (0, crop.size[0] + 16):
            d.line([(a[0] + dx, a[1] + TOP), (b[0] + dx, b[1] + TOP)], fill=col, width=2)
        d.text((min(a[0], b[0]) + 3, min(a[1], b[1]) + TOP - F1.size - 3), lab, fill=col, font=F1)
    d.line([(crop.size[0] + 8, 0), (crop.size[0] + 8, cv.size[1])], fill=(90, 90, 100), width=3)
    p = os.path.join(OUT, 'v7_0_check_%s.jpg' % tag)
    cv.save(p, quality=92)
    print(u'  → %s' % os.path.basename(p))
    return ph, crop, proj, TOP


def main():
    if '--no-shot' not in sys.argv:
        print(u'[1] レンダリング')
        paths = shoot()
    else:
        paths = {'small': os.path.join(OUT, 'v7_0_check_10_small_render_raw.jpg'),
                 'big': os.path.join(OUT, 'v7_0_check_11_big_render_raw.jpg')}

    print(u'[2] 突合図')
    # ── 小窓写真 (E壁 x=1055) ──
    E = 1055.0
    g_small = [
        ((E, 107.0, 240.0), (E, 418.0, 240.0), (255, 70, 70), u'天井240'),
        ((E, 107.0, 0.0), (E, 418.0, 0.0), (255, 70, 70), u'床0'),
        ((E, 107.0, 90.6), (E, 418.0, 90.6), (120, 255, 120), u'腰見切り90.6'),
        ((E, 198.0, 203.5), (E, 242.0, 203.5), (0, 225, 255), u'WIN-06 上端203.5'),
        ((E, 198.0, 157.5), (E, 242.0, 157.5), (0, 225, 255), u'WIN-06 下端157.5'),
        ((E, 258.5, 203.5), (E, 302.5, 203.5), (0, 225, 255), u'WIN-07 上端'),
        ((E, 258.5, 157.5), (E, 302.5, 157.5), (0, 225, 255), u'WIN-07 下端'),
        ((E - 6.5, 185.5, 210.7), (E - 6.5, 315.0, 210.7), (255, 170, 0), u'F-51 レール中心210.7'),
        ((E - 21.0, 110.0, 203.5), (E - 21.0, 204.0, 203.5), (255, 0, 255), u'A3 下端203.5'),
        ((E - 21.0, 110.0, 232.0), (E - 21.0, 204.0, 232.0), (255, 0, 255), u'A3 上端232.0'),
    ]
    build('small', paths['small'], '01_small_vs_render', g_small,
          u'小窓写真.jpg (明るさ補正のみ)',
          u'room.html v7.0 / ROOM_DATA v6.7 — 同画角レンダ (f=1269.4 / カメラ x745.3 y454.2 床上137.7)')

    # ── 大窓写真 (N壁 y=107) ──
    N = 107.0
    g_big = [
        ((800.0, N, 0.0), (1055.0, N, 0.0), (255, 70, 70), u'床0'),
        ((800.0, N, 90.6), (1055.0, N, 90.6), (120, 255, 120), u'腰見切り90.6'),
        ((848.5, N, 213.5), (1013.5, N, 213.5), (0, 225, 255), u'WIN-05 上端213.5'),
        ((848.5, N, 22.5), (1013.5, N, 22.5), (0, 225, 255), u'WIN-05 下端22.5'),
        ((848.5, N, 22.5), (848.5, N, 213.5), (0, 225, 255), u'開口西端848.5'),
        ((1013.5, N, 22.5), (1013.5, N, 213.5), (0, 225, 255), u'開口東端1013.5'),
        ((834.0, N + 6.5, 221.5), (1038.0, N + 6.5, 221.5), (255, 170, 0), u'F-52 レール中心221.5'),
        ((845.0, N + 2.5, 120.0), (845.0, N + 2.5, 120.0), (255, 255, 0), u'房掛け(左)'),
        ((1017.0, N + 2.5, 120.0), (1017.0, N + 2.5, 120.0), (255, 255, 0), u'房掛け(右)'),
        ((993.7, 153.1, 240.0), (993.7, 153.1, 195.9), (0, 255, 180), u'F-53 物干し'),
    ]
    build('big', paths['big'], '03_big_vs_render', g_big,
          u'大窓写真.jpg (明るさ補正のみ)',
          u'room.html v7.0 / ROOM_DATA v6.7 — 同画角レンダ (f=%.0f)' % CAMS['big']['f'])
    print(u'\n[3] ROOM_DATA を写真へ直接オーバーレイ + 残差')
    overlay_small()
    overlay_big()
    print(u'\n出力先: %s' % OUT)


def _proj_of(key):
    c = CAMS[key]
    f, px, py = c['f'], c['px'], c['py']
    CX, CY, CZ = c['cam']
    ex, ey, ez = c['ex'], c['ey'], c['ez']

    def proj(P):
        w = (P[0] - CX, P[1] - CY, P[2] - CZ)
        X = w[0] * ex[0] + w[1] * ey[0] + w[2] * ez[0]
        Y = w[0] * ex[1] + w[1] * ey[1] + w[2] * ez[1]
        Z = w[0] * ex[2] + w[1] * ey[2] + w[2] * ez[2]
        return None if Z <= 1e-6 else (px + f * X / Z, py + f * Y / Z)
    return proj


def _poly(d, proj, pts, col, w=3, close=True):
    q = [proj(p) for p in pts]
    if any(v is None for v in q):
        return
    n = len(q) if close else len(q) - 1
    for i in range(n):
        d.line([q[i], q[(i + 1) % len(q)]], fill=col, width=w)


def overlay_small():
    c = CAMS['small']
    proj = _proj_of('small')
    ph = ImageOps.exif_transpose(Image.open(os.path.join(D62, c['name']))).convert('RGB')
    ph = ImageEnhance.Brightness(ph).enhance(1.45)
    d = ImageDraw.Draw(ph)
    E = 1055.0
    for y0, y1 in ((198.0, 242.0), (258.5, 302.5)):
        _poly(d, proj, [(E, y0, 157.5), (E, y1, 157.5), (E, y1, 203.5), (E, y0, 203.5)], (0, 230, 255))
    _poly(d, proj, [(E - 6.5, 185.5, 209.9), (E - 6.5, 315.0, 209.9),
                    (E - 6.5, 315.0, 211.5), (E - 6.5, 185.5, 211.5)], (255, 170, 0))
    for off in (0.0, 21.0):
        _poly(d, proj, [(E - off, 110.0, 203.5), (E - off, 204.0, 203.5),
                        (E - off, 204.0, 232.0), (E - off, 110.0, 232.0)], (255, 0, 255), 2)
    a = proj((993.7, 153.1, 240.0)); b = proj((993.7, 153.1, 195.9))
    if a and b:
        d.line([a, b], fill=(0, 255, 180), width=3)
        d.ellipse([b[0] - 7, b[1] - 7, b[0] + 7, b[1] + 7], outline=(0, 255, 180), width=3)
    TOP = 48
    cv = Image.new('RGB', (ph.size[0], ph.size[1] + TOP), (20, 20, 24))
    cv.paste(ph, (0, TOP))
    dd = ImageDraw.Draw(cv)
    dd.text((8, 5), u'小窓写真 に ROOM_DATA v6.7 を重ねたもの', fill=(255, 255, 255), font=font(17))
    dd.text((8, 27), u'青=WIN-06/07 開口 / 橙=F-51 レール / 紫=A3 エアコン(壁面と前面) / 緑=F-53 室内物干し',
            fill=(200, 200, 200), font=font(14))
    p = os.path.join(OUT, 'v7_0_check_02_small_overlay.jpg')
    cv.save(p, quality=93)
    print(u'  \u2192 %s' % os.path.basename(p))

    print(u'    \u2500\u2500 横方向 残差 (ROOM_DATA の投影 vs 写真から直接測った縦線) \u2500\u2500')
    for lab, P3, um in ((u'WIN-06 西端', (E, 198.0, 175.0), 414.20),
                        (u'WIN-06 東端', (E, 242.0, 175.0), 535.79),
                        (u'WIN-07 西端', (E, 258.5, 175.0), 586.04),
                        (u'WIN-07 東端', (E, 302.5, 175.0), 730.89)):
        q = proj(P3)
        du = q[0] - um
        print(u'      %-12s 投影 u=%7.2f  実測 u=%7.2f  残差 %+5.2f px (%+0.2f cm)'
              % (lab, q[0], um, du, du / 3.4))
    print(u'    \u2500\u2500 縦方向 残差 \u2500\u2500')
    for lab, P3, vm in ((u'WIN-06 上端', (E, 220.0, 203.5), 499.97),
                        (u'WIN-06 下端', (E, 220.0, 157.5), 670.63),
                        (u'WIN-07 上端', (E, 280.0, 203.5), 484.69),
                        (u'WIN-07 下端', (E, 280.0, 157.5), 670.16)):
        q = proj(P3)
        dv = q[1] - vm
        print(u'      %-12s 投影 v=%7.2f  実測 v=%7.2f  残差 %+5.2f px (%+0.2f cm)'
              % (lab, q[1], vm, dv, dv / 3.42))


def overlay_big():
    c = CAMS['big']
    proj = _proj_of('big')
    ph = ImageOps.exif_transpose(Image.open(os.path.join(D62, c['name']))).convert('RGB')
    ph = ImageEnhance.Brightness(ph).enhance(2.3)
    d = ImageDraw.Draw(ph)
    N = 107.0
    _poly(d, proj, [(848.5, N, 22.5), (1013.5, N, 22.5), (1013.5, N, 213.5), (848.5, N, 213.5)],
          (0, 230, 255))
    _poly(d, proj, [(834.0, N + 6.5, 220.7), (1038.0, N + 6.5, 220.7),
                    (1038.0, N + 6.5, 222.3), (834.0, N + 6.5, 222.3)], (255, 170, 0))
    for tx in (845.0, 1017.0):
        q = proj((tx, N + 3.0, 120.0))
        if q:
            d.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9], outline=(255, 255, 0), width=3)
    a = proj((993.7, 153.1, 240.0)); b = proj((993.7, 153.1, 195.9))
    if a and b:
        d.line([a, b], fill=(0, 255, 180), width=3)
    _poly(d, proj, [(800.0, N, 90.6), (1055.0, N, 90.6)], (120, 255, 120), 2, close=False)
    _poly(d, proj, [(800.0, N, 0.0), (1055.0, N, 0.0)], (255, 70, 70), 2, close=False)
    _poly(d, proj, [(1055.0, N, 0.0), (1055.0, N, 240.0)], (255, 70, 70), 2, close=False)
    TOP = 48
    cv = Image.new('RGB', (ph.size[0], ph.size[1] + TOP), (20, 20, 24))
    cv.paste(ph, (0, TOP))
    dd = ImageDraw.Draw(cv)
    dd.text((8, 5), u'大窓写真 に ROOM_DATA v6.7 を重ねたもの', fill=(255, 255, 255), font=font(17))
    dd.text((8, 27), u'青=WIN-05 開口 / 橙=F-52 レール / 黄=房掛け / 緑=F-53 物干し / 薄緑=腰見切り90.6 / 赤=床0とE壁入隅',
            fill=(200, 200, 200), font=font(14))
    p = os.path.join(OUT, 'v7_0_check_04_big_overlay.jpg')
    cv.save(p, quality=93)
    print(u'  \u2192 %s' % os.path.basename(p))


if __name__ == '__main__':
    main()

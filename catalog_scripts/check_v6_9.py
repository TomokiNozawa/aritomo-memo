# -*- coding: utf-8 -*-
u"""
v6.9 検証: 洋室4.8 南壁を 写真59 / 写真60 と 同画角レンダリング で突き合わせる。

前段 (ブラウザ側) — room.html?debug=1 を http で開き、__noza で撮る:

  ▼ 写真60 用 (縦長ウィンドウ)
      window.switchRoom('south48');
      __noza.fov(62.32);
      __noza.cam(255.15, 118.8, 579.5, 255.15, 118.8, 819.5);
      fetch('/__save?name=v6_9_check_00_render_48_south_photo60.jpg',
            {method:'POST', body: __noza.shot(1100)});

  ▼ 写真59 用 (横長ウィンドウ)
      __noza.fov(64.5);
      __noza.cam(269.9, 120.9, 608.7, 269.9, 120.9, 819.5);
      fetch('/__save?name=v6_9_check_10_render_48_south_photo59.jpg',
            {method:'POST', body: __noza.shot(1400)});

  静的サーバは catalog_scripts/verify_server_v6_4.py (POST /__save が Box の 確認用切り出し へ保存)。

■ 写真60 の内部標定 (v6.8 で決めた値をそのまま使う)
    EXIF orientation=6 → exif_transpose で 2250x4000 / 主点 (1125,2000) / f=3307px / ロール tan=0.0116
    ※ CAM_X=255.15 は WIN-03 (今回 動かしていない窓) を基準に決まるので v6.4 でも変わらない。

■ 写真59 の内部標定 (v6.9 で新規に決めた値)
    EXIF orientation=1 / 4000x2250 / 2.68mm 超広角 (16mm相当 → f≈1777px)
    南壁に沿った 1次元射影写像 (u = 画像x, X = 室内x):
        X = P + Q/(u - v)      v = -87437 (見切り縁×床見切りの交点),
                               Q = 9.4964e8, P = -10343.9
      アンカー: SE入隅 u=836.4 ↔ X=414.5 / CL東面 u=2971.0 ↔ X=160.5 (チェーン全長 254)
      ※ v は 床見切り線のフィット条件で -87k〜-552k と振れるが、 いずれも十分遠方なので
        写像はほぼアフィンで、 読み取り結果の変動は 2cm 未満 (measure_v6_9_photo59.py で確認)。
    → カメラ 横位置 X≈269.9 / 南壁からの距離 D≈210.8cm (= f / 8.43px/cm)

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v6_9.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM')
OUT = os.path.join(BOX, '確認用切り出し')
PH60 = os.path.join(BOX, '間取り図等', '05_4.8帖', 'LINE_ALBUM_20260820 内覧_260820_60.jpg')
PH59 = os.path.join(BOX, '間取り図等', '05_4.8帖', 'LINE_ALBUM_20260820 内覧_260820_59.jpg')
RN60 = os.path.join(OUT, 'v6_9_check_00_render_48_south_photo60.jpg')
RN59 = os.path.join(OUT, 'v6_9_check_10_render_48_south_photo59.jpg')

# ── 写真60 ──
P60_F, P60_CX, P60_CY, P60_ROLL = 3307.0, 1125.0, 2000.0, 0.0116
FOV60, CAMH60, CAMX60, D60 = 62.32, 118.8, 255.15, 240.0
# ── 写真59 ──
P59_V, P59_Q, P59_P = -87437.0, 9.4964e8, -10343.9
FOV59, CAMH59, CAMX59, D59 = 64.5, 120.9, 269.9, 210.8

# ── ROOM_DATA v6.4 の 4.8帖 南壁チェーン ──
CHAIN = [
    (414.5, u'東壁 x414.5', (255, 80, 80)),
    (288.5, u'WIN-04 東端 288.5', (0, 230, 255)),
    (276.0, u'WIN-04 西端 276.0', (0, 230, 255)),
    (259.5, u'WIN-03 東端 259.5', (0, 230, 255)),
    (216.5, u'WIN-03 西端 216.5', (0, 230, 255)),
    (160.5, u'CL東面 x160.5', (255, 80, 80)),
]
OLD = [(296.5, u'旧v6.3 WIN-04 東端 296.5'), (284.0, u'旧v6.3 WIN-04 西端 284.0')]
SEGS = [(414.5, 288.5, u'壁 126.0 (旧118)'), (288.5, 276.0, u'WIN-04 12.5'),
        (276.0, 259.5, u'小壁 16.5 (旧24.5)'), (259.5, 216.5, u'WIN-03 43.0'),
        (216.5, 160.5, u'壁 56.0 (不変)')]
RAIL = (207.0, 302.5)


def font(sz):
    for p in ('C:/Windows/Fonts/meiryo.ttc', 'C:/Windows/Fonts/msgothic.ttc'):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def norm_photo60(RW, RH, f):
    u"""写真60 を レンダと同じ焦点距離・主点へ正規化して RWxRH のキャンバスへ貼る"""
    ph = ImageOps.exif_transpose(Image.open(PH60))
    ph = ph.rotate(-math.degrees(math.atan(P60_ROLL)), resample=Image.BICUBIC, center=(P60_CX, P60_CY))
    s = f / P60_F
    ph = ph.resize((int(round(2250 * s)), int(round(4000 * s))), Image.LANCZOS)
    cp = Image.new('RGB', (RW, RH), (0, 0, 0))
    cp.paste(ph, (int(round(RW / 2.0 - P60_CX * s)), int(round(RH / 2.0 - P60_CY * s))))
    return ImageEnhance.Contrast(ImageEnhance.Brightness(cp).enhance(1.95)).enhance(1.05), s


def main():
    F1, F2 = font(15), font(13)
    TOP = 34

    # ══════════ 写真60 ══════════
    rn = Image.open(RN60).convert('RGB')
    RW, RH = rn.size
    f = (RH / 2.0) / math.tan(math.radians(FOV60 / 2.0))

    def ry60(h, D=D60):
        return RH / 2.0 - f * (h - CAMH60) / D

    def rx60(x, D=D60):
        return RW / 2.0 - (x - CAMX60) * f / D

    cp, _ = norm_photo60(RW, RH, f)
    print(u'写真60: render %dx%d  f=%.1f' % (RW, RH, f))

    # 01 並列比較
    guides = [(240, u'天井 240', (255, 70, 70)), (237.5, u'レール下端 237.5', (255, 170, 0)),
              (232.5, u'窓 上端 232.5', (0, 225, 255)), (17.5, u'窓 下端 17.5', (0, 225, 255)),
              (0, u'床 0', (255, 70, 70))]
    cv = Image.new('RGB', (RW * 2 + 18, RH + TOP), (20, 20, 24))
    cv.paste(cp, (0, TOP)); cv.paste(rn, (RW + 18, TOP))
    d = ImageDraw.Draw(cv)
    d.text((8, 8), u'写真60 (EXIF補正+ロール除去+レンダと同焦点距離へ正規化)', fill=(255, 255, 255), font=F1)
    d.text((RW + 26, 8), u'room.html v6.9 / ROOM_DATA v6.4 (fov62.32・床上118.8・南壁から240)',
           fill=(255, 255, 255), font=F1)
    for h, lab, col in guides:
        y = ry60(h) + TOP
        d.line([(0, y), (RW * 2 + 18, y)], fill=col, width=1)
        d.text((4, y - 17), lab, fill=col, font=F1)
    d.line([(RW + 8, 0), (RW + 8, RH + TOP)], fill=(90, 90, 100), width=3)
    cv.save(os.path.join(OUT, 'v6_9_check_01_photo60_vs_render.jpg'), quality=92)

    # 02 写真60 に v6.4 / v6.3 を重ねる (16.5 是正の可視化)
    ov = cp.copy(); d2 = ImageDraw.Draw(ov)
    for x0, x1, lab in ((216.5, 259.5, u'WIN-03 43'), (276.0, 288.5, u'WIN-04 12.5 ★v6.4 西へ8.0')):
        a, b = rx60(x1), rx60(x0)
        d2.rectangle([a, ry60(232.5), b, ry60(17.5)], outline=(0, 230, 255), width=3)
        d2.text((min(a, b) + 2, ry60(232.5) - 18), lab, fill=(0, 230, 255), font=F2)
    for x0, x1 in ((284.0, 296.5),):
        a, b = rx60(x1), rx60(x0)
        d2.rectangle([a, ry60(232.5), b, ry60(17.5)], outline=(255, 60, 60), width=2)
        d2.text((min(a, b) + 2, ry60(17.5) + 4), u'旧 v6.3 WIN-04 (離隔24.5)', fill=(255, 60, 60), font=F2)
    ya, yb = ry60(232.5), ry60(232.5) + 26
    d2.line([(rx60(259.5), yb), (rx60(276.0), yb)], fill=(0, 255, 130), width=3)
    d2.text((rx60(276.0) + 3, yb + 3), u'小壁 16.5 (実測)', fill=(0, 255, 130), font=F2)
    for off, col, lab in ((9.0, (255, 120, 0), u'ドレープ用 壁から9.0'),
                          (2.7, (255, 215, 0), u'レース用 壁から2.7')):
        D = D60 - off
        a, b = rx60(RAIL[1], D), rx60(RAIL[0], D)
        d2.line([(a, ry60(238.1, D)), (b, ry60(238.1, D))], fill=col, width=3)
        d2.text((a + 4, ry60(238.1, D) + (4 if off < 5 else -18)), lab, fill=col, font=F2)
    for h in (240, 0):
        d2.line([(0, ry60(h)), (RW, ry60(h))], fill=(255, 70, 70), width=1)
    cv2 = Image.new('RGB', (RW, RH + TOP), (20, 20, 24))
    cv2.paste(ov, (0, TOP))
    ImageDraw.Draw(cv2).text(
        (8, 8), u'写真60 × ROOM_DATA v6.4 (青=新WIN / 赤=旧v6.3 WIN-04 / 緑=小壁16.5 / 橙黄=レール)',
        fill=(255, 255, 255), font=F1)
    cv2.save(os.path.join(OUT, 'v6_9_check_02_photo60_overlay_gap165.jpg'), quality=93)

    # ══════════ 写真59 ══════════
    rn9 = Image.open(RN59).convert('RGB')
    RW9, RH9 = rn9.size
    f9 = (RH9 / 2.0) / math.tan(math.radians(FOV59 / 2.0))

    def rx59(x):
        return RW9 / 2.0 - (x - CAMX59) * f9 / D59

    ph = ImageOps.exif_transpose(Image.open(PH59)).convert('RGB')
    PW, PH_ = ph.size
    php = ImageEnhance.Brightness(ph).enhance(1.35)

    def pu59(x):
        u"""室内x → 写真59 の画像x"""
        return P59_V + P59_Q / (x - P59_P)

    print(u'写真59: %dx%d / render %dx%d f=%.1f' % (PW, PH_, RW9, RH9, f9))
    print(u'  チェーン投影 (写真59 の画像x):')
    for x, lab, _c in CHAIN:
        print(u'    %-22s u=%7.1f' % (lab, pu59(x)))

    # 03 写真59 に チェーンを重ねる (これが ① の主証拠)
    o3 = php.copy(); d3 = ImageDraw.Draw(o3)
    for i, (x, lab, col) in enumerate(CHAIN):
        u = pu59(x)
        d3.line([(u, 60), (u, PH_ - 60)], fill=col, width=4)
        ty = 80 + (i % 3) * 46
        tw = d3.textlength(lab, font=font(30))
        tx = u + 8 if u + 8 + tw < PW else u - 8 - tw
        d3.rectangle([tx - 4, ty - 4, tx + tw + 4, ty + 38], fill=(15, 15, 18))
        d3.text((tx, ty), lab, fill=col, font=font(30))
    for i, (x, lab) in enumerate(OLD):
        u = pu59(x)
        d3.line([(u, 60), (u, PH_ - 60)], fill=(255, 0, 220), width=3)
        ty = PH_ - 210 + i * 46
        tw = d3.textlength(lab, font=font(28))
        d3.rectangle([u + 4, ty - 4, u + 12 + tw, ty + 36], fill=(15, 15, 18))
        d3.text((u + 8, ty), lab, fill=(255, 0, 220), font=font(28))
    for a, b, lab in SEGS:
        ua, ub = pu59(a), pu59(b)
        yy = PH_ - 300
        d3.line([(ua, yy), (ub, yy)], fill=(0, 255, 130), width=4)
        d3.line([(ua, yy - 12), (ua, yy + 12)], fill=(0, 255, 130), width=4)
        d3.line([(ub, yy - 12), (ub, yy + 12)], fill=(0, 255, 130), width=4)
        tw = d3.textlength(lab, font=font(28))
        tx = (ua + ub) / 2.0 - tw / 2.0
        d3.rectangle([tx - 4, yy + 12, tx + tw + 4, yy + 52], fill=(15, 15, 18))
        d3.text((tx, yy + 16), lab, fill=(0, 255, 130), font=font(28))
    for k, (u, lab, col) in enumerate(((pu59(RAIL[0]), u'レール西端 207.0', (255, 170, 0)),
                                       (pu59(RAIL[1]), u'レール東端 302.5', (255, 170, 0)))):
        d3.line([(u, 30), (u, 300)], fill=col, width=4)
        tw = d3.textlength(lab, font=font(28))
        tx = u + 8 if k else u - 8 - tw
        d3.rectangle([tx - 4, 296, tx + tw + 4, 336], fill=(15, 15, 18))
        d3.text((tx, 300), lab, fill=col, font=font(28))
    hdr = Image.new('RGB', (PW, PH_ + 60), (20, 20, 24))
    hdr.paste(o3, (0, 60))
    ImageDraw.Draw(hdr).text(
        (10, 16), u'写真59 × ROOM_DATA v6.4 南壁チェーン (青=窓 / 赤=壁の両端 / 桃=旧v6.3 WIN-04 / 緑=区間 / 橙=レール)',
        fill=(255, 255, 255), font=font(34))
    hdr.thumbnail((2000, 2000), Image.LANCZOS)
    hdr.save(os.path.join(OUT, 'v6_9_check_03_photo59_chain_overlay.jpg'), quality=90)

    # 04 写真59 と レンダの並列 (同じ x に縦線)
    ph_s = php.resize((RW9, int(PH_ * RW9 / float(PW))), Image.LANCZOS)
    sc = RW9 / float(PW)
    cv4 = Image.new('RGB', (RW9, ph_s.height + RH9 + TOP * 2 + 8), (20, 20, 24))
    cv4.paste(ph_s, (0, TOP)); cv4.paste(rn9, (0, TOP * 2 + ph_s.height + 8))
    d4 = ImageDraw.Draw(cv4)
    d4.text((8, 8), u'写真59 (縦線 = ROOM_DATA v6.4 の南壁チェーン)', fill=(255, 255, 255), font=F1)
    d4.text((8, TOP + ph_s.height + 14), u'room.html v6.9 / ROOM_DATA v6.4 同画角レンダリング '
            u'(fov64.5・床上120.9・南壁から210.8・x269.9)', fill=(255, 255, 255), font=F1)
    for x, lab, col in CHAIN:
        d4.line([(pu59(x) * sc, TOP), (pu59(x) * sc, TOP + ph_s.height)], fill=col, width=2)
        d4.line([(rx59(x), TOP * 2 + ph_s.height + 8), (rx59(x), cv4.height)], fill=col, width=2)
    for u, x in ((pu59(RAIL[0]), RAIL[0]), (pu59(RAIL[1]), RAIL[1])):
        d4.line([(u * sc, TOP), (u * sc, TOP + ph_s.height)], fill=(255, 170, 0), width=2)
        d4.line([(rx59(x), TOP * 2 + ph_s.height + 8), (rx59(x), cv4.height)], fill=(255, 170, 0), width=2)
    cv4.save(os.path.join(OUT, 'v6_9_check_04_photo59_vs_render.jpg'), quality=90)

    print(u'→ %s に v6_9_check_01〜04 を出力しました' % OUT)


if __name__ == '__main__':
    main()

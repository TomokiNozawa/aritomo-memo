# -*- coding: utf-8 -*-
u"""
v6.8 検証: 写真60 (洋室4.8 南窓) と 同画角レンダリング の 突合図を作る。

前段 (ブラウザ側) — room.html?debug=1 を http で開き、 縦長ウィンドウにしてから:

    window.switchRoom('south48');
    __noza.fov(62.32);
    __noza.cam(255.15, 118.8, 579.5, 255.15, 118.8, 819.5);   // 床上118.8 / 南壁から240
    fetch('/__save?name=v6_8_check_00_render_4_8_south_raw.jpg',
          {method:'POST', body: __noza.shot(720)});

  静的サーバは catalog_scripts/verify_server_v6_4.py (POST /__save が Box の 確認用切り出し へ保存)。

このスクリプトは その生レンダを読み、 写真60 を **レンダと同じ焦点距離・同じ主点** へ正規化して
  01 並列比較 (共通の高さガイド線つき)
  02 ROOM_DATA の外形を写真へ重ねたもの
  03 カーテンレール部の拡大 (上下2段)
  04 レール左右端の予測位置と実物のズレ
を Box の 確認用切り出し へ出力する。

■ 写真60 のカメラ内部標定 (v6.8 で決めた値。 再測しない限りこの定数を使う)
    EXIF orientation=6 → ImageOps.exif_transpose で 2250x4000
    主点 = (1125, 2000) / 焦点距離 = 3307 px / ロール = atan(0.0116) ≈ 0.66°
    (焦点距離は 天井見切り線 y=361.5-0.01964x と 巾木下端 y=3649.4-0.0079x の差 = 天井高240cm から。
     同じ縮尺で測った開口幅が WIN-03 42.8cm / WIN-04 13.3cm と ROOM_DATA に一致することで相互検証済み)

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v6_8_photo60.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM')
OUT = os.path.join(BOX, '確認用切り出し')
PHOTO60 = os.path.join(BOX, '間取り図等', '05_4.8帖', 'LINE_ALBUM_20260820 内覧_260820_60.jpg')
RENDER = os.path.join(OUT, 'v6_8_check_00_render_4_8_south_raw.jpg')

# ── 写真60 の内部標定 ──
P_F = 3307.0                 # 焦点距離 [px] @ 2250x4000
P_CX, P_CY = 1125.0, 2000.0  # 主点
P_ROLL = 0.0116              # 天井/巾木線の傾き (tan)

# ── レンダのカメラ ──
FOV = 62.32                  # 垂直画角 [deg]
CAM_H = 118.8                # カメラ高さ [cm]
CAM_X = 255.15               # カメラの 室x (= 画面中心に写る 壁面の x)
WALL_D = 240.0               # カメラ → 南壁 の距離 [cm]


def font(sz):
    try:
        return ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', sz)
    except Exception:
        return ImageFont.load_default()


def main():
    rn = Image.open(RENDER).convert('RGB')
    RW, RH = rn.size
    f = (RH / 2.0) / math.tan(math.radians(FOV / 2.0))

    def ry(h, D=WALL_D):
        return RH / 2.0 - f * (h - CAM_H) / D

    def rx(x, D=WALL_D):
        return RW / 2.0 - (x - CAM_X) * f / D

    # 写真を レンダと同じ焦点距離・主点へ正規化
    ph = Image.open(PHOTO60)
    ph = ImageOps.exif_transpose(ph)
    ph = ph.rotate(-math.degrees(math.atan(P_ROLL)), resample=Image.BICUBIC, center=(P_CX, P_CY))
    s = f / P_F
    ph = ph.resize((int(round(2250 * s)), int(round(4000 * s))), Image.LANCZOS)
    cp = Image.new('RGB', (RW, RH), (0, 0, 0))
    cp.paste(ph, (int(round(RW / 2.0 - P_CX * s)), int(round(RH / 2.0 - P_CY * s))))
    cp = ImageEnhance.Contrast(ImageEnhance.Brightness(cp).enhance(1.95)).enhance(1.05)
    print(u'render %dx%d f=%.1f / photo scale %.4f' % (RW, RH, f, s))

    F1, F2 = font(15), font(14)
    TOP = 34

    # ── 01 並列比較 ──
    guides = [(240, u'天井 240', (255, 70, 70)), (237.5, u'レール下端 237.5', (255, 170, 0)),
              (232.5, u'窓 上端 232.5', (0, 225, 255)), (17.5, u'窓 下端 17.5', (0, 225, 255)),
              (0, u'床 0', (255, 70, 70))]
    cv = Image.new('RGB', (RW * 2 + 18, RH + TOP), (20, 20, 24))
    cv.paste(cp, (0, TOP))
    cv.paste(rn, (RW + 18, TOP))
    d = ImageDraw.Draw(cv)
    d.text((8, 8), u'写真60 (EXIF補正+ロール除去+レンダと同焦点距離へ正規化)', fill=(255, 255, 255), font=F1)
    d.text((RW + 26, 8), u'room.html v6.8 / ROOM_DATA v6.3 (fov62.32・カメラ 床上118.8・南壁から240)',
           fill=(255, 255, 255), font=F1)
    for h, lab, col in guides:
        y = ry(h) + TOP
        d.line([(0, y), (RW * 2 + 18, y)], fill=col, width=1)
        d.text((4, y - 17), lab, fill=col, font=F1)
    d.line([(RW + 8, 0), (RW + 8, RH + TOP)], fill=(90, 90, 100), width=3)
    cv.save(os.path.join(OUT, 'v6_8_check_01_photo60_vs_render.jpg'), quality=92)

    # ── 02 オーバーレイ ──
    ov = cp.copy()
    d2 = ImageDraw.Draw(ov)
    for x0, x1, lab in [(216.5, 259.5, u'WIN-03 43'), (284.0, 296.5, u'WIN-04 12.5')]:
        a, b = rx(x1), rx(x0)
        d2.rectangle([a, ry(232.5), b, ry(17.5)], outline=(0, 230, 255), width=3)
        d2.text((min(a, b) + 2, ry(232.5) - 18), lab, fill=(0, 230, 255), font=F1)
    for off, col, lab in ((9.0, (255, 120, 0), u'ドレープ用 壁から9.0'),
                          (2.7, (255, 215, 0), u'レース用 壁から2.7')):
        D = WALL_D - off
        a, b = rx(305.5, D), rx(210.0, D)
        d2.line([(a, ry(238.1, D)), (b, ry(238.1, D))], fill=col, width=3)
        d2.text((a + 4, ry(238.1, D) + (4 if off < 5 else -19)), lab, fill=col, font=F1)
    for h in (240, 0):
        d2.line([(0, ry(h)), (RW, ry(h))], fill=(255, 70, 70), width=1)
    cv2 = Image.new('RGB', (RW, RH + TOP), (20, 20, 24))
    cv2.paste(ov, (0, TOP))
    ImageDraw.Draw(cv2).text(
        (8, 8), u'写真60 に ROOM_DATA v6.3 を重ねたもの (青=窓開口 / 橙・黄=カーテンレール2本 / 赤=天井240・床0)',
        fill=(255, 255, 255), font=F1)
    cv2.save(os.path.join(OUT, 'v6_8_check_02_overlay_on_photo60.jpg'), quality=92)

    # ── 03 レール部 拡大 (上=写真 / 下=レンダ) ──
    Z, BOXR = 3, (100, int(ry(240)) - 42, 620, int(ry(228)))

    def zoom(im):
        c = im.crop(BOXR)
        return c.resize((c.width * Z, c.height * Z), Image.LANCZOS)

    a, b = zoom(cp), zoom(rn)
    cv3 = Image.new('RGB', (a.width, a.height * 2 + 30 * 2 + 8), (20, 20, 24))
    cv3.paste(a, (0, 30))
    cv3.paste(b, (0, 30 * 2 + a.height + 8))
    d3 = ImageDraw.Draw(cv3)
    d3.text((8, 6), u'写真60 カーテンレール部 拡大', fill=(255, 255, 255), font=F1)
    d3.text((8, 30 + a.height + 14),
            u'room.html v6.8 同部位 (F-50 天井付けダブル / 出2.7・9.0 / 下端237.5)', fill=(255, 255, 255), font=F1)
    for h, col, lab in ((240, (255, 70, 70), u'天井240'), (238.1, (255, 170, 0), u'レール中心238.1')):
        for base in (30, 30 * 2 + a.height + 8):
            y = base + (ry(h) - BOXR[1]) * Z
            d3.line([(0, y), (cv3.width, y)], fill=col, width=1)
            d3.text((4, y + 2), lab, fill=col, font=F1)
    cv3.save(os.path.join(OUT, 'v6_8_check_03_rail_closeup.jpg'), quality=93)

    # ── 04 レール左右端 ──
    Z4 = 6

    def marked(im, roomx):
        cf, cb = rx(roomx, WALL_D - 9.0), rx(roomx, WALL_D - 2.7)
        bx = (int(min(cf, cb)) - 46, int(ry(240)) - 32, int(max(cf, cb)) + 46, int(ry(233)))
        c = im.crop(bx).resize(((bx[2] - bx[0]) * Z4, (bx[3] - bx[1]) * Z4), Image.LANCZOS)
        dd = ImageDraw.Draw(c)
        dd.line([((cf - bx[0]) * Z4, 0), ((cf - bx[0]) * Z4, c.height)], fill=(255, 140, 0), width=2)
        dd.line([((cb - bx[0]) * Z4, 0), ((cb - bx[0]) * Z4, c.height)], fill=(255, 225, 0), width=2)
        dd.line([(0, (ry(240) - bx[1]) * Z4), (c.width, (ry(240) - bx[1]) * Z4)], fill=(255, 70, 70), width=2)
        return c

    rows = [(marked(cp, x), marked(rn, x), lab) for x, lab in ((305.5, u'西端 x=305.5'), (210.0, u'東端 x=210.0'))]
    Wp = max(r[0].width for r in rows)
    Hp = rows[0][0].height
    cv4 = Image.new('RGB', (Wp * 2 + 16, (Hp + 26) * 2 + 8), (20, 20, 24))
    d4 = ImageDraw.Draw(cv4)
    for i, (pa, pb, lab) in enumerate(rows):
        yy = i * (Hp + 26 + 4)
        d4.text((6, yy + 4), u'写真60 / レール %s (橙=ドレープ用の端 予測 / 黄=レース用の端 予測 / 赤=天井240)' % lab,
                fill=(255, 255, 255), font=F2)
        d4.text((Wp + 22, yy + 4), u'レンダリング 同部位', fill=(255, 255, 255), font=F2)
        cv4.paste(pa, (0, yy + 26))
        cv4.paste(pb, (Wp + 16, yy + 26))
    cv4.save(os.path.join(OUT, 'v6_8_check_04_rail_ends.jpg'), quality=94)

    print(u'→ %s に 01〜04 を出力しました' % OUT)


if __name__ == '__main__':
    main()

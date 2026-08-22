# -*- coding: utf-8 -*-
u"""v7.0 実測: 洋室6.2帖 の 2枚の新規写真 (小窓写真.jpg / 大窓写真.jpg) を
**3消失点によるフルキャリブレーション** で逆投影し、

  ・カーテンレール2本 (高さ / 壁からの出 / 長さ / 種類)
  ・室内物干し (天井付け) の 取付位置 と 下がり長さ
  ・WIN-05 / WIN-06 / WIN-07 の sill / height / 幅 / 位置
  ・エアコン A3 の 位置・下端高さ
  ・腰見切り縁 の高さ

を cm で読む。

■ 方法 (v6.8/v6.9 の 1次元射影写像を 2次元へ拡張したもの)
  1. 直交する3方向 (壁に沿う水平 / それに直交する水平 / 鉛直) の消失点 V1,V2,V3 を
     画像中の直線群 (巾木・腰見切り・天井見切り・窓の頭/下端・窓枠の縦材) から最小二乗で求める。
  2. 3消失点は互いに直交する方向なので、 **主点 = 三角形 V1V2V3 の垂心 / f² = -(V1-P)·(V2-P)**
     でカメラ内部標定が決まる (トリミング済みの画像でも主点を仮定しなくてよい)。
     → f² > 0 になること 自体が「3直線群が本当に直交している」ことの検算になる。
  3. 各方向の単位ベクトル (カメラ座標) が決まるので、 既知の3D点2つ (部屋の入隅の 床点 と 天井点)
     からカメラ位置 C を解く。 u と v の 両方から独立に解けるので これも検算になる。
  4. あとは 任意の画像点を 既知平面 (壁 x=1055 / 天井 z=240 / 床 z=0) へ 逆投影するだけ。

■ 使い方
  bash ~/.claude/scripts/run_py.sh catalog_scripts/measure_v7_0.py
"""
import io
import json
import math
import os

from PIL import Image, ImageOps

BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM')
D62 = os.path.join(BOX, '間取り図等', '04_6.2帖')

HERE = os.path.dirname(os.path.abspath(__file__))
CH = 240.0            # 天井高 (ROOM_DATA 既定・写真60 で検証済)


# ══════════════════════════════════════════════════════════════════ 画像ユーティリティ
class Photo(object):
    def __init__(self, name):
        self.im = ImageOps.exif_transpose(Image.open(os.path.join(D62, name))).convert('RGB')
        self.px = self.im.load()
        self.W, self.H = self.im.size

    def lum(self, x, y):
        xi = max(0, min(self.W - 1, int(x)))
        yi = max(0, min(self.H - 1, int(y)))
        c = self.px[xi, yi]
        return 0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]

    # ── 縦エッジ (行ごとに x を拾って x = a*y + b を最小二乗) ──
    def vline(self, label, y0, y1, ystep, x0, x1, sign, mode='grad', guess=None):
        pts = []
        for y in range(y0, y1, ystep):
            f = (lambda x: sum(self.lum(x + 2, y + d) - self.lum(x - 2, y + d)
                               for d in (-1, 0, 1)) / 3.0 * sign)
            if mode == 'min':                       # 入隅の陰 (輝度の谷)
                f = (lambda x: -sum(self.lum(x + d, y + e) for d in (-2, 0, 2)
                                    for e in (-2, 0, 2)) / 9.0)
            if guess is not None:
                gc = guess[1] + guess[0] * (y - y0)
                x0, x1 = int(gc - guess[2]), int(gc + guess[2])
            best = None
            for x in range(x0 + 2, x1 - 2):
                s = f(x)
                if best is None or s > best[1]:
                    best = (x, s)
            if best is None:
                continue
            xb = best[0]
            a_, b_, c_ = f(xb - 1), f(xb), f(xb + 1)
            den = a_ - 2 * b_ + c_
            dx = 0.5 * (a_ - c_) / den if den else 0.0
            pts.append((xb + max(-1.0, min(1.0, dx)), float(y)))
        return _fit(label, pts, swap=True)

    # ── 横エッジ (列ごとに y を拾って y = a*x + b を最小二乗) ──
    #    guess=(slope, y@x0, halfwidth) を渡すと 傾いた帯の中だけを探す (レール等)
    def hline(self, label, x0, x1, xstep, y0, y1, sign, mode='grad', xs=None, guess=None):
        pts = []
        cols = xs if xs is not None else range(x0, x1, xstep)
        for x in cols:
            f = (lambda y: sum(self.lum(x + d, y + 2) - self.lum(x + d, y - 2)
                               for d in (-1, 0, 1)) / 3.0 * sign)
            if mode == 'min':
                f = (lambda y: -sum(self.lum(x + d, y + e) for d in (-2, 0, 2)
                                    for e in (-2, 0, 2)) / 9.0)
            if guess is not None:
                gc = guess[1] + guess[0] * (x - x0)
                lo, hi = int(gc - guess[2]), int(gc + guess[2])
            else:
                lo, hi = y0, y1
            best = None
            for y in range(lo + 2, hi - 2):
                s = f(y)
                if best is None or s > best[1]:
                    best = (y, s)
            if best is None:
                continue
            yb = best[0]
            a_, b_, c_ = f(yb - 1), f(yb), f(yb + 1)
            den = a_ - 2 * b_ + c_
            dy = 0.5 * (a_ - c_) / den if den else 0.0
            pts.append((float(x), yb + max(-1.0, min(1.0, dy))))
        return _fit(label, pts, swap=False)


def _fit(label, pts, swap):
    u"""swap=False: y = a*x+b / swap=True: x = a*y+b  (2σ で1回外れ値除去)"""
    for _ in range(2):
        n = len(pts)
        if n < 3:
            break
        if swap:
            P = [(p[1], p[0]) for p in pts]         # (独立=y, 従属=x)
        else:
            P = [(p[0], p[1]) for p in pts]
        sx = sum(q[0] for q in P); sy = sum(q[1] for q in P)
        sxx = sum(q[0] ** 2 for q in P); sxy = sum(q[0] * q[1] for q in P)
        a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        b = (sy - a * sx) / n
        r = [abs(q[1] - (a * q[0] + b)) for q in P]
        rms = (sum(v * v for v in r) / n) ** 0.5
        pts = [p for p, rr in zip(pts, r) if rr < 2.5 * rms + 0.4]
    print(u'    %-26s %s  n=%3d  rms %.2f px' %
          (label, ('x = %+0.5f*y %+8.2f' % (a, b)) if swap else
                  ('y = %+0.5f*x %+8.2f' % (a, b)), len(pts), rms))
    return (a, b, swap)


def isect(L1, L2):
    u"""2直線の交点 (それぞれ (a,b,swap))"""
    def coef(L):
        a, b, sw = L
        return (1.0, -a, -b) if sw else (-a, 1.0, -b)   # (A,B,C): A*x + B*y + C = 0
    A1, B1, C1 = coef(L1); A2, B2, C2 = coef(L2)
    d = A1 * B2 - A2 * B1
    return ((B1 * C2 - B2 * C1) / d, (A2 * C1 - A1 * C2) / d)


def vp_from_lines(lines):
    u"""複数直線の最小二乗交点"""
    M = [[0.0, 0.0], [0.0, 0.0]]; r = [0.0, 0.0]
    for L in lines:
        a, b, sw = L
        A, B, C = (1.0, -a, -b) if sw else (-a, 1.0, -b)
        nn = (A * A + B * B) ** 0.5
        A, B, C = A / nn, B / nn, C / nn
        M[0][0] += A * A; M[0][1] += A * B; M[1][0] += A * B; M[1][1] += B * B
        r[0] -= A * C; r[1] -= B * C
    d = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    return ((r[0] * M[1][1] - r[1] * M[0][1]) / d, (M[0][0] * r[1] - M[1][0] * r[0]) / d)


# ══════════════════════════════════════════════════════════════════ カメラ
class Cam(object):
    u"""3直交消失点 V1(水平A) V2(水平B) V3(鉛直) から 内部標定 + 姿勢を組む"""

    def __init__(self, V1, V2, V3, e1, e2, e3):
        # 主点 = 垂心
        (x1, y1), (x2, y2), (x3, y3) = V1, V2, V3
        # 頂点3から辺12への垂線 / 頂点2から辺13への垂線
        a1, b1 = x2 - x1, y2 - y1
        a2, b2 = x3 - x1, y3 - y1
        # a1*(x-x3)+b1*(y-y3)=0 , a2*(x-x2)+b2*(y-y2)=0
        det = a1 * b2 - a2 * b1
        c1 = a1 * x3 + b1 * y3
        c2 = a2 * x2 + b2 * y2
        px = (c1 * b2 - c2 * b1) / det
        py = (a1 * c2 - a2 * c1) / det
        f2 = -((x1 - px) * (x2 - px) + (y1 - py) * (y2 - py))
        self.px, self.py, self.f = px, py, math.sqrt(f2)
        self.f2 = f2
        # 各消失点 → カメラ座標での単位方向 (e* は その消失点が表す 部屋座標の向き)
        self.axes = {}
        for V, e in ((V1, e1), (V2, e2), (V3, e3)):
            d = ((V[0] - px) / self.f, (V[1] - py) / self.f, 1.0)
            n = math.sqrt(sum(t * t for t in d))
            u = tuple(t / n for t in d)
            self.axes[e[0]] = tuple(t * e[1] for t in u)     # e = ('x', +1/-1)
        self.ex, self.ey, self.ez = self.axes['x'], self.axes['y'], self.axes['z']

    def orth_report(self):
        def dot(a, b):
            return sum(p * q for p, q in zip(a, b))
        print(u'    f = %.1f px / 主点 = (%.1f, %.1f)   直交残差 %.5f %.5f %.5f'
              % (self.f, self.px, self.py,
                 dot(self.ex, self.ey), dot(self.ey, self.ez), dot(self.ex, self.ez)))

    def to_cam(self, w):
        u"""部屋ベクトル → カメラ座標"""
        return tuple(w[0] * self.ex[i] + w[1] * self.ey[i] + w[2] * self.ez[i] for i in range(3))

    def to_room(self, v):
        return (sum(v[i] * self.ex[i] for i in range(3)),
                sum(v[i] * self.ey[i] for i in range(3)),
                sum(v[i] * self.ez[i] for i in range(3)))

    def solve_C(self, P1, uv1, P2, uv2):
        u"""同一鉛直線上の既知2点 (床点/天井点) から カメラ位置を解く"""
        dz = self.to_cam((P2[0] - P1[0], P2[1] - P1[1], P2[2] - P1[2]))
        k1 = (uv1[0] - self.px) / self.f
        k2 = (uv2[0] - self.px) / self.f
        # X = k1*Z ; X+dz0 = k2*(Z+dz2)
        Z = (k2 * dz[2] - dz[0]) / (k1 - k2)
        X = k1 * Z
        Y = (uv1[1] - self.py) / self.f * Z
        # v での検算
        Yc = (uv2[1] - self.py) / self.f * (Z + dz[2])
        chk = (Y + dz[1]) - Yc
        w = self.to_room((X, Y, Z))
        self.C = (P1[0] - w[0], P1[1] - w[1], P1[2] - w[2])
        print(u'    カメラ位置 = (x %.1f, y %.1f, 床上 %.1f)   v による検算残差 %.2f px相当'
              % (self.C[0], self.C[1], self.C[2], chk / Z * self.f))
        return self.C

    def ray(self, u, v):
        u"""画像点 → 部屋座標での視線方向"""
        d = ((u - self.px) / self.f, (v - self.py) / self.f, 1.0)
        return self.to_room(d)

    def on_plane(self, u, v, axis, val):
        u"""画像点を 平面 (axis=0/1/2 の座標が val) へ逆投影"""
        d = self.ray(u, v)
        t = (val - self.C[axis]) / d[axis]
        return tuple(self.C[i] + t * d[i] for i in range(3))

    def project(self, P):
        v = self.to_cam((P[0] - self.C[0], P[1] - self.C[1], P[2] - self.C[2]))
        return (self.px + self.f * v[0] / v[2], self.py + self.f * v[1] / v[2])


def line_y_at(L, x):
    a, b, sw = L
    if sw:                       # x = a*y + b → y = (x-b)/a  (縦線用: 使わない)
        return (x - b) / a
    return a * x + b


def on_line_vert(L, cam, x_guess, plane_axis, plane_val):
    pass


# ══════════════════════════════════════════════════════════════════ 小窓写真
def small():
    print(u'\n════════ 小窓写真.jpg (洋室6.2帖 E壁 = 高所小窓2連) ════════')
    ph = Photo(u'小窓写真.jpg')
    print(u'  画像 %dx%d' % (ph.W, ph.H))

    print(u'  [1] E壁 (x=1055) 上の水平線')
    Lfloor = ph.hline(u'巾木下端 (h=0)', 240, 790, 8, 1050, 1262, -1)
    Lchair = ph.hline(u'腰見切り縁 下端', 240, 930, 8, 845, 960, -1)
    Lceil = ph.hline(u'天井見切り (h=240)', 500, 945, 5, 270, 400, 0, mode='min')
    Lhead1 = ph.hline(u'WIN-06 開口 上端', 418, 534, 2, 488, 512, 1)
    Lhead2 = ph.hline(u'WIN-07 開口 上端', 590, 730, 2, 466, 496, 1)
    Lsill1 = ph.hline(u'WIN-06 窓台 上面', 424, 528, 2, 655, 674, 1)
    Lsill2 = ph.hline(u'WIN-07 窓台 上面', 594, 724, 2, 655, 676, 1)
    # レールは 傾いた細い帯なので guess (傾き -0.0995 / x=400 で y=470) の ±7px だけ探す
    Lrail = ph.hline(u'カーテンレール 上エッジ', 396, 768, 2, 0, 0, 1,
                     guess=(-0.0995, 468.0, 7.0))
    Lrailb = ph.hline(u'カーテンレール 下エッジ', 396, 768, 2, 0, 0, -1,
                      guess=(-0.0995, 476.0, 7.0))

    print(u'  [2] N壁 (y=107) 上の水平線')
    Nfloor = ph.hline(u'N壁 巾木下端', 96, 214, 4, 1090, 1180, -1)
    Nchair = ph.hline(u'N壁 腰見切り 下端', 96, 214, 4, 855, 895, -1)

    print(u'  [3] 鉛直線 (窓の開口端)')
    Vs = [ph.vline(u'WIN-06 西端', 505, 670, 2, 404, 424, 1),
          ph.vline(u'WIN-06 東端', 505, 655, 2, 528, 546, -1),
          ph.vline(u'WIN-07 西端', 500, 670, 2, 576, 596, 1),
          ph.vline(u'WIN-07 東端', 505, 650, 2, 724, 744, -1)]

    # V1 は 画像の全幅にわたる 3本 (巾木/腰見切り/天井見切り) だけで決める。
    # 窓の頭/下端/レールは x 範囲が短く 傾きが不安定なので VP には使わず、
    # 「V1 を通る」 前提で 自分の列での y だけを使う (= 高さの測定値として扱う)。
    V1 = vp_from_lines([Lfloor, Lchair, Lceil])
    V2 = vp_from_lines([Nfloor, Nchair])
    V3 = vp_from_lines(Vs)
    print(u'  [4] 消失点   V(y方向)=(%.0f, %.0f)  V(x方向)=(%.0f, %.0f)  V(鉛直)=(%.0f, %.0f)'
          % (V1[0], V1[1], V2[0], V2[1], V3[0], V3[1]))

    # V1 は「画像左に向かう = 部屋 y が減る」向き / V2 は「画像右 = 部屋 x が増える」/ V3 は「下 = z が減る」
    cam = Cam(V1, V2, V3, ('y', -1), ('x', +1), ('z', -1))
    cam.orth_report()

    # 入隅 (1055,107) の 床点/天井点 で カメラ位置
    cf = isect(Lfloor, Nfloor)
    Vcorner = (( V3[0] - cf[0]) / (V3[1] - cf[1]), cf[0] - (V3[0] - cf[0]) / (V3[1] - cf[1]) * cf[1], True)
    cc = isect(Lceil, Vcorner)
    print(u'    入隅 床点 = (%.1f, %.1f) / 天井点 = (%.1f, %.1f)' % (cf[0], cf[1], cc[0], cc[1]))
    cam.solve_C((1055.0, 107.0, 0.0), cf, (1055.0, 107.0, CH), cc)

    # ── E壁 (x=1055) 上の特徴を逆投影 ──
    def wall(u, v):
        return cam.on_plane(u, v, 0, 1055.0)

    def hgt(L, x):
        return wall(x, line_y_at(L, x))[2]

    def ypos(Lv, y_img):
        a, b, _ = Lv
        return wall(a * y_img + b, y_img)[1]

    print(u'  [5] 高さ (E壁面へ逆投影)')
    for lab, L, xs in ((u'天井見切り', Lceil, 600), (u'腰見切り縁', Lchair, 600),
                       (u'WIN-06 上端', Lhead1, 475), (u'WIN-07 上端', Lhead2, 658),
                       (u'WIN-06 下端(窓台)', Lsill1, 475), (u'WIN-07 下端(窓台)', Lsill2, 658),
                       (u'巾木下端', Lfloor, 600)):
        print(u'    %-18s 床から %7.1f cm' % (lab, hgt(L, xs)))

    print(u'  [6] E壁に沿った位置 (部屋 y)')
    names = [u'WIN-06 西端', u'WIN-06 東端', u'WIN-07 西端', u'WIN-07 東端']
    ys = [ypos(L, 590) for L in Vs]
    for nm, yy in zip(names, ys):
        print(u'    %-14s y = %7.1f  (N入隅から %6.1f cm)' % (nm, yy, yy - 107.0))
    print(u'    → WIN-06 幅 %.1f / 2窓の離隔 %.1f / WIN-07 幅 %.1f / 合計 %.1f'
          % (ys[1] - ys[0], ys[2] - ys[1], ys[3] - ys[2], ys[3] - ys[0]))

    # ── カーテンレール ──
    print(u'  [7] カーテンレール (E壁・小窓側)')
    camH = cam.C[2]
    D = 1055.0 - cam.C[0]
    for lab, L in ((u'上エッジ', Lrail), (u'下エッジ', Lrailb)):
        happ = [wall(x, line_y_at(L, x))[2] for x in (410, 500, 600, 700, 760)]
        print(u'    %s 壁面見かけ高さ: %s (cm)' % (lab, ' / '.join('%.1f' % h for h in happ)))
    hmid = 0.5 * (wall(600, line_y_at(Lrail, 600))[2] + wall(600, line_y_at(Lrailb, 600))[2])
    print(u'    → 見かけ中心 (壁面上) %.1f cm' % hmid)
    for off in (0.0, 5.5, 6.5, 7.5, 9.0):
        hr = camH + (hmid - camH) * (1.0 - off / D)
        print(u'      壁からの出 %4.1f cm と仮定 → レール中心 床から %5.1f cm' % (off, hr))
    # 見かけの太さ (= 実寸 × D/(D-o)) から レールの見かけ径
    t = (wall(600, line_y_at(Lrailb, 600))[2] - wall(600, line_y_at(Lrail, 600))[2])
    print(u'    見かけ上下幅 %.1f cm' % abs(t))
    # レール端 (u=383 は エアコンに隠れる直前 / u=775 が右端キャップ)
    for uu, nm in ((383.0, u'左端(エアコン陰から現れる位置)'), (776.0, u'右端キャップ')):
        p = wall(uu, line_y_at(Lrail, uu))
        y_app = p[1]
        y_true = cam.C[1] + (y_app - cam.C[1]) * (1.0 - 7.0 / D)
        print(u'    %s: 壁面見かけ y=%.1f → 出7cm 補正後 y=%.1f' % (nm, y_app, y_true))

    # ── エアコン A3 ──
    print(u'  [8] エアコン A3 (E壁・北端)')
    Lac_b = ph.hline(u'A3 下端(吹出口下)', 200, 370, 4, 500, 530, -1)
    Vac_l = ph.vline(u'A3 左(北)端', 430, 500, 1, 140, 168, 1)
    Vac_r = ph.vline(u'A3 右(南)端', 410, 495, 1, 370, 394, -1)
    DEP = 21.0                                    # 一般的な壁掛エアコンの奥行 ≒ 21cm
    for nm, Lv in ((u'北端', Vac_l), (u'南端', Vac_r)):
        a, b, _ = Lv
        uu = a * 460 + b
        p = wall(uu, 460.0)
        y_true = cam.C[1] + (p[1] - cam.C[1]) * (1.0 - DEP / D)
        print(u'    A3 %s: 壁面見かけ y=%.1f → 奥行%dcm 補正後 y=%.1f' % (nm, p[1], DEP, y_true))
    Lac_t = ph.hline(u'A3 上端(天面前縁)', 200, 330, 4, 0, 0, 1,
                     guess=(-0.155, 412.0, 8.0))
    hb_app = wall(270, line_y_at(Lac_b, 270))[2]
    ht_app = wall(270, line_y_at(Lac_t, 270))[2]
    fb = lambda h: camH + (h - camH) * (1.0 - DEP / D)
    print(u'    A3 下端 見かけ %.1f → 補正後 %.1f cm / 上端 見かけ %.1f → 補正後 %.1f cm  (高さ %.1f)'
          % (hb_app, fb(hb_app), ht_app, fb(ht_app), fb(ht_app) - fb(hb_app)))

    # ── ダウンライト (天井面へ逆投影) ──
    print(u' [8b] ダウンライト (天井 z=240 へ逆投影)')
    for i, (uu, vv) in enumerate(((112.0, 182.0), (216.0, 154.0), (345.0, 112.0))):
        p = cam.on_plane(uu, vv, 2, CH)
        print(u'    DL%d: 部屋 (x %.1f, y %.1f)  E壁から %.1f / N壁から %.1f'
              % (i + 1, p[0], p[1], 1055.0 - p[0], p[1] - 107.0))

    # ── 室内物干し (天井付け) ──
    print(u'  [9] 室内物干し (天井付け・E壁より手前)')
    top = cam.on_plane(134.0, 331.0, 2, CH)       # 天井プレート → 天井面 z=240
    print(u'    天井プレート: 部屋 (x %.1f, y %.1f)   E壁から %.1f / N壁から %.1f cm'
          % (top[0], top[1], 1055.0 - top[0], top[1] - 107.0))
    d = cam.ray(140.0, 510.0)                     # フック下端 (真下なので x,y は同じ)
    t = (top[0] - cam.C[0]) / d[0]
    zb = cam.C[2] + t * d[2]
    t2 = (top[1] - cam.C[1]) / d[1]
    print(u'    フック下端 床から %.1f cm (x基準) / %.1f cm (y基準)  → 下がり %.1f cm'
          % (zb, cam.C[2] + t2 * d[2], CH - zb))
    print(u'    ※ 対になる2台目の候補位置を投影して 写真上のどこに来るか:')
    for dx, dy in ((-100, 0), (-80, 0), (0, 100), (0, 80), (-60, 0)):
        q = cam.project((top[0] + dx, top[1] + dy, CH))
        print(u'      (x %+4d, y %+4d) → 画像 (%.0f, %.0f)%s'
              % (dx, dy, q[0], q[1], u'  ※画角外' if not (0 <= q[0] < ph.W and 0 <= q[1] < ph.H) else u''))
    return cam, ph


# ══════════════════════════════════════════════════════════════════ 大窓写真
def big(chair_h):
    print(u'\n════════ 大窓写真.jpg (洋室6.2帖 N壁 = バルコニー大窓 WIN-05) ════════')
    ph = Photo(u'大窓写真.jpg')
    print(u'  画像 %dx%d' % (ph.W, ph.H))

    print(u'  [1] N壁 (y=107) 上の水平線')
    Lfloor = ph.hline(u'巾木下端 (h=0)', 0, 0, 0, 1195, 1345, -1,
                      xs=list(range(12, 112, 3)) + list(range(846, 1046, 3)))
    Lchair = ph.hline(u'腰見切り 下端', 0, 0, 0, 880, 930, -1,
                      xs=list(range(12, 104, 2)) + list(range(890, 1048, 2)))
    # 開口上端 = 壁面(暗) → 頭リビール(明) の境。 傾きは V1(4848,815) を通る線として与える。
    Lhead = ph.hline(u'開口 上端 (壁→頭リビール)', 150, 780, 3, 0, 0, 1,
                     guess=(0.12054, 248.8, 10.0))
    # 開口下端 = 黒サッシ下框(暗) → 白い窓台(明) の境 (= 窓台の奥エッジ。手前エッジは視差で下がる)
    Lsill = ph.hline(u'開口 下端 (サッシ→窓台奥)', 150, 780, 3, 0, 0, 1,
                     guess=(-0.08545, 1216.5, 9.0))
    Lrail = ph.hline(u'カーテンレール 上エッジ', 180, 1000, 3, 0, 0, 1,
                     guess=(0.1287, 184.0, 9.0))
    Lrailb = ph.hline(u'カーテンレール 下エッジ', 180, 1000, 3, 0, 0, -1,
                      guess=(0.1287, 196.0, 9.0))

    print(u'  [3] 鉛直線 (帯を傾けて追跡)')
    Vs = [ph.vline(u'左 開口端(壁→黒枠)', 330, 900, 3, 0, 0, -1, guess=(0.0600, 104.0, 6.0)),
          ph.vline(u'左 黒枠→ガラス', 330, 900, 3, 0, 0, 1, guess=(0.0600, 136.0, 6.0)),
          ph.vline(u'右 ガラス→黒枠', 420, 1130, 3, 0, 0, -1, guess=(-0.0743, 828.0, 6.0)),
          ph.vline(u'右 黒枠→リビール', 420, 1130, 3, 0, 0, 1, guess=(-0.0800, 868.0, 7.0))]
    V1 = vp_from_lines([Lfloor, Lchair])
    V3 = vp_from_lines(Vs)
    print(u'  [4] 消失点   V(x方向)=(%.0f, %.0f)   V(鉛直)=(%.0f, %.0f)'
          % (V1[0], V1[1], V3[0], V3[1]))
    return wallmodel(ph, V1, V3, chair_h, Lfloor, Lchair, Lhead, Lsill, Lrail, Lrailb)


def wallmodel(ph, V1, V3, chair_h, Lfloor, Lchair, Lhead, Lsill, Lrail, Lrailb):
    u"""壁面2Dモデル: 水平は V1 を通る線 / 鉛直は V3 を極とする射影写像 (床0 と 腰見切り で拘束)"""
    XREF = 400.0
    yf = line_y_at(Lfloor, XREF)
    yc = line_y_at(Lchair, XREF)
    Yv = V3[1]
    # y(h) = (a h + yf)/(c h + 1) , a/c = Yv
    c = (yc - yf) / (chair_h * (Yv - yc))
    a = Yv * c

    def H(L):
        y = line_y_at(L, XREF)
        return (yf - y) / (c * y - a)

    print(u'  [5] 高さ (床=0 / 腰見切り=%.1f を拘束条件にした射影モデル)' % chair_h)
    print(u'    極 Yv = %.0f   (この値に対する感度も併記)' % Yv)
    res = {}
    for lab, L in ((u'WIN-05 開口 上端', Lhead), (u'WIN-05 窓台上面(開口下端)', Lsill),
                   (u'カーテンレール 上エッジ', Lrail), (u'カーテンレール 下エッジ', Lrailb)):
        res[lab] = H(L)
        alt = []
        for yv2 in (Yv * 0.75, Yv * 1.35):
            c2 = (yc - yf) / (chair_h * (yv2 - yc)); a2 = yv2 * c2
            y = line_y_at(L, XREF)
            alt.append((yf - y) / (c2 * y - a2))
        print(u'    %-26s 床から %7.1f cm   (Yv±: %.1f 〜 %.1f)'
              % (lab, res[lab], alt[0], alt[1]))
    hs = res[u'WIN-05 窓台上面(開口下端)']; hh = res[u'WIN-05 開口 上端']
    print(u'    → WIN-05 sill %.1f / 高さ %.1f / 上端 %.1f' % (hs, hh - hs, hh))
    hr = 0.5 * (res[u'カーテンレール 上エッジ'] + res[u'カーテンレール 下エッジ'])
    # カメラ高さ = 地平線の高さ
    yh = V1[1]
    camH = (yf - yh) / (c * yh - a)
    print(u'    カメラ高さ (地平線) %.1f cm / レール見かけ中心 %.1f cm' % (camH, hr))
    for D in (240.0, 270.0, 300.0):
        for off in (5.5, 6.5, 9.0):
            print(u'      壁からの距離 %3.0f・出 %3.1f → レール中心 %.1f'
                  % (D, off, camH + (hr - camH) * (1.0 - off / D)))
        break
    # ── N壁に沿った 1次元射影写像 (開口 848.5..1013.5 = 165 を基準) ──
    Lo_l = ph.vline(u'開口 左端(壁面)', 330, 900, 3, 0, 0, -1, guess=(0.0600, 104.0, 6.0))
    Lo_r = ph.vline(u'開口 右端(リビール→壁)', 420, 1130, 3, 0, 0, -1, guess=(-0.0850, 891.0, 8.0))
    xv, yv1 = V1
    ul = Lo_l[0] * 700 + Lo_l[1]
    ur = Lo_r[0] * 700 + Lo_r[1]
    Q = 165.0 / (1.0 / (ur - xv) - 1.0 / (ul - xv))

    def X(u):
        return 848.5 + Q * (1.0 / (u - xv) - 1.0 / (ul - xv))

    print(u'  [6] N壁に沿った位置 (開口幅165 を基準に較正)')
    print(u'    開口 左端 u=%.1f → x=%.1f / 右端 u=%.1f → x=%.1f (=1013.5 のはず)'
          % (ul, X(ul), ur, X(ur)))
    print(u'    画像左端 u=0 → x=%.1f / 画像右端 u=%.0f → x=%.1f  (E壁 1055 は u=%.0f 付近)'
          % (X(0.0), ph.W - 1, X(ph.W - 1.0),
             xv + 1.0 / (1.0 / (ul - xv) + (1055.0 - 848.5) / Q)))

    def Hxy(u, v):
        u"""画像点 (u,v) を N壁面へ逆投影した (x, h)"""
        y400 = yv1 + (v - yv1) * (XREF - xv) / (u - xv)
        return (X(u), (yf - y400) / (c * y400 - a))

    print(u'  [7b] レール端 と 房掛け候補')
    for uu, nm in ((52.0, u'レール 左端'), (1012.0, u'レール 右端')):
        vv = line_y_at(Lrail, uu)
        x_, h_ = Hxy(uu, vv)
        print(u'    %-12s 画像(%.0f,%.0f) → 壁面 x=%.1f h=%.1f' % (nm, uu, vv, x_, h_))
    for uu, vv, nm in ((126.0, 763.0, u'左 房掛け候補'), (842.0, 890.0, u'右 房掛け候補')):
        x_, h_ = Hxy(uu, vv)
        print(u'    %-12s 画像(%.0f,%.0f) → 壁面 x=%.1f h=%.1f' % (nm, uu, vv, x_, h_))
    return {'V1': V1, 'V3': V3, 'camH': camH, 'sill': hs, 'head': hh, 'rail': hr,
            'yf': yf, 'yc': yc, 'a': a, 'c': c, 'XREF': XREF,
            'Lo_l': Lo_l, 'Lo_r': Lo_r, 'Lfloor': Lfloor, 'Lchair': Lchair, 'chair_h': chair_h}

    # カメラ位置: N壁 (y=107) 上の 床線 と 腰見切り線 (h=chair_h) から 解く。
    # 同一鉛直線 (画像 x=60 付近) 上の2点を使う。
    ux = 60.0
    p_f = (ux, line_y_at(Lfloor, ux))
    # その鉛直線 (V3 へ向かう) と 腰見切り線 の交点
    Lvert = ((V3[0] - p_f[0]) / (V3[1] - p_f[1]),
             p_f[0] - (V3[0] - p_f[0]) / (V3[1] - p_f[1]) * p_f[1], True)
    p_c = isect(Lchair, Lvert)
    print(u'    基準鉛直線: 床点 (%.1f, %.1f) / 腰見切り点 (%.1f, %.1f)'
          % (p_f[0], p_f[1], p_c[0], p_c[1]))
    # x 位置は未知なので 仮に x=900 として解き、 あとで窓の位置から平行移動する
    cam.solve_C((900.0, 107.0, 0.0), p_f, (900.0, 107.0, chair_h), p_c)

    def wall(u, v):
        return cam.on_plane(u, v, 1, 107.0)

    print(u'  [5] 高さ (N壁面へ逆投影)')
    for lab, L, xx in ((u'巾木下端(検算=0)', Lfloor, 400), (u'腰見切り(検算=%.1f)' % chair_h, Lchair, 400),
                       (u'WIN-05 開口 上端', Lhead, 400), (u'WIN-05 窓台上面', Lsill, 400)):
        print(u'    %-22s 床から %7.1f cm' % (lab, wall(xx, line_y_at(L, xx))[2]))
    hh = wall(400, line_y_at(Lhead, 400))[2]
    hs = wall(400, line_y_at(Lsill, 400))[2]
    print(u'    → WIN-05 sill %.1f / 高さ %.1f / 上端 %.1f' % (hs, hh - hs, hh))

    print(u'  [6] N壁に沿った位置 (部屋 x / 仮原点)')
    xs = []
    for lab, Lv in zip((u'左 サッシ外端', u'中央 召し合わせ', u'右 サッシ外端', u'右 開口(壁面)端'), Vs):
        a, b, _ = Lv
        uu = a * 700 + b
        p = wall(uu, 700.0)
        xs.append(p[0])
        print(u'    %-16s x = %8.1f' % (lab, p[0]))
    print(u'    → 左サッシ外端→右開口端 = %.1f cm / 画像右端まで %.1f cm'
          % (xs[3] - xs[0], wall(1058.0, 700.0)[0] - xs[3]))

    print(u'  [7] カーテンレール (N壁・大窓側)')
    camH = cam.C[2]
    D = cam.C[1] - 107.0
    for lab, L in ((u'上エッジ', Lrail), (u'下エッジ', Lrailb)):
        happ = [wall(x, line_y_at(L, x))[2] for x in (200, 400, 600, 800, 950)]
        print(u'    %s 壁面見かけ高さ: %s' % (lab, ' / '.join('%.1f' % h for h in happ)))
    hmid = 0.5 * (wall(600, line_y_at(Lrail, 600))[2] + wall(600, line_y_at(Lrailb, 600))[2])
    print(u'    見かけ中心 %.1f cm  / 見かけ上下幅 %.1f cm'
          % (hmid, wall(600, line_y_at(Lrailb, 600))[2] - wall(600, line_y_at(Lrail, 600))[2]))
    for off in (0.0, 5.5, 6.5, 9.0):
        print(u'      壁からの出 %4.1f → レール中心 床から %.1f cm'
              % (off, camH + (hmid - camH) * (1.0 - off / D)))
    for uu, nm in ((56.0, u'左端'), (1012.0, u'右端')):
        p = wall(uu, line_y_at(Lrail, uu))
        print(u'    %s: 壁面見かけ x=%.1f → 出6.5補正後 %.1f'
              % (nm, p[0], cam.C[0] + (p[0] - cam.C[0]) * (1.0 - 6.5 / D)))

    print(u'  [8] 室内物干し (天井 z=240 へ逆投影)')
    for nm, uu, vv, hu, hv in ((u'左', 140.0, 76.0, 143.0, 272.0),
                               (u'右', 1032.0, 100.0, 1022.0, 330.0)):
        p = cam.on_plane(uu, vv, 2, CH)
        d = cam.ray(hu, hv)
        t = (p[1] - cam.C[1]) / d[1]
        zb = cam.C[2] + t * d[2]
        print(u'    %s: 天井 (x %.1f, y %.1f)  N壁から %.1f / フック下端 %.1f (下がり %.1f)'
              % (nm, p[0], p[1], p[1] - 107.0, zb, CH - zb))
    return cam


# ══════════════════════════════════════════════════════════════════ レンダ用カメラ諸元
def render_params(cam, W, H, label, name):
    u"""写真と同画角のレンダを作るための __noza の引数を出す。

    three.js は 主点がキャンバス中心にしか置けないので、 **主点を中心に持つ一回り大きい
    キャンバス** を描画し、 そのうち 写真に対応する矩形だけを切り出して比較する。
      A = max(px, W-px) / B = max(py, H-py)  → レンダは 2A × 2B (写真ピクセル単位)
      写真の (u,v) は レンダの (u - (px-A), v - (py-B)) に対応する。
    """
    A = max(cam.px, W - cam.px)
    B = max(cam.py, H - cam.py)
    fov = 2.0 * math.degrees(math.atan(B / cam.f))
    ox, oy = cam.px - A, cam.py - B
    d = cam.ray(cam.px, cam.py)                      # 主点方向 = カメラ光軸
    tgt = tuple(cam.C[i] + 400.0 * d[i] for i in range(3))
    print(u'\n──── %s: 同画角レンダの諸元 ────' % label)
    print(u'  レンダ キャンバス比 %.1f : %.1f  (= %.4f)   垂直画角 %.3f deg' % (2 * A, 2 * B, A / B, fov))
    print(u'  __noza.fov(%.3f);' % fov)
    print(u'  __noza.cam(%.2f, %.2f, %.2f, %.2f, %.2f, %.2f);'
          % (cam.C[0], cam.C[2], cam.C[1], tgt[0], tgt[2], tgt[1]))
    print(u'  ※ three.js は (x, 高さ, z=図面y) の順。 上は その並びに直してある。')
    print(u'  写真 %dx%d の左上は レンダ上の (%.1f, %.1f) / スケール s = 描画幅 / %.1f'
          % (W, H, -ox, -oy, 2 * A))
    return {'name': name, 'W': W, 'H': H, 'A': A, 'B': B, 'fov': fov, 'ox': ox, 'oy': oy,
            'cam': list(cam.C), 'tgt': list(tgt), 'f': cam.f, 'px': cam.px, 'py': cam.py,
            'ex': list(cam.ex), 'ey': list(cam.ey), 'ez': list(cam.ez)}


def big_camera(res):
    u"""大窓写真の 3D カメラを解く。

    2消失点 (V1=x方向 / V3=鉛直) しか無いので f が1自由度だけ余る。 そこで
      「開口幅が 165cm になる f」
    を二分法で解く (= 較正基準を 3Dモデル側にも一致させる)。 ロールは無しと見なし Px = V3x。
    """
    ph = Photo(u'大窓写真.jpg')
    V1, V3 = res['V1'], res['V3']
    Lo_l, Lo_r = res['Lo_l'], res['Lo_r']
    Lfloor, Lchair = res['Lfloor'], res['Lchair']
    chair_h = res['chair_h']

    def build(f):
        Px = V3[0]
        # (V1-P)·(V3-P) = -f²  かつ Px = V3x → (V1y-Py)(V3y-Py) = -f²
        # t = Py - V1y とおくと t(V3y - V1y - t) = f²
        L = V3[1] - V1[1]
        disc = L * L - 4.0 * f * f
        if disc < 0:
            return None
        t = (L - math.sqrt(disc)) / 2.0
        Py = V1[1] + t
        cam = Cam.__new__(Cam)
        cam.px, cam.py, cam.f, cam.f2 = Px, Py, f, f * f
        cam.axes = {}
        for V, e in ((V1, ('x', +1)), (V3, ('z', -1))):
            d = ((V[0] - Px) / f, (V[1] - Py) / f, 1.0)
            n = math.sqrt(sum(q * q for q in d))
            cam.axes[e[0]] = tuple(q / n * e[1] for q in d)
        ex, ez = cam.axes['x'], cam.axes['z']
        ey = (ez[1] * ex[2] - ez[2] * ex[1], ez[2] * ex[0] - ez[0] * ex[2], ez[0] * ex[1] - ez[1] * ex[0])
        # 部屋 +y (南) は カメラから見て 手前向き = z成分が負になる向きを選ぶ
        if ey[2] > 0:
            ey = tuple(-q for q in ey)
        cam.ex, cam.ey, cam.ez = ex, ey, ez
        cam.axes['y'] = ey
        # カメラ位置: 画像 x=60 の鉛直線上の 床点 と 腰見切り点 から
        ux = 60.0
        p_f = (ux, line_y_at(Lfloor, ux))
        a_ = (V3[0] - p_f[0]) / (V3[1] - p_f[1])
        Lvert = (a_, p_f[0] - a_ * p_f[1], True)
        p_c = isect(Lchair, Lvert)
        try:
            cam.solve_C((900.0, 107.0, 0.0), p_f, (900.0, 107.0, chair_h), p_c)
        except ZeroDivisionError:
            return None
        return cam

    def width_of(f):
        cam = build(f)
        if cam is None:
            return None
        ul = Lo_l[0] * 700 + Lo_l[1]
        ur = Lo_r[0] * 700 + Lo_r[1]
        pl = cam.on_plane(ul, 700.0, 1, 107.0)
        pr = cam.on_plane(ur, 700.0, 1, 107.0)
        return abs(pr[0] - pl[0])

    print(u'\n  [9] 大窓写真の 3Dカメラ — 「開口幅=165」 を満たす f を二分法で解く')
    import contextlib
    lo, hi = 400.0, (V3[1] - V1[1]) / 2.0 - 1.0
    buf = []
    for f in (420.0, 460.0, 500.0, 540.0, 570.0, 600.0, 700.0, 900.0, 1200.0, 1800.0):
        if f >= hi:
            continue
        with contextlib.redirect_stdout(io_null()):
            w = width_of(f)
        buf.append((f, w))
    for f, w in buf:
        print(u'    f=%6.0f → 開口幅 %s' % (f, ('%.1f' % w) if w else 'n/a'))
    # 単調なら二分法
    fa, fb = None, None
    for i in range(len(buf) - 1):
        if buf[i][1] and buf[i + 1][1] and (buf[i][1] - 165.0) * (buf[i + 1][1] - 165.0) < 0:
            fa, fb = buf[i][0], buf[i + 1][0]
            break
    if fa is None:
        print(u'    ⚠ 165 を挟む区間が見つからない → 大窓写真の同画角レンダは f=1250 の近似で作る')
        f = 1250.0
    else:
        for _ in range(60):
            fm = (fa + fb) / 2.0
            with contextlib.redirect_stdout(io_null()):
                w = width_of(fm)
            if (width_of_cached(buf, fa) - 165.0) * (w - 165.0) <= 0:
                fb = fm
            else:
                fa = fm
                buf.append((fa, w))
        f = (fa + fb) / 2.0
        print(u'    → f = %.1f px' % f)
    cam = build(f)
    # ★ゲージ合わせ: solve_C は 「画像 x=60 の鉛直線 = 部屋 x=900」 という仮の原点で解いているので、
    #   横位置は任意にずれている。 開口の西端が x=848.5 に来るように カメラを x 方向へ平行移動する。
    ul = Lo_l[0] * 700 + Lo_l[1]
    pl = cam.on_plane(ul, 700.0, 1, 107.0)
    cam.C = (cam.C[0] + (848.5 - pl[0]), cam.C[1], cam.C[2])
    ur = Lo_r[0] * 700 + Lo_r[1]
    print(u'    ゲージ合わせ後: 開口 西端 → x=%.2f (期待 848.5) / 東端 → x=%.2f (期待 1013.5)'
          % (cam.on_plane(ul, 700.0, 1, 107.0)[0], cam.on_plane(ur, 700.0, 1, 107.0)[0]))
    print(u'    カメラ = (x %.1f, y %.1f, 床上 %.1f)' % (cam.C[0], cam.C[1], cam.C[2]))
    return cam, ph


def width_of_cached(buf, f):
    for a, b in buf:
        if abs(a - f) < 1e-9:
            return b
    return None


class io_null(object):
    def write(self, *a):
        pass

    def flush(self):
        pass


if __name__ == '__main__':
    cam1, ph1 = small()
    p1 = render_params(cam1, ph1.W, ph1.H, u'小窓写真', u'小窓写真.jpg')
    res = big(90.6)
    cam2, ph2 = big_camera(res)
    if cam2 is not None:
        p2 = render_params(cam2, ph2.W, ph2.H, u'大窓写真', u'大窓写真.jpg')
    with io.open(os.path.join(HERE, '_v7_0_cams.json'), 'w', encoding='utf-8') as fp:
        fp.write(json.dumps({'small': p1, 'big': p2}, ensure_ascii=False, indent=1))
    print(u'\n→ %s に レンダ諸元を書き出しました' % os.path.join(HERE, '_v7_0_cams.json'))

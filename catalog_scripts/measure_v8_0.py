# -*- coding: utf-8 -*-
u"""v8.0 実測 — キッチン天板の長手方向を 写真38 から逆投影し、ROOM_DATA v6.10 と重ねて残差を出す。

■ 対象写真 (間取り図等/03_キッチン。EXIF orientation は exif_transpose で正立させてから読む)
    写真38 … 作業側 (東) から 天板を見下ろした 4000x2250。 天板の南端・シンク・コンロが1枚に入る。

■ 何を測るか
    天板は 1枚の平面。 その上の
      ・奥行方向 (部屋X) に平行な直線群  → 消失点 V_x
      ・長手方向 (部屋Y) に平行な直線群  → 消失点 V_y
    が取れれば、 天板平面上の任意の点の 長手座標が 1次元射影写像で読める。

    ★ V_x は **基準3本だけ** で決める:
        (a) 天板の南端        (b) コンロ 南端        (c) コンロ 北端
    ★ 長手のスケールは **基準2本だけ** で決める:
        天板 南端 = y388.5   /   コンロ 南端 = y282.5 (= 北壁208.5 + 実測15 + 実測59)
    ★ その上で **シンクの南リム・北リム** を測る。 これは スケール決定に使っていないので
      「間43 / シンク55 / 南端の余り8」 に対する 独立した検算になる。

■ 出力
    ・残差表 (cm)
    ・オーバーレイ画像 v8_0_overlay_photo38.png
        緑 = ROOM_DATA v6.10 が予測する境界 / 赤 = 写真から検出した境界
      → catalog_scripts\\ と Box\\…\\nozaROOM\\確認用切り出し\\ に保存

■ 使い方
    bash ~/.claude/scripts/run_py.sh catalog_scripts/measure_v8_0.py
"""
import glob
import os
import shutil

from PIL import Image, ImageOps, ImageDraw, ImageFont

BOXR = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                    u'野沢用', 'claude', 'nozaROOM')
DK = os.path.join(BOXR, u'間取り図等', u'03_キッチン')
OUTDIR = os.path.dirname(os.path.abspath(__file__))


def jpfont(sz):
    u"""日本語が出るフォント (無ければ既定フォント)"""
    for f in (r'C:WindowsFontsmeiryo.ttc', r'C:WindowsFontsYuGothM.ttc',
              r'C:WindowsFontsmsgothic.ttc'):
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, sz)
            except Exception:
                pass
    return ImageFont.load_default()
BOXOUT = os.path.join(BOXR, u'確認用切り出し')

# ROOM_DATA v6.10 のキッチン (既知として使うのは 天板の 180 / 208.5 / 388.5 と 実測 15・59 だけ)
Y_WALL, Y_SOUTH = 208.5, 388.5
STOVE_N, STOVE_S = 223.5, 282.5          # = 208.5+15, +59
SINK_N, SINK_S = 325.5, 380.5            # = 282.5+43, +55  ← これを検算する


class Photo(object):
    def __init__(self, num):
        g = glob.glob(os.path.join(DK, '*_%s.jpg' % num))
        self.im = ImageOps.exif_transpose(Image.open(g[0])).convert('RGB')
        self.px = self.im.load()
        self.W, self.H = self.im.size

    def lum(self, x, y):
        c = self.px[max(0, min(self.W - 1, int(x))), max(0, min(self.H - 1, int(y)))]
        return 0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]

    def vline(self, label, ys, slope, x_at_y0, half, sign):
        u"""縦エッジを 行ごとに サブピクセルで拾い x = a*y + b を最小二乗"""
        pts = []
        for y in ys:
            gc = x_at_y0 + slope * (y - ys[0])
            lo, hi = int(gc - half), int(gc + half)
            f = (lambda xx: sum(self.lum(xx + 2, y + d) - self.lum(xx - 2, y + d)
                                for d in (-1, 0, 1)) / 3.0 * sign)
            best = None
            for xx in range(lo + 2, hi - 2):
                s = f(xx)
                if best is None or s > best[1]:
                    best = (xx, s)
            if best is None:
                continue
            xb = best[0]
            a_, b_, c_ = f(xb - 1), f(xb), f(xb + 1)
            den = a_ - 2 * b_ + c_
            dx = 0.5 * (a_ - c_) / den if den else 0.0
            pts.append((xb + max(-1.0, min(1.0, dx)), float(y)))
        return _fit(label, pts, swap=True)

    def hline(self, label, xs, slope, y_at_x0, half, sign):
        pts = []
        for x in xs:
            gc = y_at_x0 + slope * (x - xs[0])
            lo, hi = int(gc - half), int(gc + half)
            f = (lambda yy: sum(self.lum(x + d, yy + 2) - self.lum(x + d, yy - 2)
                                for d in (-1, 0, 1)) / 3.0 * sign)
            best = None
            for yy in range(lo + 2, hi - 2):
                s = f(yy)
                if best is None or s > best[1]:
                    best = (yy, s)
            if best is None:
                continue
            yb = best[0]
            a_, b_, c_ = f(yb - 1), f(yb), f(yb + 1)
            den = a_ - 2 * b_ + c_
            dy = 0.5 * (a_ - c_) / den if den else 0.0
            pts.append((float(x), yb + max(-1.0, min(1.0, dy))))
        return _fit(label, pts, swap=False)


def _fit(label, pts, swap):
    a = b = rms = 0.0
    n = 0
    for _ in range(3):
        n = len(pts)
        if n < 3:
            break
        P = [(p[1], p[0]) for p in pts] if swap else [(p[0], p[1]) for p in pts]
        sx = sum(q[0] for q in P); sy = sum(q[1] for q in P)
        sxx = sum(q[0] ** 2 for q in P); sxy = sum(q[0] * q[1] for q in P)
        a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        b = (sy - a * sx) / n
        r = [abs(q[1] - (a * q[0] + b)) for q in P]
        rms = (sum(v * v for v in r) / n) ** 0.5
        pts = [p for p, rr in zip(pts, r) if rr < 2.5 * rms + 0.5]
    print(u'    %-22s %s  n=%3d  rms %.2f px'
          % (label, ('x = %+0.5f*y %+9.2f' % (a, b)) if swap
             else ('y = %+0.5f*x %+9.2f' % (a, b)), n, rms))
    return (a, b, swap)


def coef(L):
    a, b, sw = L
    return (1.0, -a, -b) if sw else (-a, 1.0, -b)


def isect(L1, L2):
    A1, B1, C1 = coef(L1); A2, B2, C2 = coef(L2)
    d = A1 * B2 - A2 * B1
    return ((B1 * C2 - B2 * C1) / d, (A2 * C1 - A1 * C2) / d)


def vp(lines, label):
    M = [[0.0, 0.0], [0.0, 0.0]]; r = [0.0, 0.0]
    for L in lines:
        A, B, C = coef(L)
        nn = (A * A + B * B) ** 0.5
        A, B, C = A / nn, B / nn, C / nn
        M[0][0] += A * A; M[0][1] += A * B; M[1][0] += A * B; M[1][1] += B * B
        r[0] -= A * C; r[1] -= B * C
    d = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    V = ((r[0] * M[1][1] - r[1] * M[0][1]) / d, (M[0][0] * r[1] - M[1][0] * r[0]) / d)
    res = []
    for L in lines:
        A, B, C = coef(L)
        nn = (A * A + B * B) ** 0.5
        res.append(abs(A * V[0] + B * V[1] + C) / nn)
    print(u'    → %s = (%.1f, %.1f)   各直線までの残差 %s px'
          % (label, V[0], V[1], ' / '.join('%.1f' % v for v in res)))
    return V


def line_through(P, Q):
    if abs(Q[0] - P[0]) >= abs(Q[1] - P[1]):
        a = (Q[1] - P[1]) / (Q[0] - P[0]); return (a, P[1] - a * P[0], False)
    a = (Q[0] - P[0]) / (Q[1] - P[1]); return (a, P[0] - a * P[1], True)


def main():
    print(u'\n════════ 写真38 (作業側=東から見下ろし) の 天板平面メトロロジー ════════')
    ph = Photo('38')
    print(u'  画像 %dx%d (EXIF 正立済み)' % (ph.W, ph.H))

    print(u'\n  ── 基準となる 奥行(X)方向の3直線 ──')
    #  天板の南端: 左が背景(明) / 右が天板(暗)。 y=380..470 の帯だけ画面内に残る
    l_cend = ph.vline(u'天板 南端', list(range(406, 474, 2)), -2.105, 1194.2 - 2.105 * 406, 26, -1)
    #  コンロ 南端: 左が天板(明) / 右が黒ガラス(暗) → 銀フレームの立ち上がりを + で拾う
    l_ss = ph.vline(u'コンロ 南端', list(range(400, 606, 4)), 0.45, 2262.0, 26, +1)
    #  コンロ 北端: 左が黒ガラス(暗) / 右が天板(明)
    l_sn = ph.vline(u'コンロ 北端', list(range(384, 476, 2)), 2.05, 3268.0, 26, +1)
    Vx = vp([l_cend, l_ss, l_sn], 'V_x')

    print(u'\n  ── 長手(Y)方向の2直線 (V_y 用) ──')
    l_front = ph.hline(u'天板 前縁(東) 上端', list(range(240, 3400, 24)), 0.0035, 654.0, 16, -1)
    l_back = ph.hline(u'天板 奥縁(西)', list(range(1560, 2060, 8)), 0.0, 280.0, 16, -1)
    Vy = vp([l_front, l_back], 'V_y')

    # ── 長手方向の 1次元射影写像 (天板 前縁の直線上で) ────────────────────
    #   前縁は天板平面上の直線なので、 V_y = その直線の無限遠点。
    #   既知2点 (天板南端 / コンロ南端) + 無限遠点 で 射影写像が確定する。
    P_cend = isect(l_front, l_cend)
    P_ss = isect(l_front, l_ss)
    t = (lambda P: P[0])
    t_inf = t(Vy)
    t1, v1 = t(P_cend), Y_SOUTH
    t2, v2 = t(P_ss), STOVE_S
    k1, k2 = t1 - t_inf, t2 - t_inf
    A = (v1 * k1 - v2 * k2) / (t1 - t2)
    B = v1 * k1 - A * t1
    Ymap = (lambda P: (A * t(P) + B) / (t(P) - t_inf))
    print(u'\n  ── 長手スケール (基準2点のみ) ──')
    print(u'    天板南端 x=%.1f → y%.1f  /  コンロ南端 x=%.1f → y%.1f  /  無限遠 x=%.0f'
          % (t1, v1, t2, v2, t_inf))

    # ── 測定対象 (スケール決定に使っていない = 独立検算) ─────────────────
    print(u'\n  ── 測定 (シンクのリム / コンロ北端) ──')
    l_sk_s = ph.vline(u'シンク 南リム', list(range(430, 566, 4)), -1.83, 287.0 + 1.83 * 70, 30, +1)
    l_sk_n = ph.vline(u'シンク 北リム', list(range(420, 586, 4)), -0.517, 1450.0 + 0.517 * 80, 30, +1)

    meas = [
        (u'コンロ 北端',   l_sn,   STOVE_N),
        (u'シンク 北リム', l_sk_n, SINK_N),
        (u'シンク 南リム', l_sk_s, SINK_S),
    ]
    print(u'\n  ── 残差 (写真から読んだ値 − ROOM_DATA v6.10) ──')
    print(u'    %-14s %10s %10s %10s' % (u'要素', u'写真[cm]', u'モデル[cm]', u'残差[cm]'))
    rows = []
    for nm, L, exp in meas:
        got = Ymap(isect(l_front, L))
        rows.append((nm, got, exp))
        print(u'    %-14s %10.1f %10.1f %+10.2f' % (nm, got, exp, got - exp))

    # 区間 (実測値そのものとの突合)
    y_sn, y_skn, y_sks = rows[0][1], rows[1][1], rows[2][1]
    print(u'\n  ── 区間で見る (ユーザー実測との突合) ──')
    seg = [
        (u'コンロ〜北壁',        y_sn - Y_WALL, 15.0),
        (u'コンロ 長手',         STOVE_S - y_sn, 59.0),
        (u'コンロ〜シンクの間',  y_skn - STOVE_S, 43.0),
        (u'シンク 長手',         y_sks - y_skn, 55.0),
        (u'南端の余り',          Y_SOUTH - y_sks, 8.0),
    ]
    tot = 0.0
    for nm, got, exp in seg:
        tot += got
        print(u'    %-18s %8.1f cm  [実測/割付 %4.1f]  残差 %+6.2f cm' % (nm, got, exp, got - exp))
    print(u'    %-18s %8.1f cm  [天板 180.0]        残差 %+6.2f cm' % (u'合計', tot, tot - 180.0))

    # ── オーバーレイ画像 ────────────────────────────────────────────────
    im = ph.im.copy()
    d = ImageDraw.Draw(im)

    def draw_at_y(yc, color, w):
        u"""長手座標 yc の 奥行方向の直線を 天板前縁の点と V_x を通る直線として描く"""
        # 前縁上の点 (Ymap の逆写像): y = (A t + B)/(t - t_inf) → t = (B + yc*t_inf)/(yc - A)
        tt = (B + yc * t_inf) / (yc - A)
        a, b, sw = l_front
        P = (tt, a * tt + b)
        dx_, dy_ = Vx[0] - P[0], Vx[1] - P[1]
        n = (dx_ ** 2 + dy_ ** 2) ** 0.5
        ux, uy = dx_ / n, dy_ / n
        d.line([(P[0] - ux * 260, P[1] - uy * 260), (P[0] + ux * 620, P[1] + uy * 620)],
               fill=color, width=w)

    for yc in (Y_SOUTH, SINK_S, SINK_N, STOVE_S, STOVE_N):        # モデル = 緑
        draw_at_y(yc, (0, 255, 90), 7)
    for nm, got, exp in rows:                                      # 検出 = 赤
        draw_at_y(got, (255, 40, 40), 4)
    fnt = jpfont(34)
    d.rectangle([24, 24, 2360, 210], fill=(0, 0, 0))
    d.text((40, 36), u'緑 = ROOM_DATA v6.10 (v8.0) が予測する境界', fill=(0, 255, 90), font=fnt)
    d.text((40, 84), u'赤 = 写真38 から検出した境界', fill=(255, 90, 90), font=fnt)
    d.text((40, 132), u'残差 ' + u' / '.join(u'%s %+.2fcm' % (n2, g - e) for n2, g, e in rows),
           fill=(255, 255, 255), font=fnt)
    p = os.path.join(OUTDIR, 'v8_0_overlay_photo38.png')
    im.save(p)
    os.makedirs(BOXOUT, exist_ok=True)
    shutil.copy2(p, os.path.join(BOXOUT, os.path.basename(p)))
    print(u'\n  オーバーレイ: %s (+ Box にコピー)' % p)
    worst = max(abs(g - e) for _, g, e in rows)
    print(u'\n════ 最大残差 %.2f cm ════' % worst)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

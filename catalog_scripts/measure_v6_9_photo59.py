# -*- coding: utf-8 -*-
u"""
v6.9 実測: 写真59 から 洋室4.8 南壁チェーン (CL東面 → 東壁 = 254cm) の内訳を逆投影で読む。

写真59 (間取り図等\\05_4.8帖\\..._59.jpg) は **南壁が SE入隅から CL東面まで丸ごと1枚に収まる
唯一の写真** で、 これ1枚で チェーンの全区間を1つの縮尺で読める。

手順
  1. 南壁上の水平線を2本フィット (見切り縁 / 床見切り) → 交点 = 水平方向の消失点 VP
     ・2本が独立に同じ yv を与えることで 相互検証になる。
  2. VP が分かれば 壁に沿った 1次元射影写像は 2点アンカーで決まる:
         X = P + Q/(u - v)          (u = 画像x, X = 室内x, v = VP の x)
     アンカー = チェーンの両端 (SE入隅 X=414.5 / CL東面 X=160.5)。 全長 254 だけを既知にする。
  3. 各特徴 (窓の開口端 / 入隅) を「行ごとのエッジ位置」→ 直線フィット で求め、 y=900 の行で評価。
     壁の水平線は 2000px 進んでも 40px しか下がらないので、 同一行で評価する誤差は 0.5px 未満。
  4. 出てきた区間長を ROOM_DATA と突き合わせる。
     窓幅 43 / 12.5 と 西側の壁 56 が再現されれば 写像は信用でき、
     残った 「2窓の離隔」 と 「東側の壁」 が 実測値として読める。

エッジの取り方
  ・窓の開口端 (壁 ↔ 開口/白リビール) は R-B (赤−青) が ベージュのクロスで +25 前後、
    ガラス/白リビールで マイナスになるので、 R-B = +12 の交差点を線形補間で取る。
  ・入隅 (SE / CL) は 陰影の段差なので 輝度の水平勾配のピークを放物線補間で取る。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/measure_v6_9_photo59.py
"""
import os

from PIL import Image, ImageOps

BOX = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM')
PHOTO = os.path.join(BOX, '間取り図等', '05_4.8帖', 'LINE_ALBUM_20260820 内覧_260820_59.jpg')

EVAL_ROW = 900          # 全特徴を評価する行
CHAIN_W, CHAIN_E = 160.5, 414.5     # CL東面 / 4.8帖 東壁 (= 全長 254 だけを既知として使う)

_im = ImageOps.exif_transpose(Image.open(PHOTO)).convert('RGB')
_px = _im.load()
W, H = _im.size


def rb(x, y):
    c = _px[x, y]
    return c[0] - c[2]


def lum(x, y):
    c = _px[x, y]
    return 0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def fit_vertical(pts):
    u"""x = a*y + b の最小二乗 (外れ値を1回除去)"""
    for _ in range(2):
        n = len(pts)
        sy = sum(q[1] for q in pts); sx = sum(q[0] for q in pts)
        syy = sum(q[1] * q[1] for q in pts); sxy = sum(q[0] * q[1] for q in pts)
        a = (n * sxy - sx * sy) / (n * syy - sy * sy)
        b = (sx - a * sy) / n
        rms = (sum((q[0] - (a * q[1] + b)) ** 2 for q in pts) / n) ** 0.5
        pts = [q for q in pts if abs(q[0] - (a * q[1] + b)) < 2.5 * rms + 1]
    return a, b, rms, len(pts)


def fit_horizontal(pts):
    u"""y = a*x + b の最小二乗 (外れ値を1回除去)"""
    for _ in range(2):
        n = len(pts)
        sx = sum(q[0] for q in pts); sy = sum(q[1] for q in pts)
        sxx = sum(q[0] * q[0] for q in pts); sxy = sum(q[0] * q[1] for q in pts)
        a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        b = (sy - a * sx) / n
        rms = (sum((q[1] - (a * q[0] + b)) ** 2 for q in pts) / n) ** 0.5
        pts = [q for q in pts if abs(q[1] - (a * q[0] + b)) < 2.5 * rms + 0.5]
    return a, b, rms, len(pts)


def edge_rb(label, ys, x0, x1, thr=12):
    u"""行ごとに R-B が thr を跨ぐ位置 (x0 → x1 の走査方向で最初の下降交差) を取り 直線フィット"""
    step = 1 if x1 > x0 else -1
    pts = []
    for y in ys:
        prev = None
        for x in range(x0, x1, step):
            v = (rb(x, y - 1) + rb(x, y) + rb(x, y + 1)) / 3.0
            if prev is not None and prev[1] > thr >= v:
                t = (thr - prev[1]) / (v - prev[1])
                pts.append((prev[0] + t * step, y))
                break
            prev = (x, v)
    a, b, rms, n = fit_vertical(pts)
    print(u'  %-10s x = %+.5f*y %+9.2f   rms %.2f px  n=%d   x@y%d = %.2f'
          % (label, a, b, rms, n, EVAL_ROW, a * EVAL_ROW + b))
    return a * EVAL_ROW + b


def edge_lum(label, ys, x0, x1, sign):
    u"""行ごとに 輝度の水平勾配ピーク (sign=+1 で明るくなる側) を取り 直線フィット"""
    pts = []
    for y in ys:
        best = None
        for x in range(x0, x1):
            s = sum(lum(x + 4, y + dy) - lum(x - 4, y + dy) for dy in (-6, -2, 2, 6)) * sign / 4.0
            if best is None or s > best[1]:
                best = (x, s)
        if best[1] > 1.0:
            pts.append((float(best[0]), y))
    a, b, rms, n = fit_vertical(pts)
    print(u'  %-10s x = %+.5f*y %+9.2f   rms %.2f px  n=%d   x@y%d = %.2f'
          % (label, a, b, rms, n, EVAL_ROW, a * EVAL_ROW + b))
    return a * EVAL_ROW + b


def hline(label, xs, y0, y1):
    u"""列ごとに 輝度の垂直勾配ピークを取り 水平線をフィット"""
    pts = []
    for x in xs:
        best = None
        for y in range(y0, y1):
            s = sum(lum(x + dx, y + 3) - lum(x + dx, y - 3) for dx in (-6, -2, 2, 6)) / 4.0
            if best is None or abs(s) > abs(best[1]):
                best = (y, s)
        if abs(best[1]) >= 3.0:      # 弱いピーク (床のフローリング目地など) は捨てる
            pts.append((x, float(best[0])))
    a, b, rms, n = fit_horizontal(pts)
    print(u'  %-10s y = %+.6f*x %+9.2f   rms %.2f px  n=%d' % (label, a, b, rms, n))
    return a, b


def main():
    print(u'写真59 %dx%d' % (W, H))

    print(u'\n[1] 南壁の水平線 → 水平方向の消失点')
    ca, cb = hline(u'見切り縁', [x for x in range(900, 1800, 10)] + [x for x in range(2550, 2900, 10)],
                   1380, 1500)
    fa, fb = hline(u'床見切り', [x for x in range(900, 3900, 10)], 2050, 2200)
    vx = (fb - cb) / (ca - fa)
    vy = ca * vx + cb
    print(u'  VP = (%.1f, %.1f)   ※ 見切り縁と床見切りが独立に同じ点を指すことが相互検証'
          % (vx, vy))

    print(u'\n[2] 特徴の縦線 (y=%d の行で評価)' % EVAL_ROW)
    ys = [y for y in range(520, 1050, 4)] + [y for y in range(1250, 1380, 4)]
    ys2 = [y for y in range(420, 1350, 3)]
    u_se = edge_lum(u'SE入隅', ys2, 700, 900, -1)
    u_w4e = edge_rb(u'WIN-04 東', ys, 1810, 1900)
    u_w4w = edge_rb(u'WIN-04 西', ys, 2050, 1940)
    u_w3e = edge_rb(u'WIN-03 東', ys, 2060, 2160)
    u_w3w = edge_rb(u'WIN-03 西', ys, 2600, 2450)
    u_cl = edge_lum(u'CL入隅', ys2, 2880, 3010, +1)

    print(u'\n[3] 1次元射影写像 X = P + Q/(u - v)  (アンカー = チェーン両端のみ)')
    s_e = 1.0 / (u_se - vx)
    s_w = 1.0 / (u_cl - vx)
    Q = (CHAIN_W - CHAIN_E) / (s_w - s_e)
    P = CHAIN_E - Q * s_e
    print(u'  v = %.1f / Q = %.5g / P = %.1f' % (vx, Q, P))

    def X(u):
        return P + Q / (u - vx)

    x_se, x_w4e, x_w4w = X(u_se), X(u_w4e), X(u_w4w)
    x_w3e, x_w3w, x_cl = X(u_w3e), X(u_w3w), X(u_cl)

    print(u'\n[4] 読み取り結果 (cm) ── ROOM_DATA v6.4 と比較')
    rows = [
        (u'東壁 → WIN-04 東端', x_se - x_w4e, 126.0, u'旧118 / ★ここが吸収先'),
        (u'WIN-04 幅', x_w4e - x_w4w, 12.5, u'est / 写真60 では 13.3'),
        (u'2窓の離隔 (小壁)', x_w4w - x_w3e, 16.5, u'旧24.5 (閉合の余り) / 写真60 では 16.5'),
        (u'WIN-03 幅', x_w3e - x_w3w, 43.0, u'写真60 では 42.8'),
        (u'WIN-03 西端 → CL東面', x_w3w - x_cl, 56.0, u'★不変 = 写像の検算'),
    ]
    tot = 0.0
    for lab, val, ref, note in rows:
        tot += val
        print(u'  %-22s 実測 %6.1f   データ %6.1f   差 %+5.1f   %s' % (lab, val, ref, val - ref, note))
    print(u'  %-22s 実測 %6.1f   データ %6.1f   (アンカーなので一致は自明)'
          % (u'合計', tot, CHAIN_E - CHAIN_W))
    print(u'\n  → 窓幅と 西側の壁 が ±1.6cm 以内で再現されるのに 「2窓の離隔」 だけが ▲8.4cm ずれる。')
    print(u'    離隔は元々 実測ではなく 閉合の余り (254-56-43-12.5-118) だったので、')
    print(u'    離隔 16.5 を採り 余る 8.0cm は 東側の壁 (118 → 126) が吸収する、が結論。')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
u"""
洗濯機パン 全高 / 洗濯水栓 高さ / 上部棚 高さ を 写真から推定した計算の 再現スクリプト (v6.6 の根拠)。

対象写真 (Box: nozaROOM/間取り図等/07_洗面・風呂場/):
  LINE_ALBUM_20260820 内覧_260820_42.jpg   … Sony SO-51D (Xperia 1 VI) 超広角 16mm相当 (EXIF FocalLength 2.68mm)
  LINE_ALBUM_20260820 内覧_260820_41.jpg   … 同 24mm相当 (EXIF 6.08mm)。検証の参考

手法 (単一視点メトロロジー):
  1. 写真42 で 洗濯機パン 天面の 4隅 を画素で拾う。パン外寸 64x64cm は ユーザー実測確定なので
     「既知の正方形」として使える。
  2. 天面4隅 + 手前(SW)/右(SE) の 垂直稜線の足元 (床との接点) の 計6点を観測値とし、
     未知数 = カメラ姿勢 (回転3 + 並進3) + パン全高 H の 7 個 を Levenberg-Marquardt で解く。
     f は EXIF の 16mm相当 から f_px ≒ 1778 (= 4000 * 16/36) を採用し、1700/1778/1850 で感度も見る。
  3. 得られた姿勢で 壁面 (部屋座標 y=18) へ逆投影し、JIS 1連プレート (コンセント No.13 の
     プレート = 120 x 70 mm) の 天地 を測る。これが 12.0cm になるべき所を 12.55cm と出したので
     スケール補正 k = 12.0/12.55 = 0.956 を全高さに適用する。
  4. 同じ逆投影で 洗濯水栓の最下端 / 棚ブラケット壁プレートの上端 (=棚板下端) の 床からの高さを出す。

結果 (このスクリプトの出力):
  パン全高 H          = 17.3cm (補正前) → 16.6cm (k適用)  → v6.6 は 16.5cm を採用 (est)
  洗濯水栓 最下端      = 136.7cm (補正前) → 130.7cm (k適用) → 天面から 114.1cm
                        ★ ユーザー実測「天面→蛇口 115cm」と ±1cm 一致 (相互検証OK)
                        → v6.6 は ユーザー実測を正として 天面16.5 + 115 = 床から 131.5cm を採用
  棚板 下端           = 195.3 / 194.6cm (補正前・ブラケット左右) → 186.7 / 186.1cm (k適用)
                        → v6.6 は 187cm を採用 (est)
  カメラ             = 部屋座標 (445, 232) / 床から 163cm … 引き戸の外 (キッチン通路) に立って
                        撮った状況と整合するので 解が物理的に妥当であることの傍証になる
  ⚠ コンセント No.13  = 中心 床から 約129cm と出た。ROOM_DATA の C-13 は h=110 (est) のままなので
                        いずれ再実測して是正したい (v6.6 のスコープ外)。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/estimate_washpan_v6_6.py
"""
import numpy as np

# ───────── 観測値 (写真42 の原寸 4000x2250 画素座標) ─────────
# パン天面 4隅 (部屋座標: NW=(533,18) NE=(597,18) SE=(597,82) SW=(533,82))
TOP = {'NW': (1425.8, 1831.3), 'NE': (1791.3, 1685.8), 'SE': (2084.2, 1863.3), 'SW': (1671.4, 2091.1)}
# 垂直稜線の足元 (床との接点)
BOT = {'SEb': (2077.5, 1957.5), 'SWb': (1666.1, 2242.0)}
# 壁面 (y=18) 上の計測点
WALL = {
    # コンセント No.13 プレート (JIS 1連 = 天地120mm)。x1612..1655 の列平均の輝度プロファイルで
    # 壁(≈120) → プレート(≈137) の立ち上がりが y=870、プレート → 影(≈76)/壁 の落ちが y=960.5。
    # ※ 影の帯 (961〜966) をプレートに含めると 5px 大きく読んでしまうので 960.5 を使う。
    'outlet_top': (1634, 870.0),
    'outlet_bot': (1634, 960.5),
    'faucet_center': (1708, 895),     # 洗濯水栓 フランジ中心
    'faucet_bottom': (1727, 937),     # 洗濯水栓 最下端 (吐水口)
    'bracketL_top': (1296, 455),      # 棚ブラケット (左) 壁プレート 上端 = 棚板 下端
    'bracketR_top': (1935, 535),      # 棚ブラケット (右) 同上
    'bracketL_bot': (1296, 702.5),
}
LOCAL = {'NW': (0, 0), 'NE': (64, 0), 'SE': (64, 64), 'SW': (0, 64)}
BOT_LOCAL = {'SEb': (64, 64), 'SWb': (0, 64)}
CX, CY = 2000.0, 1125.0          # 主点 (4000x2250 の中心)
PLATE_H = 12.0                   # JIS 1連プレート 天地 (mm120)


def rod(rv):
    th = np.linalg.norm(rv)
    if th < 1e-12:
        return np.eye(3)
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def lm(fun, x0, iters=200):
    x = np.array(x0, float)
    lam = 1e-3
    r = fun(x)
    c = r @ r
    for _ in range(iters):
        J = np.zeros((len(r), len(x)))
        for i in range(len(x)):
            d = max(1e-6, abs(x[i]) * 1e-6)
            xp = x.copy()
            xp[i] += d
            J[:, i] = (fun(xp) - r) / d
        A, g = J.T @ J, J.T @ r
        for _ in range(30):
            try:
                dx = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-12), -g)
            except np.linalg.LinAlgError:
                lam *= 10
                continue
            xn = x + dx
            rn = fun(xn)
            cn = rn @ rn
            if cn < c:
                x, r, c = xn, rn, cn
                lam = max(lam * 0.3, 1e-9)
                break
            lam *= 3
        else:
            break
    return x, c


def solve(f):
    def fun(p):
        R, t, H = rod(p[0:3]), p[3:6], p[6]
        res = []
        for k, (X, Y) in LOCAL.items():
            P = R @ np.array([X, Y, 0.0]) + t
            res += [f * P[0] / P[2] + CX - TOP[k][0], f * P[1] / P[2] + CY - TOP[k][1]]
        for k, (X, Y) in BOT_LOCAL.items():
            P = R @ np.array([X, Y, H]) + t          # z は下向き = 床側
            res += [f * P[0] / P[2] + CX - BOT[k][0], f * P[1] / P[2] + CY - BOT[k][1]]
        return np.array(res)
    best = None
    for seed in range(30):
        rng = np.random.default_rng(seed)
        x, c = lm(fun, np.concatenate([rng.normal(0, 1.0, 3), [0, 0, 200.0], [15.0]]))
        R, t = rod(x[0:3]), x[3:6]
        C = -R.T @ t
        if C[1] < 50 or C[2] > 0 or x[6] < 3:        # カメラは パンより南 かつ 天面より上
            continue
        if best is None or c < best[1]:
            best = (x, c)
    return best


def backproj_wall(px, py, R, t, f, H):
    u"""壁面 (パンローカル y=0 = 部屋座標 y=18) へ逆投影 → (部屋x, 床からの高さ)"""
    d = np.array([(px - CX) / f, (py - CY) / f, 1.0])
    C, dw = -R.T @ t, R.T @ d
    P = C + ((0.0 - C[1]) / dw[1]) * dw
    return 533 + P[0], H - P[2]


def main():
    for f in (1700.0, 1778.0, 1850.0):
        x, c = solve(f)
        R, t, H = rod(x[0:3]), x[3:6], x[6]
        C = -R.T @ t
        vals = {k: backproj_wall(v[0], v[1], R, t, f, H) for k, v in WALL.items()}
        plate = vals['outlet_top'][1] - vals['outlet_bot'][1]
        k = PLATE_H / plate
        print(u'── f_px = %.0f  (EXIF 16mm相当 → 4000*16/36 = 1778 が本命) ────────────' % f)
        print(u'   rms = %.2f px   カメラ = 部屋(%.0f, %.0f) 床から %.0f cm'
              % (np.sqrt(c / 12), 533 + C[0], 18 + C[1], H - C[2]))
        print(u'   パン全高 H          = %.2f cm  → k適用 %.2f cm' % (H, H * k))
        print(u'   JIS 1連プレート天地  = %.2f cm (真値 12.0) → スケール補正 k = %.3f' % (plate, k))
        for nm in ('faucet_bottom', 'faucet_center', 'bracketL_top', 'bracketR_top', 'outlet_top', 'outlet_bot'):
            xw, h = vals[nm]
            print(u'   %-14s 部屋x=%.0f  床から %.1f cm  → k適用 %.1f cm' % (nm, xw, h, h * k))
        print(u'   洗濯水栓 最下端 − パン天面 = %.1f cm  (ユーザー実測 115cm と突合)'
              % ((vals['faucet_bottom'][1] - H) * k))
        print('')


if __name__ == '__main__':
    main()

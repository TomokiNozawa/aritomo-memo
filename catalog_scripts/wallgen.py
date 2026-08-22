# -*- coding: utf-8 -*-
u"""ROOM_DATA.walls を 部屋ポリゴン + 開口 から 決定論的に再生成する。

出典: Box\\...\\nozaROOM\\room_data_scripts\\annotate_names_v6_1.py の build_walls() /
      attach_wall_features() を そのまま移植 (room.html buildWalls() と同一手順)。
      開口の壁面一致許容 tol だけ 呼び出し側から与える (room.html の OPEN_MATCH_TOL に対応)。
"""
import re

ROOM_CODE = {
    "ldk": "LDK", "west4_5": "R45", "west6_2": "R62", "west4_8": "R48",
    "corridor": "COR", "washroom": "WSH", "bathroom": "BTH", "toilet": "WC",
    "genkan": "GEN", "wic": "WIC", "balcony_main": "BLM", "balcony_ne": "BLN",
}
ROOM_SHORT = {
    "ldk": "LDK", "west4_5": u"4.5帖", "west6_2": u"6.2帖", "west4_8": u"4.8帖",
    "corridor": u"廊下", "washroom": u"洗面", "bathroom": u"浴室", "toilet": u"トイレ",
    "genkan": u"玄関", "wic": "WIC", "balcony_main": u"バルコニー南西", "balcony_ne": u"バルコニー北東",
}
DIR_JA = {"N": u"北", "S": u"南", "E": u"東", "W": u"西"}
MINOR_LEN = 15.0
NUM_JA = u"①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"

FIX_TYPE_JA = {
    "kitchen": u"キッチン", "sink": u"シンク", "stove": u"コンロ", "glass": u"ガラス",
    "rangehood": u"レンジフード", "duct": u"ダクト", "tile_wall": u"タイル壁", "panel": u"パネル",
    "stub_wall": u"仕切壁", "pocket_panel": u"戸袋パネル", "closet": u"収納", "counter": u"カウンター",
    "petbase": u"ペット小部屋", "wall_cabinet": u"吊戸棚", "shelf": u"棚", "monitor": u"モニター",
    "hook_rail": u"フックレール", "vent": u"換気口", "curtain_box": u"カーテンボックス",
    "bathtub": u"浴槽", "washstand": u"洗面台", "washer_pan": u"洗濯機パン", "faucet": u"水栓",
    "toilet": u"便器", "entrance": u"土間", "step": u"段差", "slide_zone": u"走行帯",
    "mirror": u"ミラー", "pillar": u"柱", "balcony": u"バルコニー",
}
SKIP_FEATURE_TYPES = {"balcony", "entrance", "step", "slide_zone", "curtain_box"}


def short_ja(label, fallback=u""):
    if not label:
        return fallback
    s = re.split(u"[（(]", str(label))[0]
    s = re.split(u"★", s)[0]
    s = re.sub(r"\s+", " ", s).strip(u" 　/・-")
    return s or fallback


def point_in_poly(pt, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        if ((yi > pt[1]) != (yj > pt[1])) and pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def opening_range(o):
    oh = abs(o["wallFrom"][1] - o["wallTo"][1]) < 0.01
    return {
        "horiz": oh,
        "c": o["wallFrom"][1] if oh else o["wallFrom"][0],
        "a": min(o["wallFrom"][0], o["wallTo"][0]) if oh else min(o["wallFrom"][1], o["wallTo"][1]),
        "b": max(o["wallFrom"][0], o["wallTo"][0]) if oh else max(o["wallFrom"][1], o["wallTo"][1]),
    }


def touches_building(rooms, horiz, c, a, b):
    for r in rooms:
        if r["key"].startswith("balcony"):
            continue
        poly = r["poly"]
        for i in range(len(poly)):
            q1, q2 = poly[i], poly[(i + 1) % len(poly)]
            qh = abs(q1[1] - q2[1]) < 0.01
            if qh != horiz:
                continue
            qc = q1[1] if qh else q1[0]
            if abs(qc - c) > 25:
                continue
            qa = min(q1[0], q2[0]) if qh else min(q1[1], q2[1])
            qb = max(q1[0], q2[0]) if qh else max(q1[1], q2[1])
            if min(qb, b) - max(qa, a) > 10:
                return True
    return False


def _fmt(v):
    v = float(v)
    return ("%g" % v) if v != int(v) else ("%.1f" % v)


def build_walls(data, tol=12.0):
    rooms, openings = data["rooms"], data["openings"]
    ch = data["ceilingH"]
    raw = []
    for room in rooms:
        is_bal = room["key"].startswith("balcony")
        H = 110 if is_bal else ch
        poly = room["poly"]
        n = len(poly)
        for i in range(n):
            p1, p2 = poly[i], poly[(i + 1) % n]
            horiz = abs(p1[1] - p2[1]) < 0.01
            c = p1[1] if horiz else p1[0]
            a = min(p1[0], p2[0]) if horiz else min(p1[1], p2[1])
            b = max(p1[0], p2[0]) if horiz else max(p1[1], p2[1])
            if b - a < 0.5:
                continue
            probe = [(a + b) / 2, c - 2] if horiz else [c - 2, (a + b) / 2]
            in_neg = point_in_poly(probe, poly)
            if is_bal and touches_building(rooms, horiz, c, a, b):
                continue
            out_sign = 1 if in_neg else -1
            direction = ("S" if in_neg else "N") if horiz else ("E" if in_neg else "W")
            ops = []
            for o in openings:
                r0 = opening_range(o)
                if r0["horiz"] != horiz or abs(r0["c"] - c) > tol:
                    continue
                if min(r0["b"], b) - max(r0["a"], a) <= 2:
                    continue
                ops.append({"o": o, "s": max(r0["a"], a), "e": min(r0["b"], b)})
            ops.sort(key=lambda x: x["s"])
            segs, cur = [], a
            for x in ops:
                if x["s"] > cur:
                    segs.append((cur, x["s"]))
                cur = max(cur, x["e"])
            if cur < b:
                segs.append((cur, b))
            for (s, e) in segs:
                if e - s < 0.5:
                    continue
                raw.append({"room": room["key"], "dir": direction, "horiz": horiz,
                            "c": round(c, 3), "s": round(s, 3), "e": round(e, 3),
                            "outSign": out_sign, "h": H, "isBal": is_bal})
    walls = []
    room_name = dict((r["key"], r["name"]) for r in rooms)
    by_key = {}
    for w in raw:
        by_key.setdefault((w["room"], w["dir"]), []).append(w)
    for (rk, d), lst in by_key.items():
        lst.sort(key=lambda w: (w["s"], w["c"]))
        code = ROOM_CODE.get(rk, rk.upper()[:3])
        for idx, w in enumerate(lst, 1):
            w["seq"] = idx
            w["total"] = len(lst)
            w["id"] = u"W-%s-%s%d" % (code, d, idx)
    for w in raw:
        length = round(w["e"] - w["s"], 2)
        axis = "x" if w["horiz"] else "y"
        cross = "y" if w["horiz"] else "x"
        rn = ROOM_SHORT.get(w["room"], short_ja(room_name.get(w["room"], w["room"])))
        marker = NUM_JA[w["seq"] - 1] if w["seq"] <= len(NUM_JA) else str(w["seq"])
        kind = u" " + DIR_JA[w["dir"]] + u"手すり" if w["isBal"] else DIR_JA[w["dir"]] + u"壁"
        walls.append({
            "id": w["id"], "name": u"%s%s%s" % (rn, kind, marker), "room": w["room"], "dir": w["dir"],
            "horiz": w["horiz"], "c": w["c"], "from": w["s"], "to": w["e"],
            "length": length, "height": w["h"], "outSign": w["outSign"],
            "where": u"%s%s〜%s (%s%s)" % (axis, _fmt(w["s"]), _fmt(w["e"]), cross, _fmt(w["c"])),
            "seq": w["seq"], "of": w["total"], "minor": length < MINOR_LEN,
        })
    order = dict((r["key"], i) for i, r in enumerate(rooms))
    dorder = {"N": 0, "E": 1, "S": 2, "W": 3}
    walls.sort(key=lambda w: (order.get(w["room"], 99), dorder[w["dir"]], w["seq"]))
    return walls


def compact_fix_name(f):
    nm = f.get("shortLabel")
    if nm:
        return nm
    lab = short_ja(f.get("label"), u"")
    if "=" in lab:
        tail = lab.split("=")[-1].strip()
        if 0 < len(tail) <= 12 and tail.endswith(u"壁"):
            return tail
    if len(lab) <= 10:
        return lab or FIX_TYPE_JA.get(f.get("type"), f.get("type"))
    return FIX_TYPE_JA.get(f.get("type")) or (lab[:10] + u"…")


def attach_wall_features(walls, fixtures):
    for w in walls:
        hits = []
        for f in fixtures:
            if f.get("room") != w["room"] or not f.get("rect"):
                continue
            if f.get("type") in SKIP_FEATURE_TYPES:
                continue
            x, y, dx, dy = f["rect"]
            if w["horiz"]:
                fc0, fc1, fa0, fa1 = y, y + dy, x, x + dx
            else:
                fc0, fc1, fa0, fa1 = x, x + dx, y, y + dy
            if min(abs(fc0 - w["c"]), abs(fc1 - w["c"])) > 14:
                continue
            ov = min(fa1, w["to"]) - max(fa0, w["from"])
            if ov < 20:
                continue
            nm = compact_fix_name(f)
            if nm and nm not in [h[0] for h in hits]:
                hits.append((nm, ov))
        if hits:
            hits.sort(key=lambda h: -h[1])
            w["feature"] = u" / ".join(h[0] for h in hits[:4])
            w["name"] = w["name"] + u"（" + hits[0][0] + u"）"
    return walls


def regen(data, tol=12.0):
    return attach_wall_features(build_walls(data, tol), data["fixtures"])

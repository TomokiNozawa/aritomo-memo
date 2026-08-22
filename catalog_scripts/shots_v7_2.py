# -*- coding: utf-8 -*-
u"""★v7.2 検証ショット — F-16 削除後の白壁 / C-06 の新位置 / PS・DPS・MB の並び

  00  LDK 南壁 正対 (x350..560 の帯) … 旧ペット小部屋の位置が **ただの白壁** か
  01  同上 やや斜め … 穴・残パネルが無いか (奥行方向)
  02  LDK 南東を真上から … C-06 / 仕切壁61 / シューズBOX の位置関係
  03  玄関まわりを真上から … PS / DPS / MB が重ならず図面どおり並ぶか
  04  before (git stash 前の room.html) と比較するための 同画角 … 手動比較用

出力: 確認用切り出し\\v7_2_check_*.jpg
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/shots_v7_2.py
前提: catalog_scripts/serve_room.py が :8712 で稼働
"""
import base64
import io
import json
import os

from playwright.sync_api import sync_playwright

URL = "http://localhost:8712/room.html?debug=1"
OUT = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                   '野沢用', 'claude', 'nozaROOM', '確認用切り出し')

# (tag, room, fov, campos + target)
SHOTS = [
    # 旧 F-16 (x438..513) を正面から。 南壁 y=553.5 の北 220cm から見る
    ('00_ldk_south_wall_front', 'ldk', 78, (475.5, 55, 330.0, 475.5, 55, 553.5)),
    # 斜めから (穴・残パネルの有無)
    ('01_ldk_south_wall_oblique', 'ldk', 60, (300.0, 150, 300.0, 500.0, 70, 553.5)),
    # LDK 南東を真上から (C-06 / 仕切壁61 / シューズBOX)
    ('02_ldk_se_top', 'ldk', 5.5, (490.0, 4200, 500.0, 490.0, 0, 499.5)),
    # 玄関まわりを真上から (PS / DPS / MB)
    ('03_genkan_band_top', 'genkan', 4.2, (498.0, 4200, 608.0, 498.0, 0, 607.5)),
]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 940})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.goto(URL)
        pg.wait_for_function("window.__noza && window.__noza.state", timeout=30000)
        pg.wait_for_timeout(900)

        def js(code):
            return pg.evaluate("(function(){" + code + "})()")

        # 配置済みアイテムは 壁の見え方の邪魔になるので全部どける
        for k in js("return Object.keys(__noza.state().items);"):
            js("__noza.sel('%s'); window.deleteItem();" % k)
            pg.wait_for_timeout(80)
            js("const b=document.getElementById('cmOk'); if(b) b.click();")
            pg.wait_for_timeout(80)
        js("__noza.sel(null);")

        for tag, room, fov, cam in SHOTS:
            js("switchRoom('%s');" % room)
            pg.wait_for_timeout(420)
            js("__noza.clearRulers();")
            if tag.startswith('02'):
                # 旧 F-16 の東西端 (赤) と C-06 の x (緑)。 真上から見るので 高さ 3cm の床ラインにする
                js("__noza.ruler('x',438,0xff3b30,0.8,3);__noza.ruler('x',513,0xff3b30,0.8,3);"
                   "__noza.ruler('x',475.5,0x00ff5a,0.8,3);")
            if tag.startswith('03'):
                # PS(緑) / DPS(青) / 玄関西壁 内法555(赤)
                js("__noza.ruler('x',443.5,0x00ff5a,0.8,3);__noza.ruler('x',493,0x00ff5a,0.8,3);"
                   "__noza.ruler('x',500,0x2196f3,0.8,3);__noza.ruler('x',545,0x2196f3,0.8,3);"
                   "__noza.ruler('x',555,0xff3b30,0.8,3);")
            pg.evaluate("window.__noza.fov(%s)" % fov)
            pg.evaluate("window.__noza.cam(%s)" % ",".join(str(v) for v in cam))
            pg.wait_for_timeout(400)
            url = pg.evaluate("window.__noza.shot(1250)")
            path = os.path.join(OUT, "v7_2_check_%s.jpg" % tag)
            with io.open(path, "wb") as f:
                f.write(base64.b64decode(url.split(",", 1)[1]))
            print("  shot %-28s -> %s (%d KB)" % (tag, os.path.basename(path),
                                                  os.path.getsize(path) // 1024))
        js("__noza.clearRulers();")

        rd = pg.evaluate("JSON.stringify({v:ROOM_DATA.meta.version,"
                         "n:ROOM_DATA.fixtures.length,"
                         "pet:ROOM_DATA.fixtures.filter(f=>f.type==='petbase').length,"
                         "c6:ROOM_DATA.outlets.find(o=>o.id==='C-06').pos})")
        print('  runtime ROOM_DATA:', rd)
        print('  console errors:', errs if errs else 'なし')
        br.close()
        return 1 if errs else 0


if __name__ == '__main__':
    raise SystemExit(main())

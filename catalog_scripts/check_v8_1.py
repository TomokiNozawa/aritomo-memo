# -*- coding: utf-8 -*-
u"""★v8.1 検証 — ニトリ 収納付きベッド (アザン3 / 2050630) 追加 + ベッド描画のデータ駆動化

  ① 機械検証: ROOM_DATA 不変 (v6.10) / CATALOG_SEED v2.8・35商品 / 新商品のフィールド
  ② BED_MODELS: 4エントリ / bedModelOf の振り分け / 公式サイズ図の寸法チェーンが閉じるか
  ③ 3D: 宮 (棚+LED+2口コンセント) / 床下引き出し2杯が drawers レジストリに載る /
     引き出しを開くと 前方の残り幅が出る / 左右付け替えが効く
  ④ UI: 家具シートに 寸法サマリー・据付必要すきま・引き出しの向きセグメントが出る
  ⑤ 6.2帖への収まり: 実際に配置して 窓・引き戸・エアコン・レール・物干し・WIC扉 との
     クリアランスと、 引き出しを引く余地 (左右どちら側か) を cm で出す
  ⑥ スクショ: 正面 / 斜め / 引き出しオープン / ヘッドボード寄り / 部屋俯瞰 /
     モバイル375x812 / Aerus との並べ比較

出力: catalog_scripts\\v8_1_check_*.png + Box\\…\\nozaROOM\\確認用切り出し\\
実行: bash ~/.claude/scripts/run_py.sh catalog_scripts/check_v8_1.py
前提: python -m http.server 8777 が ~/aritomo-memo で稼働
⚠カメラは部屋ポリゴンの内側に (6.2帖 = x800..1055 / y107..418 + 南のアルコーブ x800..872 y418..553.5)
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/room.html?debug=1"
HERE = os.path.dirname(os.path.abspath(__file__))
BOXR = os.path.join(os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
                    u'野沢用', 'claude', 'nozaROOM')
BOX = os.path.join(BOXR, u'確認用切り出し')

# 6.2帖 (west6_2) の内寸
RX0, RX1 = 800.0, 1055.0        # 西内面 / 東内面   (255)
RY0, RY1 = 107.0, 418.0         # 北内面 / 南内面   (311)

# ★提案する配置: ヘッドボードを東壁 (x1055) に付け、 頭↔足 を東西に取る (rotY=90)
BED_W, BED_D = 97.0, 211.0
BX = RX1 - BED_D / 2            # 949.5  (x 844.0 .. 1055.0)
BZ = 288.5                      # 幅97 が y240.0 .. y337.0
BROT = 90

fails = []
shots = []


def jpfont(sz):
    for f in (r'C:\Windows\Fonts\meiryo.ttc', r'C:\Windows\Fonts\YuGothM.ttc',
              r'C:\Windows\Fonts\msgothic.ttc'):
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def chk(cond, label, got=None):
    print(u'  [%s] %s%s' % ('OK  ' if cond else 'FAIL', label,
                            '' if got is None else (u'  -> %s' % (got,))))
    if not cond:
        fails.append(label)


def side_by_side(tag, a_path, b_path, note):
    a = Image.open(a_path).convert('RGB')
    b = Image.open(b_path).convert('RGB')
    H = 700
    a = a.resize((int(a.width * H / a.height), H), Image.LANCZOS)
    b = b.resize((int(b.width * H / b.height), H), Image.LANCZOS)
    out = Image.new('RGB', (a.width + b.width + 12, H + 40), (20, 20, 24))
    out.paste(a, (0, 40))
    out.paste(b, (a.width + 12, 40))
    ImageDraw.Draw(out).text((8, 10), note, fill=(235, 235, 240), font=jpfont(19))
    p = os.path.join(HERE, 'v8_1_check_%s.png' % tag)
    out.save(p)
    shots.append(p)
    print(u'  cmp  %-26s -> %s (%d KB)' % (tag, os.path.basename(p), os.path.getsize(p) // 1024))


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
            path = os.path.join(HERE, "v8_1_check_%s.png" % tag)
            pg.screenshot(path=path)
            shots.append(path)
            print(u'  shot %-26s -> %s (%d KB)' % (tag, os.path.basename(path),
                                                   os.path.getsize(path) // 1024))
            return path

        def cam(px, py, pz, tx, ty, tz, wait=1100):
            mjs("__noza.cam(%f,%f,%f,%f,%f,%f); return 1;" % (px, py, pz, tx, ty, tz))
            pg.wait_for_timeout(wait)

        mjs("switchRoom('east62'); return 1;")
        pg.wait_for_timeout(500)
        pg.add_style_tag(content="#vpHint{display:none !important;}")

        # ══════════════ ① データ ══════════════
        print(u'\n■ ① データ')
        meta = mjs("return {v: R.meta.version, nf: R.fixtures.length,"
                   " cs: CATALOG_SEED.version, n: CATALOG_SEED.items.length};")
        chk(meta['v'] == '6.10', u'① ROOM_DATA は v6.10 のまま (触っていない)', meta['v'])
        chk(meta['nf'] == 53, u'① fixtures 53件のまま', meta['nf'])
        chk(meta['cs'] == '2.8', u'① CATALOG_SEED v2.8', meta['cs'])
        chk(meta['n'] == 35, u'① 商品 35件 (34 + アザン3)', meta['n'])
        beds = mjs("return __noza.catFull().filter(function(c){return c.type==='bed';});")
        chk(len(beds) == 4, u'① ベッドは4件 (Aerus S/SS/D + アザン3)', len(beds))
        chk(len([b for b in beds if 'Aerus' in b['name']]) == 3,
            u'① 既存の RASIK Aerus 3種は削除されていない')
        AZ = ([b for b in beds if u'アザン' in b['name']] or [None])[0]
        chk(AZ is not None, u'① アザン3 が1件ある')
        if AZ:
            print(u'    %s' % AZ['model'])
            print(u'    %s × %s × %s / room=%s / color=%s' % (AZ['w'], AZ['d'], AZ['h'], AZ['room'], AZ['color']))
            chk([AZ['w'], AZ['d'], AZ['h']] == [97, 211, 85], u'① 外形 97 × 211 × 85 (公式)')
            chk(AZ['room'] == 'east62', u'① 配置先は east62 (洋室6.2帖)', AZ['room'])
            chk(AZ['memo'] == '', u'① memo は空 (ユーザーの自由入力欄)', repr(AZ['memo']))
            chk('2050630' in (AZ['specNote'] or ''), u'① specNote に商品コード 2050630')
            chk('2050620' in (AZ['specNote'] or ''), u'① specNote に 2050620 との違いを記載')
            cat = mjs("return __noza.run('1') && (function(){var c=Object.keys(catalogData)"
                      ".map(function(k){return catalogData[k];}).filter(function(q){return /アザン/.test(q.name);})[0];"
                      " return {colors:c.colors, install:c.install, floorH:c.floorH};})();")
            chk(len(cat['colors']) == 4, u'① カラースウォッチ 4色 (公式4色)', len(cat['colors']))
            for c in cat['colors']:
                print(u'      %-34s %s' % (c['name'], c['hex']))
            chk(cat['install']['doorSide'] == 'both' and cat['install']['doorSideCm'] == 47,
                u'① install: 左右どちらにも取付可・張り出し47cm', cat['install'])
            chk(cat['floorH'] == 25, u'① 床板高さ 25cm (公式)', cat['floorH'])

        # ══════════════ ② BED_MODELS ══════════════
        print(u'\n■ ② BED_MODELS (データ駆動)')
        bm = mjs("return BED_MODELS.map(function(m){ return {label:m.label,"
                 " test: m.test? String(m.test):null, shelf: m.shelf? m.shelf.kind : null,"
                 " light: !!m.light, outlet: m.outlet? m.outlet.caps : 0,"
                 " storage: m.storage||null, floorH: m.floorH, deck: m.deck,"
                 " mattress: m.mattress? m.mattress.length : 0 }; });")
        chk(len(bm) == 4, u'② BED_MODELS は 4エントリ (Aerus / アザン3 / 宮棚汎用 / 既定)', len(bm))
        for m in bm:
            print(u'    %-58s test=%-12s 宮=%-6s 照明%-5s ｺﾝｾﾝﾄ%d 収納%-5s 床面高%s すのこ%d'
                  % (m['label'][:56], (m['test'] or '(既定)')[:12], m['shelf'], m['light'],
                     m['outlet'], bool(m['storage']), m['floorH']['def'], m['deck']['slats']))
        pick = mjs("var az=__noza.catFull().filter(function(c){return /アザン/.test(c.name);})[0];"
                   "return {aerus: bedModelOf('Aerus すのこベッド シングル ホワイト').label,"
                   " azan: bedModelOf(az.name + ' ' + az.specNote).label,"
                   " miya: bedModelOf('自作 宮棚ベッド').label,"
                   " free: bedModelOf('自作ベッド').label};")
        chk(u'Aerus' in pick['aerus'], u'② bedModelOf: Aerus → Aerus エントリ', pick['aerus'][:40])
        chk(u'アザン' in pick['azan'], u'② bedModelOf: アザン3 → 収納ベッド エントリ', pick['azan'][:40])
        chk(u'宮棚付き (汎用)' in pick['miya'], u'② bedModelOf: 宮棚 → 汎用宮棚エントリ', pick['miya'])
        chk(pick['free'] == u'ベッドフレーム (汎用)', u'② bedModelOf: 未知のベッド → 既定エントリ', pick['free'])

        print(u'\n■ ② 公式サイズ図の寸法チェーンが閉じるか')
        az = [m for m in bm if u'アザン' in m['label']][0]
        head, foot = 14.0, az['deck']['foot']
        inner = 211.0 - head - foot
        st = az['storage']
        fw = (inner - st['gap'] * (st['count'] + 1)) / st['count']
        print(u'    奥行: ヘッドボード %.1f + 床板(内寸) %.1f + フット %.1f = %.1f (公式 211)'
              % (head, inner, foot, head + inner + foot))
        print(u'    引出し割付: あき%.1f + 前板%.1f + あき%.1f + 前板%.1f + あき%.1f = %.1f'
              % (st['gap'], fw, st['gap'], fw, st['gap'], inner))
        chk(abs(inner - 196.5) < 0.01, u'② 床板(内寸)長さ = 196.5 (公式サイズ図)', inner)
        chk(abs(fw - 96.0) < 0.01, u'② 引き出し前板の幅 = 96 (公式サイズ図 引出し外寸長さ96)', fw)
        chk(st['depth'] == 47, u'② 引き出しの張り出し = 47 (公式 引出し奥行)', st['depth'])
        chk(st['count'] == 2, u'② 引き出し 2杯 (公式)', st['count'])
        chk(az['deck']['slats'] == 0, u'② 床板は一枚板 (公式画像 ww_09/ww_10 で確認)')
        chk(az['floorH']['def'] == 25, u'② 床板高さ 25 (公式)')

        # ══════════════ ③ 3D モデル ══════════════
        print(u'\n■ ③ 3D モデル')
        cid = mjs("return Object.keys(catalogData).filter(function(k){"
                  " return /アザン/.test(catalogData[k].name); })[0];")
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(cid))
        pg.wait_for_timeout(600)
        iid = mjs("var ks=Object.keys(workItems); return ks[ks.length-1];")
        # 提案配置へ移動
        mjs("var it=workItems[%s]; it.x=%f; it.z=%f; it.rotY=%d;"
            " syncItemMesh(furnMeshes[%s], it); deselect(); return 1;"
            % (json.dumps(iid), BX, BZ, BROT, json.dumps(iid)))
        pg.wait_for_timeout(600)
        nmesh = mjs("var n=0; furnMeshes[%s].traverse(function(o){ if(o.isMesh) n++; }); return n;"
                    % json.dumps(iid))
        chk(nmesh >= 26, u'③ アザン3 のメッシュ数 (宮の板組 + 見切り + 引き出し2杯)', nmesh)
        drs = mjs("return __noza.drawers().filter(function(d){ return /アザン/.test(d.label); });")
        chk(len(drs) == 2, u'③ 引き出しが drawers レジストリに 2杯 載る', len(drs))
        for d in drs:
            print(u'    %s' % d['label'])
        # 照明 (暖色) と コンセント (2口) のメッシュ
        lit = mjs("var n=0; furnMeshes[%s].traverse(function(o){ if(o.isMesh && o.material &&"
                  " o.material.color && o.material.color.getHex()===0xffd9a0) n++; }); return n;"
                  % json.dumps(iid))
        chk(lit == 2, u'③ 宮の LED 照明が 左右2区画に灯る', lit)
        comps = mjs("var NI=bedModelOf('アザン').shelf; return bedNicheComps(NI);")
        print(u'    宮の区画: ' + ' / '.join([u'幅%.1f (中心x %+.1f)' % (c['w'], c['c']) for c in comps]))
        chk(len(comps) == 3, u'③ 宮は 3区画 (公式画像 ww_13 の仕切り2枚)', len(comps))
        chk(abs(comps[1]['w'] - 42.0) < 0.01, u'③ 中央区画の幅 = 42 (公式サイズ図)', comps[1]['w'])

        # 引き出しを開く → 前方の残り幅
        print(u'\n■ ③ 引き出しを開く (左=北へ引く / 右=南へ引く)')
        for side in ('left', 'right'):
            mjs("var it=workItems[%s]; it.drawerSide=%s; syncItemMesh(furnMeshes[%s], it); return 1;"
                % (json.dumps(iid), json.dumps(side), json.dumps(iid)))
            pg.wait_for_timeout(500)
            ids = mjs("return __noza.drawers().filter(function(d){return /アザン/.test(d.label);})"
                      ".map(function(d){return d.id;});")
            rem = []
            for did in ids:
                r = mjs("return __noza.drawer(%s);" % json.dumps(did))
                rem.append(r['remain'])
                mjs("__noza.drawer(%s); return 1;" % json.dumps(did))    # 閉じる
            side_ja = u'左 (= 部屋の北へ)' if side == 'left' else u'右 (= 部屋の南へ)'
            print(u'    %-18s 引き切った先端から前方の残り: %s cm' % (side_ja, rem))
            chk(all(r is not None for r in rem), u'③ %s に引いた時の残り幅が測れる' % side_ja, rem)

        # ══════════════ ④ UI ══════════════
        print(u'\n■ ④ 家具シートの表示')
        mjs("select(%s); return 1;" % json.dumps(iid))
        pg.wait_for_timeout(400)
        html = mjs("return document.getElementById('itemSheet') ? "
                   "document.getElementById('itemSheet').innerText : document.body.innerText;")
        for key, lab in [(u'幅W 97', u'④ 寸法サマリー 幅W 97 × 奥行D 211 × 高さH 85'),
                         (u'引き出しの向き: 左右どちらの側面にも取り付け可', u'④ install: 左右どちらにも取付可'),
                         (u'引く側へ 47cm', u'④ install: 引く側へ 47cm 必要'),
                         (u'引き出しの向き (左右付け替え可)', u'④ 引き出しの向き セグメント'),
                         (u'左側に引く', u'④ 「左側に引く」ボタン'),
                         (u'右側に引く', u'④ 「右側に引く」ボタン')]:
            chk(key in html, lab)
        chk(u'床面高 (すのこ面の高さ)' not in html, u'④ 床面高セグメントは出ない (アザン3 は切替不可)')
        chk(u'マットレス (セット表示' not in html, u'④ マットレスON/OFF は出ない (アザン3 はフレーム単体)')
        # Aerus 側は従来どおり出るか
        acid = mjs("return Object.keys(catalogData).filter(function(k){"
                   " return /Aerus すのこベッド シングル/.test(catalogData[k].name); })[0];")
        pg.evaluate("window.addFromCatalog(%s);" % json.dumps(acid))
        pg.wait_for_timeout(600)
        aid = mjs("var ks=Object.keys(workItems); return ks[ks.length-1];")
        mjs("select(%s); return 1;" % json.dumps(aid))
        pg.wait_for_timeout(400)
        ahtml = mjs("return document.getElementById('itemSheet').innerText;")
        chk(u'床面高 (すのこ面の高さ)' in ahtml, u'④ Aerus は 床面高セグメントが従来どおり出る')
        chk(u'19.5cm (ロー)' in ahtml and u'32cm (ハイ)' in ahtml, u'④ Aerus 19.5/32 の2択')
        chk(u'ニトリLH3 97×198×38' in ahtml, u'④ Aerus はマットレスのセット表示が従来どおり出る')
        chk(u'引き出しの向き' not in ahtml, u'④ Aerus には引き出しの向きは出ない')

        # ══════════════ ⑤ 6.2帖への収まり ══════════════
        print(u'\n■ ⑤ 洋室6.2帖への収まり (提案配置)')
        # Aerus は比較ショットまで残すが、いったん部屋の外へ避ける
        mjs("var it=workItems[%s]; it.x=%f; it.z=%f; syncItemMesh(furnMeshes[%s], it);"
            " deselect(); return 1;" % (json.dumps(aid), 880.0, 170.0, json.dumps(aid)))
        pg.wait_for_timeout(300)
        x0, x1 = BX - BED_D / 2, BX + BED_D / 2
        z0, z1 = BZ - BED_W / 2, BZ + BED_W / 2
        print(u'    ベッド外形: x %.1f 〜 %.1f (奥行211=東西) / y %.1f 〜 %.1f (幅97=南北) / rotY=%d'
              % (x0, x1, z0, z1, BROT))
        print(u'    ヘッドボード = 東壁 x1055 に付ける / 足元 = 西 x844')
        clears = [
            (u'北: 大窓WIN-05 の壁 (y107) まで', z0 - RY0),
            (u'南: 主室の南壁 (y418) まで', RY1 - z1),
            (u'西: 西壁 (x800) まで', x0 - RX0),
            (u'WIC扉 D-06/D-11 まわり: WIC扉の前 (y426) まで', 426.0 - z1),
        ]
        for lab, v in clears:
            print(u'    %-42s %6.1f cm' % (lab, v))
        chk(x0 >= RX0 and z0 >= RY0 and z1 <= RY1, u'⑤ ベッドが 6.2帖の主室に収まる')
        chk(z0 - RY0 >= BED_W, u'⑤ 北側に 引き出し47cm + 通路 が取れる (残り %.0fcm)' % (z0 - RY0))
        # 実機の干渉判定 (アプリの当たり判定 API があれば使う)
        ov = mjs("var it=workItems[%s]; var a=itemAabb(it); var out=[];"
                 " R.fixtures.concat([]).forEach(function(f){ if(f.room!=='west6_2'||!f.rect) return;"
                 "  var b={x0:f.rect[0],x1:f.rect[0]+f.rect[2],z0:f.rect[1],z1:f.rect[1]+f.rect[3]};"
                 "  var ix=Math.min(a.x1,b.x1)-Math.max(a.x0,b.x0), iz=Math.min(a.z1,b.z1)-Math.max(a.z0,b.z0);"
                 "  if(ix>0.5&&iz>0.5) out.push({id:f.id,label:String(f.label).slice(0,28),"
                 "     h:f.h, bottomH:f.bottomH||0, ix:Math.round(ix*10)/10, iz:Math.round(iz*10)/10}); });"
                 " return out;" % json.dumps(iid))
        if ov:
            for o in ov:
                print(u'    平面重なり: %s「%s」 床から %s〜%s cm (重なり %s × %s)'
                      % (o['id'], o['label'], o['bottomH'], o['h'], o['ix'], o['iz']))
        chk(all((o['bottomH'] or 0) >= 85 for o in ov),
            u'⑤ 平面で重なる設備は すべて床から85cm より上 (ベッド上端85 と当たらない)',
            [(o['id'], o['bottomH']) for o in ov])
        # 窓・エアコン・コンセントとの関係
        info = mjs("var it=workItems[%s]; var a=itemAabb(it); var o={};"
                   " o.win = R.openings.filter(function(q){return q.room==='west6_2';}).map(function(q){"
                   "   return {id:q.id, from:q.wallFrom, to:q.wallTo, sill:q.sillH};});"
                   " o.out = R.outlets.filter(function(q){return q.room==='west6_2';}).map(function(q){"
                   "   return {id:q.id, pos:q.pos, h:q.h};});"
                   " o.ac = R.aircons.filter(function(q){return q.room==='west6_2';}).map(function(q){"
                   "   return {id:q.id, pos:q.pos, bottomH:q.bottomH};});"
                   " o.aabb=a; return o;" % json.dumps(iid))
        print(u'    窓/コンセント/エアコン との関係:')
        for w in info['win']:
            print(u'      %s sill %.1fcm (ベッド上端85cm %s)'
                  % (w['id'], w['sill'], u'より高い = 干渉なし' if w['sill'] >= 85 else u'より低い = 要確認'))
        for o in info['out']:
            d = min(abs(o['pos'][1] - z0), abs(o['pos'][1] - z1)) if abs(o['pos'][0] - RX1) < 1 else None
            print(u'      %s (x%.0f,y%.0f) 床から%.0fcm%s'
                  % (o['id'], o['pos'][0], o['pos'][1], o['h'],
                     (u' — ヘッドボード端から %.0fcm (公式コード長100cm内)' % d) if d is not None else ''))
        for a in info['ac']:
            print(u'      %s (x%.0f,y%.0f) 下端 床から%.1fcm' % (a['id'], a['pos'][0], a['pos'][1], a['bottomH']))

        # ══════════════ ⑥ スクショ ══════════════
        print(u'\n■ ⑥ スクショ')
        mjs("var it=workItems[%s]; it.drawerSide='left'; syncItemMesh(furnMeshes[%s], it);"
            " deselect(); return 1;" % (json.dumps(iid), json.dumps(iid)))
        mjs("var m=furnMeshes[%s]; m.visible=false; return 1;" % json.dumps(aid))   # Aerus は一旦隠す
        pg.wait_for_timeout(400)
        # ── (a)〜(c) 無地背景のスタジオ撮影 (公式画像と1対1で見比べる用。壁を消すだけ)
        mjs("__noza.studio(true); return 1;")
        pg.wait_for_timeout(400)
        cam(BX, 62, -60, BX, 38, BZ)                     # 引き出し側 (長辺) の正面
        shot('01_studio_side_drawer')
        cam(742, 128, 92, BX + 5, 35, BZ)                # 斜め (引き出し側 + 足元)
        shot('02_studio_angle')
        ids = mjs("return __noza.drawers().filter(function(d){return /アザン/.test(d.label);})"
                  ".map(function(d){return d.id;});")
        for did in ids:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(did))
        pg.wait_for_timeout(700)
        cam(736, 132, 86, BX + 5, 30, BZ)
        shot('03_studio_drawers_open')
        mjs("__noza.studio(false); return 1;")
        pg.wait_for_timeout(400)
        # ── (d) 部屋の中で引き出しを開けた状態 (残り幅ラベル付き)
        cam(830, 175, 405, 950, 25, 250)
        shot('04_room_drawers_open')
        cam(870, 40, 130, 960, 14, 225)
        shot('04b_room_drawers_open_low')
        for did in ids:
            mjs("__noza.drawer(%s); return 1;" % json.dumps(did))       # 閉じる
        pg.wait_for_timeout(500)
        # (e) ヘッドボードの宮 寄り (宮の開口は床から 69〜84cm)
        mjs("__noza.fov(34); return 1;")
        cam(895, 112, BZ - 4, 1046, 76, BZ)
        shot('05_headboard_shelf')
        cam(958, 104, BZ + 46, 1046, 78, BZ + 30)     # 右区画 (コンセント + LED)
        shot('06_headboard_outlet')
        mjs("__noza.fov(52); return 1;")
        # (f) 部屋に置いた俯瞰 (部屋の内側から)
        cam(812, 232, 412, 960, 10, 250, 1500)
        shot('07_room_overview')
        cam(1046, 150, 412, 930, 20, 240, 1500)       # 南東の隅から
        shot('08_room_overview2')
        # (g) 真上 (配置の収まり)
        mjs("__noza.fov(40); return 1;")
        cam((RX0 + RX1) / 2, 700, (RY0 + RY1) / 2 + 0.5, (RX0 + RX1) / 2, 20, (RY0 + RY1) / 2, 1600)
        shot('09_plan_top')
        mjs("__noza.fov(52); return 1;")
        # (h) Aerus との比較 (2台を並べて 見分けがつくか / Aerus が変わっていないか)
        mjs("var m=furnMeshes[%s]; m.visible=true; var it=workItems[%s];"
            " it.x=%f; it.z=%f; it.rotY=90; syncItemMesh(m, it); return 1;"
            % (json.dumps(aid), json.dumps(aid), 951.25, 160.0))
        pg.wait_for_timeout(600)
        cam(812, 210, 410, 960, 25, 230, 1500)
        shot('10_compare_aerus')
        cam(830, 95, 405, 960, 40, 220, 1400)
        shot('11_compare_aerus_low')
        # (i) 家具シート (寸法サマリー + 据付すきま + 引き出しの向き)
        mjs("select(%s); return 1;" % json.dumps(iid))
        pg.wait_for_timeout(600)
        cam(812, 190, 408, 960, 25, 260)
        shot('12_item_sheet')
        # (j) モバイル 375x812
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.wait_for_timeout(700)
        mjs("deselect(); return 1;")
        mjs("__noza.fov(46); return 1;")
        cam((RX0 + RX1) / 2, 560, (RY0 + RY1) / 2 + 0.5, (RX0 + RX1) / 2, 20, (RY0 + RY1) / 2, 1600)
        shot('13_mobile_375x812')
        mjs("__noza.fov(52); return 1;")
        mjs("select(%s); return 1;" % json.dumps(iid))
        pg.wait_for_timeout(700)
        shot('14_mobile_sheet')
        pg.set_viewport_size({"width": 1280, "height": 940})

        br.close()

    # (k) Aerus 単体の 共通化前後 比較 (studio モードの実写)
    ba = os.path.join(HERE, '_bedshot_before_2b.png')
    aa = os.path.join(HERE, '_bedshot_after_2b.png')
    if os.path.exists(ba) and os.path.exists(aa):
        side_by_side('15_aerus_before_after', ba, aa,
                     u'RASIK Aerus シングル — 左: v8.0 (共通化まえ) / 右: v8.1 (BED_MODELS 共通化あと)'
                     u'  ※メッシュ台帳は snap_bed_mesh.py で完全一致を確認済み')

    if errs:
        print(u'\n⚠ console error:')
        for e in errs[:10]:
            print(u'   ' + e)
        fails.append(u'console error')

    # Box へコピー
    if os.path.isdir(BOX):
        for s in shots:
            shutil.copy2(s, os.path.join(BOX, os.path.basename(s)))
        print(u'\n  Box へコピー: %s (%d枚)' % (BOX, len(shots)))
    else:
        print(u'\n  ⚠ Box フォルダが見つからない: %s' % BOX)

    print(u'\n════ 結果: FAIL %d 件 / スクショ %d 枚 ════' % (len(fails), len(shots)))
    for f in fails:
        print(u'   ✗ ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

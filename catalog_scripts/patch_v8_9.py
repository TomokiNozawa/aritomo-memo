# -*- coding: utf-8 -*-
u"""v8.9: キッチンボード リガーレ の **下台の左右を入れ替える** (左40 炊飯器スライドテーブル + 右60 引出し4段)。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v8_9.py

冪等。 ROOM_DATA は一切変更しない。 CATALOG_SEED v2.12 → v2.13 (商品37件は不変)。

━━ 依頼 (野沢さん 2026-09-17) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
「キッチンボードについて、下の棚を左右入れ替えて欲しい (左側が炊飯器の引き出し、右側が棚のみの方)」
  v7.7〜v8.8 = 左60 (H50-60C 引出し4段) + 右40 (H50-40J スライドテーブル)
  v8.9〜     = **左40 (H50-40J スライドテーブル = 炊飯器) + 右60 (H50-60C 引出し4段)**
ユニットの中身・寸法は一切変えない (並び順だけ)。 上台・中天板・家電オープンは左右対称なので不変。

━━ やり方 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ① JS: 下台の部品だけ x を鏡映する `BL` / `seamL` / `MX` を足し、 下台ブロックの B( → BL( へ。
        `RG_LOWER_MIRROR` を false にすれば 左60+右40 に戻る (並び順は購入者が選ぶ商品で、 既に2回入れ替えている)。
  ② JS: 引き出し開閉 (itemDrawerSet) の x0 と ラベルの「左60cm/右40cm」を追従。
  ③ CATALOG_SEED: 商品名を「左40+右60」へ。 **model は変えない** (差分シードのキーが model||name なので
        変えると Firebase 側に同じ商品が二重登録される)。 specNote に v8.9 の追記。
  ④ JS: 商品名の追従 = シードの `prevNames` (旧シード名) と一致する名前だけを 新しい名前へ読み替える汎用処理
        (カタログ + 配置済みアイテム。 メモリ内のみ・ユーザーが自分で付けた名前は触らない)。
"""
import hashlib
import io
import json
import re
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'

OLD_NAME = u'キッチンボード リガーレ (上台ハイ109+下台ハイ93 / 左60+右40)'
NEW_NAME = u'キッチンボード リガーレ (上台ハイ109+下台ハイ93 / 左40+右60)'

# ═══ ① ヘルパー (seam の定義の直後へ) ═══════════════════════════════════════
OLD_SEAM = u"    const seam = function (y, x0, x1) { B(x0, x1, y - 0.35, y + 0.35, 26.2, 26.8, line); };\n"
NEW_SEAM = OLD_SEAM + u"""    // ★v8.9 下台の並び = **左40 (H50-40J 炊飯器スライドテーブル) + 右60 (H50-60C 引出し4段)** (ユーザー指示 2026-09-17)。
    //   下台ブロックの座標・コメントは v7.7〜v8.8 の「左60 + 右40」のまま書いてあり、 下台の部品だけ
    //   x を鏡映して置く (BL / seamL / MX)。 = コメント中の「左60」は実際は右、「右40」は実際は左に出る。
    //   上台・中天板・家電オープンは左右対称なので鏡映しない。 false にすれば 左60 + 右40 に戻る
    //   (組み合わせ商品で 並び順は購入者が選ぶ。 v7.7 と v8.9 で 既に2回入れ替えている)。
    const RG_LOWER_MIRROR = true;
    const MX = function (x) { return RG_LOWER_MIRROR ? -x : x; };
    const BL = function (x0, x1, y0, y1, z0, z1, col, opts) {
      return RG_LOWER_MIRROR ? B(-x1, -x0, y0, y1, z0, z1, col, opts) : B(x0, x1, y0, y1, z0, z1, col, opts);
    };
    const seamL = function (y, x0, x1) { if (RG_LOWER_MIRROR) seam(y, -x1, -x0); else seam(y, x0, x1); };
"""

BLOCK_BEGIN = u"    // ══ ★v7.9 下台 左60cm (H50-60C 引出し4段) ══\n"
BLOCK_END = u"    // ══ 中天板 (セラミック天板 グレー/ブラック) ══"
N_LOWER_B = 15          # 下台ブロック内の B( の数 (60ユニット 5 + 40ユニット 10)
OLD_JOINT = u"    B(9.5, 10.5, 0, 93, 26.2, 26.8, line);   // 60|40 ユニットの合わせ目 (縦)"
NEW_JOINT = u"    BL(9.5, 10.5, 0, 93, 26.2, 26.8, line);   // 60|40 ユニットの合わせ目 (縦)"

OLD_SEAMS = u"""    seam(4, 13, 47);        // 台輪
    seam(54, 13, 47);       // 深引出し 天
    seam(65, 13, 47);       // スライドテーブル 天 (= 炊飯器オープン 床)
    seam(4, -47.5, 7.5);    // ★v7.9 台輪 (左60)
    RG60.forEach(function (b) { if (b[1] < 92) seam(b[1], -47.5, 7.5); });"""
NEW_SEAMS = u"""    seamL(4, 13, 47);        // 台輪
    seamL(54, 13, 47);       // 深引出し 天
    seamL(65, 13, 47);       // スライドテーブル 天 (= 炊飯器オープン 床)
    seamL(4, -47.5, 7.5);    // ★v7.9 台輪 (60ユニット)
    RG60.forEach(function (b) { if (b[1] < 92) seamL(b[1], -47.5, 7.5); });"""

# ═══ ② 引き出し開閉 ═══════════════════════════════════════════════════════
OLD_DR = u"""               label: 'リガーレ 引出し' + b[3] + '(左60cm H50-60C・内寸51.5×43.5×' + b[2] + ')',
               y0: Y(b[0]), rh: Y(b[1] - b[0]), depth: Z(44), kind: 'drawer', x0: X(-20), bw: X(55) };
    });
    itemDrawerSet(g, it, RG_DEF.concat([
      { key: 'ddr', label: 'リガーレ 深引出し(右40cm H50-40J・内寸31.5×43.5×44)', y0: Y(4), rh: Y(50),
        depth: Z(44), kind: 'drawer', x0: X(30), bw: X(34) },
      { key: 'tbl', label: 'リガーレ スライドテーブル(右40cm H50-40J・炊飯器スペース)', y0: Y(61), rh: Y(4),
        depth: Z(38), kind: 'table', x0: X(30), bw: X(32) }"""
NEW_DR = u"""               label: 'リガーレ 引出し' + b[3] + '(' + RG_SIDE60 + '60cm H50-60C・内寸51.5×43.5×' + b[2] + ')',
               y0: Y(b[0]), rh: Y(b[1] - b[0]), depth: Z(44), kind: 'drawer', x0: X(MX(-20)), bw: X(55) };
    });
    itemDrawerSet(g, it, RG_DEF.concat([
      { key: 'ddr', label: 'リガーレ 深引出し(' + RG_SIDE40 + '40cm H50-40J・内寸31.5×43.5×44)', y0: Y(4), rh: Y(50),
        depth: Z(44), kind: 'drawer', x0: X(MX(30)), bw: X(34) },
      { key: 'tbl', label: 'リガーレ スライドテーブル(' + RG_SIDE40 + '40cm H50-40J・炊飯器スペース)', y0: Y(61), rh: Y(4),
        depth: Z(38), kind: 'table', x0: X(MX(30)), bw: X(32) }"""
OLD_RGDEF = u"    const RG_DEF = RG60.map(function (b, i) {\n"
NEW_RGDEF = (u"    const RG_SIDE60 = RG_LOWER_MIRROR ? '右' : '左', RG_SIDE40 = RG_LOWER_MIRROR ? '左' : '右';   // ★v8.9 ラベルの左右\n"
             + OLD_RGDEF)

OLD_X0C = u"// 面に沿う方向の中心 (リガーレ 下台左40cm/右60cm ユニットの中心)"
# ↑ v3.3 時代の表記のまま残っていたが v8.9 で再び正しくなる = 変更しない (存在確認だけする)

# ═══ ④ 商品名の追従 (汎用) ═══════════════════════════════════════════════
OLD_SYNC = u"        if (s && s.specNote && c.createdBy === 'seed' && c.specNote !== s.specNote) c.specNote = s.specNote;\n"
NEW_SYNC = OLD_SYNC + u"""        // ★v8.9 商品名の追従: シードの `prevNames` (= 過去のシード名) と一致する名前だけを 現在のシード名へ読み替える。
        //   キー (model||name) は変えない前提。 ユーザーが自分で付けた名前は prevNames に無いので触らない (メモリ内のみ)。
        if (s && s.prevNames && s.prevNames.indexOf(c.name) >= 0) c.name = s.name;
"""
OLD_MIG = u"        if (cat && cat.specNote && !it.specNote) it.specNote = cat.specNote;   // スペックは内部へ退避\n"
NEW_MIG = OLD_MIG + u"""        // ★v8.9 配置済みアイテムの名前も同じ規則で追従 (旧シード名のままのものだけ。 次の保存で DB にも載る)
        if (cat && SEED_PREV_NAMES[it.name] && SEED_PREV_NAMES[it.name].model === (cat.model || cat.name)) {
          it.name = SEED_PREV_NAMES[it.name].name;
        }
"""
OLD_MIGFN = u"function migrateSeedMemos(seedSpecTexts) {\n"
NEW_MIGFN = u"""// ★v8.9 旧シード名 → 現在のシード商品 の索引 (CATALOG_SEED.items[].prevNames から作る。 商品側に1行足すだけで効く)
const SEED_PREV_NAMES = {};
((typeof CATALOG_SEED !== 'undefined' && CATALOG_SEED && CATALOG_SEED.items) || []).forEach(function (s) {
  (s.prevNames || []).forEach(function (n) { SEED_PREV_NAMES[n] = { name: s.name, model: s.model || s.name }; });
});
""" + OLD_MIGFN

NOTE_ADD = (u' ★v8.9 (2026-09-17 ユーザー指示): **下台の並びを【左40 (H50-40J スライドテーブル=炊飯器) + 右60 (H50-60C 引出し4段)】へ入れ替え**。 '
            u'ユニットの中身・寸法は不変で 並び順だけ (v7.7〜v8.8 は 左60+右40)。 3Dは下台の部品だけ x を鏡映して描く。 '
            u'本文中の「左60」「右40」という呼び方は v7.7 時点の並びでの記述で、 現在は 60ユニットが右・40ユニットが左。 '
            u'結果として 完成品SKU 100KB (左40+右60) と同じ並びになった。')


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def rep1(src, old, new, what):
    assert src.count(old) == 1, u'%s の置換元が %d 箇所 (1でない)' % (what, src.count(old))
    return src.replace(old, new, 1)


def main():
    src = io.open(P, encoding='utf-8').read()
    rd_before = sha(RD_PAT, src)
    cs = json.loads(re.search(CS_PAT, src, re.S).group(1))

    if cs['version'] == '2.13' and u'RG_LOWER_MIRROR' in src:
        print(u'適用0件 / skip 全件 (既に CATALOG_SEED v2.13 + 下台の鏡映 = 適用済み)')
        return 0
    assert cs['version'] == '2.12', u'CATALOG_SEED が v2.12 でない: %s' % cs['version']
    assert len(cs['items']) == 37, u'商品が 37件でない: %d' % len(cs['items'])
    assert u'RG_LOWER_MIRROR' not in src
    assert src.count(OLD_X0C) == 1

    # ① ヘルパー + 下台ブロックの B( → BL(
    src = rep1(src, OLD_SEAM, NEW_SEAM, u'① seam の直後へ BL/seamL/MX')
    a = src.index(BLOCK_BEGIN)
    b = src.index(BLOCK_END, a)
    blk = src[a:b]
    n = len(re.findall(r'(?m)^( +)B\(', blk))
    assert n == N_LOWER_B, u'下台ブロックの B( が %d 個 (想定 %d)' % (n, N_LOWER_B)
    blk = re.sub(r'(?m)^( +)B\(', r'\1BL(', blk)
    src = src[:a] + blk + src[b:]
    src = rep1(src, OLD_JOINT, NEW_JOINT, u'① 60|40 の合わせ目')
    src = rep1(src, OLD_SEAMS, NEW_SEAMS, u'① 下台の見切りライン seam → seamL')

    # ② 引き出し開閉
    src = rep1(src, OLD_DR, NEW_DR, u'② 引き出し開閉の x0 とラベル')
    src = rep1(src, OLD_RGDEF, NEW_RGDEF, u'② ラベルの左右')

    # ④ 商品名の追従
    src = rep1(src, OLD_SYNC, NEW_SYNC, u'④ カタログの商品名追従')
    src = rep1(src, OLD_MIG, NEW_MIG, u'④ 配置済みアイテムの商品名追従')
    src = rep1(src, OLD_MIGFN, NEW_MIGFN, u'④ SEED_PREV_NAMES')

    # ③ CATALOG_SEED
    hit = [i for i in cs['items'] if i.get('name') == OLD_NAME]
    assert len(hit) == 1, u'リガーレが %d件 (1でない)' % len(hit)
    others = json.dumps([i for i in cs['items'] if i is not hit[0]], ensure_ascii=False, sort_keys=True)
    model_before = hit[0]['model']
    hit[0]['name'] = NEW_NAME
    hit[0]['prevNames'] = [OLD_NAME]
    hit[0]['specNote'] = hit[0]['specNote'] + NOTE_ADD
    assert hit[0]['model'] == model_before
    assert json.dumps([i for i in cs['items'] if i is not hit[0]], ensure_ascii=False,
                      sort_keys=True) == others, u'他の商品が変化した'
    cs['version'] = '2.13'
    cs['updatedAt'] = '2026-09-17'
    cs['_comment'] += (
        u' ★v2.13 の変更点 (2026-09-17): **リガーレの下台の並びを 左40 (スライドテーブル=炊飯器) + 右60 (引出し4段) へ入れ替え** '
        u'(ユーザー指示。 中身・寸法は不変)。 商品名を「左40+右60」へ。 model は差分シードのキーなので不変。 '
        u'新フィールド `prevNames` = 過去のシード名。 これと一致する名前 (カタログ・配置済みアイテム) だけを '
        u'現在の商品名へ読み替える (ユーザーが付けた名前は触らない) ★アプリ v8.9')

    m = re.search(CS_PAT, src, re.S)
    src = (src[:m.start()] + 'var CATALOG_SEED = '
           + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n' + src[m.end():])

    assert sha(RD_PAT, src) == rd_before, u'ROOM_DATA が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用4件')
    print(u'  ① JS: 下台の部品 %d個 + 合わせ目 + 見切り を x 鏡映 (BL / seamL / RG_LOWER_MIRROR=true)' % N_LOWER_B)
    print(u'  ② JS: 引き出し開閉 6杯の x0 とラベルの左右を追従')
    print(u'  ③ CATALOG_SEED: リガーレの商品名 → 左40+右60 / prevNames / specNote 追記 (model 不変)')
    print(u'  ④ JS: prevNames による商品名の追従 (カタログ + 配置済みアイテム)')
    print(u'CATALOG_SEED v2.12 → v2.13 / 商品 37件 (不変) / ROOM_DATA sha256 %s (不変)' % rd_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

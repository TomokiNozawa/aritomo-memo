# -*- coding: utf-8 -*-
"""v7.6: 三菱 MR-MD45N を 左開き (MR-MD45NL) で既定登録する。冪等。

- CATALOG_SEED v2.3 -> v2.4 (該当1件のみ変更。他32件はバイト単位で不変を assert)
- FRIDGE_MODELS の hinge を実際に描画で使い、扉の開き側を見分けられるようにする
  (v7.5 までの hinge は宣言されているだけで描画に使われておらず、値を変えても見た目が変わらなかった)
- install に doorSide / doorSideCm を新設し、扉がどちら側へ開くかをツールチップに出す
  (冷蔵庫専用にせず、設置条件を持つ商品の共通フィールドとして足す)
- ROOM_DATA は不変 (sha256 assert)
"""
import io
import re
import json
import hashlib
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


src = io.open(P, encoding='utf-8').read()
rd_before = sha(RD_PAT, src)
items_before = json.loads(re.search(CS_PAT, src, re.S).group(1))['items']

if 'MR-MD45NL' in src and 'freeSign' in src:
    print('適用0件 / skip 5件 (既に適用済み)')
    sys.exit(0)

applied = 0

# ---- (1) hinge の意味をドキュメント化 ----
old = "//   handles… 縦長ハンドルの中心x [cm] (本体中心が 0。 マイナス=左)。 フラット扉の機種は空"
new = (old + "\n"
       "//   hinge … front:'hinge' (1枚扉) の 吊元。 'l'=左吊元(=右開き) / 'r'=右吊元(=左開き)。\n"
       "//           吊元の反対側 (= 扉が開いてくる自由端) に 見切り線を描くので 左右が見分けられる。\n"
       "//           ★v7.6 まで hinge は宣言されているだけで描画に使われておらず、\n"
       "//             値を変えても見た目が変わらなかった (効かない設定は事故源なので実際に使う)")
assert old in src
src = src.replace(old, new, 1)
applied += 1

# ---- (2) 1枚扉の自由端に見切り線を描く ----
old = "    for (let i = rows.length - 1; i >= 0; i--) {                          // 縦長ハンドル"
new = ("    for (let i = rows.length - 1; i >= 0; i--) {                          // ★v7.6 1枚扉の自由端 (開いてくる側) の見切り線\n"
       "      const r = rows[i], y0 = rowY(i - 1), y1 = rowY(i);\n"
       "      if (r.front !== 'hinge' || !r.hinge) continue;\n"
       "      const freeSign = (r.hinge === 'r') ? -1 : 1;                        // 吊元が右('r') なら 自由端は左\n"
       "      P(0.9, y1 - y0 - 3, 0.8, freeSign * (w / 2 - 1.6), y0 + (y1 - y0) / 2, zF + 0.35, line);\n"
       "    }\n"
       + old)
assert old in src
src = src.replace(old, new, 1)
applied += 1

# ---- (3) 三菱の行を 左開き (吊元=右) に ----
old = """    //   ⚠ MDシリーズはフラット扉で **縦ハンドルが無い** ので handles は付けず、
    //     冷蔵室扉は下端の全幅グリップ (gy:'bottom') で表現する = 日立の観音2本ハンドルと見分けがつく。
    test: /MR-MD45|MDシリーズ/,"""
new = """    //   ⚠ MDシリーズはフラット扉で **縦ハンドルが無い** ので handles は付けず、
    //     冷蔵室扉は下端の全幅グリップ (gy:'bottom') で表現する = 日立の観音2本ハンドルと見分けがつく。
    //   ★v7.6 ユーザー確定: **左開き (MR-MD45NL)** を既定にする → 吊元は右 = hinge:'r'。
    //     ⚠ 左開き機で 製氷室/瞬冷凍室 の左右が入れ替わるかは公式資料で確認できず、右開き機と同じ並びのまま (est)。
    test: /MR-MD45|MDシリーズ/,"""
assert old in src
src = src.replace(old, new, 1)
applied += 1

old = """      { key: 'fridge',  top: 1, front: 'hinge', hinge: 'r',
        panels: [{ gw: 'full', gx: 0, gy: 'bottom' }] }"""
new = """      { key: 'fridge',  top: 1, front: 'hinge', hinge: 'r',   // 吊元=右 → 左開き
        panels: [{ gw: 'full', gx: 0, gy: 'bottom' }] }"""
assert old in src
src = src.replace(old, new, 1)

# ---- (4) install.doorSide を新設し ツールチップに出す ----
old = "//     doorFront           … 扉/引き出しを開いた時に前方へ必要な寸法 (本体前面から)"
new = (old + "\n"
       "//     doorSide            … ★v7.6 扉がどちら側へ開くか 'left'|'right' (置き場所の判断に効く)\n"
       "//     doorSideCm          … その側方へ必要な寸法 (本体側面から cm)")
assert old in src
src = src.replace(old, new, 1)
applied += 1

old = """  if (N(ins.doorFront) !== null) {
    rows.push('扉の開放: 本体前面から ' + tipN(N(ins.doorFront)) + 'cm' +
              (ins.doorNote ? ' (' + ins.doorNote + ')' : ''));
  }"""
new = """  if (ins.doorSide === 'left' || ins.doorSide === 'right') {
    rows.push('扉の開き: ' + (ins.doorSide === 'left' ? '左開き (吊元=右)' : '右開き (吊元=左)') +
              (N(ins.doorSideCm) === null ? ''
                : ' → ' + (ins.doorSide === 'left' ? '左' : '右') + 'へ ' + tipN(N(ins.doorSideCm)) + 'cm 必要'));
  }
""" + old
assert old in src
src = src.replace(old, new, 1)

# ---- (5) CATALOG_SEED: 該当1件を左開きへ ----
m = re.search(CS_PAT, src, re.S)
cs = json.loads(m.group(1))
hit = 0
for it in cs['items']:
    if it.get('model') == 'MR-MD45N':
        hit += 1
        it['name'] = '冷蔵庫 三菱 MDシリーズ 451L (左開き)'
        it['model'] = 'MR-MD45NL'
        it['specNote'] = (
            '三菱電機「置けるスマート大容量 MDシリーズ」MR-MD45N の【左開き】モデル。'
            '★ユーザー確定 (2026-08-23): 左開きを既定登録。'
            '★出典 = 三菱電機 公式製品ページ に「左開きもあります」と明記。'
            'カラーは フラットリネンホワイト(W) / フラットアンバーグレー(H) の2色。'
            '外形 幅600 × 奥行699 × 高さ1826mm / 質量106kg / 定格内容積451L '
            '(冷蔵室243L・冷凍室81L・野菜室87L・製氷室18L・瞬冷凍室22L) / 年間消費電力量251kWh/年 / '
            '運転音 約15dB(A) / 5ドア・真ん中野菜室・自動製氷 / 2026年1月23日発売・オープン価格 '
            '(公式製品ページ + 三菱電機WIN2K pid=357235)。'
            '⚠左開きの形名は公式サイトに形名としての記載がなく、販売店 (Joshin web) の表記 '
            'MR-MD45NL-W (JAN 4573637027352) が出典。公式の純正部品 適合機種一覧には '
            'W / H / WJ / HJ / LW / LH / LWJ / LHJ の8形名があり L=左開き。'
            '⚠店頭POPの型番表記 WJ (バーコード 4573637027659) は公式カラー一覧(W/H)に該当がなく未特定。'
            '流通ルート違いの枝番の可能性が高いが裏付け出典なし → 色は W (フラットリネンホワイト) を暫定採用。'
            '⚠左開き機で 製氷室/瞬冷凍室 の左右が入れ替わるかは公式資料で確認できず、3Dは右開き機と同じ並びのまま (est)。'
            '⚠引き出しを引いた時の前方張り出しは公式に記載なし。据付図の印字は 前後1,270mm / 側方411mm の2つのみで、'
            '開き角のラベルが無いため安全側で扱っている。'
        )
        ins = it.get('install') or {}
        ins['doorSide'] = 'left'
        ins['doorSideCm'] = 41.1
        ins['doorNote'] = ('左開き。公式据付図の前後1,270mm − 本体奥行699mm。'
                           '側方は左へ411mm (開き角のラベルは図に無いので安全側)')
        it['install'] = ins
assert hit == 1, '対象の冷蔵庫が %d 件 (1件のはず)' % hit
cs['version'] = '2.4'
cs['updatedAt'] = '2026-08-23'
src = (src[:m.start()]
       + 'var CATALOG_SEED = ' + json.dumps(cs, ensure_ascii=False, separators=(',', ':')) + ';\n'
       + src[m.end():])
applied += 1

# ---- 検証 ----
assert sha(RD_PAT, src) == rd_before, 'ROOM_DATA が変化した'
items_after = json.loads(re.search(CS_PAT, src, re.S).group(1))['items']
assert len(items_after) == len(items_before) == 33, 'アイテム数が変わった'
J = (lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True))
changed = [a.get('model') for a, b in zip(items_after, items_before) if J(a) != J(b)]
assert changed == ['MR-MD45NL'], '意図しない商品が変わった: %s' % changed

io.open(P, 'w', encoding='utf-8', newline='').write(src)
print('適用%d件 (三菱を左開き MR-MD45NL へ / hinge を描画で使用 / install.doorSide 新設)' % applied)
print('ROOM_DATA sha256 %s (不変)' % rd_before[:12])
print('変更された商品: %s のみ (他32件はバイト単位で不変)' % changed[0])

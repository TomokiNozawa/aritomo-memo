# -*- coding: utf-8 -*-
"""v8.3: ニトリ アザン3 にもマットレスのセット表示 (接着) を付ける。冪等。

ユーザー指示 (2026-08-24):
  ・シングルのマットレス、ピッタリ乗りそうじゃん
  ・他のベッドフレームと同様にマットレス接着出来るようにしてね

v8.1 は `mattress: null` にしていたため、アザン3 だけ Aerus にある
「マットレス ON / OFF (フレームのみ)」の切替が出なかった。BED_MODELS に
mattress[] を足すだけで、描画・UI・保存 (item.mattress) は既存の共通機構が全部やる。

敷くマットレス = ニトリ Nスリープ ラグジュアリー LH3 シングル 97×198×38
  幅 97 = フレーム幅 97 と完全一致 (公式)
  長さ 198 vs アザン3 の床板内寸 196.5 → 足側へ 1.5cm はみ出す
  (参考: 同じマットレスを Aerus S に載せると内寸195 に対し +3cm。アザン3 は その半分)

あわせて、いままで**幅のはみ出ししか警告していなかった**のを **長さのはみ出しも
警告する**ようにする (アザン3専用の分岐にはせず、BED_MODELS の deck から内寸を
計算する共通処理にして 全機種に効かせる)。

CATALOG_SEED / ROOM_DATA とも不変 (JS のみの変更)。
"""
import io
import re
import hashlib
import sys

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


src = io.open(P, encoding='utf-8').read()
rd_before, cs_before = sha(RD_PAT, src), sha(CS_PAT, src)

if 'bedInnerLen' in src:
    print('適用0件 / skip 3件 (既に適用済み)')
    sys.exit(0)

applied = 0

# ---- (1) アザン3 に mattress[] を足す ----
old = """               handle: 'none', label: 'アザン3 引き出し',
               labelSuffix: ' (外寸96×47×高11/有効内寸12.5・スライドレール)' },
    mattress: null
  },"""
new = """               handle: 'none', label: 'アザン3 引き出し',
               labelSuffix: ' (外寸96×47×高11/有効内寸12.5・スライドレール)' },
    // ★v8.3 マットレスのセット表示 (Aerus と同じ機構)。
    //   公式の対応マットレスは シングル 97×195 だが、 野沢さんが検討中なのは
    //   ニトリ Nスリープ ラグジュアリー LH3 シングル 97×198×38 (既にカタログにある商品)。
    //   幅97 = フレーム幅97 と完全一致 / 長さ198 は 床板内寸196.5 に対し 足側へ 1.5cm はみ出す
    //   (同じマットレスを Aerus S に載せると内寸195 に対し +3cm なので その半分)。
    mattress: [
      { test: null, w: 97, d: 198, h: 38, col: 0x3e4147, label: 'ニトリLH3 97×198×38' }
    ]
  },"""
assert old in src
src = src.replace(old, new, 1)
applied += 1

# ---- (2) 床板の内寸 (頭↔足) を BED_MODELS から求める共通関数 ----
old = "function bedMattressOf(BM, nm) {"
new = """// ★v8.3 床板の内寸 (ヘッドボード内面 〜 フット板内面)。 マットレスが長さ方向に
//   収まるかの判定に使う。 機種ごとの分岐は作らず BED_MODELS の値だけで出す。
function bedInnerLen(BM, bed) {
  const d = Number(bed.d) || 0;
  const headT = Number(BM.headT) || 0;
  const foot = (BM.deck && Number(BM.deck.foot)) || 0;
  return Math.max(d - headT - foot, 0);
}
function bedMattressOf(BM, nm) {"""
assert old in src
src = src.replace(old, new, 1)
applied += 1

# ---- (3) 幅だけでなく長さのはみ出しも警告する ----
old = """      (ms && ms.w > (Number(it.w) || 0)
        ? '<div class="dim-note">⚠ マットレス幅' + ms.w + 'cm &gt; フレーム' + tipN(it.w) +
          'cm — 実物同様はみ出して表示されます</div>'
        : '') +"""
new = """      (ms && ms.w > (Number(it.w) || 0)
        ? '<div class="dim-note">⚠ マットレス幅' + ms.w + 'cm &gt; フレーム' + tipN(it.w) +
          'cm — 実物同様はみ出して表示されます</div>'
        : '') +
      // ★v8.3 長さ方向のはみ出しも出す (幅だけ見ていたので 「床板に載るか」 が分からなかった)
      (function () {
        if (!ms) return '';
        const inner = bedInnerLen(BMu, it);
        if (!inner) return '';
        const over = Math.round((ms.d - inner) * 10) / 10;
        if (over > 0.05) {
          return '<div class="dim-note">⚠ マットレス長さ' + ms.d + 'cm &gt; 床板内寸' +
                 tipN(inner) + 'cm — 足側へ ' + tipN(over) + 'cm はみ出します</div>';
        }
        return '<div class="dim-note">✓ 床板内寸 ' + tipN(inner) + 'cm に収まります (余り ' +
               tipN(Math.round((inner - ms.d) * 10) / 10) + 'cm)</div>';
      })() +"""
assert old in src
src = src.replace(old, new, 1)
applied += 1

assert sha(RD_PAT, src) == rd_before, 'ROOM_DATA が変化した'
assert sha(CS_PAT, src) == cs_before, 'CATALOG_SEED が変化した'

io.open(P, 'w', encoding='utf-8', newline='').write(src)
print('適用%d件 (アザン3 に mattress[] / bedInnerLen 新設 / 長さのはみ出し警告)' % applied)
print('ROOM_DATA %s・CATALOG_SEED %s ともに不変' % (rd_before[:8], cs_before[:8]))

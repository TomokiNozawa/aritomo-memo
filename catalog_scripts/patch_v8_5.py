# -*- coding: utf-8 -*-
u"""v8.5: 野沢さん 2026-08-24 回答4件の反映。冪等 (再実行で「適用0件 / skip 全件」)。

ROOM_DATA v6.11 -> v6.12 / CATALOG_SEED は不変 (sha256 前後一致を assert)。

  ① 3室のクローゼットを **折れ戸** に是正 (D-02 4.5帖 / D-04 4.8帖 / D-11 WIC)。
     3室バラバラの実装にせず、構成 (組数・1組の枚数・吊元・パネル幅) だけを ROOM_DATA の
     o.fold がデータで持ち、描画と開閉は JS の共通コード1本 (foldDoorSets + 折れ戸ブロック) で行う
     = FRIDGE_MODELS / BED_MODELS と同じ流儀。 ⚠LDK の F-24 は 片開き1枚のまま (v8.4 で写真確定)。
  ② 「はみ出し」の定義を **最大まで開いた状態で 柱から 扉の先端まで** に統一
     (install.doorFront の意味 + ツールチップ文言 + doorFrontFrom で起点をデータ化)。
  ③ F-24 の rect を v8.4 以前の [103, 283.5, 57.0, 70.5] へ戻す (est も true へ)。
     install.doorFront = 38 だけ残す。 → 実測 204 / 199.5 が再び閉じる。
  ④ 実測「空気口の壁 → WIC の左側 44」 を反映。 終点は **壁**。
     D-11 の東端 x1013 → x1011 (幅 60 → 58) で W-R62-S3 = 42 → 44。
     西端 x953 は動かさないので W-R62-S2 = 81 も不変、東壁チェーン 311 も無関係で不変。

★実測が正。 折れ戸の幾何と実測が食い違う箇所は 勝手に寸法を捏ねず、差を label と報告に残す。
"""
import io
import re
import json
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wallgen  # noqa: E402

P = r'C:\Users\t2262\aritomo-memo\room.html'
RD_PAT = r'var ROOM_DATA = (\{.*?\});\s*\n'
CS_PAT = r'var CATALOG_SEED = (\{.*?\});\s*\n'
OPEN_MATCH_TOL = 18.0

ANS = u'★v8.5 【野沢さん 2026-08-24 回答 — ユーザー確定】'
SWING5 = (u'実測 = 最大まで開いた状態で 柱から 開いた扉の先端まで '
          u'(2026-08-24 野沢さん確定の定義)')

# ═══ 折れ戸の畳み込み幾何 と 実測の照合 (捏ねない・報告する) ═══════════════
#   折れ戸 (2枚折れ) を最大まで開くと 2枚が面どうしで畳まれて 側方へ寄るので、
#   柱面から戸先までの出 ≒ **パネル1枚の幅** (+建具厚ぶんの数cm)。
#     D-02  開口145 / 2枚折れ×2組 = 4枚 → 1枚 36.25  vs 実測36   (−0.25)
#     D-04  開口160 / 2枚折れ×2組 = 4枚 → 1枚 40.00  vs 実測35   (−5.00) ⚠
#     D-11  開口 58 / 2枚折れ×1組 = 2枚 → 1枚 29.00  vs 実測32   (+3.00 = 建具厚+金物ぶん)
FOLD = {
    'D-02': {'sets': 2, 'panels': 2, 'hinge': 'outer'},
    'D-04': {'sets': 2, 'panels': 2, 'hinge': 'outer'},
    'D-11': {'sets': 1, 'panels': 2, 'hinge': 'e'},
}


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def by_id(arr, i):
    for e in arr:
        if e['id'] == i:
            return e
    raise AssertionError(u'%s が見つからない' % i)


def rep1(src, old, new, what):
    assert src.count(old) == 1, u'%s の置換元が %d 箇所 (1でない)' % (what, src.count(old))
    return src.replace(old, new, 1)


def main():
    src = io.open(P, encoding='utf-8').read()
    cs_before = sha(CS_PAT, src)
    m = re.search(RD_PAT, src, re.S)
    rd = json.loads(m.group(1))
    rd_before = json.loads(m.group(1))          # 対象外の要素が動いていないかの照合用

    if rd['meta'].get('version') == '6.12' and 'function foldDoorSets(' in src:
        print(u'適用0件 / skip 全件 (既に ROOM_DATA v6.12 + 折れ戸の共通コード = 適用済み)')
        return 0
    assert rd['meta'].get('version') == '6.11', u'ROOM_DATA が v6.11 でない: %s' % rd['meta'].get('version')

    applied = []

    # ═══ ④ 先に D-11 の東端を動かす (①の パネル幅 58/2 に効く) ═══════════════
    #   実測「空気口の壁 (= 6.2帖 東壁 x1055) → WIC の左側 44」。 野沢さん回答で 終点 = **壁**。
    #   現データの相当値は W-R62-S3 (= WIC開口の東の壁) = x1013〜1055 = 42 で 2cm 差。
    #   ・部屋ポリゴン (6.2帖 / WIC) は 実測ハード制約 (東壁 311 等) に効くので動かさない。
    #   ・D-11 は est=true (位置も幅も推定) なので **開口の東端だけ** 2cm 西へ寄せる。
    #   ・西端 x953 は動かさない → 幅 60 → 58 になり、 ラベルの「間取り図実測≈58」と一致する。
    d11 = by_id(rd['openings'], 'D-11')
    assert d11['wallFrom'] == [953.0, 426.0] and d11['wallTo'] == [1013.0, 426.0] and d11['width'] == 60, \
        u'D-11 の開口が想定と違う: %s %s %s' % (d11['wallFrom'], d11['wallTo'], d11['width'])
    d11['wallTo'] = [1011.0, 426.0]
    d11['width'] = 58
    applied.append(u'④ D-11 東端 x1013→x1011 (幅60→58) / W-R62-S3 42→44 (実測44)')

    # ═══ ① 3室を折れ戸へ ═════════════════════════════════════════════════════
    d02 = by_id(rd['openings'], 'D-02')
    d04 = by_id(rd['openings'], 'D-04')
    for oid in ('D-02', 'D-04', 'D-11'):
        o = by_id(rd['openings'], oid)
        assert 'fold' not in o, u'%s に fold が既にある' % oid
        o['fold'] = dict(FOLD[oid], panelW=None)   # panelW=null → 開口÷総枚数。実測が出たら入れる
    # 名前・ラベルの「両開き」「片開き」表記を 折れ戸へ是正 (旧表記が残ると tipDoorKind の
    # フォールバック判定 (/両開き/) と食い違う = 効かない設定は事故源)
    assert d02['name'] == u'洋室4.5→クローゼット 両開き扉'
    d02['name'] = u'洋室4.5→クローゼット 折れ戸4枚 (2枚折れ×2組)'
    d02['label'] = rep1(d02['label'], u'両開き扉(白2枚・銀ハンドル/両リーフとも4.5帖側=西へ開く',
                        u'折れ戸(白 2枚折れ×2組=4枚・銀ハンドル/2組とも4.5帖側=西へ畳まれる',
                        u'D-02 label 頭')
    assert d04['name'] == u'洋室4.8→クローゼット 両開き2組4枚'
    d04['name'] = u'洋室4.8→クローゼット 折れ戸4枚 (2枚折れ×2組)'
    d04['label'] = rep1(d04['label'], u'両開き2組4枚(白・各40・銀ハンドル/',
                        u'折れ戸 2枚折れ×2組=4枚(白・各40・銀ハンドル/', u'D-04 label 頭')
    assert d04.get('leaves') == 4
    del d04['leaves']                      # 折れ戸では意味を持たない旧フィールドを残さない
    assert d11['name'] == u'洋室6.2→WIC 白片開き戸'
    d11['name'] = u'洋室6.2→WIC 白折れ戸2枚 (2枚折れ×1組)'
    d11['label'] = rep1(d11['label'], u'白片開き戸(6.2帖側=北へ開く・吊元=東端x1013.5',
                        u'白折れ戸 2枚折れ×1組(6.2帖側=北へ畳まれる・吊元=東端x1011',
                        u'D-11 label 頭')

    NOTE_FOLD = (
        u' ' + ANS + u'【①折れ戸に是正】v8.4 の写真調査 (開いた戸の自由端に付く丁番・床の下部ピボット金具・'
        u'原図の∨記号) のとおり **両開きではなく折れ戸** と 野沢さん確定。'
        u' 3室ぶんの描画を別々に作らず、 **構成だけを ROOM_DATA の `fold` が持ち、'
        u'描画/開閉は JS の共通コード1本 (foldDoorSets + 折れ戸ブロック) で行う** '
        u'(FRIDGE_MODELS / BED_MODELS と同じ流儀)。'
        u' 開くと 2枚が面どうしに畳まれて 吊元の側方へ寄る = 90°回転の開き戸表現ではなくなった。')
    NOTE_SWING = (
        u' ' + ANS + u'【②はみ出しの定義】「柱から、最大まで開いた扉の先端までの距離」 で確定。'
        u' 折れ戸を最大まで開くと 2枚が畳まれて側方に寄るので、 柱面からの出は '
        u'**≒ パネル1枚の幅 (+建具厚・金物ぶんの数cm)** になる。 実測との照合:'
        u' D-02 開口145÷4枚 = 1枚36.25 に対し 実測36 (−0.25 = 一致) /'
        u' D-11 開口58÷2枚 = 1枚29.0 に対し 実測32 (+3.0 = 建具厚+丁番の出ぶん。ほぼ一致) /'
        u' ⚠**D-04 だけ 開口160÷4枚 = 1枚40.0 に対し 実測35 で −5.0 合わない**。'
        u' 実測35 から逆算すると 4枚×35 = 140 で 開口160 に 20cm 足りないので、'
        u' 考えられるのは (a) 開口160 (= 側壁169 − 枠9) が過大 (b) 4.8帖の収納は造作ボックスで、'
        u'その東面 x160.5 より 柱の面が 5cm 手前に出ている (= 柱面起点だと 40−5=35) '
        u'(c) 戸が最後まで畳まれていない — のいずれか。 **数値は捏ねず 幾何どおり (開口÷枚数) のまま**にした。'
        u' 確定には **扉1枚の見付け幅** と **柱面と戸面の前後差** の2つを測ってもらう必要がある。')
    for oid in ('D-02', 'D-04', 'D-11'):
        o = by_id(rd['openings'], oid)
        o['label'] += NOTE_FOLD + NOTE_SWING
        o['install']['doorNote'] = SWING5
        o['install']['doorFrontFrom'] = u'柱(枠)の面'
    d11['label'] += (
        u' ' + ANS + u'【④WICの壁まで44】実測「空気口の壁 → WIC の左側 44」 の終点は '
        u'**扉の開口端ではなく壁** と野沢さん確定。 現データの相当値 W-R62-S3 (WIC開口の東の壁) は '
        u'x1013〜1055 = 42 で 2cm 差だった。 部屋ポリゴン (6.2帖/WIC) は 東壁チェーン311 等の'
        u'実測ハード制約に効くので動かさず、 **est だった D-11 の東端だけ x1013→x1011 へ 2cm 西へ**寄せて'
        u'W-R62-S3 = **44.0** とした。 西端 x953 は不動なので W-R62-S2 = 81.0 も不変、'
        u'南壁チェーン 183 = 81 + 58 + 44 で閉じる。 副産物として 開口幅が 60 → **58** になり、'
        u'このラベルが元から持っていた 「間取り図実測≈58」 と一致した (独立な2つの根拠が揃った)。'
        u' 東壁チェーン (311 = 89+44+17+44+117) は y方向なので 無関係・不変。'
        u' ⚠ 44 の起点「空気口の壁」= 東壁 x1055 と解釈している (空気口 F-55 自体は x1051〜1055 で壁の面)。')
    applied.append(u'① D-02 / D-04 / D-11 を折れ戸へ (fold データ + 共通描画)。F-24 は片開きのまま')

    # ═══ ③ F-24 を v8.4 以前へ戻す (doorFront 38 だけ残す) ═══════════════════
    f24 = by_id(rd['fixtures'], 'F-24')
    assert f24['rect'] == [103.0, 283.5, 65.0, 66.0], u'F-24 の rect が v8.4 の 65×66 でない'
    f24['rect'] = [103.0, 283.5, 57.0, 70.5]
    f24['est'] = True                       # v8.4 以前と同じ (65/66 を採らないので実測確定ではない)
    f24['label'] += (
        u' ' + ANS + u'【③一旦もとのサイズに戻す】野沢さん「そしたらF24は一旦前のままでいいか、'
        u'扉開いた際の長さだけ直してもらえれば一旦良いかな」。 → rect を v8.4 の 幅65×奥行66 から '
        u'**奥行57.0 × 幅70.5 (= v8.4 以前) へ戻し**、 install.doorFront = 38 だけ残した。'
        u' 実測値まとめ v1.7 には 65×66 と記載があるが、 写真65 からの逆投影は 見付け57.3cm で'
        u'両立しない (見付けが65なら収納高さが272cm でないと成立しない = 天井高240 と矛盾)。'
        u' 2026-08-24 ユーザー判断で 一旦 57×70.5 に戻し、 扉のはみ出し38のみ採用。'
        u' **扉1枚の見付け幅の再実測待ち**。'
        u' これで v8.4 で再現できなくなっていた 実測2件が再び閉じる: '
        u'東面 x160 = LDK北壁内隅 x364 から **204.0** (実測204 ✓) /'
        u' 南面 y354 = LDK南壁 y553.5 から **199.5** (実測199.5 ✓)。'
        u' 西壁チェーン 270 = 収納70.5 + 壁31.0 + 窓165 + 3.5 / 北壁チェーン 261 = 収納57 + 204 も閉合。'
        u' ⚠**はみ出し38 は 片開き単板では 依然として説明できない**: 見付け57.3 (or 実測65) の1枚扉を'
        u'90°開ければ 柱面から 見付けぶん (57〜65) 出るはずで、 38 になるのは 開き角が 40°前後の時。'
        u' 写真68 の全開カットでは 戸は 90°以上開いており 干渉物も無い。'
        u' → **扉1枚の見付け幅 (写真では46.5cm) と 38 をどこからどこまで測ったか** を確認したい (要確認)。')
    applied.append(u'③ F-24 rect 65×66 → 57.0×70.5 (v8.4 以前) / est を true へ戻す / doorFront 38 は維持')

    # ═══ ② はみ出しの定義を統一 (起点をデータで持つ) ═══════════════════════════
    f24['install']['doorNote'] = SWING5 + (
        u' / ⚠片開き単板では 90°開けば見付けぶん (57〜65) 出るはずで 38 と合わない (要確認)')
    f24['install']['doorFrontFrom'] = u'柱(枠)の面'
    f01 = by_id(rd['fixtures'], 'F-01')
    f01['install']['doorFrontFrom'] = u'本体前面 (カウンター東面)'
    f01['install']['doorNote'] = (
        u'実測「逆の壁 (LDK東壁 x790) から 開いたコンロ引き出しまで 117」 から算出 (143.5 - 117)'
        u' / 最大まで引き出した状態での 前面から先端まで')
    applied.append(u'② install.doorFront = 「最大開時に 起点の面から扉/引き出しの先端まで」 に定義統一'
                   u' (起点は doorFrontFrom でデータ化: 4室=柱(枠)の面 / キッチン=本体前面)')

    # walls を 部屋ポリゴン + 開口 から再生成 (S2 整合を機械的に保証)
    rd['walls'] = wallgen.regen(json.loads(json.dumps(rd)), OPEN_MATCH_TOL)
    rd['meta']['version'] = '6.12'
    rd['meta'].setdefault('notes', []).append(
        u'★v6.12 (2026-08-24 野沢さん回答4件) ①4.5帖 D-02 / 4.8帖 D-04 / WIC D-11 を **折れ戸** に是正'
        u' (構成だけを openings[].fold がデータで持ち、描画/開閉は JS の共通コード1本。LDK の F-24 は'
        u'片開き1枚のまま)。 ②「はみ出し」= **最大まで開いた状態で 柱から扉の先端まで** に定義統一し'
        u' install.doorFront の意味・ツールチップ文言・起点 (doorFrontFrom) を揃えた。'
        u' ③F-24 の rect を v8.4 以前 (57.0×70.5) へ戻し 実測204 / 199.5 の閉合を回復 (doorFront38 は維持)。'
        u' ④実測「空気口の壁→WICの左側 44」 の終点=壁 を反映し D-11 の東端を x1013→x1011 (幅58) へ。'
        u' ⚠折れ戸の畳み込み幾何と実測は D-02 / D-11 は一致するが D-04 のみ 5cm 合わない (label に詳細)。')

    # ── 対象外の要素が1つも変わっていないことを機械 assert ──
    TOUCHED = {'D-02', 'D-04', 'D-11', 'F-24', 'F-01'}
    J = lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True)
    for key in ('rooms', 'openings', 'outlets', 'aircons', 'fixtures', 'lights', 'zones'):
        old = dict((e['id'], e) for e in rd_before[key])
        new = dict((e['id'], e) for e in rd[key])
        assert set(new) == set(old), u'%s の ID 集合が変わった: +%s / -%s' % (
            key, set(new) - set(old), set(old) - set(new))
        for i in old:
            if J(old[i]) != J(new[i]):
                assert i in TOUCHED, u'対象外の要素が変わった: %s (%s)' % (i, key)
    print(u'  機械照合: 変更したのは %s の5件 + walls 再生成のみ' % ', '.join(sorted(TOUCHED)))

    src = (src[:m.start()] + 'var ROOM_DATA = '
           + json.dumps(rd, ensure_ascii=False, separators=(',', ':')) + ';\n' + src[m.end():])

    # ═══ JS ①: 折れ戸のレジストリ (共通ロジック) ═════════════════════════════
    old = u"""function buildOpeningPanel(g, o, s, e, sill, top, horiz, wc, outSign, c) {"""
    new = u"""// ═══ ★v8.5 収納建具「折れ戸」のレジストリ ═══
//   4.5帖 (D-02) / 4.8帖 (D-04) / 6.2帖WIC (D-11) の3室は 両開き扉ではなく **折れ戸**
//   (2枚1組が面どうしに畳まれて 吊元の側方へ寄る)。 v8.4 まで 90°回転する開き戸として描いていた。
//   3室ぶんの描画を別々に書くと 1室を直しても他室へ伝わらないので、
//   FRIDGE_MODELS / BED_MODELS と同じ流儀で **構成だけを ROOM_DATA がデータで持ち、
//   描画と開閉は buildOpeningPanel の折れ戸ブロック 1本だけ** にする。
//
//   ROOM_DATA: openings[].fold = {
//     sets   … 組数 (2 = 開口の左右から1組ずつ / 1 = 片側だけ)
//     panels … 1組の枚数 (2 = 2枚折れ)
//     hinge  … 吊元。 'outer' = 各組の外側 (2組の既定) / 'e' | 's' = 1組の時の吊元側
//     panelW … 1枚の幅 [cm]。 null なら 開口幅 ÷ 総枚数 (= 幾何どおり)。 実測が出たらここに入れる
//   }
//   返り値 = 組ごとの [{ hu: 吊元の along 座標, dir: 吊元→戸先の向き(+1/-1), n: 枚数, w: 1枚の幅 }]
function foldDoorSets(o, s, e) {
  const f = o && o.fold;
  if (!f) return null;
  const sets = Math.max(1, f.sets || 1), n = Math.max(2, f.panels || 2);
  const w = Number(f.panelW) || ((e - s) / (sets * n));
  const out = [];
  for (let i = 0; i < sets; i++) {
    // 吊元は 既定 = 各組の外側 (両端)。 1組だけの時は fold.hinge / o.hinge で東西どちらかを選ぶ
    const atE = (sets === 1) ? (f.hinge === 'e' || o.hinge === 'e') : (i === sets - 1);
    out.push({ hu: atE ? e : s, dir: atE ? -1 : 1, n: n, w: w });
  }
  return out;
}

function buildOpeningPanel(g, o, s, e, sill, top, horiz, wc, outSign, c) {"""
    src = rep1(src, old, new, u'JS① foldDoorSets の追加')

    # ═══ JS ②: 収納扉ブロックに 折れ戸の描画/開閉を追加 ═══════════════════════
    old = u"""      pickables.push(frame);                                 // 枠は静的 (クリック対象のみ)
      const leaves = o.leaves || (/両開き/.test(o.label || '') ? 2 : 1);"""
    new = u"""      pickables.push(frame);                                 // 枠は静的 (クリック対象のみ)
      const fsets = foldDoorSets(o, s, e);
      if (fsets) {
        // ★v8.5 折れ戸 (3室 共通コード)。 1枚ごとに Group を作り、**Group の原点 = そのパネルの丁番**。
        //   閉: 全パネルが壁面上に一列 / 開: 蛇腹に畳まれて 吊元の側方へ寄る (偶数枚目は外向き・
        //   奇数枚目は折り返し)。 丁番位置と向きだけを差し替えるので 開閉は既存の doors レジストリ
        //   (位置 + rotation.y の組を持つ) にそのまま乗る。
        //   → 開いた時の 壁面からの出 ≒ パネル1枚の幅 = 実物の折れ戸と同じ挙動。
        const FT = 3.4;                                      // 建具厚 (畳んだ時の重なりピッチ)
        fsets.forEach(function (fs) {
          for (let j = 0; j < fs.n; j++) {
            const hu0 = fs.hu + fs.dir * fs.w * j;           // 閉時の このパネルの丁番 (along)
            const lu = fs.dir * fs.w / 2;                    // 丁番→パネル中心 (ローカル)
            const pg = new THREE.Group();
            pg.position.set(horiz ? hu0 : wc, 0, horiz ? wc : hu0);
            g.add(pg);
            const leaf = addBox(pg, horiz ? fs.w - 1.2 : FT, hgt - 5, horiz ? FT : fs.w - 1.2,
              horiz ? lu : 0, cy - 1, horiz ? 0 : lu, 0xf7f5f0,
              { kind: 'fixture', info: o.label || '収納扉', doorId: door.id });
            pickables.push(leaf);
            if (j === fs.n - 1) {                            // 取っ手は各組の戸先 (最後の1枚の自由端寄り)
              const hu2 = lu + fs.dir * fs.w * 0.36;
              addBox(pg, horiz ? 2 : 7, 12, horiz ? 7 : 2,
                horiz ? hu2 : 0, cy, horiz ? 0 : hu2, 0x9a9a9a, { doorId: door.id });
            }
            // 開いた状態: 偶数枚目の丁番は壁面上 / 奇数枚目は側方へ w 出た所。 向きは1枚ごとに反転
            const oV = wc + sI * ((j % 2 === 0) ? 0 : fs.w);
            const oU = fs.hu + fs.dir * FT * (j + 0.5);
            const rot = (horiz ? -1 : 1) * sI * fs.dir * (Math.PI / 2) * ((j % 2 === 0) ? 1 : -1);
            door.parts.push({ mesh: pg, cx: pg.position.x, cz: pg.position.z, crot: 0,
                              ox: horiz ? oU : oV, oz: horiz ? oV : oU, orot: rot });
          }
        });
        return;
      }
      const leaves = o.leaves || (/両開き/.test(o.label || '') ? 2 : 1);"""
    src = rep1(src, old, new, u'JS② 折れ戸の描画ブロック')

    # ═══ JS ③: ツールチップ 「種類」 に折れ戸 ═══════════════════════════════
    old = u"""  const leaves = o.leaves || (/両開き/.test(lb) ? 2 : 1);
  if (leaves >= 4) return '両開き扉 2組' + leaves + '枚';"""
    new = u"""  if (o.fold) {                                     // ★v8.5 折れ戸 (構成は ROOM_DATA の fold)
    const n = Math.max(2, o.fold.panels || 2), st = Math.max(1, o.fold.sets || 1);
    return '折れ戸 (' + n + '枚折れ' + (st > 1 ? '×' + st + '組' : '') + '=' + (n * st) + '枚' +
           (o.fold.panelW ? '・各' + tipN(o.fold.panelW) + 'cm' : '') + ')';
  }
  const leaves = o.leaves || (/両開き/.test(lb) ? 2 : 1);
  if (leaves >= 4) return '両開き扉 2組' + leaves + '枚';"""
    src = rep1(src, old, new, u'JS③ tipDoorKind の折れ戸')

    old = u"""  const he = (o.hinge === 'e') || /ヒンジ南/.test(o.label || '');"""
    new = u"""  if (o.fold && Math.max(1, o.fold.sets || 1) > 1) parts.push('吊元: 両端 (各組の外側)');   // ★v8.5
  const he = (o.hinge === 'e') || /ヒンジ南/.test(o.label || '');"""
    src = rep1(src, old, new, u'JS③ tipDoorMotion の吊元')

    # ═══ JS ④: はみ出しの文言を 確定した定義に統一 ═══════════════════════════
    old = u"""  if (N(ins.doorFront) !== null) {
    rows.push(oKind + 'の開放: 本体前面から ' + tipN(N(ins.doorFront)) + 'cm' +
              (ins.doorNote ? ' (' + ins.doorNote + ')' : ''));
  }"""
    new = u"""  if (N(ins.doorFront) !== null) {
    // ★v8.5 doorFront の定義を ユーザー確定の1つに統一:
    //   「**最大まで開いた状態**で、起点の面から **開いた扉/引き出しの先端** までの距離」。
    //   起点は要素ごとに違う (クローゼット = 柱(枠)の面 / キッチン = 本体前面) ので
    //   install.doorFrontFrom がデータで持つ (アプリ側に室ごとの分岐を作らない)。
    rows.push(oKind + 'の開放: ' + (ins.doorFrontFrom || '本体前面') + 'から先端まで ' +
              tipN(N(ins.doorFront)) + 'cm (最大まで開いた状態)' +
              (ins.doorNote ? ' (' + ins.doorNote + ')' : ''));
  }"""
    src = rep1(src, old, new, u'JS④ installClearanceRows の文言')
    applied.append(u'JS 折れ戸の共通コード (foldDoorSets + 描画/開閉) / ツールチップ「種類」「開放」 の是正')

    assert sha(CS_PAT, src) == cs_before, u'CATALOG_SEED が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用%d件' % len(applied))
    for a in applied:
        print(u'  ' + a)
    print(u'ROOM_DATA v6.11 → v6.12 / CATALOG_SEED sha256 %s (不変)' % cs_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

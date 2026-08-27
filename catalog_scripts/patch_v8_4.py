# -*- coding: utf-8 -*-
u"""v8.4: 野沢さん 2026-08-24 追加実測の反映。冪等 (再実行で「適用0件 / skip 全件」)。

ROOM_DATA v6.10 -> v6.11 / CATALOG_SEED は不変 (sha256 前後一致を assert)。

  A. 洋室6.2帖 高所小窓 WIN-06 / WIN-07 — 実測で sill / height / y位置 / 離隔 を是正
  B. 洋室6.2帖 カーテンレール F-51 — 天井から30cm の実測へ (y も小窓と同じ 2.0 を戻す)
  C. キッチン シンク F-02 — ボウル深さ 19cm の est を外す (実測と一致)
  D. 洋室6.2帖 空気口 F-55 を新規追加 (東壁 x1055 / y375〜396 / 床上24〜45)
  E. LDK 左収納 F-24 — 実測 横(東西)65 × 奥行(南北)66 へ是正
  F. 「扉/引き出しを開いた時のはみ出し」 を **既存の汎用機構 install.doorFront に合流**
     クローゼット専用の作り込みをせず、4室 + キッチン を同じ1つのフィールドで持つ:
       D-02 (洋室4.5) 36 / D-04 (洋室4.8) 35 / D-11 (WIC) 32 / F-24 (LDK) 38 / F-01 (キッチン) 26.5
  G. JS — installClearanceRows() を 建具 (openings) と 設備 (fixtures) のツールチップにも配線し、
     キッチン引き出しの張り出し量 (旧: 定数 45 のベタ書き) を install.doorFront から読ませる

★実測が正。 写真からの逆投影と食い違った箇所は 実測を採用し、 差は報告に残す (下記コメント参照)。
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

MEAS = u'★v8.4 【野沢さん 2026-08-24 実測 — 実測が正】'


def sha(pat, s):
    return hashlib.sha256(re.search(pat, s, re.S).group(1).encode()).hexdigest()


def by_id(arr, i):
    for e in arr:
        if e['id'] == i:
            return e
    raise AssertionError(u'%s が見つからない' % i)


def main():
    src = io.open(P, encoding='utf-8').read()
    cs_before = sha(CS_PAT, src)
    m = re.search(RD_PAT, src, re.S)
    rd = json.loads(m.group(1))
    rd_before = json.loads(m.group(1))          # 対象外の要素が動いていないかの照合用

    if rd['meta'].get('version') == '6.11' and '"F-55"' in m.group(1) and 'installClearanceRows(o)' in src:
        print(u'適用0件 / skip 全件 (既に ROOM_DATA v6.11 + F-55 + JS配線 = 適用済み)')
        return 0
    assert rd['meta'].get('version') == '6.10', u'ROOM_DATA が v6.10 でない: %s' % rd['meta'].get('version')

    applied = []

    # ═══ A. 洋室6.2帖 高所小窓 WIN-06 / WIN-07 ═══════════════════════════════
    #   実測 (天井240 基準): 枠上端 = 天井から39 → 床上201.0 / 枠下端 = 天井から88 → 床上152.0
    #                        → 高さ 49.0 (v7.0 の逆投影 46.0 より +3.0)
    #   実測: 2窓の離隔 17 (逆投影 16.5)
    #   実測: エアコン側の壁端 (= 東壁 北の入隅 y107) → 左(北)の小窓枠 左端 まで 89 (逆投影 91.0)
    #   幅44.0 は今回の実測に含まれないので 逆投影値 (43.9 / 43.8) を据え置く。
    W6_Y0, WW, GAP, SILL, HGT = 107.0 + 89.0, 44.0, 17.0, 152.0, 49.0     # 196.0
    W7_Y0 = W6_Y0 + WW + GAP                                              # 257.0
    NOTE_A = (
        MEAS + u'天井(240)からの実測 枠上端39 / 枠下端88 → **床上 152.0 〜 201.0 (高さ49.0)**。'
        u' v7.0 の3消失点逆投影 (sill157.5 / 高さ46.0 / 上端203.5) に対し 下端-5.5 / 上端-2.5 / 高さ+3.0 の差があり '
        u'**実測を採用**した。 高さが3cm増えたのは 逆投影が 下端に「窓台上端」・上端に「額縁上端」 という'
        u'チグハグな基準を使っていたためで、 写真を再較正して 額縁外法を測ると 49.6cm と出て 実測49 と一致する。'
        u' 2窓の離隔も 実測17 を採用 (逆投影の再測は 16.6 なので実質同値)。'
        u' y位置は 実測「エアコン側の壁端 (東壁 北の入隅 y107) から 左の小窓枠 左端 まで89」 で確定し '
        u'WIN-06 198.0→**196.0** / WIN-07 258.5→**257.0** (ともに北へ2.0)。'
        u' 東壁チェーン 311 = 89 + 44 + 17 + 44 + **117.0** で閉じる (南の壁 115.5→117.0)。'
        u' ⚠**天井起点の実測3件 (枠上39 / 枠下88 / レール30) がそろって 写真より約3cm低く出る**一方、'
        u'床起点の実測 (空気口の下24) は写真と完全一致する。 メジャーのゼロを 廻り縁/見切りの下端に取ったか、'
        u'実際の天井高が240でなく約243 のどちらかの可能性 — **床〜天井の直接採寸を要依頼**。')
    for oid, y0 in (('WIN-06', W6_Y0), ('WIN-07', W7_Y0)):
        o = by_id(rd['openings'], oid)
        o['wallFrom'], o['wallTo'] = [1055.0, y0], [1055.0, y0 + WW]
        o['sillH'], o['height'], o['est'] = SILL, HGT, False
        o['label'] += NOTE_A
    applied.append(u'A WIN-06/07 sill157.5→152.0 / 高さ46.0→49.0 / y を北へ2.0 / 離隔16.5→17.0')

    # ═══ B. カーテンレール F-51 ═════════════════════════════════════════════
    f51 = by_id(rd['fixtures'], 'F-51')
    assert f51['rect'] == [1043.0, 185.5, 12.0, 129.5], u'F-51 の rect が想定と違う'
    f51['rect'] = [1043.0, 183.5, 12.0, 129.5]
    f51['bottomH'] = 208.8                       # レール中心 210.0 (見かけ半幅 1.2)
    f51['label'] += (
        MEAS + u'天井(240)から レールまで 30 → **レール中心 床上210.0** (逆投影の210.7 と0.7差 = 実測を採用し'
        u' 下端 209.5→208.8)。 y は 小窓と同じ逆投影 (同じ写真・同じ較正) から出た値なので、'
        u' 小窓に掛けたのと同じ 2.0cm を同じ向き (北) に戻し y185.5〜315.0 → **y183.5〜313.0**'
        u' (長さ129.5・出6.5・シングル は不変)。'
        u' ⚠「天井から30」 が レール中心 / 下端 / 上端 のどれを指すかは実測メモから確定できない — 中心と解釈した (要確認)。')
    applied.append(u'B F-51 レール中心 210.7→210.0 / y を北へ2.0')

    # ═══ C. シンク F-02 のボウル深さ est を外す ══════════════════════════════
    f02 = by_id(rd['fixtures'], 'F-02')
    assert f02['bottomH'] == 66, u'F-02 の bottomH が想定と違う'
    old_c = u'ボウル深さ19 (h85=天面 / bottomH66=底) は est'
    assert old_c in f02['label']
    f02['label'] = f02['label'].replace(old_c, old_c.replace(u' は est', u'') + (
        u' ' + MEAS + u'「シンクの深さ19」 と一致したので **est を解除 = 実測確定**。'
        u' (写真では追認できない — 俯角19°では手前リムに遮られてボウル底が写らないため'
        u' 「深さ13cm以上」 としか言えない。 否定もされない。)'))
    applied.append(u'C F-02 ボウル深さ19 の est を解除 (実測と一致)')

    # ═══ D. 洋室6.2帖 空気口 F-55 (新規) ═════════════════════════════════════
    #   実測: 縦21 × 横21 / 床から下まで24 / 「WICの壁から空気口の左側まで43」
    #   写真96 の壁面ホモグラフィ (北入隅・南入隅の2本の鉛直線で拘束) で
    #   東壁 (x1055) 上に在ることを確定 (カバー左端のワールドY が画像行に依らず 375.5 一定)。
    #   43 = WIC側の壁面 y418 → 空気口の北(左)端  →  y = 418 - 43 = 375.0 (写真実測 375.5)
    #   4.8帖の F-22 と同じ type='vent' / 同じ「壁面から室内へ薄く出る板」 の描き方に揃える。
    assert not any(f['id'] == 'F-55' for f in rd['fixtures']), u'F-55 が既にある'
    assert max(int(f['id'].split('-')[1]) for f in rd['fixtures']) == 54, u'F の最大が54でない'
    rd['fixtures'].append({
        'type': 'vent', 'room': 'west6_2',
        'label': (
            u'空気口(白の角型ルーバー・縦スリット/洋室6.2 東壁 x1055 の南端寄り/21×21・床上24〜45/'
            u'すぐ南隣に2連プレート(2口コンセント+黄タグ)、その南が WIC側の入隅) ' + MEAS +
            u'新規登録 — 従来 ROOM_DATA に該当要素が無かった。 縦21×横21 / 床から下まで24 /'
            u'「WICの壁から空気口の左側まで43」 で位置を確定: WIC側の壁面 y418 から北へ43 → **y375.0〜396.0**。'
            u' 写真96 の壁面ホモグラフィ (北入隅・南入隅の2本の鉛直線だけで拘束) による実測は'
            u' 左(北)端 Y=375.5 (画像行1160〜1270 で一定 = 小窓と同一平面 = 東壁 上にあることの証明)・'
            u'下端 床上約24 (視差補正後) で、 実測と 0.5cm 以内で一致する。'
            u' 4.8帖の F-22 通気口 と同じ type=vent・同じ「壁面から室内へ4cm出る薄板」 の描き方に揃えた'
            u' (専用実装を作らない)。'
            u' ⚠壁からの出 4.0 は est — 写真ではカバーの見かけが24cm (実測21) あり 3〜4cm 手前に出ているが'
            u' 奥行を直接は測れない。'
            u' ⚠実測「空気口の壁から WIC の左側まで44」 は **未反映** — 「WICの左側」 が WIC扉開口の東端か'
            u' WIC の壁かを写真で確定できず (y418 面には既知点が入隅1点しかなく平面較正が組めない)、'
            u' 現データの相当値は W-R62-S3 = x1013〜1055 = 42 で 2cm 差。 D-11 は元々 est だが'
            u' 解釈が未確定のため動かしていない (要確認)。'),
        'est': True,
        'rect': [1051.0, 375.0, 4.0, 21.0],      # 東壁 x1055 から室内 (西) へ 4cm 出る
        'bottomH': 24.0, 'h': 45.0,
        'shortLabel': u'空気口', 'short': u'空気口',
        'id': 'F-55', 'name': u'空気口', 'minor': True, 'showDim': False,
    })
    applied.append(u'D F-55 空気口を新規追加 (東壁 x1055 / y375〜396 / 床上24〜45 / 21×21)')

    # ═══ E. LDK 左収納 F-24 — 実測 横(東西)65 × 奥行(南北)66 ═══════════════════
    #   原典 実測値まとめ v1.7 / コンセント付き v1.4 を4倍拡大して矢印の指す辺を確認:
    #     「65」= 横向き矢印 (西壁内面 → 収納の東外端)   = 東西 = x = 見付け幅
    #     「66」= 縦向き矢印 (収納の北内面 → 扉線)        = 南北 = y = 奥行
    #     扉記号 = 四分円の弧 + 直線1本 = 片開き1枚・吊元=西・南(LDK側)へ開く ← 現ラベルと一致
    f24 = by_id(rd['fixtures'], 'F-24')
    assert f24['rect'] == [103.0, 283.5, 57.0, 70.5], u'F-24 の rect が想定と違う'
    f24['rect'] = [103.0, 283.5, 65.0, 66.0]
    f24['est'] = False
    f24['label'] += (
        u' ' + MEAS + u'野沢さん明示「F-24 は 横65, 奥行き66 って実測値にあるでしょ」。'
        u' 原典 (実測値まとめ v1.7 / コンセント付き v1.4) を4倍拡大して矢印の指す辺を確認したところ、'
        u' **「65」= 横向き矢印 (西壁内面→収納の東外端) = 東西(x) = 見付け幅** /'
        u' **「66」= 縦向き矢印 (収納の北内面→扉線) = 南北(y) = 奥行** だった。'
        u' → rect を 奥行57.0×幅70.5 から **幅(x)65.0 × 奥行(y)66.0** へ是正 (x103〜168 / y283.5〜349.5)。'
        u' 扉記号は 四分円の弧+直線1本 = 片開き1枚・吊元=西・南(LDK側)へ開く で 従来ラベルと一致 (写真68 の全開'
        u'カットでも 単板・枠側に丁番4個・下レール無し を確認、折れ戸でも両開きでもない)。'
        u' ⚠**同じ実測メモの中で 65 と 204 が両立しない**: 「東面→LDK北壁内隅 204」 を満たすには 見付け57 が必要で、'
        u' 幅65 だと 364-168 = **195 (実測204 と -9)**。 また 「南面→LDK南壁 199.5」 は 奥行66 だと'
        u' 553.5-349.5 = **204.0 (実測199.5 と +4.5)**。'
        u' ⚠**写真は 204 側 (=57) を支持する**: 写真65 は扉面がほぼ正対 (消失点 x≈32000px / 短縮率0.997) で、'
        u' 見付け/収納高さ = 498/2085px = 0.2388。 収納は床〜天井 (240) なので 見付け = **57.3cm** と出る'
        u' (= 天井高に依らない比の議論。 見付けが65なら収納高さは272cmでないと成立しない)。'
        u' それでも **実測を正とする方針に従い 65/66 を採用**した。 次回内覧で 扉1枚の見付け (写真では46.5cm) を'
        u' 直接測ってもらえれば確定する。'
        u' なお 西壁・北壁のチェーンは 収納の寸法を変えても自動的に閉じる'
        u' (西壁 270 = 66 + 壁35.5 + 窓165 + 3.5 / 北壁 261 = 65 + 196) ため、'
        u' **WIN-02・F-25 など周囲の要素は一切動かしていない**。'
        u' (旧ラベルの「西壁チェーン 収納70.5+壁11+窓165+壁23.5」 の 11/23.5 は誤記で、実データは 31/3.5。)')
    applied.append(u'E F-24 rect 57.0×70.5 → 幅(x)65.0 × 奥行(y)66.0')

    # ═══ F. 「開いた時のはみ出し」 を install.doorFront に合流 ═══════════════════
    #   4室 + キッチン を **同じ1つの汎用フィールド** で持つ (クローゼット専用の作り込みをしない)。
    #   install は もともと カタログ商品の据付条件 (冷蔵庫の放熱すきま等) 用に v7.5 で入れた汎用機構で、
    #   doorFront = 「扉/引き出しを開いた時に前方へ必要な寸法 (本体前面から)」。 意味がそのまま一致する。
    SWING = u'実測 = 柱部分から扉がはみ出す量'
    for eid, cm, arr, note in (
        ('D-02', 36.0, rd['openings'], u'洋室4.5 クローゼット'),
        ('D-04', 35.0, rd['openings'], u'洋室4.8 クローゼット'),
        ('D-11', 32.0, rd['openings'], u'洋室6.2 WIC'),
        ('F-24', 38.0, rd['fixtures'], u'LDK 左収納'),
    ):
        e = by_id(arr, eid)
        assert 'install' not in e, u'%s に install が既にある' % eid
        e['install'] = {'doorFront': cm, 'openKind': 'door', 'doorNote': SWING, 'est': False}
    f24['install']['doorNote'] = SWING + u' / ⚠片開き単板なので 90°開けば見付けぶん出るはずで 38 と合わない (要確認)'
    f01 = by_id(rd['fixtures'], 'F-01')
    assert 'install' not in f01
    f01['install'] = {
        'doorFront': 26.5, 'openKind': 'drawer',
        'doorNote': u'実測「逆の壁 (LDK東壁 x790) から 開いたコンロ引き出しまで 117」 から算出 (143.5 - 117)',
        'est': False}
    f01['label'] += (
        u' ' + MEAS + u'コンロ下引き出しの張り出しを install.doorFront = **26.5** で持つ'
        u' (キッチン専用の定数にせず、 クローゼット4室と同じ汎用フィールドに合流)。'
        u' 根拠: 「逆の壁から、開いたコンロ引き出しまで117」。 実在する壁で 117 が成立するのは'
        u' **LDK東壁 x790 のみ** (カウンター東面646.5 から東壁まで143.5 → 143.5-117 = 26.5)。'
        u' 他候補は不成立 — 背面通路の西壁 x364 は 364+117=481 がカウンター西面572より手前、'
        u' 冷蔵庫仕切りスタブ F-08 x724 は 724-117=607 がカウンター東面より西になる。'
        u' ⚠**実測「コンロの引き出し 30.5」 は前板の高さではない**: 写真38/39 を2通りの較正で独立に測ると'
        u' 天板厚4 / 上段前板21 / 下段前板36 / キックプレート23 で、 30.5 になる段が無い。'
        u' 残る整合解は (a) 下段引き出しの有効内寸高さ (前板36 − レール/逃げ ≒ 30.5)、'
        u' (b) 張り出し量30.5 — の2つ。 (b) なら 30.5+117 = 147.5 が カウンター東面→東壁の実寸になり'
        u' 現データ143.5 と **4cm 差** (カウンターの x 位置は図面トレース由来で実測ハード制約が無い箇所)。'
        u' **どちらか確定できないので カウンターは動かさず、 張り出しは 117 から出る 26.5 を採った** (要確認)。'
        u' ⚠あわせて 写真で判明した現ラベルの誤り (未修正・要確認): 東面の実際の割付は'
        u' 上段=[シンク側 幅67 ハンドル無しの固定ダミー前板 / 幅7 の黒い縦長パネル(正体不明・未登録) /'
        u' 幅31 引き出し / HARMAN コンロ前面63 (左操作+グリル扉+右操作) / 北端 幅12 の細前板]、'
        u' 下段=[幅74 / 幅106 の2枚] で、 「引き出し2列×2段」 とは違う。')
    applied.append(u'F install.doorFront = D-02 36 / D-04 35 / D-11 32 / F-24 38 / F-01 26.5 (汎用機構に合流)')

    # walls を 部屋ポリゴン + 開口 から再生成 (S2 整合を機械的に保証)
    rd['walls'] = wallgen.regen(json.loads(json.dumps(rd)), OPEN_MATCH_TOL)
    rd['meta']['version'] = '6.11'
    rd['meta'].setdefault('notes', []).append(
        u'★v6.11 (2026-08-24 野沢さん追加実測) 洋室6.2帖の高所小窓 (sill/高さ/y/離隔) と カーテンレール、'
        u' LDK左収納 F-24 の 見付け65×奥行66、 空気口 F-55 の新規登録、'
        u' 4室クローゼット+キッチンの「開いた時のはみ出し」 を install.doorFront で共通化。'
        u' 実測と写真逆投影が食い違った箇所 (小窓の絶対高さ 約3cm / F-24 の見付け 65 vs 57.3) は'
        u' いずれも **実測を採用**し、 差の内訳を各要素の label に残した。')

    # ── 対象外の要素が1つも変わっていないことを機械 assert ──
    TOUCHED = {'WIN-06', 'WIN-07', 'F-51', 'F-02', 'F-55', 'F-24', 'D-02', 'D-04', 'D-11', 'F-01'}
    J = lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True)
    for key in ('rooms', 'openings', 'outlets', 'aircons', 'fixtures', 'lights', 'zones'):
        old = dict((e['id'], e) for e in rd_before[key])
        new = dict((e['id'], e) for e in rd[key])
        assert set(new) - set(old) == ({'F-55'} if key == 'fixtures' else set()), \
            u'%s に想定外の追加: %s' % (key, set(new) - set(old))
        assert not (set(old) - set(new)), u'%s から削除された: %s' % (key, set(old) - set(new))
        for i in old:
            if J(old[i]) != J(new[i]):
                assert i in TOUCHED, u'対象外の要素が変わった: %s (%s)' % (i, key)
    print(u'  機械照合: 変更したのは %s の10件 + walls 再生成のみ' % ', '.join(sorted(TOUCHED)))

    src = (src[:m.start()] + 'var ROOM_DATA = '
           + json.dumps(rd, ensure_ascii=False, separators=(',', ':')) + ';\n' + src[m.end():])

    # ═══ G. JS — 汎用機構の配線 ═══════════════════════════════════════════════
    # (G-1) 建具 (openings) のツールチップに 据付/はみ出し行を出す
    old = """      rows.push('種類: ' + tipDoorKind(o));
      const mo = tipDoorMotion(o);
      if (mo) rows.push(mo);"""
    new = """      rows.push('種類: ' + tipDoorKind(o));
      const mo = tipDoorMotion(o);
      if (mo) rows.push(mo);
      // ★v8.4 「開いた時のはみ出し」 は install.doorFront (v7.5 の汎用機構) をそのまま使う。
      //   クローゼット専用の分岐を作らず、 建具・設備・カタログ商品 が同じ1つのフィールドを共有する。
      installClearanceRows(o).forEach(function (r) { rows.push(r); });"""
    assert old in src
    src = src.replace(old, new, 1)

    # (G-2) 設備 (fixtures) のツールチップにも同じ行を出す (F-24 / F-01 用)
    old = """    const inner = tipFixInner(o);
    if (inner) rows.push(inner);"""
    new = """    const inner = tipFixInner(o);
    if (inner) rows.push(inner);
    installClearanceRows(o).forEach(function (r) { rows.push(r); });   // ★v8.4 扉/引き出しのはみ出し"""
    assert old in src
    src = src.replace(old, new, 1)

    # (G-3) キッチン引き出しの張り出し量を install.doorFront から読む (定数 45 のベタ書きをやめる)
    old = """    const KD = 45, fE = x + dx;"""
    new = """    // ★v8.4 引き出しの張り出しは ROOM_DATA の install.doorFront から読む (旧: 定数45 のベタ書き)。
    //   実測「逆の壁 (LDK東壁 x790) から 開いたコンロ引き出しまで117」 → 143.5 - 117 = 26.5cm。
    const KD = ((f.install && Number(f.install.doorFront)) || 45), fE = x + dx;"""
    assert old in src
    src = src.replace(old, new, 1)
    applied.append(u'G JS 建具/設備のツールチップに installClearanceRows を配線 + キッチンの張り出しを data 駆動化')

    assert sha(CS_PAT, src) == cs_before, u'CATALOG_SEED が変化した'
    io.open(P, 'w', encoding='utf-8', newline='').write(src)
    print(u'適用%d件' % len(applied))
    for a in applied:
        print(u'  ' + a)
    print(u'ROOM_DATA v6.10 → v6.11 / CATALOG_SEED sha256 %s (不変)' % cs_before[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
u"""nozaROOM v7.5 — room.html への冪等パッチ (CATALOG_SEED v2.2 → v2.3)

やること:
  ① CATALOG_SEED に 「冷蔵庫 三菱 MDシリーズ 451L」 (MR-MD45N) を1点追加。
     公式 幅600 × 奥行699 × 高さ1826mm → w60 / d69.9 / h182.6 / room=ldk / zone=kitchen / type='fridge'
     既存の 「冷蔵庫 日立 HZC 540L」 (R-HZC54Y XH) は **削除しない** (検討中の比較対象)。
  ② **冷蔵庫の3Dモデルをデータ駆動へ共通化**。 これまでは
        `type === 'fridge' && /HZC/.test(nm)` … 日立専用の描画 (べた書き)
        `type === 'fridge'`                   … 汎用の簡易2ドア
     という 「機種ごとに if を足す」 形だった。 機種が増えるたびに描画コードが分岐して
     1機種直しても他へ伝わらないので、 **扉の段構成だけをデータ (FRIDGE_MODELS) で持ち、
     描画は1本の共通コードに集約** する (TOP_STACK_TYPES / WALL_HANG_TYPES と同じレジストリ流儀)。
     日立 (フレンチ6ドア) と 三菱 (5ドア・真ん中野菜室・1枚扉) を同じコードで描く。
     → 新機種は FRIDGE_MODELS に 1エントリ足すだけ。
     ⚠ 日立の見た目は **1メッシュも変えない** (snap_fridge_mesh.py で before/after 台帳を機械照合)。
  ③ **据付必要すきま (放熱スペース) の汎用フィールド `install`** を新設し、
     家具シートの寸法サマリー (v6.4 itemDimSummaryHtml) に1行足す。
     冷蔵庫専用にせず 「カタログ商品が持てる設置条件」 として実装する
     (洗濯機・オーブン等も install を足すだけで同じ行が出る)。
     日立 R-HZC54Y XH にも 既に specNote に文章で書いてあった値を install として構造化する
     (= 既存商品への唯一の差分。 specNote 本文は変更しない)。

安全装置:
  * ROOM_DATA の sha256 が パッチ前後で **不変** であることを assert (今回は触らない)
  * CATALOG_SEED の sha256 が **変わる** ことを assert
  * 既存32商品は 日立の `install` 追加 1点を除き **完全に無変更** であることを assert
  * 2回目以降の実行は 「適用 0 / skip N」 で終わる (冪等)

実行:  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v7_5.py
"""
import copy
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, 'room.html')

CATALOG_SHA_BEFORE = '5e5f4633d6926661ec002f23726eb302255b4a6a8d2d823b245a54414226ee3d'

applied, skipped, problems = [], [], []


def ok(t):
    applied.append(t)
    print(u'  [APPLY] ' + t)


def sk(t):
    skipped.append(t)
    print(u'  [skip ] ' + t)


def die(t):
    print(u'  [FAIL ] ' + t)
    problems.append(t)


src = io.open(TARGET, encoding='utf-8').read()
orig = src


def seed_block(s):
    m = re.search(r'var CATALOG_SEED = (\{.*?\});\n', s, re.S)
    assert m, 'CATALOG_SEED が見つからない'
    return m.group(1)


def room_block(s):
    m = re.search(r'var ROOM_DATA = (\{.*?\});\n', s, re.S)
    assert m, 'ROOM_DATA が見つからない'
    return m.group(1)


ROOM_SHA_BEFORE = hashlib.sha256(room_block(src).encode('utf-8')).hexdigest()
seed_before = seed_block(src)
SEED_OBJ_BEFORE = json.loads(seed_before)
ITEMS_BEFORE = copy.deepcopy(SEED_OBJ_BEFORE['items'])
if hashlib.sha256(seed_before.encode('utf-8')).hexdigest() != CATALOG_SHA_BEFORE:
    if 'MR-MD45N' not in seed_before:
        die(u'CATALOG_SEED の sha256 が想定 (5e5f4633…) と違い、 かつ MR-MD45N も未適用 '
            u'— 想定外の版なので中断する')
        sys.exit(1)


def edit(tag, old, new, marker):
    u"""old → new の単発置換。 marker が既にあれば skip。 old が無い/複数あれば FAIL。"""
    global src
    if marker in src:
        sk(tag)
        return
    n = src.count(old)
    if n != 1:
        die(u'%s: アンカーが %d 箇所 (1 でない) — %r' % (tag, n, old[:70]))
        return
    src = src.replace(old, new, 1)
    ok(tag)


# ═══════════════════════════════════════════════════════════════════
# ① CATALOG_SEED: 三菱 MR-MD45N を1点追加 + 日立に install を構造化
# ═══════════════════════════════════════════════════════════════════
MD45N_SPEC = (
    u'三菱電機 冷蔵庫「置けるスマート大容量」MDシリーズ MR-MD45N '
    u'(451L・5ドア・右開き・真ん中野菜室・2026年1月23日発売・オープン価格)。'
    u'★出典 = 三菱電機 公式製品ページ '
    u'https://www.mitsubishielectric.co.jp/home/reizouko/product/mr-md45n/index.html / '
    u'公式 製品仕様ページ .../mr-md45n/spec/index.html / '
    u'公式 据付必要寸法図 .../mr-md45n/img/img_size_01.png / '
    u'公式 各室定格内容積図 .../mr-md45n/img/img_size_02.png / '
    u'公式 取扱説明書PDF (mr-md45n_ib.pdf) / 三菱電機WIN2K (pid=357235)。'
    u'★公式 外形寸法: 幅600 × 奥行699 × 高さ1,826mm → W60 × D69.9 × H182.6cm。'
    u'⚠奥行の取り方: 公式表記の「奥行 69.9cm」は **(ドア角まで)** = 扉前面までの値 '
    u'(公式据付必要寸法図の青字注記そのまま)。同図には別に **709mm (脚カバー含む)** も入っている。'
    u'**「ハンドルを除く」に相当する注記は公式に存在しない** '
    u'(取扱説明書48ページ全文にもドアハンドルの寸法注記は無く、MDシリーズは'
    u'扉前面より前へ出っ張る縦ハンドルを持たないフラット扉のため)。'
    u'★公式 定格内容積 451L = 冷蔵室243L〈191L〉/ 製氷室18L〈4L〉/ 瞬冷凍室22L〈12L〉/ '
    u'野菜室87L〈59L〉/ 冷凍室81L〈54L〉(〈〉= 食品収納スペースの目安)。'
    u'質量106kg / 年間消費電力量251kWh/年 / 運転音 約15dB(A) / 自動製氷あり。'
    u'★据付必要すきま: **左右 各0.5cm以上・上部 5cm以上** '
    u'(取扱説明書 p8 の本文 + 公式据付必要寸法図の「5 ←600→ 5」「50」表記の2点が一致)。'
    u'→ 設置に必要な幅 610mm。⚠背面のすきまは **公式に数値の記載なし** '
    u'(取説は「音や壁の汚れ・変色、結露が気になるときは壁から離す」という定性的記述のみ / '
    u'据付図の側面図では本体背面が壁線に接している) → install の back は 0 としている。'
    u'公式注記「設置条件により若干異なることがありますので10mm程度余裕をとってください」あり。'
    u'★ドア開放時 (公式据付必要寸法図 上面図に印字されている数値は次の2つだけ): '
    u'前後方向 **1,270mm** (背面基準線〜扉先端) / 側方への張り出し **411mm** (本体側面から外側へ)。'
    u'→ 本体前面から前方へは 1,270 − 699 = **571mm**。'
    u'⚠この2つが 90度開放時 / 最大開放時 の どちらに対応するかの **ラベルは図に無い** ので、'
    u'両方を確保する安全側で見ること。'
    u'⚠**野菜室・冷凍室・製氷室・瞬冷凍室の引き出し時の前方張り出しは公式に記載なし** '
    u'(取説全文・前年モデル MR-MD45M の取説にも無し)。'
    u'★ヒンジ/ハンドル: 右開き = **ヒンジは正面から見て右、扉は右へ開く**。'
    u'公式据付必要寸法図の上面図で ドアの回転中心が本体の右前角にあり 張り出し411mmが右方向であること、'
    u'および 公式ドア開放写真 (img_md45n_white_open.png) で扉が右へ開き扉ポケットが左を向いていることの2点で確定。'
    u'⚠**縦ハンドルは無い**: 公式スタジオ画像 (img_pro_mr_md45n.jpg) を拡大確認したところ、'
    u'冷蔵室扉の前面は完全にフラットで、**扉の下端に全幅の横一文字シルバー凹みグリップ**がある。'
    u'各引き出しも同様に**前板の上端に全幅の横グリップ**。'
    u'(価格.com のスペック表では W=樹脂ハンドル / H=アルミハンドル と表記)。'
    u'★カラー (公式): W = フラットリネンホワイト (JAN 4573637027338) / '
    u'H = フラットアンバーグレー (JAN 4573637027345) の2色。'
    u'⚠★未特定 (要確認): 店頭POPの型番表記 `MRMD45N WJ` / POPのバーコード JAN **4573637027659** '
    u'のカラー名は **特定できなかった** (2026-08-23 調査)。'
    u'判明したのは次の3点 — ①`MR-MD45N-WJ` という形名自体は実在する '
    u'(三菱電機 純正部品 給水タンク組立 M20ZF9520 の適合機種一覧に '
    u'W / H / WJ / HJ / LW / LH / LWJ / LHJ の8形名が並ぶ。L=左開き)。'
    u'②三菱電機公式 (製品ページ・WIN2K・取説PDF全48p) には -WJ / -HJ の記載が一切無く、'
    u'公式のカラーは W / H の2色だけ。'
    u'③価格.com・ヨドバシ・ビック・ヤマダ・ケーズ・エディオン・ノジマ・楽天・Yahoo!・Amazon を横断しても '
    u'-WJ の販売ページは0件、JAN 4573637027659 も検索0件 '
    u'(コード自体は チェックデジット有効・4573637=三菱電機のGS1事業者プレフィックスで W と同一ブロック)。'
    u'→ 形名が W↔WJ / H↔HJ と1対1で対応し色数が増えていないことから '
    u'**J は新色ではなく流通ルート違いの枝番の可能性が高い**が、これは構造からの推測で裏付け出典は無い。'
    u'**本カタログは指示どおり暫定で W (フラットリネンホワイト) を採用**しているので、'
    u'実機が グレー系なら 家具シートのカラースウォッチで H に切り替えること。'
    u'確定させるには 三菱電機お客様相談センターに JAN を伝えて照会するか 店頭で実機の色を確認する。'
    u'★カラーの16進値は est: W #edece9 / H #625a52 は '
    u'公式製品写真 (img_pro_mr_md45n.jpg / img_md45n_white_close.png / _gray_close.png) の '
    u'扉面を画素実測したレンジ (W #c7c6c6〜#e9e8e6 中央値#dedddc / H #4e453e〜#7a736b 中央値#5f5851) から、'
    u'写真が陰影込みであることを見込んで素材色として1段明るく取った値 '
    u'(三菱は色見本の数値を公開していない)。H は名前に反して かなり濃い暖色寄りチャコール。'
    u'★3Dモデル: ★v7.5 で 冷蔵庫の描画を FRIDGE_MODELS (扉の段構成データ) + '
    u'共通コード (buildItemParts の fridge 分岐) に集約した。本機のデータは 下から '
    u'冷凍室 / 野菜室(真ん中) / 製氷室|瞬冷凍室(横並び) / 冷蔵室(1枚扉・縦ハンドル無し・下端グリップ) の4段。'
    u'・冷蔵室扉の下端 = 床から **969mm** (公式据付必要寸法図の側面図に印字) → '
    u'全高比 0.531 は **公式値**。冷蔵室扉の高さ 857mm (1,826−969)。'
    u'・⚠est: 冷凍室の上端 0.210 / 野菜室の上端 0.425 / '
    u'製氷室|瞬冷凍室 を左右に割る位置 -0.02 (中心よりわずかに左 = 製氷室18Lの方が狭い) は '
    u'**公式に段ごとの高さ寸法の記載が無い**ため、公式写真の扉の合わせ目を画素計測して起こした値。'
    u'straight-on の公式ドア開放写真 と 公式スタジオ画像 の2枚で独立に測り、'
    u'両者とも 冷蔵室扉下端が公式969mmと 1.5%以内で一致することを確認したうえで平均している '
    u'(公式値ではない)。'
    u'★一次資料は Box の catalog\\商品公式資料\\MR-MD45N\\ に README 付きで保存。'
)

MD45N_INSTALL = {
    u'left': 0.5, u'right': 0.5, u'top': 5, u'back': 0,
    u'doorFront': 57.1,
    u'doorNote': u'右開き。公式据付図の前後1,270mm − 本体奥行699mm。側方は右へ411mm '
                 u'(開き角のラベルは図に無いので安全側)',
    u'note': u'公式 = 取説p8「左右0.5cm以上・上部5cm以上」+ 公式据付必要寸法図。'
             u'⚠背面のすきまは公式に数値の記載なし (0として扱っている)。'
             u'各引き出しの引き出し時の前方張り出しも公式に記載なし',
}

MD45N_ITEM = {
    u'name': u'冷蔵庫 三菱 MDシリーズ 451L',
    u'model': u'MR-MD45N',
    u'room': u'ldk',
    u'zone': u'kitchen',
    u'w': 60,
    u'd': 69.9,
    u'h': 182.6,
    u'color': u'#edece9',
    u'colors': [
        {u'name': u'フラットリネンホワイト (W)', u'hex': u'#edece9'},
        {u'name': u'フラットアンバーグレー (H)', u'hex': u'#625a52'},
    ],
    u'type': u'fridge',
    u'url': u'https://www.mitsubishielectric.co.jp/home/reizouko/product/mr-md45n/index.html',
    u'install': MD45N_INSTALL,
    u'memo': u'',
    u'specNote': MD45N_SPEC,
}

SEED_NOTE = (
    u' ★v2.3 の変更点 (2026-08-23): **冷蔵庫 三菱 MDシリーズ 451L (MR-MD45N) を1点追加** '
    u'(room=ldk / zone=kitchen / type=\'fridge\' / W60×D69.9×H182.6)。'
    u'寸法は 三菱電機 公式の 幅600×奥行699×高さ1,826mm が出典 '
    u'(奥行69.9は公式表記どおり「ドア角まで」。脚カバー含むと70.9)。'
    u'⚠カラーは 店頭POPの `WJ` / JAN 4573637027659 が公式のカラー一覧 (W/H) にも量販店にも無く'
    u'**未特定**のため、指示どおり暫定で W (フラットリネンホワイト) を採用している。'
    u'**既存の 冷蔵庫 日立 HZC 540L (R-HZC54Y XH) は検討中の比較対象として残す** '
    u'(= カタログに冷蔵庫が2機種並ぶ)。'
    u'あわせて **冷蔵庫の3Dモデルをデータ駆動へ共通化** した: '
    u'v2.2 までは 「日立HZC専用の描画」 + 「汎用の簡易2ドア」 の2本の if だったので、'
    u'機種が増えるたびに描画コードが分岐して 1機種直しても他へ伝わらなかった。'
    u'★v7.5 では **扉の段構成だけを FRIDGE_MODELS というデータで持ち、描画は1本の共通コードに集約** '
    u'(TOP_STACK_TYPES / WALL_HANG_TYPES と同じレジストリ流儀) → '
    u'新機種は FRIDGE_MODELS に1エントリ足すだけで描ける。'
    u'日立 (フレンチ観音6ドア) の見た目は 1メッシュも変えていない '
    u'(snap_fridge_mesh.py で before/after のメッシュ台帳を機械照合済み)。'
    u'さらに **据付必要すきま (放熱スペース) の汎用フィールド `install`** を新設し、'
    u'家具シートの寸法サマリーに1行出すようにした '
    u'(冷蔵庫専用にせず、洗濯機・オーブン等も install を足すだけで同じ行が出る)。'
    u'日立 R-HZC54Y XH には specNote に文章で書いてあった据付条件を install として構造化した '
    u'(specNote 本文と 他の全商品は無変更) ★アプリ v7.5'
)

HITACHI_INSTALL = {
    u'left': 0.5, u'right': 0.5, u'top': 3, u'back': 0,
    u'doorFront': 41.2,
    u'doorNote': u'フレンチ観音。公式据付図 最下段引き出し最大引き出し時 1,111mm − 本体奥行699mm',
    u'note': u'公式据付必要寸法図より。据付に必要な高さ187.3cm '
             u'(上方3cm = 1,873 − 本体高さ1,843。図に印字の「50」は'
             u'背面側の一段低い天面からの値)。'
             u'側方は 左ドア開放で左へ約20cm・右ドア開放で右へ約23.5cm',
}


# ═══════════════════════════════════════════════════════════════════
# ② 冷蔵庫の扉構成レジストリ (データ駆動へ共通化)
# ═══════════════════════════════════════════════════════════════════
FRIDGE_CORE = u'''
// ═══ ★v7.5 冷蔵庫 (type 'fridge') の扉構成レジストリ ═══
//   v7.4 まで 冷蔵庫は 「日立 HZC 専用の描画」 + 「汎用の簡易2ドア」 の 2本の if だった。
//   機種が増えるたびに if を足す作りだと 1機種を直しても他機種へ伝わらないので、
//   **扉の段構成だけをデータで持ち、描画は 1本の共通コード (buildFridgeFront) に集約** する
//   (TOP_STACK_TYPES / WALL_HANG_TYPES と同じレジストリ流儀)。
//   新機種は FRIDGE_MODELS に 1エントリ足すだけで描ける。
//
//   rows は **下から上** の順。 top = その段の上端 (全高 h に対する比。 最上段は 1)。
//   front:
//     'drawer' … 引き出し (前板の下端に 手掛けグルーブ)
//     'french' … 観音開き (段の中央に縦の合わせ目 + 縦長ハンドル×2)
//     'hinge'  … 1枚扉 (ヒンジの反対側に 縦長ハンドル1本)
//   split  … 段を左右に割る合わせ目の中心x (w に対する比)。 undefined/null = 割らない
//   panels … 横一文字の手掛けグルーブ
//             [{ gw: 'full'(=w-10) | w に対する比, gx: w に対する比,
//                gy: 'top'(既定。 引き出し前板の上端) | 'bottom'(扉の下端グリップ) }, ...]
//   handles… 縦長ハンドルの中心x [cm] (本体中心が 0。 マイナス=左)。 フラット扉の機種は空
const FRIDGE_MODELS = [
  {
    // 日立 R-HZC54Y XH (フレンチ6ドア・540L)。★v2.1 の描画をそのままデータ化したもの
    //   下から 野菜室 / 冷凍下段 / (製氷|冷凍上段) / 冷蔵室フレンチ観音
    test: /HZC/,
    label: 'フレンチ6ドア (日立 HZC)',
    rows: [
      { key: 'veg',    top: 0.215, front: 'drawer', panels: [{ gw: 'full', gx: 0 }] },
      { key: 'frz_lo', top: 0.385, front: 'drawer', panels: [{ gw: 'full', gx: 0 }] },
      { key: 'ice_frz', top: 0.505, front: 'drawer', split: -0.1,
        panels: [{ gw: 0.32, gx: -0.29 }, { gw: 0.5, gx: 0.2 }] },
      { key: 'fridge', top: 1, front: 'french', handles: [-4, 4] }
    ]
  },
  {
    // 三菱 MR-MD45N (MDシリーズ 5ドア・451L)。★v7.5 追加
    //   下から 冷凍室 / 野菜室(真ん中) / (製氷|瞬冷凍 横並び) / 冷蔵室(1枚扉・右開き)
    //   ⚠ 冷蔵室扉の下端 0.531 (= 床から969mm) だけが公式値。
    //     冷凍室 0.210 / 野菜室 0.425 / 左右の割り位置 -0.02 は 公式写真からの実測 est。
    //   ⚠ MDシリーズはフラット扉で **縦ハンドルが無い** ので handles は付けず、
    //     冷蔵室扉は下端の全幅グリップ (gy:'bottom') で表現する = 日立の観音2本ハンドルと見分けがつく。
    test: /MR-MD45|MDシリーズ/,
    label: '5ドア・真ん中野菜室・フラット扉 (三菱 MD)',
    rows: [
      { key: 'freezer', top: 0.210, front: 'drawer', panels: [{ gw: 'full', gx: 0 }] },
      { key: 'veg',     top: 0.425, front: 'drawer', panels: [{ gw: 'full', gx: 0 }] },
      { key: 'ice_qf',  top: 0.531, front: 'drawer', split: -0.02,
        panels: [{ gw: 0.39, gx: -0.26 }, { gw: 0.43, gx: 0.24 }] },
      { key: 'fridge',  top: 1, front: 'hinge', hinge: 'r',
        panels: [{ gw: 'full', gx: 0, gy: 'bottom' }] }
    ]
  }
];
function fridgeModelOf(nm) {
  for (let i = 0; i < FRIDGE_MODELS.length; i++) {
    if (FRIDGE_MODELS[i].test.test(nm)) return FRIDGE_MODELS[i];
  }
  return null;
}
'''

FRIDGE_BRANCH = u"""  } else if (type === 'fridge' && fridgeModelOf(nm)) {
    // ★v7.5 冷蔵庫 詳細モデル (共通コード)。 機種差は FRIDGE_MODELS の rows データだけ。
    //   フラット前面 + 段の合わせ目 + ハンドル / 手掛けグルーブ を 下記の順で描く:
    //     本体 → キックプレート → 水平の合わせ目 (下→上) → 縦の合わせ目 (上→下)
    //     → 縦長ハンドル (上→下) → 手掛けグルーブ (上→下)
    //   ※ この描画順は ★v2.1 の日立モデルと 1メッシュ単位で同一 (見た目を変えないための制約)
    const rows = fridgeModelOf(nm).rows;
    const zF = d / 2;
    const line = dark.clone().multiplyScalar(0.85);
    const rowY = function (i) { return i < 0 ? 0 : h * rows[i].top; };
    P(w, h, d, 0, h / 2, 0, base);                                        // 本体 (フラット面)
    P(w - 2, h * 0.03, 1, 0, h * 0.015, zF + 0.2, 0x26282b);              // 下部キックプレート
    for (let i = 0; i < rows.length - 1; i++) {                           // 水平の合わせ目 (最上段の上端=天面は描かない)
      P(w - 1.5, 1.1, 0.8, 0, rowY(i), zF + 0.35, line);
    }
    for (let i = rows.length - 1; i >= 0; i--) {                          // 縦の合わせ目 (観音の中央 / 横並びの境)
      const r = rows[i], y0 = rowY(i - 1), y1 = rowY(i);
      const sx = (r.front === 'french') ? 0 : (r.split === undefined || r.split === null ? null : r.split);
      if (sx === null) continue;
      P(1.1, y1 - y0 - 1.5, 0.8, w * sx, y0 + (y1 - y0) / 2, zF + 0.35, line);
    }
    for (let i = rows.length - 1; i >= 0; i--) {                          // 縦長ハンドル
      const r = rows[i], y0 = rowY(i - 1), y1 = rowY(i);
      (r.handles || []).forEach(function (hx) {
        P(2.2, (y1 - y0) * 0.72, 1.5, hx, y0 + (y1 - y0) * 0.5, zF + 0.9, 0x33353a);
      });
    }
    for (let i = rows.length - 1; i >= 0; i--) {                          // 横一文字の手掛けグルーブ
      const r = rows[i];
      (r.panels || []).forEach(function (pn) {
        P(pn.gw === 'full' ? w - 10 : w * pn.gw, 1.6, 1, w * pn.gx,
          pn.gy === 'bottom' ? rowY(i - 1) + 2.8 : rowY(i) - 2.8,        // 扉の下端 / 引き出し前板の上端
          zF + 0.5, 0x2b2d30);
      });
    }
  } else if (type === 'fridge') {"""


OLD_FRIDGE_BLOCK = u"""  } else if (type === 'fridge' && /HZC/.test(nm)) {
    // ★v2.1 日立 R-HZC54Y XH 詳細モデル (公式: フレンチ6ドア・チャコールグレー・540L)
    //        上=冷蔵室フレンチ観音2枚 (縦長ハンドル) / 中段=製氷(左小)+冷凍上段(右) 引き出し2 /
    //        下段=冷凍下段+野菜室 引き出し2。フラット前面 + 分割線 + 手掛けグルーブ表現
    const zF = d / 2;
    const line = dark.clone().multiplyScalar(0.85);
    const y1 = h * 0.215, y2 = h * 0.385, y3 = h * 0.505;   // 野菜室/冷凍下段/中段 の各上端
    P(w, h, d, 0, h / 2, 0, base);                                        // 本体 (フラット面)
    P(w - 2, h * 0.03, 1, 0, h * 0.015, zF + 0.2, 0x26282b);              // 下部キックプレート
    [y1, y2, y3].forEach(function (yy) {                                  // 水平分割線 x3
      P(w - 1.5, 1.1, 0.8, 0, yy, zF + 0.35, line);
    });
    P(1.1, h - y3 - 1.5, 0.8, 0, y3 + (h - y3) / 2, zF + 0.35, line);     // フレンチ観音 中央縦線
    P(1.1, y3 - y2 - 1.5, 0.8, -w * 0.1, y2 + (y3 - y2) / 2, zF + 0.35, line);  // 中段 製氷|冷凍上段 縦線
    const hh = (h - y3) * 0.72;                                           // 縦長ハンドル (観音の中央寄り)
    P(2.2, hh, 1.5, -4, y3 + (h - y3) * 0.5, zF + 0.9, 0x33353a);
    P(2.2, hh, 1.5, 4, y3 + (h - y3) * 0.5, zF + 0.9, 0x33353a);
    P(w * 0.32, 1.6, 1, -w * 0.29, y3 - 2.8, zF + 0.5, 0x2b2d30);         // 手掛けグルーブ: 製氷
    P(w * 0.5, 1.6, 1, w * 0.2, y3 - 2.8, zF + 0.5, 0x2b2d30);            // 冷凍上段
    P(w - 10, 1.6, 1, 0, y2 - 2.8, zF + 0.5, 0x2b2d30);                   // 冷凍下段
    P(w - 10, 1.6, 1, 0, y1 - 2.8, zF + 0.5, 0x2b2d30);                   // 野菜室
  } else if (type === 'fridge') {"""


# ═══════════════════════════════════════════════════════════════════
# ③ 据付必要すきま (install) の汎用表示
# ═══════════════════════════════════════════════════════════════════
INSTALL_CORE = u'''
// ═══ ★v7.5 据付必要すきま (放熱スペース等) の汎用フィールド `install` ═══
//   冷蔵庫専用にせず、「設置条件を持つカタログ商品」 の共通表示にする
//   (洗濯機・オーブンレンジ・食洗機なども シードに install を足すだけで同じ行が出る)。
//   単位は全部 cm。 値が無い面は null / 省略で「非表示」。
//     left/right/top/back … 本体からその方向へ必要なすきま
//     doorFront           … 扉/引き出しを開いた時に前方へ必要な寸法 (本体前面から)
//     note                … 上記に収まらない条件 (文章)
//   ★出典は 各商品の specNote に書く (ここは表示だけ)。 est の値は note に est と明記する。
function installClearanceOf(it) {
  if (!it) return null;
  const c = it.catalogId ? catalogData[it.catalogId] : null;
  return (c && c.install) || it.install || null;
}
function installClearanceRows(it) {
  const ins = installClearanceOf(it);
  if (!ins) return [];
  const rows = [], N = function (v) { return (v === null || v === undefined || v === '') ? null : Number(v); };
  const sides = [['左', N(ins.left)], ['右', N(ins.right)], ['上方', N(ins.top)], ['背面', N(ins.back)]]
    .filter(function (p) { return p[1] !== null && isFinite(p[1]); })
    .map(function (p) { return p[0] + ' ' + tipN(p[1]) + 'cm'; });
  if (sides.length) {
    const l = N(ins.left), r = N(ins.right), iw = Number(it.w) || 0;
    const need = (l === null || r === null) ? null : Math.round((iw + l + r) * 10) / 10;
    rows.push('据付必要すきま: ' + sides.join(' / ') +
              (need === null ? '' : ' → 設置に必要な幅 ' + tipN(need) + 'cm'));
  }
  if (N(ins.doorFront) !== null) {
    rows.push('扉の開放: 本体前面から ' + tipN(N(ins.doorFront)) + 'cm' +
              (ins.doorNote ? ' (' + ins.doorNote + ')' : ''));
  }
  if (ins.note) rows.push('設置メモ: ' + ins.note);
  return rows;
}
'''


# ═══════════════════════════════════════════════════════════════════
# 適用
# ═══════════════════════════════════════════════════════════════════
def apply_seed():
    global src
    seed_obj = json.loads(seed_block(src))
    changed = False
    if any((it.get('model') == 'MR-MD45N') for it in seed_obj['items']):
        sk(u'CATALOG_SEED: 三菱 MR-MD45N は追加済み')
    else:
        seed_obj['items'].append(MD45N_ITEM)
        changed = True
        ok(u'CATALOG_SEED: 三菱 MR-MD45N を追加 (32 → 33 商品。 日立 R-HZC54Y XH は残す)')
    hit = [x for x in seed_obj['items'] if x.get('model') == 'R-HZC54Y XH']
    if not hit:
        die(u'既存の 日立 R-HZC54Y XH が CATALOG_SEED に見つからない')
        return
    if hit[0].get('install'):
        sk(u'CATALOG_SEED: 日立 R-HZC54Y XH の install は設定済み')
    else:
        hit[0]['install'] = HITACHI_INSTALL
        changed = True
        ok(u'CATALOG_SEED: 日立 R-HZC54Y XH の specNote 内の据付条件を install として構造化 '
           u'(specNote 本文は無変更)')
    if not changed:
        return
    if SEED_NOTE not in seed_obj['_comment']:
        seed_obj['_comment'] = seed_obj['_comment'] + SEED_NOTE
    seed_obj['version'] = '2.3'
    seed_obj['updatedAt'] = '2026-08-23'
    seed_new = json.dumps(seed_obj, ensure_ascii=False, separators=(',', ':'))
    cur = seed_block(src)
    assert src.count(cur) == 1
    src = src.replace(cur, seed_new, 1)


apply_seed()

edit(u'JS: 冷蔵庫の扉構成レジストリ FRIDGE_MODELS を新設 (データ駆動)',
     u'function buildItemParts(g, it) {',
     FRIDGE_CORE + u'function buildItemParts(g, it) {',
     u'const FRIDGE_MODELS = [')

edit(u'JS: fridge の描画を 1本の共通コードへ集約 (日立べた書き分岐を廃止)',
     OLD_FRIDGE_BLOCK,
     FRIDGE_BRANCH,
     u"} else if (type === 'fridge' && fridgeModelOf(nm)) {")

edit(u'JS: 据付必要すきま (install) の汎用ヘルパーを新設',
     u'// 配置した家具 (カタログ商品) の 寸法サマリー (家具シートの先頭に出す)',
     INSTALL_CORE + u'// 配置した家具 (カタログ商品) の 寸法サマリー (家具シートの先頭に出す)',
     u'function installClearanceRows(it) {')

edit(u'JS: 寸法サマリーに 据付必要すきま の行を合流',
     u'  const rot = ((Math.round(Number(it.rotY) || 0) % 360) + 360) % 360;',
     u'  installClearanceRows(it).forEach(function (r) { rows.push(r); });   '
     u'// ★v7.5 据付必要すきま (放熱スペース)\n'
     u'  const rot = ((Math.round(Number(it.rotY) || 0) % 360) + 360) % 360;',
     u'installClearanceRows(it).forEach(function (r) { rows.push(r); });')

edit(u'JS: install をシードから既存カタログへ追従 (colors / baseW と同じ流儀)',
     u'        if (s && s.baseW && !c.baseW) { c.baseW = s.baseW; c.baseD = s.baseD; }',
     u'        if (s && s.baseW && !c.baseW) { c.baseW = s.baseW; c.baseD = s.baseD; }\n'
     u'        if (s && s.install && !c.install) c.install = s.install;   '
     u'// ★v7.5 据付必要すきま (放熱スペース)',
     u'if (s && s.install && !c.install) c.install = s.install;')


# ═══════════════════════════════════════════════════════════════════
# 書き出し + 検証
# ═══════════════════════════════════════════════════════════════════
if problems:
    print(u'\n════ 失敗 %d 件 — 書き込みを中止 ════' % len(problems))
    sys.exit(1)

if src == orig:
    print(u'\n════ 適用0件 / skip %d件 (既に適用済み。room.html は変更なし) ════' % len(skipped))
    sys.exit(0)

room_after = hashlib.sha256(room_block(src).encode('utf-8')).hexdigest()
seed_after_raw = seed_block(src)
seed_after = hashlib.sha256(seed_after_raw.encode('utf-8')).hexdigest()
assert room_after == ROOM_SHA_BEFORE, \
    u'ROOM_DATA の sha256 が変わった (%s → %s) — 今回は触らないはず' % (ROOM_SHA_BEFORE[:12], room_after[:12])
assert seed_after != CATALOG_SHA_BEFORE, u'CATALOG_SEED が変わっていない'

seed_obj_after = json.loads(seed_after_raw)
items_after = seed_obj_after['items']
assert seed_obj_after['version'] == '2.3', u'CATALOG_SEED version が 2.3 でない'
assert len(items_after) == 33, u'商品数が 33 でない: %d' % len(items_after)

# 既存32商品は 日立の install 追加 1点だけを除いて 完全に無変更であること
diffs = []
for i, (b, a) in enumerate(zip(ITEMS_BEFORE, items_after[:32])):
    if b == a:
        continue
    a2 = dict(a)
    popped = a2.pop('install', None)
    if a2 == b and b.get('model') == 'R-HZC54Y XH':
        diffs.append(u'#%d %s: install を追加 (それ以外は無変更) = %s'
                     % (i, b.get('model'), json.dumps(popped, ensure_ascii=False)))
    else:
        diffs.append(u'⚠ #%d %s: 想定外の差分!' % (i, b.get('model')))
        problems.append(u'既存商品 #%d が想定外に変わった' % i)
assert not problems, u'既存商品に想定外の差分がある'

mit = [x for x in items_after if x.get('model') == 'MR-MD45N']
assert len(mit) == 1, u'MR-MD45N が1件でない'
m = mit[0]
assert (m['w'] == 60 and m['d'] == 69.9 and m['h'] == 182.6 and m['room'] == 'ldk'
        and m['zone'] == 'kitchen' and m['type'] == 'fridge' and m['memo'] == ''), \
    u'追加した商品の値が想定と違う: %s' % json.dumps(m, ensure_ascii=False)[:300]
assert [x for x in items_after if x.get('model') == 'R-HZC54Y XH'], \
    u'既存の 日立 R-HZC54Y XH が消えている'

io.open(TARGET, 'w', encoding='utf-8', newline='').write(src)

print(u'')
for dtxt in diffs:
    print(u'  既存商品の差分: ' + dtxt)
print(u'  ROOM_DATA    sha256 %s → %s  (不変 ✓)' % (ROOM_SHA_BEFORE[:12], room_after[:12]))
print(u'  CATALOG_SEED sha256 %s → %s  (変化 ✓)' % (CATALOG_SHA_BEFORE[:12], seed_after[:12]))
print(u'  商品数 %d → %d' % (len(ITEMS_BEFORE), len(items_after)))
print(u'════ 適用 %d件 / skip %d件 ════' % (len(applied), len(skipped)))

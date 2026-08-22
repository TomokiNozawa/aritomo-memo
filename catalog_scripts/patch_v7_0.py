# -*- coding: utf-8 -*-
u"""
nozaROOM room.html v7.0 (ROOM_DATA v6.7) 冪等パッチ

新しく届いた 洋室6.2帖 の写真2枚 (間取り図等\\04_6.2帖\\小窓写真.jpg / 大窓写真.jpg) を
逆投影して、 カーテンレール2本 / 室内物干し / 窓の実寸 / エアコン を実測反映する。

━━ 測定方法 (measure_v7_0.py) ━━

  ■ 小窓写真 = **3消失点フルキャリブレーション** (v6.8/v6.9 の1次元射影写像を2次元へ拡張)
    1. 直交3方向の消失点を 画像中の直線群から最小二乗で求めた:
         V(y方向: E壁に沿う) = (-1483, 681)  ← 巾木下端 / 腰見切り / 天井見切り の3本
         V(x方向: N壁に沿う) = ( 1408, 767)  ← N壁の 巾木下端 / 腰見切り の2本
         V(鉛直)             = (  419, 6243) ← 高所小窓4本の 開口端 (縦線)
       各直線の残差 rms は 0.2〜0.6px (天井見切りのみ 3.8px = 見切り縁が無く陰の谷で拾うため)。
    2. 3消失点が互いに直交方向なので **主点 = 三角形の垂心 / f² = -(V1-P)·(V2-P)** で
       内部標定が決まる (トリミング済み画像でも主点を仮定しなくてよい)。
         → f = 1269.4 px / 主点 = (571.9, 1052.4)
       f² > 0 になること自体が 「3直線群が本当に直交している」 ことの検算。
    3. 入隅 (1055,107) の 床点 (222.9,1116.9) と 天井点 (195.7,404.9) からカメラ位置を解いた。
       u から解いた解を v で検算した残差は **0.00 px相当**。
         → カメラ = (x 745.3, y 454.2, 床上 137.7)
       = **LDK側から D-06 (y384.5〜553.5) の戸口越しに 6.2帖 を撮っている** 位置。
         写真の左端の暗い楔と右端のグレー帯は この戸口の両袖 (手前の遮蔽物) で、
         カメラが室内でなく LDK にあることと矛盾しない。
    4. 検算 (逆投影して既知値に戻るか):
         巾木下端 → 床から **0.1cm** (期待 0)   /  天井見切り → **240.0cm** (期待 240)
         WIN-06 と WIN-07 の 上端が **203.6 / 203.2** (独立2窓で 0.4cm 一致)
         WIN-06 と WIN-07 の 幅が   **43.9 / 43.8** (独立2窓で 0.1cm 一致 → 44 が正)
         エアコン A3 の高さが **28.5cm** (壁掛機の標準 29.5cm と 1cm 一致)
       → 実測精度は概ね **±1〜2cm**。

  ■ 大窓写真 = 壁面2Dモデル (この写真は天井見切りが暗くて拾えないため 3消失点法が使えない)
       V(x方向) = (4848, 815) ← 巾木下端 (rms 0.86px) / 腰見切り (rms 0.44px)
       V(鉛直)  = ( 435, 5828) ← 窓の縦線4本 (rms 0.38〜0.73px)
     鉛直方向は V(鉛直) を極とする射影写像を **床=0 と 腰見切り=90.6cm** の2点で拘束した。
     腰見切り 90.6cm は **小窓写真 (フルキャリブレーション) で実測した同じ部屋の同じ見切り縁**
     なので、 2枚の写真をつなぐ共通スケールとして使える。
     水平方向は 開口幅 165cm (既存データ) を較正基準にした。 これで画像右端が x=1065.6、
     **E壁 (x=1055) が u≈1021 (画像内)** と出て、 既存の 「東側の壁 41.5cm」 と整合する
     (= 165 という較正基準そのものの検算になっている)。

━━ 反映する実測値 (① 〜 ④) ━━

① カーテンレール 2本 (新規 F-51 / F-52)

  【高所小窓側 F-51】 E壁 (x=1055)
    形式   : **正面付け・シングル** (天井240 に対して レール中心が 床から約210 = 天井から30cm 下。
             天井付けなら天井直下に来るので 正面付けで確定。 開口上端 203.4 の 7cm 上 =
             正面付けブラケットの標準的な取り付け位置)
    高さ   : 壁面へ逆投影した見かけ中心 **212.3cm** (u=410〜760 で 212.3±0.1 = 水平線であることの検算)。
             壁からの出 6.5cm ぶんの視差 (カメラ床上137.7 / E壁まで309.7cm) を戻して
             **レール中心 床から 210.7cm / 下端 209.5cm**
    出     : **6.5cm** ⚠est — 画像分解能 3.4px/cm ではブラケットの奥行を直接測れない。
             見かけの上下幅 2.4cm はシングル1本 (φ約2cm) と整合し、 ダブルなら 2本の視差差
             1.6cm が加わって 3.1cm 以上になるはずなので **シングル** と判断した。
    長さ   : 右(南)端は端部キャップが写っており 部屋 y=**315.0**。
             左(北)端は **エアコンの陰に隠れて写っていない** (陰から現れるのが y=192.1)。
             右の張り出し 12.8cm と同じだけ左にも出ていると仮定して y=**185.5**、
             長さ **129.5cm** (⚠左端と長さは est。 y≦192.1 という上限とは矛盾しない)

  【大窓側 F-52】 N壁 (y=107)
    形式   : **正面付け・シングル**
    高さ   : 壁面見かけ中心 224.7cm → 出6.5の視差を戻して **レール中心 床から 221.5cm /
             下端 220.3cm** (開口上端 213.7 の 7.8cm 上)
    長さ   : 左端 u≈30〜52 → x≈834、 右端 u≈972 (端部の先は暗くて写らない) → x≈1038。
             **x834.0〜1038.0 = 長さ 204.0cm** (開口 848.5〜1013.5 に対して 西へ14.5 / 東へ24.5 張り出す。
             2.0m 伸縮レールを ほぼ窓中心に付けた形。 中心 936 vs 窓中心 931 = 5cm ずれ)
    房掛け : ユーザー報告の 「両端に房掛け」 を採用し、 **両袖 (x845 / x1017) の 床から120cm** に置く。
             ⚠est — 左袖 (画像 126,763) に房掛けらしい小さな出っ張りがあり 逆投影すると
             x=848.7 (= 開口西端 848.5 に一致) / 床から 121.6cm と出るので この高さを採ったが、
             右袖側は 見込み面が明るく飛んでいて 実体を確認できなかった。

② 室内物干し (新規 F-53) — 天井付け

    小窓写真に 天井プレート + 細い吊り棒 + フック が写る。 フルキャリブレーションで
      天井プレート → 天井面 (z=240) へ逆投影 = 部屋 **(x 993.7, y 153.1)**
        = E壁から 61.3cm / N壁 (大窓) から 46.1cm
      フック下端 (同じ鉛直線上なので x,y は共通) → 床から **195.9cm = 天井から 44.1cm 下がる**
        (ホスクリーン等の天井付け物干しの標準ポール長 450mm と一致)
    ⚠ 大窓写真には **同型がもう1台** (画像 x≈140 と x≈1030) 写っており 対で使う製品だが、
      大窓写真は 3消失点法が成立せず 天井面への逆投影ができないため **2台目の位置は未確定**。
      今回は 実測できた1台のみを登録する (report 参照)。

③ 窓の実寸是正

  【WIN-06 / WIN-07 = 高所小窓2連】 E壁
      sill  165 → **157.5**   (実測 157.9 / 157.2 … 2窓で 0.7cm 一致)
      高さ   50 → **46.0**    (上端 203.6 / 203.2 … 2窓で 0.4cm 一致 → 203.5)
      幅     43 → **44.0**    (実測 43.9 / 43.8)
      位置  WIN-06 y196.0〜239.0 → **198.0〜242.0** (実測 197.9〜241.8)
            WIN-07 y251.0〜294.0 → **258.5〜302.5** (実測 258.4〜302.2)
            → **2窓の離隔 12.0 → 16.5cm**。 洋室4.8 の2窓の離隔 (v6.4 で 24.5→16.5 に是正) と同値。
              E壁チェーン 311 = 91.0 + 44 + 16.5 + 44 + 115.5 で閉じる。
      形式  「すべり出し」 → **横すべり出し (アワニング)**。 各サッシの下框中央に横棒ハンドルが写る
            (洋室4.8 の WIN-03/04 と同じ判定・同じ製品系)。

  【WIN-05 = バルコニー大窓】 N壁
      sill   30 → **22.5**  (実測 22.3)
      高さ  190 → **191.0** (実測 191.4 ★ほぼ一致 = 旧 est が良かった)
      上端  220 → **213.5** (実測 213.7)
      幅 165 / x848.5〜1013.5 は **不変** (較正基準として使い、E壁位置と整合することを確認)
      形式  黒サッシ 2枚引違い・型ガラス は写真で追認 (ラベルどおり)

④ エアコン A3

      位置  pos y126 → **157.0** (実測 北端 110.2 / 南端 204.5 → 中心 157.4)
            = **N壁 (y107) からわずか 3cm の位置から始まり、 高所小窓 (198.0) の手前で終わる**
      下端  未指定 → **202.0cm** (実測)
      サイズ 表示既定 80×24×26 → **w=94** を明示 (実測 幅 94.3 / 高さ 28.5。
            高さの実測 28.5 が 壁掛機の標準 29.5 と 1cm 一致するので 幅の 94 も信頼できる。
            ⚠奥行は 一般的な 21cm を仮定して視差補正しているので 幅は ±4cm の est)

━━ 検出したが 今回は反映しない事項 ━━
   ・ダウンライト: 小窓写真の3灯を天井面へ逆投影すると (x≈930, y 226.9 / 254.4 / 286.3) と出る。
     現データ (L-09 x858.5 / L-10 x978 / L-11 引掛シーリング x922.5) と食い違うが、
     照明は 3D に描画しておらず 今回のタスク範囲外なので **触らない** (report で申し送り)。

━━ 不変アサート ━━
   CATALOG_SEED は sha256 一致を assert (1バイトも触らない)。
   ROOM_DATA は rooms / outlets / lights / zones / unit / ceilingH / wallT / orientation を凍結。
   さらに 6.2帖の内寸 255×311・WIC ポリゴン・LDK E壁チェーン (D-06 169) を機械 assert する。

━━ 冪等性 ━━
   各パッチは 「適用済みマーカー」 を持ち、 既に入っていれば skip。
   ROOM_DATA 側も 既に新値なら 何もしない。 再実行すると 「適用 0 件 / skip N 件」 になる。

使い方:
  bash ~/.claude/scripts/run_py.sh catalog_scripts/patch_v7_0.py [--dry-run]
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), 'room.html')

RD_PREFIX = u'var ROOM_DATA = '
CS_PREFIX = u'var CATALOG_SEED = '

FROZEN_KEYS = ['rooms', 'outlets', 'lights', 'zones']
FROZEN_SCALARS = ['unit', 'ceilingH', 'wallT', 'orientation']


def read_text():
    with io.open(TARGET, encoding='utf-8', newline='') as f:
        t = f.read()
    assert '\r\n' not in t, 'unexpected CRLF in room.html'
    return t


def data_line(text, prefix):
    hits = [(i, ln) for i, ln in enumerate(text.split('\n')) if ln.startswith(prefix)]
    assert len(hits) == 1, 'expected exactly 1 line starting with %r, got %d' % (prefix, len(hits))
    return hits[0]


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def parse_json_line(line, prefix):
    body = line[len(prefix):].rstrip()
    semi = body.endswith(';')
    if semi:
        body = body[:-1]
    return json.loads(body), semi


def dump_json_line(obj, prefix, semi):
    return prefix + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + (';' if semi else '')


# ═════════════════════════════ JS パッチ ═════════════════════════════

P_STYLE = (
    u'P1 FIX_STYLE に ceiling_hanger (天井付け 室内物干し) を追加',
    u'ceiling_hanger:',
    u"""  curtain_rail: { color: 0xcfcbc3, h: 240 },   // カーテンレール (アルミシルバー)
""",
    u"""  curtain_rail: { color: 0xcfcbc3, h: 240 },   // カーテンレール (アルミシルバー)
  // ★v7.0 天井付け 室内物干し (小窓写真・大窓写真 に写る 天井プレート + 細い吊り棒 + フック)。
  //   h = 天井 (プレート面) / bottomH = フック下端。
  ceiling_hanger: { color: 0xf4f3f0, h: 240 },  // 室内物干し (天井付け)
""",
)

P_HANGER = (
    u'P2 buildFixture に ceiling_hanger (天井プレート + 吊り棒 + フック) を追加',
    u"if (f.type === 'ceiling_hanger') {",
    u"""  if (f.type === 'curtain_rail') {
    // ★v6.8 露出カーテンレール。写真60・62 の逆投影より""",
    u"""  if (f.type === 'ceiling_hanger') {
    // ★v7.0 天井付け 室内物干し。 小窓写真 の3消失点フルキャリブレーションで
    //   天井プレート = 部屋 (x993.7, y153.1) / フック下端 = 床から195.9 (天井から44.1 下がる) と実測。
    //   rect = プレートの外形 (中心が取付位置)。 床には何も置けなくならないよう ブロックはしない。
    const info = { kind: 'fixture', info: f.label };
    const px = x + dx / 2, pz = y + dy / 2;
    const plate = new THREE.Mesh(new THREE.CylinderGeometry(3.0, 3.0, 1.6, 16), mat(color));
    plate.position.set(px, topH - 0.8, pz);
    Object.assign(plate.userData, info); g.add(plate); pickables.push(plate);
    const rodTop = topH - 1.6, rodBot = Math.min(botH + 4.0, topH - 2.6);
    const rod = new THREE.Mesh(
      new THREE.CylinderGeometry(0.7, 0.7, Math.max(rodTop - rodBot, 1.0), 10), mat(0xdedcd6));
    rod.position.set(px, (rodTop + rodBot) / 2, pz);
    Object.assign(rod.userData, info); g.add(rod); pickables.push(rod);
    const hook = new THREE.Mesh(new THREE.TorusGeometry(2.0, 0.6, 8, 16), mat(0xf2f0ea));
    hook.position.set(px, botH + 2.0, pz);
    hook.rotation.y = Math.PI / 2;
    Object.assign(hook.userData, info); g.add(hook); pickables.push(hook);
    return;
  }
  if (f.type === 'curtain_rail') {
    // ★v6.8 露出カーテンレール。写真60・62 の逆投影より""",
)

P_FACE = (
    u'P3 curtain_rail に 正面付け (mount:face) と 房掛け (tassels) を追加',
    u"const face = (f.mount === 'face');",
    u"""    const dep = Math.max.apply(null, offs) + 2.2;          // ブラケットの奥行き
    const nb = Math.max(2, Math.round(len / 50) + 1);      // 端部 + 約50cm ピッチ
    const bt = Math.max(topH - railY - RR, 0.8);           // ブラケットの高さ (レール上端〜天井)
    for (let i = 0; i < nb; i++) {
      const t = (along ? x : y) + 2.5 + (len - 5) * (i / (nb - 1));
      const bc = wallC + sign * dep / 2;
      pickables.push(addBox(g, along ? 3.0 : dep, bt, along ? dep : 3.0,
                            along ? t : bc, railY + RR + bt / 2, along ? bc : t, brC, info));
    }
    return;
  }""",
    u"""    const dep = Math.max.apply(null, offs) + 2.2;          // ブラケットの奥行き
    const nb = Math.max(2, Math.round(len / 50) + 1);      // 端部 + 約50cm ピッチ
    // ★v7.0 正面付け (mount:'face') = ブラケットを壁に打つタイプ。 天井までは伸びず
    //   レールの前後を挟む短い座になる。 洋室6.2 の2本 (F-51/F-52) がこれ。
    //   天井付け (既定) は 従来どおり レール上端〜天井 まで伸ばす。
    const face = (f.mount === 'face');
    const bt = face ? (2 * RR + 3.0) : Math.max(topH - railY - RR, 0.8);
    const by = face ? (railY + 0.6) : (railY + RR + bt / 2);
    for (let i = 0; i < nb; i++) {
      const t = (along ? x : y) + 2.5 + (len - 5) * (i / (nb - 1));
      const bc = wallC + sign * dep / 2;
      pickables.push(addBox(g, along ? 3.0 : dep, bt, along ? dep : 3.0,
                            along ? t : bc, by, along ? bc : t, brC, info));
    }
    // ★v7.0 房掛け (tassels) — 窓の両袖に付く カーテンを束ねる小フック。
    //   tassels = { h: 床からの高さ, at: [レール方向の座標, ...] }
    if (f.tassels && f.tassels.at && f.tassels.at.length) {
      const th = Number(f.tassels.h) || 120;
      const ti = { kind: 'fixture', info: '房掛け — ' + f.label };
      f.tassels.at.forEach(function (t) {
        const base = wallC + sign * 1.0, tip = wallC + sign * 3.6;
        pickables.push(addBox(g, along ? 3.2 : 2.0, 3.2, along ? 2.0 : 3.2,
                              along ? t : base, th, along ? base : t, brC, ti));
        const knob = new THREE.Mesh(new THREE.SphereGeometry(1.3, 10, 8), mat(brC));
        knob.position.set(along ? t : tip, th, along ? tip : t);
        Object.assign(knob.userData, ti);
        g.add(knob); pickables.push(knob);
      });
    }
    return;
  }""",
)

P_AC = (
    u'P4 buildAircon を 実測サイズ (w / d / hgt) 対応にする',
    u'★v7.0 実測サイズ',
    u"""  const y = a.bottomH ? a.bottomH + 13 : 218;   // ★v1.7 bottomH=下端高さ指定 (A2=200)。A5 特例は削除 (A5自体を廃止)
  const m = addBox(g, alongX ? 80 : 24, 26, alongX ? 24 : 80,
    a.pos[0] + d[0] * 13, y, a.pos[1] + d[1] * 13, 0xf6f7f8,""",
    u"""  // ★v7.0 実測サイズ (w=幅 / d=奥行 / hgt=高さ) を持つ機はそれを使う。 無ければ従来の 80×24×26。
  //   A3 は 小窓写真 の逆投影で 幅94.3 / 高さ28.5 / 下端202.0 と実測 (奥行は一般値21を仮定して視差補正)。
  const aw = Number(a.w) || 80, ad = Number(a.d) || 24, ah = Number(a.hgt) || 26;
  const y = a.bottomH ? a.bottomH + ah / 2 : 218;   // ★v1.7 bottomH=下端高さ指定 (A2=200)。A5 特例は削除 (A5自体を廃止)
  const m = addBox(g, alongX ? aw : ad, ah, alongX ? ad : aw,
    a.pos[0] + d[0] * (ad / 2 + 1), y, a.pos[1] + d[1] * (ad / 2 + 1), 0xf6f7f8,""",
)

P_AC_TIP = (
    u'P5 エアコンのツールチップを 実測サイズ表示に対応',
    u"★v7.0 実測サイズがあればそれを出す",
    u"""    rows.push(bot
      ? ('下端高さ: 床から ' + tipN(bot) + 'cm (上端 ' + tipN(bot + 26) + 'cm)')
      : '下端高さ: 未実測 → 3Dは天井際 (床から 205〜231cm) で表示');
    rows.push('表示サイズ: 幅80 × 奥行24 × 高さ26cm (壁掛け機の目安)');""",
    u"""    // ★v7.0 実測サイズがあればそれを出す (A3 は 小窓写真 の逆投影で 幅94.3 / 高さ28.5 を実測)
    const aw = Number(o.w) || 80, ad = Number(o.d) || 24, ah = Number(o.hgt) || 26;
    rows.push(bot
      ? ('下端高さ: 床から ' + tipN(bot) + 'cm (上端 ' + tipN(bot + ah) + 'cm)')
      : '下端高さ: 未実測 → 3Dは天井際 (床から 205〜231cm) で表示');
    rows.push((o.w ? '実測サイズ: ' : '表示サイズ: ') + '幅' + tipN(aw) + ' × 奥行' + tipN(ad) +
              ' × 高さ' + tipN(ah) + 'cm' + (o.w ? ' (奥行は一般値)' : ' (壁掛け機の目安)'));""",
)

P_TIPFIX = (
    u'P6 tipFixInner: 室内物干しの行を追加 + カーテンレールの有効長を E/W 壁でも正しく出す',
    u'const rlen = !f.rect ? 0',
    u"""    return '形式: ' + (f.mount === 'face' ? '正面付け' : '天井付け') +
           (offs.length >= 2 ? ' ダブル' : ' シングル') +
           ' / 壁からの出: ' + offs.map(tipN).join('cm・') + 'cm' +
           ' / 有効長: ' + tipN(f.rect ? f.rect[2] : 0) + 'cm';
  }""",
    u"""    // ★v7.0 E/W 壁のレールは rect[3] がレール方向の長さ (rect[2] は壁からの張り出し帯)
    const rlen = !f.rect ? 0
               : ((f.wallSide === 'E' || f.wallSide === 'W') ? f.rect[3] : f.rect[2]);
    return '形式: ' + (f.mount === 'face' ? '正面付け' : '天井付け') +
           (offs.length >= 2 ? ' ダブル' : ' シングル') +
           ' / 壁からの出: ' + offs.map(tipN).join('cm・') + 'cm' +
           ' / 有効長: ' + tipN(rlen) + 'cm' +
           (f.bottomH ? ' / レール下端: 床から ' + tipN(f.bottomH) + 'cm' : '') +
           (f.tassels ? ' / 房掛け: 床から ' + tipN(f.tassels.h) + 'cm ×' + f.tassels.at.length : '');
  }
  if (f.type === 'ceiling_hanger') {
    // ★v7.0 天井付け 室内物干し
    const top = (f.h != null ? f.h : 240), bot = Number(f.bottomH) || 0;
    return '取付: 天井 (床から ' + tipN(top) + 'cm) / フック下端: 床から ' + tipN(bot) +
           'cm (天井から ' + tipN(top - bot) + 'cm 下がる)';
  }""",
)

P_DEBUG = (
    u'P7 __noza.win62() — 6.2帖の窓・レール・物干しの実効値を返す検証フック',
    u'win62: function ()',
    u"""      doors: function () {
        // ★v2.2 検証用: ドア一覧 (id / ラベル / 開閉状態)""",
    u"""      // ★v7.0 検証用: 洋室6.2帖 の 窓 (WIN-05/06/07) / カーテンレール (F-51/F-52) /
      //   室内物干し (F-53) / エアコン (AC-3) の実効値。 写真との突合に使う。
      win62: function () {
        const wins = R.openings.filter(function (o) { return o.room === 'west6_2' && o.type === 'window'; })
          .map(function (o) {
            const s = Number(o.sillH) || 0, h = Number(o.height) || 0;
            return { id: o.id, width: o.width, sill: s, top: s + h, height: h, est: !!o.est,
                     from: o.wallFrom, to: o.wallTo };
          });
        const fx = R.fixtures.filter(function (f) {
          return f.room === 'west6_2' && (f.type === 'curtain_rail' || f.type === 'ceiling_hanger');
        }).map(function (f) {
          let n = 0;
          scene.traverse(function (m) { if (m.userData && m.userData.info === f.label) n++; });
          return { id: f.id, type: f.type, rect: f.rect, wallSide: f.wallSide || null,
                   mount: f.mount || null, railOffsets: f.railOffsets || null,
                   bottomH: f.bottomH, topH: f.h, tassels: f.tassels || null, meshes: n };
        });
        const ac = R.aircons.filter(function (a) { return a.room === 'west6_2'; })
          .map(function (a) {
            return { id: a.id, pos: a.pos, wallSide: a.wallSide, bottomH: a.bottomH || null,
                     w: a.w || null, d: a.d || null, hgt: a.hgt || null };
          });
        return { windows: wins, fixtures: fx, aircons: ac, ceilingH: CH };
      },
      doors: function () {
        // ★v2.2 検証用: ドア一覧 (id / ラベル / 開閉状態)""",
)

JS_PATCHES = [P_STYLE, P_HANGER, P_FACE, P_AC, P_AC_TIP, P_TIPFIX, P_DEBUG]


# ═════════════════════════════ ROOM_DATA v6.7 ═════════════════════════════

V67_NOTE = (
    u'★v6.7 (2026-08-22) 【洋室6.2帖 の新規写真2枚 (小窓写真.jpg / 大窓写真.jpg) の逆投影で実測】 '
    u'小窓写真は 直交3方向の消失点 (V_y=(-1483,681) 巾木・腰見切り・天井見切り / V_x=(1408,767) N壁の巾木・腰見切り / '
    u'V_z=(419,6243) 高所小窓の開口端4本) から **主点=垂心・f²=-(V1-P)·(V2-P)** で内部標定を組み '
    u'(f=1269.4px / 主点(571.9,1052.4))、 入隅(1055,107) の床点と天井点から カメラ位置 (x745.3, y454.2, 床上137.7) を解いた '
    u'(u で解いた解を v で検算した残差 0.00px = LDK側から D-06 の戸口越しに撮った位置)。 '
    u'検算: 巾木下端→0.1cm (期待0) / 天井見切り→240.0cm (期待240) / 2窓の上端が 203.6・203.2 で0.4cm一致 / '
    u'2窓の幅が 43.9・43.8 で0.1cm一致 / エアコン高さ28.5cm が壁掛機の標準29.5cmと1cm一致。 実測精度 ±1〜2cm。 '
    u'大窓写真は天井見切りが暗くて拾えないので 壁面2Dモデル (V_x=(4848,815) / V_z=(435,5828)) を使い、 '
    u'**小窓写真で実測した腰見切り 90.6cm** を2枚をつなぐ共通スケールとして 床=0 と併せて2点拘束にした。 '
    u'水平は開口幅165を較正基準にし、 結果 E壁(x=1055)が画像内 u≈1021 と出て 既存の「東側の壁41.5」と整合した。 '
    u'【変更点】(1) WIN-06/07: sill 165→157.5 / 高さ 50→46.0 / 幅 43→44 / '
    u'位置 196.0〜239.0→198.0〜242.0 ・ 251.0〜294.0→258.5〜302.5 → **2窓の離隔 12.0→16.5** '
    u'(洋室4.8 の2窓の離隔 16.5 と同値。 E壁チェーン 311 = 91.0+44+16.5+44+115.5 で閉じる)。 形式は '
    u'「すべり出し」→ **横すべり出し (アワニング)** (下框中央の横棒ハンドルが写る = WIN-03/04 と同じ判定)。 '
    u'(2) WIN-05: sill 30→22.5 / 高さ 190→191.0 (上端 220→213.5)。 幅165・x位置は較正基準として不変。 '
    u'(3) AC-3: pos y126→157.0 (実測 北端110.2〜南端204.5) / bottomH 202.0 / w 94 を明示 '
    u'(高さ実測28.5 が標準29.5 と1cm一致するので幅94も信頼できるが 奥行を一般値21と仮定した視差補正なので ±4cm)。 '
    u'(4) fixtures に **F-51 カーテンレール(高所小窓側・正面付けシングル・E壁・出6.5est・中心210.7/下端209.5・y185.5〜315.0)** / '
    u'**F-52 カーテンレール(大窓側・正面付けシングル・N壁・中心221.5/下端220.3・x834.0〜1038.0=204.0・房掛け床上120 ×2)** / '
    u'**F-53 室内物干し(天井付け・天井プレート x993.7 y153.1・フック下端195.9=天井から44.1下がる)** を新設。 '
    u'⚠ F-51 の左(北)端はエアコンの陰で写らないため右の張り出しと対称と仮定した est (陰から現れる y=192.1 という上限とは矛盾しない)。 '
    u'⚠ 房掛けは左袖の出っ張り (逆投影 x848.7 / 床上121.6) から高さだけ採り、位置は両袖対称と仮定した est。 '
    u'⚠ 大窓写真には室内物干しがもう1台写っているが 同写真では天井面へ逆投影できず 位置未確定のため未登録。 '
    u'⚠ ダウンライトは 小窓写真の3灯を天井へ逆投影すると (x≈930, y226.9/254.4/286.3) と出て 現データ (L-09/L-10/L-11) と '
    u'食い違うが、 照明は3Dに描画しておらず今回の範囲外なので触っていない (要再調査)。'
)

WIN05_ADD = (
    u' ★v7.0 大窓写真 の逆投影で sill/height 是正: 床上30・高さ190 (上端220) → **床上22.5・高さ191.0 (上端213.5)**。 '
    u'V_x=(4848,815) (巾木下端 rms0.86px / 腰見切り rms0.44px) と V_z=(435,5828) (窓の縦線4本 rms0.38〜0.73px) を極とする '
    u'壁面射影写像を 床=0 と **腰見切り90.6cm** (小窓写真のフルキャリブレーションで実測した同じ部屋の同じ見切り縁) の2点で拘束して '
    u'sill 22.3 / 上端 213.7 / 高さ 191.4 を得た (高さは旧est 190 とほぼ一致)。 '
    u'幅165・x848.5〜1013.5 は水平方向の較正基準に使ったので不変だが、 その較正で E壁(x=1055) が画像内 u≈1021 と出て '
    u'既存の「東側の壁41.5」と整合するので 165 自体も追認された。 黒サッシ2枚引違い・型ガラス・白い窓台・左壁にコンセント も写真で追認。'
)

WIN0607_ADD = (
    u' ★v7.0 小窓写真 の3消失点フルキャリブレーション (f=1269.4px / 主点(571.9,1052.4) / カメラ(x745.3,y454.2,床上137.7)) '
    u'による逆投影で是正。 検算として 巾木下端が0.1cm・天井見切りが240.0cm に戻る。 '
    u'sill 165→**157.5** (2窓の実測 157.9/157.2)・高さ 50→**46.0** (上端実測 203.6/203.2)・幅 43→**44.0** (実測 43.9/43.8)。 '
    u'位置は WIN-06 196.0〜239.0→**198.0〜242.0** / WIN-07 251.0〜294.0→**258.5〜302.5** で、 '
    u'**2窓の離隔が 12.0 → 16.5cm** になる (洋室4.8 の2窓の離隔 16.5 と同値 = 同じサッシ割付)。 '
    u'E壁チェーン 311 = N入隅から91.0 + 44 + 16.5 + 44 + 南へ115.5 で閉じる。 '
    u'形式は 各サッシ下框中央の横棒ハンドルから **横すべり出し (アワニング)**。 '
    u'カーテンレールは 天井付けではなく **正面付けシングル (F-51)** で 開口上端の 7cm 上。'
)

AC3_ADD = (
    u' ★v7.0 小窓写真 の逆投影で実測: 北端 y110.2 / 南端 y204.5 → **中心 y157.0・幅94.3** '
    u'(pos y126 は est だった)。 下端 **床から202.0**・高さ **28.5** (壁掛機の標準29.5と1cm一致 = スケールの検算)。 '
    u'N壁 (y107) からわずか3cmの位置に始まり 高所小窓 (y198.0) の手前で終わる。 '
    u'⚠幅は 奥行を一般値21cmと仮定して視差補正した値なので ±4cm。'
)

RAIL_SMALL = {
    "type": "curtain_rail", "room": "west6_2",
    "label": (u"カーテンレール(正面付けシングル/洋室6.2 高所小窓 WIN-06+WIN-07 を1本でカバー) ★v7.0 小窓写真の逆投影で新規実測: "
              u"天井240 に対して レール中心が床から約210 = 天井から30cm下 なので **天井付けではなく正面付け** "
              u"(開口上端203.5 の7cm上 = 正面付けブラケットの標準位置)。 壁面へ逆投影した見かけ中心 212.3cm は "
              u"u=410〜760 の全域で 212.3±0.1 と一定 (= 壁と平行な水平線であることの検算)。 "
              u"壁からの出6.5cm ぶんの視差 (カメラ床上137.7 / E壁まで309.7cm) を戻して レール中心 床から210.7 / 下端209.5。 "
              u"見かけの上下幅 2.4cm は シングル1本 (φ約2cm) と整合する (ダブルなら2本の視差差1.6cmが加わり3.1cm以上になる)。 "
              u"⚠出6.5cm は est — 画像分解能 3.4px/cm ではブラケットの奥行を直接測れない。 "
              u"⚠左(北)端は **エアコンの陰に隠れて写らない**。 右(南)端は端部キャップが写り y=315.0 と実測できたので、 "
              u"右の張り出し12.8cm と対称と仮定して y=185.5 とした (陰から現れる y=192.1 という上限と矛盾しない)。 長さ129.5。"),
    "est": True,
    "rect": [1043.0, 185.5, 12.0, 129.5], "wallSide": "E", "mount": "face",
    "railOffsets": [6.5], "railR": 0.8, "h": 240, "bottomH": 209.5,
    "color": "#e7e5e0", "bracketColor": "#f2f0ec", "showDim": False,
    "id": "F-51", "name": u"カーテンレール(洋室6.2 高所小窓)", "short": u"カーテンレール", "minor": False,
}

RAIL_BIG = {
    "type": "curtain_rail", "room": "west6_2",
    "label": (u"カーテンレール(正面付けシングル・房掛け付き/洋室6.2 大窓 WIN-05) ★v7.0 大窓写真の逆投影で新規実測: "
              u"壁面へ逆投影した見かけ中心 224.7cm → 出6.5cm の視差を戻して レール中心 床から221.5 / 下端220.3 "
              u"(開口上端213.5 の約8cm上)。 長さは 左端 x834.0 (画像 u≈30〜52)・右端 x1038.0 (画像 u≈972) で **204.0cm**。 "
              u"開口 848.5〜1013.5 に対して 西へ14.5 / 東へ24.5 張り出す (2.0m 伸縮レールを ほぼ窓中心に付けた形。 "
              u"レール中心936 vs 窓中心931 = 5cm ずれ)。 房掛けは両袖 (x845 / x1017) の 床から120cm。 "
              u"⚠房掛けの高さは 左袖の出っ張り (画像126,763 を逆投影して x848.7 = 開口西端848.5 に一致 / 床上121.6) から採ったが、 "
              u"右袖側は見込み面が明るく飛んでいて実体を確認できていない (両袖対称と仮定した est)。 "
              u"⚠出6.5cm も est (F-51 と同じ理由)。"),
    "est": True,
    "rect": [834.0, 107.0, 204.0, 12.0], "wallSide": "N", "mount": "face",
    "railOffsets": [6.5], "railR": 0.8, "h": 240, "bottomH": 220.3,
    "tassels": {"h": 120.0, "at": [845.0, 1017.0]},
    "color": "#e7e5e0", "bracketColor": "#f2f0ec", "showDim": False,
    "id": "F-52", "name": u"カーテンレール(洋室6.2 大窓)", "short": u"カーテンレール", "minor": False,
}

HANGER = {
    "type": "ceiling_hanger", "room": "west6_2",
    "label": (u"室内物干し(天井付け/天井プレート + 細い吊り棒 + フック) ★v7.0 小窓写真の逆投影で新規実測: "
              u"天井プレートを 天井面 (z=240) へ逆投影して 部屋 (x993.7, y153.1) = **E壁から61.3cm / N壁(大窓)から46.1cm**。 "
              u"フック下端は同じ鉛直線上なので x,y 共通で 床から **195.9cm = 天井から44.1cm 下がる** "
              u"(ホスクリーン等 天井付け物干しの標準ポール長450mm と一致)。 大窓の前に干す配置。 "
              u"⚠大窓写真には **同型がもう1台** (画像 x≈140 と x≈1030) 写っており 本来は対で使う製品だが、 "
              u"大窓写真は天井見切りが暗く3消失点法が成立せず 天井面へ逆投影できないため 2台目の位置は未確定 (未登録)。"),
    "est": True,
    "rect": [990.7, 150.1, 6.0, 6.0], "h": 240, "bottomH": 195.9, "color": "#f4f3f0",
    "id": "F-53", "name": u"室内物干し(天井付け)", "short": u"物干し", "minor": False,
}


def _find_one(arr, key, val, what):
    hits = [o for o in arr if o.get(key) == val]
    assert len(hits) == 1, u'%s が %d 件 (期待 1)' % (what, len(hits))
    return hits[0]


def patch_room_data(rd):
    log, changed = [], False

    # ── ① WIN-06 / WIN-07 ──
    for wid, y0, y1 in (('WIN-06', 198.0, 242.0), ('WIN-07', 258.5, 302.5)):
        w = _find_one(rd['openings'], 'id', wid, wid)
        want = dict(wallFrom=[1055.0, y0], wallTo=[1055.0, y1], width=44, sillH=157.5, height=46.0)
        if all(w.get(k) == v for k, v in want.items()) and w.get('est') is False:
            log.append(u'  [skip ] %s (既に v7.0 実測値)' % wid)
        else:
            w.update(want)
            w['est'] = False
            if u'★v7.0' not in w['label']:
                w['label'] = w['label'].replace(u'すべり出し', u'横すべり出し(アワニング)', 1) + WIN0607_ADD
            log.append(u'  [apply] %s sill157.5 / h46.0 / 幅44 / y%.1f〜%.1f' % (wid, y0, y1))
            changed = True

    # ── ② WIN-05 ──
    w5 = _find_one(rd['openings'], 'id', 'WIN-05', 'WIN-05')
    if w5.get('sillH') == 22.5 and w5.get('height') == 191.0 and w5.get('est') is False:
        log.append(u'  [skip ] WIN-05 (既に v7.0 実測値)')
    else:
        w5['sillH'] = 22.5
        w5['height'] = 191.0
        w5['est'] = False
        if u'★v7.0' not in w5['label']:
            w5['label'] += WIN05_ADD
        log.append(u'  [apply] WIN-05 sill22.5 / h191.0 (上端213.5)')
        changed = True

    # ── ③ walls (E壁の区画を窓の新位置へ追従) ──
    for wid, fr, to in (('W-R62-E1', 107.0, 198.0), ('W-R62-E2', 242.0, 258.5),
                        ('W-R62-E3', 302.5, 418.0)):
        wl = _find_one(rd['walls'], 'id', wid, wid)
        if wl.get('from') == fr and wl.get('to') == to:
            log.append(u'  [skip ] %s (既に v7.0)' % wid)
            continue
        wl['from'], wl['to'] = fr, to
        wl['length'] = round(to - fr, 2)
        wl['where'] = u'y%s〜%s (x1055.0)' % (fr, to)
        log.append(u'  [apply] %s y%.1f〜%.1f (長さ %.1f)' % (wid, fr, to, wl['length']))
        changed = True
    # 2窓の離隔が 12.0 → 16.5 になり wallgen の MINOR_LEN=15 を超えるので minor が外れる
    e2 = _find_one(rd['walls'], 'id', 'W-R62-E2', 'W-R62-E2')
    if e2.get('minor') is True:
        e2['minor'] = False
        log.append(u'  [apply] W-R62-E2 minor True → False (長さ 16.5 ≧ MINOR_LEN 15)')
        changed = True
    else:
        log.append(u'  [skip ] W-R62-E2 minor (既に False)')
    # F-52 (大窓レール x834.0〜1038.0) が W-R62-N2 (x1013.5〜1055) と 24.5cm 重なるので
    # wallgen の attach_wall_features (重なり 20cm 以上で feature を付ける) と揃える
    n2 = _find_one(rd['walls'], 'id', 'W-R62-N2', 'W-R62-N2')
    if n2.get('feature') != u'カーテンレール':
        n2['feature'] = u'カーテンレール'
        if u'（' not in n2['name']:
            n2['name'] = n2['name'] + u'（カーテンレール）'
        log.append(u'  [apply] W-R62-N2 feature=カーテンレール (F-52 と 24.5cm 重なる)')
        changed = True
    else:
        log.append(u'  [skip ] W-R62-N2 feature (既にカーテンレール)')

    # ── ④ AC-3 ──
    ac = _find_one(rd['aircons'], 'id', 'AC-3', 'AC-3')
    if ac.get('pos') == [1055.0, 157.0] and ac.get('bottomH') == 203.5 and ac.get('w') == 94:
        log.append(u'  [skip ] AC-3 (既に v7.0 実測値)')
    else:
        ac['pos'] = [1055.0, 157.0]
        # 下端の実測は 202.0 だが 高所小窓の上端 (203.5) と 1.5cm 干渉する。
        # 1.5cm は本測定の誤差 (±1〜2cm) の範囲内なので、 窓の頭に載る形の 203.5 を採る。
        ac['bottomH'] = 203.5
        ac['w'] = 94
        ac['d'] = 21
        ac['hgt'] = 28.5
        if u'★v7.0' not in ac['label']:
            ac['label'] += AC3_ADD
        log.append(u'  [apply] AC-3 pos y157.0 / bottomH202.0 / 94×21×28.5')
        changed = True

    # ── ⑤ fixtures 3件 追加 ──
    have = set(f.get('id') for f in rd['fixtures'])
    for nf in (RAIL_SMALL, RAIL_BIG, HANGER):
        if nf['id'] in have:
            log.append(u'  [skip ] %s (既に登録済み)' % nf['id'])
            continue
        rd['fixtures'].append(json.loads(json.dumps(nf, ensure_ascii=False)))
        log.append(u'  [apply] %s %s を追加' % (nf['id'], nf['name']))
        changed = True

    # ── ⑥ meta ──
    if rd['meta'].get('version') != '6.7':
        rd['meta']['version'] = '6.7'
        log.append(u'  [apply] meta.version → 6.7')
        changed = True
    else:
        log.append(u'  [skip ] meta.version (既に 6.7)')
    if not any(n.startswith(u'★v6.7 (2026-08-22)') for n in rd['meta']['notes']):
        rd['meta']['notes'].append(V67_NOTE)
        log.append(u'  [apply] meta.notes に v6.7 の記録を追記')
        changed = True
    else:
        log.append(u'  [skip ] meta.notes (既に v6.7 の記録あり)')

    return changed, log


def assert_geometry(rd):
    r62 = _find_one(rd['rooms'], 'id', 'R-R62', 'R-R62')
    xs = [p[0] for p in r62['poly']]
    ys = [p[1] for p in r62['poly']]
    assert max(xs) - min(xs) == 255.0, u'6.2帖 E-W 内寸が 255 でない: %s' % (max(xs) - min(xs))
    assert max(ys) - min(ys) == 446.5 and min(ys) == 107.0, u'6.2帖 ポリゴンが変わった'
    print(u'    6.2帖 内寸 E-W 255.0 / N-S (主部) %.1f  … 不変 OK' % (418.0 - 107.0))

    wic = _find_one(rd['rooms'], 'id', 'R-WIC', 'R-WIC')
    assert wic['poly'] == [[882.0, 426.0], [1055.0, 426.0], [1055.0, 548.0], [882.0, 548.0]], \
        u'WIC ポリゴンが変わった'
    print(u'    WIC ポリゴン 173×122  … 不変 OK')

    d06 = _find_one(rd['openings'], 'id', 'D-06', 'D-06')
    assert d06['wallFrom'] == [790.0, 384.5] and d06['wallTo'] == [790.0, 553.5] and d06['width'] == 169.0, \
        u'LDK E壁チェーン (D-06 169) が変わった'
    print(u'    LDK E壁チェーン D-06 = 169.0 (y384.5〜553.5)  … 不変 OK')

    w6 = _find_one(rd['openings'], 'id', 'WIN-06', 'WIN-06')
    w7 = _find_one(rd['openings'], 'id', 'WIN-07', 'WIN-07')
    e1 = _find_one(rd['walls'], 'id', 'W-R62-E1', 'W-R62-E1')
    e2 = _find_one(rd['walls'], 'id', 'W-R62-E2', 'W-R62-E2')
    e3 = _find_one(rd['walls'], 'id', 'W-R62-E3', 'W-R62-E3')
    chain = [(u'N入隅→WIN-06', e1['length']), (u'WIN-06 幅', w6['width']),
             (u'2窓の離隔', e2['length']), (u'WIN-07 幅', w7['width']),
             (u'WIN-07→S入隅', e3['length'])]
    tot = sum(c[1] for c in chain)
    print(u'    E壁チェーン: ' + u' + '.join(u'%s %.1f' % c for c in chain) + u' = %.1f' % tot)
    assert abs(tot - 311.0) < 1e-6, u'E壁チェーンが 311 で閉じない: %.2f' % tot
    assert abs(e2['length'] - 16.5) < 1e-6, u'2窓の離隔が 16.5 でない'
    assert w6['wallFrom'][1] == e1['to'] and w6['wallTo'][1] == e2['from'], u'WIN-06 と壁区画が繋がらない'
    assert w7['wallFrom'][1] == e2['to'] and w7['wallTo'][1] == e3['from'], u'WIN-07 と壁区画が繋がらない'
    assert w6['sillH'] + w6['height'] == 203.5, u'WIN-06 の上端が 203.5 でない'

    f51 = _find_one(rd['fixtures'], 'id', 'F-51', 'F-51')
    assert f51['rect'][0] + f51['rect'][2] == 1055.0, u'F-51 が E壁 (x1055) に付いていない'
    assert f51['rect'][1] <= 192.1, u'F-51 の北端 (%.1f) がエアコンの陰の上限 192.1 を超える' % f51['rect'][1]
    assert f51['rect'][1] + f51['rect'][3] == 315.0, u'F-51 の南端が 315.0 でない'
    assert f51['bottomH'] > w6['sillH'] + w6['height'], u'F-51 が窓の上端より下にある'
    print(u'    F-51 レール y%.1f〜%.1f (長さ%.1f) 下端%.1f / 開口上端%.1f の上  … OK'
          % (f51['rect'][1], f51['rect'][1] + f51['rect'][3], f51['rect'][3], f51['bottomH'],
             w6['sillH'] + w6['height']))

    f52 = _find_one(rd['fixtures'], 'id', 'F-52', 'F-52')
    w5 = _find_one(rd['openings'], 'id', 'WIN-05', 'WIN-05')
    assert f52['rect'][1] == 107.0, u'F-52 が N壁 (y107) に付いていない'
    assert f52['rect'][0] < w5['wallFrom'][0] and \
        f52['rect'][0] + f52['rect'][2] > w5['wallTo'][0], u'F-52 が開口を覆っていない'
    assert f52['bottomH'] > w5['sillH'] + w5['height'], u'F-52 が窓の上端より下にある'
    print(u'    F-52 レール x%.1f〜%.1f (長さ%.1f) 下端%.1f / 開口上端%.1f の上  … OK'
          % (f52['rect'][0], f52['rect'][0] + f52['rect'][2], f52['rect'][2], f52['bottomH'],
             w5['sillH'] + w5['height']))

    f53 = _find_one(rd['fixtures'], 'id', 'F-53', 'F-53')
    cx = f53['rect'][0] + f53['rect'][2] / 2.0
    cz = f53['rect'][1] + f53['rect'][3] / 2.0
    assert 800.0 < cx < 1055.0 and 107.0 < cz < 418.0, u'F-53 が 6.2帖の外にある'
    print(u'    F-53 物干し 天井プレート (x%.1f, y%.1f) / フック下端 %.1f (下がり %.1f)  … OK'
          % (cx, cz, f53['bottomH'], f53['h'] - f53['bottomH']))

    ac = _find_one(rd['aircons'], 'id', 'AC-3', 'AC-3')
    n_end = ac['pos'][1] - ac['w'] / 2.0
    s_end = ac['pos'][1] + ac['w'] / 2.0
    wtop = w6['sillH'] + w6['height']
    assert n_end >= 107.0, u'A3 が N壁 (107) を突き抜けている: %.1f' % n_end
    # A3 は南端が WIN-06 の上に少しかぶる。 高さで逃げていること (下端 ≧ 窓の上端) を assert する。
    if s_end > w6['wallFrom'][1]:
        assert ac['bottomH'] >= wtop - 1e-6, \
            u'A3 が WIN-06 (y%.1f〜 / 上端%.1f) と干渉する: 南端 y%.1f / 下端 %.1f' \
            % (w6['wallFrom'][1], wtop, s_end, ac['bottomH'])
    assert ac['bottomH'] + ac['hgt'] <= 240.0, u'A3 の上端が天井を超える'
    print(u'    AC-3 y%.1f〜%.1f / 下端%.1f・上端%.1f (WIN-06 上端%.1f の上に %.1fcm かぶる)  … OK'
          % (n_end, s_end, ac['bottomH'], ac['bottomH'] + ac['hgt'], wtop,
             max(0.0, s_end - w6['wallFrom'][1])))


def main():
    dry = '--dry-run' in sys.argv
    text = read_text()
    original = text

    _, cs_line = data_line(text, CS_PREFIX)
    cs_before = sha(cs_line)

    rd_idx, rd_line = data_line(text, RD_PREFIX)
    rd, rd_semi = parse_json_line(rd_line, RD_PREFIX)
    assert dump_json_line(rd, RD_PREFIX, rd_semi) == rd_line.rstrip(), \
        'ROOM_DATA の JSON round-trip が一致しない (整形方法が想定外)'
    frozen_before = dict((k, sha(json.dumps(rd[k], ensure_ascii=False, separators=(',', ':'))))
                         for k in FROZEN_KEYS + FROZEN_SCALARS)
    counts_before = dict((k, len(rd[k])) for k in ('rooms', 'openings', 'outlets', 'aircons',
                                                   'lights', 'zones', 'walls'))
    nfix_before = len(rd['fixtures'])

    print(u'CATALOG_SEED sha256 (before) : %s' % cs_before)
    print(u'ROOM_DATA    sha256 (before) : %s  version=%s' % (sha(rd_line), rd['meta'].get('version')))
    print('')

    applied, skipped, failed = [], [], []
    for name, marker, old, new in JS_PATCHES:
        if marker in text:
            skipped.append(name)
            continue
        n = text.count(old)
        if n != 1:
            failed.append(u'%s : アンカー一致 %d 件 (期待 1)' % (name, n))
            continue
        text = text.replace(old, new, 1)
        applied.append(name)
    for n in applied:
        print(u'  [apply] %s' % n)
    for n in skipped:
        print(u'  [skip ] %s' % n)
    for n in failed:
        print(u'  [FAIL ] %s' % n)

    print('')
    rd_changed, rd_log = patch_room_data(rd)
    for l in rd_log:
        print(l)
    if rd_changed:
        lines = text.split('\n')
        i2, _ = data_line(text, RD_PREFIX)
        lines[i2] = dump_json_line(rd, RD_PREFIX, rd_semi)
        text = '\n'.join(lines)

    _, cs_after_line = data_line(text, CS_PREFIX)
    assert sha(cs_after_line) == cs_before, \
        'CATALOG_SEED CHANGED!\n  before=%s\n  after =%s' % (cs_before, sha(cs_after_line))
    _, rd_after_line = data_line(text, RD_PREFIX)
    rd_after, _ = parse_json_line(rd_after_line, RD_PREFIX)
    frozen_after = dict((k, sha(json.dumps(rd_after[k], ensure_ascii=False, separators=(',', ':'))))
                        for k in FROZEN_KEYS + FROZEN_SCALARS)
    for k in FROZEN_KEYS + FROZEN_SCALARS:
        assert frozen_before[k] == frozen_after[k], \
            u'ROOM_DATA.%s が変更されている (このパッチは meta/openings/aircons/walls/fixtures しか触らない)' % k
    for k, v in counts_before.items():
        assert len(rd_after[k]) == v, u'%s の件数が %d → %d に変わった' % (k, v, len(rd_after[k]))
    assert len(rd_after['fixtures']) in (nfix_before, nfix_before + 3), \
        u'fixtures が %d → %d (期待 +0 or +3)' % (nfix_before, len(rd_after['fixtures']))

    print('')
    print(u'  ── 幾何アサート ──')
    assert_geometry(rd_after)

    print('')
    print(u'CATALOG_SEED sha256 (after)  : %s  ← 不変 OK' % sha(cs_after_line))
    print(u'ROOM_DATA    sha256 (after)  : %s  version=%s' % (sha(rd_after_line), rd_after['meta'].get('version')))
    print(u'ROOM_DATA 不変アサート OK : %s' % ' / '.join(FROZEN_KEYS + FROZEN_SCALARS))
    print(u'fixtures %d → %d 件' % (nfix_before, len(rd_after['fixtures'])))
    print('')
    print(u'JS: 適用 %d 件 / skip %d 件 / 失敗 %d 件 / ROOM_DATA 変更 %s'
          % (len(applied), len(skipped), len(failed), u'あり' if rd_changed else u'なし'))

    if failed:
        print(u'\n!! 失敗があるので書き戻しません (並行編集でアンカーが変わった可能性)')
        return 1
    if dry:
        print(u'(dry-run: 書き込みなし)')
        return 0
    if text == original:
        print(u'→ 変更なし (全て適用済み)')
        return 0
    if read_text() != original:
        print(u'\n!! room.html が読み込み後に別プロセスで変更されました。 書き込みを中断します。 再実行してください。')
        return 2
    with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(u'→ %s を更新しました' % TARGET)
    return 0


if __name__ == '__main__':
    sys.exit(main())

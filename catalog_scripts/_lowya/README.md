# _lowya — LOWYA 公式ページの取得結果 (v8.6 のエビデンス)

`fetch_lowya.py` が出力した 公式ページ本文 と、 色を実測したスクリプト。

- `dresser_walnut_sq.txt` … アユリナ ドレッサーデスク 幅120 / **ウォルナット：ドレッサーデスク＋正方形ミラーセット** (買う予定の組み合わせ)
- `dresser_natural_sq.txt` / `dresser.txt` … 同 シャビーナチュラル / 既定選択 (単品) — 商品番号の控え
- `chest_walnut_high.txt` … アユリナ チェスト / **ウォルナット(ハイチェスト)** (買う予定の組み合わせ)
- `chest_natural_high.txt` / `chest.txt` … 同 シャビーナチュラル / 既定選択
- `img/*_specificationimages_*.jpg` … 公式サイズ図 (本体 / ミラー / チェスト)
- `_sample.py` `_u.py` `_u2.py` `_grid.py` … カラー16進の画素実測とグリッド当て
- `_dl.sh` `_sheet.py` `_search.py` `_links.py` … 公式画像の一括DL・コンタクトシート・商品URL探索

⚠ **公式商品画像 (img/dresser/, img/chest/ の各15〜16枚) と コンタクトシートは git に入れていない**。
一次資料は Box の
`野沢用\claude\nozaROOM\catalog\商品公式資料\LOWYA_アユリナ_ドレッサーデスク120\` と
`\LOWYA_アユリナ_チェスト80\` に README 付きで保存済み (色の実測領域もそこに記録)。

再取得:
```
bash ~/.claude/scripts/run_py.sh catalog_scripts/fetch_lowya.py \
  "https://www.low-ya.com/goods/MLT4G" dresser_walnut_sq "ドレッサー+正方形ミラーセット" "ウォルナット"
```

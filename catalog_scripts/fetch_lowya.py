# -*- coding: utf-8 -*-
u"""LOWYA 公式商品ページを 実ブラウザ (playwright) で開いて 仕様テキストと画像URLを取り出す。

  bash ~/.claude/scripts/run_py.sh catalog_scripts/fetch_lowya.py <url> <tag> [選択肢ラベル...]

LOWYA は Vue の CSR なので 静的 HTML には何も無い (curl は空 / api.low-ya.com は 403)。
= ニトリ アザン3 と同じく 「実ブラウザで取得」 が必要。 バリエーション (タイプ/カラー) ごとに
「サイズ・素材・備考」 の中身が差し替わるので、 **買う予定のバリエーションを実際にクリックしてから**
取得する (既定選択のまま読むと 別バリエーションの寸法を掴む)。

出力: catalog_scripts/_lowya/<tag>.txt (本文) / <tag>_imgs.txt (画像URL)
"""
import io
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_lowya')
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def main():
    url, tag, picks = sys.argv[1], sys.argv[2], sys.argv[3:]
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 2000}, user_agent=UA)
        pg.goto(url, wait_until='domcontentloaded', timeout=60000)
        pg.wait_for_timeout(5000)
        for label in picks:                       # 例: "ドレッサー+正方形ミラーセット" "ウォルナット"
            el = pg.get_by_text(label, exact=True).first
            el.scroll_into_view_if_needed()
            el.click()
            pg.wait_for_timeout(2500)
            print(u'  クリック: %s' % label)
        for _ in range(14):                       # 遅延読み込みのタブ/画像を出すため下までスクロール
            pg.mouse.wheel(0, 1400)
            pg.wait_for_timeout(450)
        pg.wait_for_timeout(1500)
        txt = pg.inner_text('body')
        imgs = pg.eval_on_selector_all('img', "els => els.map(e => e.currentSrc || e.src)")
        title = pg.title()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    io.open(os.path.join(OUT, tag + '.txt'), 'w', encoding='utf-8').write(
        title + u'\n' + url + u'\n選択: ' + u' / '.join(picks) + u'\n\n' + txt)
    io.open(os.path.join(OUT, tag + '_imgs.txt'), 'w', encoding='utf-8').write(u'\n'.join(sorted(set(imgs))))
    print(u'%s: 本文 %d 文字 / 画像 %d 件' % (tag, len(txt), len(set(imgs))))
    return 0


if __name__ == '__main__':
    sys.exit(main())

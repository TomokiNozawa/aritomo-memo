# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
JS = "els => els.map(e => [e.href, (e.innerText || '').slice(0,90)])"
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1280, "height": 1600}, user_agent=UA)
    pg.goto("https://www.low-ya.com/goods/F501_05002", wait_until='domcontentloaded', timeout=60000)
    pg.wait_for_timeout(5000)
    for _ in range(14):
        pg.mouse.wheel(0, 1400); pg.wait_for_timeout(400)
    seen = set()
    for href, t in pg.eval_on_selector_all('a', JS):
        t = u' '.join(t.split())
        if '/goods/' in href and u'ドレッサー' in t and href not in seen:
            seen.add(href); print(href, '|', t)

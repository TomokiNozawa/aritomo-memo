# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1280, "height": 1600}, user_agent=UA)
    pg.goto("https://www.low-ya.com/search?keyword=" + "%E3%82%A2%E3%83%A6%E3%83%AA%E3%83%8A", wait_until='domcontentloaded', timeout=60000)
    pg.wait_for_timeout(6000)
    for _ in range(6):
        pg.mouse.wheel(0, 1200); pg.wait_for_timeout(400)
    links = pg.eval_on_selector_all('a', "els => els.map(e => e.href + ' | ' + (e.innerText||'').replace(/\s+/g,' ').slice(0,80))")
    for l in links:
        if '/goods/' in l:
            print(l)

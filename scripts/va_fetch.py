#!/usr/bin/env python3
"""Fetch the legislation of Vatican City State published on www.vaticanstate.va
("Stato e Governo > Legislazione e normativa"): every category page is parsed for its
document download links (PDF), which are cached under _raw/va/."""
import html
import json
import os
import re
import sys
import time

import requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://www.vaticanstate.va"
ROOT = "/it/stato-e-governo/legislazione-e-normativa"
RAW = os.path.abspath(os.environ.get("VA_RAW", os.path.join(os.path.dirname(__file__), "..", "..", "_raw", "va")))
S = requests.Session()
S.headers["User-Agent"] = UA


def get(url, tries=5):
    for i in range(tries):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 200:
                return r
            print("HTTP", r.status_code, url, file=sys.stderr)
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            print("ERR", e, url, file=sys.stderr)
        time.sleep(5 * (i + 1))
    return None


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse_category(url):
    out, start, name = [], 0, url
    while True:
        u = url + (f"?start={start}" if start else "")
        n, docs, more = parse_page(u, start)
        name = n if start == 0 else name
        out += docs
        if not more or not docs:
            return name, out
        start += 20
        time.sleep(2)


def parse_page(url, start):
    t = get(BASE + url).content.decode("utf-8", "replace")
    more = f"start={start + 20}" in t
    title = re.search(r"<title>(.*?)</title>", t, re.S)
    out = []
    # walk the page in order, remembering the latest heading seen
    heading = None
    for m in re.finditer(r'<h[1-6][^>]*>(.*?)</h[1-6]>|<a[^>]+href="([^"]*\?download=(\d+):([^"]*))"[^>]*>(.*?)</a>', t, re.S):
        if m.group(1) is not None:
            h = text(m.group(1))
            if h:
                heading = h
            continue
        href, did, slug, label = m.group(2), m.group(3), m.group(4), text(m.group(5))
        if label.lower() in ("download", "scarica", ""):
            continue
        out.append({"id": did, "slug": slug, "title": label, "heading": heading,
                    "url": html.unescape(href if href.startswith("http") else BASE + href)})
    return (text(title.group(1)) if title else url), out, more


def main():
    os.makedirs(os.path.join(RAW, "pdf"), exist_ok=True)
    idx = os.path.join(RAW, "index.json")
    if not os.path.exists(idx):
        t = get(BASE + ROOT + ".html").content.decode("utf-8", "replace")
        cats = sorted(set(re.findall(r'href="(' + re.escape(ROOT) + r'/[^"#?]+\.html)"', t)))
        items = []
        for c in cats:
            name, docs = parse_category(c)
            for d in docs:
                d["category"] = c.rsplit("/", 1)[1][:-5]
                d["category_title"] = name
            items += docs
            print(c, len(docs), file=sys.stderr)
            time.sleep(2)
        # main page may itself list documents
        _, docs, _ = parse_page(ROOT + ".html", 0)
        for d in docs:
            d["category"] = "legislazione-e-normativa"
            d["category_title"] = "Legislazione e normativa"
        items += docs
        json.dump(items, open(idx, "w"), ensure_ascii=False, indent=1)
    items = json.load(open(idx))
    seen = set()
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        f = os.path.join(RAW, "pdf", it["id"] + ".bin")
        if os.path.exists(f):
            continue
        r = get(it["url"])
        if r is not None:
            open(f, "wb").write(r.content)
            open(f + ".hdr", "w").write(r.headers.get("Content-Type", "") + "\n" + r.headers.get("Content-Disposition", ""))
        time.sleep(2)
    print("done", len(seen), file=sys.stderr)


if __name__ == "__main__":
    main()

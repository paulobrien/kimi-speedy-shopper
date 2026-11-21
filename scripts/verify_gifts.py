#!/usr/bin/env python3
"""Check that a shopper answer lists five real, live product pages.

Reads the agent's answer (lines like `1. Name — £20 — Shop — https://...`),
fetches every URL in parallel, and reports for each one: HTTP status, final
URL, page title, and product evidence (schema.org Product/Offer JSON-LD,
og:type product, product meta tags, or a price plus an add-to-basket button).

    python3 scripts/verify_gifts.py answer.txt
    openclaw agent exec ... --json | jq -r .final | python3 scripts/verify_gifts.py -
    python3 scripts/verify_gifts.py --json answer.txt     # machine-readable

Pages that refuse plain HTTP clients (403/429/timeouts) are re-checked through
Parallel's page fetcher (scripts/parallel_mcp.py); those count as live when the
extracted page shows a price and a buy/stock signal. --no-fallback turns it off.

Exit 0 when there are five distinct product URLs on at least two retail
domains and every one of them is a live product page; 1 otherwise.
Standard library only.
"""

import argparse
import concurrent.futures as cf
import gzip
import html
import json
import re
import sys
import urllib.error
import urllib.request
import zlib
from urllib.parse import urlsplit

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+"
                    r"|(?<![\w/@.])(?:[a-z0-9-]+\.)+[a-z]{2,}/[^\s<>\"')\]]+", re.I)
NOT_RETAIL = ("wikipedia.org", "youtube.com", "reddit.com", "pinterest.", "facebook.com",
              "instagram.com", "tiktok.com", "x.com", "twitter.com", "medium.com")
PRICE_RE = re.compile(r"(?:[$£€]\s?\d[\d,]*(?:\.\d{2})?|\d[\d,]*(?:\.\d{2})?\s?(?:USD|GBP|EUR))")
CART_RE = re.compile(r"add to (?:cart|basket|bag|trolley)|buy now|in stock|add-to-cart|addtocart"
                     r"|add this item|out of stock|quantity|\bsku\b|product code|read reviews"
                     r"|(?:choose|select) (?:a )?(?:colour|color|size)", re.I)


def extract_urls(text):
    seen, out = set(), []
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?*_`")
        if not url.lower().startswith("http"):
            url = "https://" + url
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9", "Accept-Encoding": "gzip, deflate"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(3_000_000)
            enc = (r.headers.get("Content-Encoding") or "").lower()
            if enc == "gzip":
                raw = gzip.decompress(raw)
            elif enc == "deflate":
                raw = zlib.decompress(raw)
            return r.status, r.geturl(), raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:  # noqa: BLE001 - network errors of every kind
        return 0, url, f"__error__ {type(e).__name__}: {e}"


def product_evidence(page):
    ev = []
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        if re.search(r'"@type"\s*:\s*\[?\s*"(?:Product|ProductGroup|Offer|AggregateOffer)"', block):
            ev.append("json-ld Product")
            break
    if re.search(r'<meta[^>]+property=["\']og:type["\'][^>]+content=["\'](?:og:)?product', page, re.I) or \
       re.search(r'<meta[^>]+content=["\'](?:og:)?product["\'][^>]+property=["\']og:type', page, re.I):
        ev.append("og:type product")
    if re.search(r'(?:product:price:amount|itemprop=["\']price["\']|og:price:amount)', page, re.I):
        ev.append("price meta")
    if PRICE_RE.search(page) and CART_RE.search(page):
        ev.append("price + buy button")
    return ev


def title_of(page):
    m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:120] if m else ""


def check(url):
    status, final, page = fetch(url)
    host = urlsplit(final or url).hostname or ""
    ev = product_evidence(page) if status == 200 else []
    blocked = status in (401, 403, 429, 503) or "__error__" in page[:20]
    return {"url": url, "status": status, "final_url": final, "domain": host.removeprefix("www."),
            "title": title_of(page), "evidence": ev,
            "ok": status == 200 and bool(ev) and not any(b in host for b in NOT_RETAIL),
            "blocked": blocked}


def fallback(results):
    todo = [r for r in results if not r["ok"] and (r["blocked"] or r["status"] == 200)]
    if not todo:
        return
    try:
        sys.path.insert(0, __import__("os").path.dirname(__file__))
        from parallel_mcp import ParallelMCP
        got = ParallelMCP().fetch([r["url"] for r in todo])
    except Exception as e:  # noqa: BLE001
        for r in todo:
            r["fallback_error"] = str(e)[:200]
        return
    by_url = {x.get("url"): x for x in got.get("results") or []}
    for r in todo:
        x = by_url.get(r["url"])
        if not x:
            continue
        text = " ".join(x.get("excerpts") or [])
        if PRICE_RE.search(text) and CART_RE.search(text):
            r["ok"] = True
            r["evidence"] = r["evidence"] + ["parallel fetch: price + buy button"]
            r["title"] = r["title"] or (x.get("title") or "")[:120]


def verify(text, need=5, use_fallback=True):
    urls = extract_urls(text)
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(check, urls))
    if use_fallback:
        fallback(results)
    good = [r for r in results if r["ok"]]
    domains = {r["domain"] for r in good}
    return {"urls": len(urls), "verified": len(good), "domains": len(domains),
            "pass": len(urls) >= need and len(good) >= need and len(domains) >= 2,
            "results": results}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("answer", help="file with the agent's answer, or - for stdin")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-fallback", action="store_true")
    a = p.parse_args()
    text = sys.stdin.read() if a.answer == "-" else open(a.answer).read()
    rep = verify(text, use_fallback=not a.no_fallback)
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        for r in rep["results"]:
            mark = "✔" if r["ok"] else ("?" if r["blocked"] else "✘")
            print(f"{mark} {r['status']:>3}  {r['domain']:<28} {', '.join(r['evidence'])[:40] or '-':<40} {r['title'][:60]}")
        print(f"\n{rep['verified']}/{rep['urls']} live product pages on {rep['domains']} retailers: "
              f"{'PASS' if rep['pass'] else 'FAIL'}")
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

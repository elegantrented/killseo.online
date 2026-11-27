#!/usr/bin/env python3
"""Rebuild the link list in index.html from links.txt (run by deploy.sh)."""
import html, os, re, sys
from urllib.parse import urlparse

here = os.path.dirname(os.path.abspath(__file__))
items = []
for n, raw in enumerate(open(os.path.join(here, "links.txt"), encoding="utf-8"), 1):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    url, _, text = (p.strip() for p in line.partition("|"))
    if not re.match(r"^https?://", url):
        url = "https://" + url
    host = urlparse(url).netloc
    if not host or " " in url:
        sys.exit(f"links.txt line {n}: not a valid link: {raw.strip()}")
    text = text or host.removeprefix("www.")
    items.append(f'<li><a href="{html.escape(url, quote=True)}">{html.escape(text)}</a></li>')

block = "<ul>\n" + "\n".join(items) + "\n</ul>\n" if items else ""
page = os.path.join(here, "index.html")
s = open(page, encoding="utf-8").read()
new, count = re.subn(r"(<!-- LINKS START[^>]*-->\n).*?(<!-- LINKS END -->)",
                     lambda m: m.group(1) + block + m.group(2), s, flags=re.S)
if count != 1:
    sys.exit("index.html: LINKS START / LINKS END markers missing")
open(page, "w", encoding="utf-8").write(new)
print(f"{len(items)} link(s) written to index.html")

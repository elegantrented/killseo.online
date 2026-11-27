#!/usr/bin/env python3
"""Build the site into public/ from settings.txt, sites.txt, templates/ and static/.

Cloudflare runs this on every commit (build command: python3 build.py).

Template syntax
  {name}                    value from settings.txt, or a built-in tag
  {each site} ... {/each}   repeated once per line of sites.txt
  {if name} ... {/if}       kept only when setting `name` is not empty
  {each other} ... {/each}  like {each site} but skips the current site (site pages only)
  {each anchor} ... {/each anchor}  repeated once per anchor phrase of a site (5th part of
                            its sites.txt line); use inside {each site}/{each other} or on site pages
Per-site tags: {url} {host} {domain} {text} {about} {review} {slug} {page_url} {n} {comma}
Settings may use per-site tags too (e.g. "paid_text: Paid by {text}"); each site gets its own version.

templates/site-page.html is rendered once per site into public/<slug>/index.html,
with that site's tags available everywhere on the page.
"""
import datetime, html, json, os, re, shutil, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
TAG = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
PER_SITE = {"url", "host", "domain", "text", "about", "slug", "page_url", "review", "anchors"}
ANCHOR_BLOCK = re.compile(r"\{each anchor\}(.*?)\{/each anchor\}", re.S)


def expand_anchors(text, site, values, esc, where):
    return ANCHOR_BLOCK.sub(lambda m: "".join(fill(m.group(1), {**values, "anchor": a}, esc, where)
                                              for a in site.get("_anchors", [])), text)


def die(msg):
    sys.exit(f"build error: {msg}")


def lines(name):
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        die(f"{name} is missing")
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.strip()
        if line and not line.startswith("#"):
            yield n, line


def load_settings():
    s = {}
    for n, line in lines("settings.txt"):
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if not sep or not TAG.fullmatch("{" + key + "}"):
            die(f"settings.txt line {n}: expected `name: value`, got: {line}")
        s[key] = value.strip()
    if not s.get("domain"):
        die("settings.txt: `domain` is required")
    today = datetime.date.today()
    s.update(site_url=f"https://{s['domain']}/", today=today.isoformat(), year=str(today.year))
    for _ in range(3):  # let settings reference other settings, e.g. {year} {site_name}
        # per-site tags like {text} or {domain} are left in place and filled for each site later
        s = {k: TAG.sub(lambda m: m.group(0) if m.group(1) in PER_SITE else s.get(m.group(1), m.group(0)), v)
             for k, v in s.items()}
    return s


def slugify(host, path):
    base = (host[4:] if host.startswith("www.") else host) + ("-" + path if path.strip("/") else "")
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def load_sites(settings):
    sites, seen = [], {}
    for n, line in lines("sites.txt"):
        parts = [p.strip() for p in line.split("|")] + ["", "", "", ""]
        url, text, about, review, anchors = parts[:5]
        if not re.match(r"^https?://", url, re.I):
            url = "https://" + url
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if "." not in host or " " in url:
            die(f"sites.txt line {n}: not a valid website: {line}")
        domain = host[4:] if host.startswith("www.") else host
        slug = slugify(host, parsed.path)
        seen[slug] = seen.get(slug, 0) + 1
        if seen[slug] > 1:
            slug = f"{slug}-{seen[slug]}"
        site = {"url": url, "host": host, "domain": domain, "text": text or domain,
                "slug": slug, "page_url": f"{settings['site_url']}{slug}/",
                "_anchors": [a.strip() for a in anchors.split(",") if a.strip()]}
        site["anchors"] = ", ".join(site["_anchors"])
        fill_in = lambda v: TAG.sub(lambda m: site.get(m.group(1), settings.get(m.group(1), m.group(0))), v)
        site["about"] = about or fill_in(settings.get("site_about", ""))
        site["review"] = review or fill_in(settings.get("review_url", ""))
        # settings that use per-site tags (e.g. "Paid by {text}") get this site's version
        for k, v in settings.items():
            if k not in site and any(t in PER_SITE for t in TAG.findall(v)):
                site[k] = fill_in(v)
        sites.append(site)
    if not sites:
        die("sites.txt has no websites")
    return sites


def escaper(filename):
    ext = os.path.splitext(filename)[1]
    if ext in (".html", ".htm"):
        return lambda v: html.escape(v, quote=True)
    if ext == ".xml":
        return lambda v: html.escape(v, quote=True)
    if ext in (".json", ".webmanifest"):
        return lambda v: json.dumps(v)[1:-1]
    return lambda v: v


def json_text(v):
    return json.dumps(v)[1:-1].replace("</", "<\\/")


def fill(text, values, esc, where):
    def sub(m):
        key = m.group(1)
        if key not in values:
            die(f"{where}: unknown tag {{{key}}} (add it to settings.txt)")
        return esc(str(values[key]))
    return TAG.sub(sub, text)


def render(text, settings, sites, esc, where, current=None):
    count = len(sites)
    page = {**settings, "count": count, **(current or {})}

    def each(m):
        group = [x for x in sites if m.group(1) != "other" or x is not current]
        out = []
        for i, site in enumerate(group, 1):
            vals = {**settings, **site, "n": i, "count": count,
                    "comma": "," if i < len(group) else ""}
            out.append(fill(expand_anchors(m.group(2), site, vals, esc, where), vals, esc, where))
        return "".join(out)

    text = re.sub(r"\{each (sites?|other)\}(.*?)\{/each\}", each, text, flags=re.S)
    text = expand_anchors(text, current or {}, page, esc, where)
    # innermost {if} first, so {if} blocks can be nested
    inner_if = re.compile(r"\{if ([a-z_][a-z0-9_]*)\}((?:(?!\{if ).)*?)\{/if\}", re.S)
    while True:
        text, n = inner_if.subn(lambda m: m.group(2) if page.get(m.group(1)) else "", text)
        if not n:
            break
    return fill(text, page, esc, where)


def render_file(name, settings, sites, current=None):
    src = open(os.path.join(ROOT, "templates", name), encoding="utf-8").read()
    esc = escaper(name)
    where = f"templates/{name}"
    if name.endswith((".html", ".htm")):
        # JSON-LD blocks need JSON escaping, not HTML escaping
        parts = re.split(r"(<script type=\"application/ld\+json\">.*?</script>)", src, flags=re.S)
        result = "".join(render(part, settings, sites, json_text if i % 2 else esc, where, current)
                         for i, part in enumerate(parts))
        for block in re.findall(r"<script type=\"application/ld\+json\">(.*?)</script>", result, flags=re.S):
            try:
                json.loads(block)
            except ValueError as e:
                die(f"{where}: structured data is not valid JSON after filling tags ({e})")
        return result
    return render(src, settings, sites, esc, where, current)


SITE_PAGE = "site-page.html"


def main():
    settings = load_settings()
    sites = load_sites(settings)
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "static"), OUT)
    for name in sorted(os.listdir(os.path.join(ROOT, "templates"))):
        if name.startswith(".") or name == SITE_PAGE:
            continue
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(render_file(name, settings, sites))
    pages = 0
    if os.path.exists(os.path.join(ROOT, "templates", SITE_PAGE)):
        for site in sites:
            if os.path.exists(os.path.join(OUT, site["slug"])):
                die(f"sites.txt: page name /{site['slug']}/ clashes with an existing file")
            os.makedirs(os.path.join(OUT, site["slug"]))
            with open(os.path.join(OUT, site["slug"], "index.html"), "w", encoding="utf-8") as f:
                f.write(render_file(SITE_PAGE, settings, sites, site))
            pages += 1
    print(f"built {settings['site_url']} with {len(sites)} site(s) and {pages} site page(s) into public/")


if __name__ == "__main__":
    main()

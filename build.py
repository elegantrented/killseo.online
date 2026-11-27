#!/usr/bin/env python3
"""Build the site into public/ from settings.txt, sites.txt, templates/ and static/.

Cloudflare runs this on every commit (build command: python3 build.py).

Template syntax
  {name}                    value from settings.txt, or a built-in tag
  {each site} ... {/each}   repeated once per line of sites.txt
  {if name} ... {/if}       kept only when setting `name` is not empty
Per-site tags (inside {each site}): {url} {host} {domain} {text} {n} {comma}
"""
import datetime, html, json, os, re, shutil, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
TAG = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


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
        s = {k: TAG.sub(lambda m: s.get(m.group(1), m.group(0)), v) for k, v in s.items()}
    return s


def load_sites():
    sites = []
    for n, line in lines("sites.txt"):
        url, _, text = (p.strip() for p in line.partition("|"))
        if not re.match(r"^https?://", url, re.I):
            url = "https://" + url
        host = urlparse(url).hostname or ""
        if "." not in host or " " in url:
            die(f"sites.txt line {n}: not a valid website: {line}")
        domain = host[4:] if host.startswith("www.") else host
        sites.append({"url": url, "host": host, "domain": domain, "text": text or domain})
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


def render(text, settings, sites, esc, where):
    count = len(sites)

    def each(m):
        out = []
        for i, site in enumerate(sites, 1):
            vals = {**settings, **site, "n": i, "count": count, "comma": "," if i < count else ""}
            out.append(fill(m.group(1), vals, esc, where))
        return "".join(out)

    text = re.sub(r"\{each sites?\}(.*?)\{/each\}", each, text, flags=re.S)
    text = re.sub(r"\{if ([a-z_][a-z0-9_]*)\}(.*?)\{/if\}",
                  lambda m: m.group(2) if settings.get(m.group(1)) else "", text, flags=re.S)
    return fill(text, {**settings, "count": count}, esc, where)


def render_file(name, settings, sites):
    src = open(os.path.join(ROOT, "templates", name), encoding="utf-8").read()
    esc = escaper(name)
    if esc is not None and name.endswith((".html", ".htm")):
        # JSON-LD blocks need JSON escaping, not HTML escaping
        parts = re.split(r"(<script type=\"application/ld\+json\">.*?</script>)", src, flags=re.S)
        out = []
        for i, part in enumerate(parts):
            is_json = i % 2 == 1
            out.append(render(part, settings, sites, json_text if is_json else esc, f"templates/{name}"))
        result = "".join(out)
        for block in re.findall(r"<script type=\"application/ld\+json\">(.*?)</script>", result, flags=re.S):
            try:
                json.loads(block)
            except ValueError as e:
                die(f"templates/{name}: structured data is not valid JSON after filling tags ({e})")
        return result
    return render(src, settings, sites, esc, f"templates/{name}")


def main():
    settings, sites = load_settings(), load_sites()
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "static"), OUT)
    for name in sorted(os.listdir(os.path.join(ROOT, "templates"))):
        if name.startswith("."):
            continue
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(render_file(name, settings, sites))
    print(f"built {settings['site_url']} with {len(sites)} site(s) into public/")


if __name__ == "__main__":
    main()

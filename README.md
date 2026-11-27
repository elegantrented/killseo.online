# killseo.online

Plain HTML site. Cloudflare rebuilds and publishes it automatically on every commit to `main` — about a minute. Edit everything right here on GitHub (pencil icon → Commit). Nothing to run locally.

## The two files you edit

**`sites.txt`** — your websites, one per line:

```
example.com
https://example.com/page
https://example.com | Text people click on
```

Optional extra parts, in order: link text, a description for that site's page, and a review link:
`https://example.com | Example | One or two sentences about it. | https://g.page/r/xyz/review`
Leave a part empty with `| |` to skip it.

Every site's page says **Paid by {text}** (`paid_text` in settings.txt) and has a **Leave {text} a review** link (`review_text` / `review_url`, Trustpilot for that domain by default). Links to listed sites carry `rel="sponsored"` (`link_rel`), which Google requires on paid links; blank it for plain follow links at your own risk.

Each line gets **its own page** at `killseo.online/<name>/` (e.g. `example.com` → `/example-com/`), built from `templates/site-page.html`, plus a link on the homepage, a sitemap entry and rows in the Google structured data. Sites without a description use `site_about` from settings.txt — write unique ones, since near-identical pages rank poorly.

**`settings.txt`** — the page-wide values (title, description, keywords, heading, intro text, footer, verification codes…), as `name: value`.

## How the tags work

Files in `templates/` are the pages, with `{tags}` where values go:

| Tag | Filled with |
|---|---|
| `{title}`, `{description}`, any `name` from settings.txt | that setting |
| `{site_url}` | `https://<domain>/` |
| `{today}`, `{year}` | build date / year |
| `{count}` | number of sites |
| `{each site}` … `{/each}` | repeated once per line of sites.txt |
| `{each other}` … `{/each}` | same, skipping the current site (site pages only) |
| `{url}` `{host}` `{domain}` `{text}` `{about}` `{review}` `{slug}` `{page_url}` `{n}` `{comma}` | per-site values, inside `{each …}` and anywhere in `site-page.html` |
| `{if name}` … `{/if}` | kept only if that setting isn't empty |

Add a new tag by adding `name: value` to settings.txt and `{name}` to a template. A setting can use per-site tags (e.g. `paid_text: Paid by {text}`), and each site gets its own version. Images and icons live in `static/` and are copied as-is.

If a line is invalid, the build fails with a message saying which line, and the previous version stays live. See the error under Cloudflare → Workers & Pages → killseo-online → Deployments.

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

**Keyword links (5th part of a line):** `https://example.com | Example | | | best business loans, cheap lease buyout` — each comma-separated phrase becomes its own link to that site, on the homepage and the site's page. Leave the 3rd/4th parts empty with `| |` if you don't have them. Keep phrases varied and honest — identical money phrases across many sites is the classic link-scheme pattern.

**`posts/`** — blog posts, one `.md` file each, published at `killseo.online/blog/<file name>/`:

```
title: Post title
description: One-sentence summary for Google
site: https://example.com
date: 2026-11-27
---
Article text. Blank line between paragraphs.

## A heading

- bullet
- bullet

1. numbered
2. numbered

**bold** and [link text](https://example.com)
```

`site:` must match a site in sites.txt; that site's page links to the post and the post links back.

**Automatic posts (no AI):** every site in sites.txt that has *no* file in `posts/` automatically gets a post filled in from the templates in `templates/auto-posts/` — add a site and its post appears on the next publish. Sites rotate through the templates (1st site → template 1, 2nd → template 2, …), so add more `.md` files there for more variety. The templates use the same tags as site pages (`{text}`, `{domain}`, `{url}`, `{about}`, `{page_url}`, `{each anchor}…{/each anchor}`, `{if anchors}…{/if}`) plus `title:`, `description:` and `slug:` header lines. To replace an automatic post with your own, add a file to `posts/` for that site — the automatic one disappears. Write each post by hand about a real topic — copy-paste posts with only the name changed are what gets a site ignored by Google.

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
| `{each anchor}` … `{/each anchor}` | repeated per keyword phrase of a site; `{anchor}` is the phrase |
| `{if name}` … `{/if}` | kept only if that setting isn't empty (can be nested) |

Add a new tag by adding `name: value` to settings.txt and `{name}` to a template. A setting can use per-site tags (e.g. `paid_text: Paid by {text}`), and each site gets its own version. Images and icons live in `static/` and are copied as-is.

If a line is invalid, the build fails with a message saying which line, and the previous version stays live. See the error under Cloudflare → Workers & Pages → killseo-online → Deployments.

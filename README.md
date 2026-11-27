# killseo.online

Plain HTML site. Cloudflare rebuilds and publishes it automatically on every commit to `main` — about a minute. Edit everything right here on GitHub (pencil icon → Commit). Nothing to run locally.

## The two files you edit

**`sites.txt`** — your websites, one per line:

```
example.com
https://example.com/page
https://example.com | Text people click on
```

Each line fills in every `{each site}` block: the link on the page, a dns-prefetch row, and two rows in the Google structured data. All links are follow links.

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
| `{url}` `{host}` `{domain}` `{text}` `{n}` `{comma}` | per-site values, inside `{each site}` |
| `{if name}` … `{/if}` | kept only if that setting isn't empty |

Add a new tag by adding `name: value` to settings.txt and `{name}` to a template. Images and icons live in `static/` and are copied as-is.

If a line is invalid, the build fails with a message saying which line, and the previous version stays live. See the error under Cloudflare → Workers & Pages → killseo-online → Deployments.

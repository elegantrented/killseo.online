#!/bin/sh
# Publish the site to Cloudflare. Run from this folder: ./deploy.sh
# Rebuilds the link list from links.txt first.
cd "$(dirname "$0")" || exit 1
python3 build-links.py || exit 1
npx -y wrangler@4.169.0 deploy

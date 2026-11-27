#!/bin/sh
# Publish the site to Cloudflare. Run from this folder: ./deploy.sh
cd "$(dirname "$0")" && npx -y wrangler@4.169.0 deploy

#!/usr/bin/env bash
# Load both tiers' models into memory before a demo. The first request after a model
# has been unloaded pays a cold start (several seconds); this pays it up front.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi

PROXY="${LITELLM_PROXY:-http://127.0.0.1:4000}"
for tier in fast smart; do
  printf 'warming %-5s ... ' "$tier"
  curl -sf "$PROXY/v1/chat/completions" \
    -H 'content-type: application/json' \
    -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-no-key}" \
    -d "{\"model\":\"$tier\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" \
    -o /dev/null \
    && echo ok \
    || { echo "FAILED (is the proxy running? ./scripts/run-proxy.sh)"; exit 1; }
done

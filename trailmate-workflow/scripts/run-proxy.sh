#!/usr/bin/env bash
# Start the LiteLLM proxy on http://127.0.0.1:4000 with TrailMate's tier config.
#
# LiteLLM runs as an isolated uv *tool* (uvx): its very large dependency tree never
# touches the service's own environment, just like a separately deployed proxy in
# production. The version and its Python (3.12) are pinned so every run, on every
# machine, behaves the same. Windows can't run this file: there (or anywhere) use
#   uv run python scripts/run_proxy.py
set -euo pipefail
cd "$(dirname "$0")/.."                                  # the trailmate-workflow directory

if [ -f .env ]; then set -a; . ./.env; set +a; fi        # export LITELLM_MASTER_KEY etc., if set

# LiteLLM (>= 1.10x) refuses to start without a strong master key. Fail fast, with the fix.
if [ -z "${LITELLM_MASTER_KEY:-}" ] && [ "${LITELLM_DANGEROUSLY_PERMIT_WEAK_OR_UNSET_MASTER_KEY:-}" != "true" ]; then
  echo "LITELLM_MASTER_KEY is not set. Create your own local key once (stored in .env, gitignored):" >&2
  echo "  uv run python scripts/setup_env.py" >&2
  exit 1
fi

# The proxy never fetches anything on its own (model catalogs, tokenizers): it only talks
# to Ollama, so it also starts without internet. Set it to false in .env to opt out.
export LITELLM_OFFLINE_MODE="${LITELLM_OFFLINE_MODE:-true}"

exec uvx --python 3.12 --from "litellm[proxy]==1.110.0" litellm \
  --config litellm/config.yaml --host 127.0.0.1 --port 4000

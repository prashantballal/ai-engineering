#!/usr/bin/env bash
# Download the two local models behind TrailMate's tiers (~3.8 GB in total).
# Keep these tags identical to litellm/config.yaml.
set -euo pipefail

ollama pull llama3.2:1b        # tier "fast"  (~1.3 GB)
ollama pull qwen3:4b-instruct  # tier "smart" (~2.5 GB). Not plain qwen3:4b, which always "thinks"
ollama list

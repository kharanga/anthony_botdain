#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
models_dir="${MODELS_DIR:-$repo_root/models}"
model_path="${MODEL_PATH:-$models_dir/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
model_port="${MODEL_PORT:-8080}"
model_context_tokens=2048

if [ ! -f "$model_path" ]; then
  echo "No model at $model_path. Run scripts/fetch_model.sh first." >&2
  exit 1
fi

exec llama-server \
  --offline \
  --model "$model_path" \
  --alias qwen2.5-1.5b-instruct \
  --host 127.0.0.1 \
  --port "$model_port" \
  --ctx-size "$model_context_tokens" \
  --parallel 1 \
  --n-gpu-layers 99 \
  --no-webui

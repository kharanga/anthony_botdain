#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
models_dir="${MODELS_DIR:-$repo_root/models}"
model_file="qwen2.5-1.5b-instruct-q4_k_m.gguf"
model_url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/$model_file"
model_sha256="6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e"
model_path="$models_dir/$model_file"

mkdir -p "$models_dir"
if [ ! -f "$model_path" ]; then
  curl --fail --location --continue-at - --output "$model_path.part" "$model_url"
  mv "$model_path.part" "$model_path"
fi
echo "$model_sha256  $model_path" | shasum -a 256 --check

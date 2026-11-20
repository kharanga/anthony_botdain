#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
models_dir="${MODELS_DIR:-$repo_root/models}"
model_file="ggml-base.en.bin"
model_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$model_file"
model_sha256="a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"
model_path="$models_dir/$model_file"

mkdir -p "$models_dir"
if [ ! -f "$model_path" ]; then
  curl --fail --location --continue-at - --output "$model_path.part" "$model_url"
  mv "$model_path.part" "$model_path"
fi
echo "$model_sha256  $model_path" | shasum -a 256 --check

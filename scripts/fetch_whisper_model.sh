#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
models_dir="${MODELS_DIR:-$repo_root/models}"
model_file="ggml-base.en.bin"
model_url="${WHISPER_MODEL_URL:-https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$model_file}"
model_sha256="${WHISPER_MODEL_SHA256:-a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002}"
model_path="$models_dir/$model_file"
partial_path="$model_path.part"

matches_checksum() {
  echo "$model_sha256  $1" | shasum -a 256 --check --status
}

mkdir -p "$models_dir"
if [ -f "$model_path" ] && matches_checksum "$model_path"; then
  echo "$model_path: OK"
  exit 0
fi
rm -f "$model_path"
curl --fail --location --continue-at - --output "$partial_path" "$model_url"
if ! matches_checksum "$partial_path"; then
  rm -f "$partial_path"
  echo "$model_url failed the SHA-256 check; deleted the download, run again to refetch" >&2
  exit 1
fi
mv "$partial_path" "$model_path"
echo "$model_path: OK"

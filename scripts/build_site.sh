#!/usr/bin/env bash
# Monta el sitio estático (web/ + data/) en el directorio indicado (por defecto _site/).
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-_site}"
rm -rf "$out"
mkdir -p "$out/data"
cp web/*.html web/*.css web/*.js "$out/"
cp data/*.json "$out/data/"
echo "Sitio montado en $out"

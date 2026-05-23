#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_PREFIX="${IMAGE_PREFIX:-ghcr.io/cstortz/monorepo_mcp}"
IMPORT="${ROOT}/../redis-memory-mcp/scripts/import-image-to-k8s.sh"

for img in postgres-mcp rest-api-mcp filesystem-mcp; do
  "$IMPORT" "${IMAGE_PREFIX}/${img}:${IMAGE_TAG}"
done

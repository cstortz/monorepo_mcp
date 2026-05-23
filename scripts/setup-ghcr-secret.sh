#!/usr/bin/env bash
set -euo pipefail

# Creates/updates ghcr-pull so cluster nodes can pull private GHCR images.
#
# Usage:
#   GHCR_TOKEN=ghp_xxx ./scripts/setup-ghcr-secret.sh
#
# Skip if GHCR packages are public (Settings -> Package settings -> Public).

NAMESPACE="${NAMESPACE:-mcp-servers}"
GITHUB_USER="${GITHUB_USER:-cstortz}"
SECRET_NAME="${SECRET_NAME:-ghcr-pull}"

if [ -z "${GHCR_TOKEN:-}" ]; then
  read -rsp "GitHub token (read:packages): " GHCR_TOKEN
  echo
fi

if [ -z "$GHCR_TOKEN" ]; then
  echo "Error: GHCR_TOKEN is required for private packages."
  exit 1
fi

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret docker-registry "$SECRET_NAME" \
  --docker-server=ghcr.io \
  --docker-username="$GITHUB_USER" \
  --docker-password="$GHCR_TOKEN" \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Created/updated secret $SECRET_NAME in namespace $NAMESPACE"

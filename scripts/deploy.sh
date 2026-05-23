#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE_TAG="${IMAGE_TAG:-latest}"
NAMESPACE="${NAMESPACE:-mcp-servers}"
IMAGE_PREFIX="${IMAGE_PREFIX:-ghcr.io/cstortz/monorepo_mcp}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [deploy|build|status]

  Preferred deploy: push to main or run GitHub Actions "Deploy" workflow
  (builds on GitHub, pushes to GHCR, deploys via self-hosted runner).

  deploy   Apply k8s manifests and set image tags (requires kubectl + images in GHCR)
  build    Build all three MCP Docker images locally
  status   Show deployment status

Environment variables:
  IMAGE_TAG      Image tag (default: latest)
  IMAGE_PREFIX   GHCR prefix (default: ghcr.io/cstortz/monorepo_mcp)
  NAMESPACE      Kubernetes namespace (default: mcp-servers)

Examples:
  ./scripts/deploy.sh build
  IMAGE_TAG=\$(git rev-parse HEAD) ./scripts/deploy.sh deploy
  ./scripts/deploy.sh status
EOF
}

build_images() {
  echo "==> Building postgres-mcp..."
  docker build -f docker/mcp_postgres/Dockerfile -t "${IMAGE_PREFIX}/postgres-mcp:${IMAGE_TAG}" .

  echo "==> Building rest-api-mcp..."
  docker build -f docker/mcp_rest_api/Dockerfile -t "${IMAGE_PREFIX}/rest-api-mcp:${IMAGE_TAG}" .

  echo "==> Building filesystem-mcp..."
  docker build -f docker/mcp_filesystem/Dockerfile -t "${IMAGE_PREFIX}/filesystem-mcp:${IMAGE_TAG}" .
}

deploy_k8s() {
  echo "==> Applying manifests..."
  kubectl apply -f k8s/namespace.yaml
  kubectl apply -f k8s/configmap.yaml
  kubectl apply -f k8s/mcp-postgres.yaml
  kubectl apply -f k8s/mcp-rest-api.yaml
  kubectl apply -f k8s/mcp-filesystem.yaml
  kubectl apply -f k8s/mcp-tcp-gateway.yaml
  kubectl apply -f k8s/mcp-portal.yaml
  kubectl apply -f k8s/ingress.yaml

  echo "==> Setting images to tag ${IMAGE_TAG}..."
  kubectl set image deployment/mcp-postgres \
    mcp-postgres="${IMAGE_PREFIX}/postgres-mcp:${IMAGE_TAG}" \
    -n "$NAMESPACE"
  kubectl set image deployment/mcp-rest-api \
    mcp-rest-api="${IMAGE_PREFIX}/rest-api-mcp:${IMAGE_TAG}" \
    -n "$NAMESPACE"
  kubectl set image deployment/mcp-filesystem \
    mcp-filesystem="${IMAGE_PREFIX}/filesystem-mcp:${IMAGE_TAG}" \
    -n "$NAMESPACE"

  for dep in mcp-postgres mcp-rest-api mcp-filesystem mcp-portal; do
    kubectl rollout status "deployment/$dep" -n "$NAMESPACE" --timeout=180s
  done

  kubectl get pods,svc -n "$NAMESPACE"
}

show_status() {
  kubectl get pods,svc -n "$NAMESPACE" -o wide
}

case "${1:-deploy}" in
  build) build_images ;;
  deploy) deploy_k8s ;;
  status) show_status ;;
  -h|--help) usage ;;
  *) echo "Unknown command: $1"; usage; exit 1 ;;
esac

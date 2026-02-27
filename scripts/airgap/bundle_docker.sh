#!/usr/bin/env bash
# Build and save Docker image for air-gapped deployment.
# Run from repo root (smrforge or smrforge-pro).
#
# Usage:
#   ./scripts/airgap/bundle_docker.sh [OUTPUT_FILE]
#
# Output: docker image .tar file for transfer and `docker load -i`
# Uses Dockerfile (Community) or Dockerfile.pro (Pro) if available.

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Pro: use Dockerfile.pro if it exists and has real content (not placeholder)
DF="Dockerfile"
if [ -d "smrforge_pro" ] && [ -f "Dockerfile.pro" ]; then
  if ! grep -q "exit 1" Dockerfile.pro 2>/dev/null; then
    DF="Dockerfile.pro"
  fi
fi

IMAGE_NAME="smrforge:latest"
[ "$DF" = "Dockerfile.pro" ] && IMAGE_NAME="smrforge-pro:latest"

OUTPUT_FILE="${1:-./smrforge-docker.tar}"
echo "==> Building with $DF"
docker build --build-arg USE_LOCKED=1 -f "$DF" -t "$IMAGE_NAME" .

echo "==> Saving to $OUTPUT_FILE"
docker save "$IMAGE_NAME" -o "$OUTPUT_FILE"

echo "==> Done. Transfer $OUTPUT_FILE to air-gapped machine, then:"
echo "    docker load -i $OUTPUT_FILE"
echo "    docker run -it $IMAGE_NAME smrforge --help"

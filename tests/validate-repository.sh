#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_FILE="$ROOT_DIR/patches/cupsik/0001-homeassistant-ingress-and-local-monitor.patch"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

grep -q '^name: Home Assistant Epson Apps$' "$ROOT_DIR/repository.yaml"
grep -q 'github.com/duyleekun/homeassistant-epson$' "$ROOT_DIR/repository.yaml"
grep -q 'github.com/romlisrl/ha-cups-airprint.git' "$ROOT_DIR/.gitmodules"

git -C "$ROOT_DIR/third_party/cups-airprint" archive HEAD | tar -x -C "$TMP_DIR"
patch --batch --forward --dry-run -p1 -d "$TMP_DIR" < "$PATCH_FILE" >/dev/null

grep -q '^ingress: true$' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '^image: ghcr.io/duyleekun/homeassistant-epson-sane_l3210$' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '^ports:$' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '6566/tcp' "$ROOT_DIR/apps/sane_l3210/config.yaml"
! grep -q '8099/tcp' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '^image: ghcr.io/duyleekun/homeassistant-epson-cupsik$' "$ROOT_DIR/apps/cupsik/config.yaml"
grep -q 'docker/build-push-action@v6' "$ROOT_DIR/.github/workflows/publish-apps.yml"
grep -q "gh release download" "$ROOT_DIR/.github/workflows/publish-apps.yml"

tracked_forbidden="$(git -C "$ROOT_DIR" ls-files | grep -E '(^|/)(.*\.deb|.*\.so|__pycache__|.*\.pyc|.*\.(jpg|jpeg|tif|tiff|SF2))$' || true)"
[ -z "$tracked_forbidden" ] || {
  printf 'forbidden tracked files:\n%s\n' "$tracked_forbidden" >&2
  exit 1
}

"$ROOT_DIR/apps/sane_l3210/tests/validate-queue-monitor.sh"
printf 'repository validation passed\n'

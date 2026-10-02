#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-/addons}"

die() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

"$ROOT_DIR/scripts/fetch-epson-scan2.sh" "$ROOT_DIR/apps/sane_l3210"

for required in \
  "$ROOT_DIR/apps/sane_l3210/packages/epsonscan2_6.7.92.0-1_amd64.deb" \
  "$ROOT_DIR/apps/sane_l3210/packages/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb" \
  "$ROOT_DIR/apps/sane_l3210/rootfs/usr/local/bin/es2button"; do
  [ -f "$required" ] || die "missing scanner file: $required"
done

STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

cp -a "$ROOT_DIR/apps/sane_l3210" "$STAGE_DIR/sane_l3210"
cp -a "$ROOT_DIR/apps/cupsik" "$STAGE_DIR/cupsik"
if [ "${USE_PUBLISHED_IMAGES:-0}" != 1 ]; then
  for app in sane_l3210 cupsik; do
    sed '/^image:/d' "$STAGE_DIR/$app/config.yaml" > "$STAGE_DIR/$app/config.yaml.local"
    mv "$STAGE_DIR/$app/config.yaml.local" "$STAGE_DIR/$app/config.yaml"
  done
fi
find "$STAGE_DIR" -type d -name __pycache__ -exec rm -rf {} +

mkdir -p "$DEST_DIR"
[ "$DEST_DIR" != / ] || die "destination must not be root"
for app in sane_l3210 cupsik; do
  rm -rf "$DEST_DIR/$app.staging"
  cp -a "$STAGE_DIR/$app" "$DEST_DIR/$app.staging"
  rm -rf "$DEST_DIR/$app"
  mv "$DEST_DIR/$app.staging" "$DEST_DIR/$app"
done

printf 'prepared %s/sane_l3210 and %s/cupsik\n' "$DEST_DIR" "$DEST_DIR"

#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-/addons}"
CUPS_PATCH="$ROOT_DIR/patches/cupsik/0001-homeassistant-ingress-and-local-monitor.patch"

die() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

command -v patch >/dev/null 2>&1 || die "patch is required"

"$ROOT_DIR/scripts/fetch-epson-scan2.sh" "$ROOT_DIR/apps/sane_l3210"

git -C "$ROOT_DIR" submodule update --init --recursive

for required in \
  "$ROOT_DIR/apps/sane_l3210/packages/epsonscan2_6.7.92.0-1_amd64.deb" \
  "$ROOT_DIR/apps/sane_l3210/packages/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb" \
  "$ROOT_DIR/apps/sane_l3210/rootfs/usr/local/bin/es2button"; do
  [ -f "$required" ] || die "missing scanner file: $required"
done

[ -f "$CUPS_PATCH" ] || die "missing CUPS patch: $CUPS_PATCH"

STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

cp -a "$ROOT_DIR/apps/sane_l3210" "$STAGE_DIR/sane_l3210"
mkdir -p "$STAGE_DIR/cupsik"
git -C "$ROOT_DIR/third_party/cups-airprint" archive HEAD | tar -x -C "$STAGE_DIR/cupsik"

(cd "$STAGE_DIR/cupsik" && patch --batch --forward -p1 < "$CUPS_PATCH")
cp -a "$ROOT_DIR/patches/cupsik/overlay/." "$STAGE_DIR/cupsik/"
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

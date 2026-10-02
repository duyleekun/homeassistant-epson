#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_ROOT="${1:-/config}"
SOURCE_DIR="$ROOT_DIR/custom_components/epson_l3210"
DEST_DIR="$DEST_ROOT/custom_components/epson_l3210"

[ -d "$SOURCE_DIR" ] || { printf 'error: missing %s\n' "$SOURCE_DIR" >&2; exit 1; }
[ "$DEST_ROOT" != / ] || { printf 'error: refusing to install into /\n' >&2; exit 1; }

mkdir -p "$DEST_ROOT/custom_components"
staging_dir="$(mktemp -d "$DEST_ROOT/.epson_l3210.XXXXXX")"
old_dir="$DEST_ROOT/custom_components/.epson_l3210.previous.$$"
cleanup() { rm -rf "$staging_dir" "$old_dir"; }
trap cleanup EXIT

cp -a "$SOURCE_DIR" "$staging_dir/epson_l3210"
if [ -e "$DEST_DIR" ] || [ -L "$DEST_DIR" ]; then
  mv "$DEST_DIR" "$old_dir"
fi
if ! mv "$staging_dir/epson_l3210" "$DEST_DIR"; then
  if [ -e "$old_dir" ]; then mv "$old_dir" "$DEST_DIR"; fi
  exit 1
fi

printf 'installed %s\n' "$DEST_DIR"

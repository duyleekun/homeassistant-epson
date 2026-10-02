#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-$ROOT_DIR/apps/sane_l3210}"
PACKAGE_DIR="$DEST_DIR/packages"
BUNDLE_URL="${EPSON_BUNDLE_URL:-https://sourceforge.net/projects/mxntrepo/files/sources/epsonscan2-bundle-6.7.92.0.x86_64.deb.tar.gz/download}"
BUNDLE_SHA256="a1997f557fa59f6f1b7278535f8700256cc0152689c56865a2c403990d98c242"
BUNDLE_NAME="epsonscan2-bundle-6.7.92.0.x86_64.deb.tar.gz"

mkdir -p "$PACKAGE_DIR"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl --fail --location --retry 3 --retry-all-errors --output "$tmp_dir/$BUNDLE_NAME" "$BUNDLE_URL"
printf '%s  %s\n' "$BUNDLE_SHA256" "$tmp_dir/$BUNDLE_NAME" | sha256sum --check --status

tar -xzf "$tmp_dir/$BUNDLE_NAME" -C "$tmp_dir"
find "$tmp_dir" -type f -name 'epsonscan2_6.7.92.0-1_amd64.deb' -exec cp {} "$PACKAGE_DIR/" \;
find "$tmp_dir" -type f -name 'epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb' -exec cp {} "$PACKAGE_DIR/" \;

test -s "$PACKAGE_DIR/epsonscan2_6.7.92.0-1_amd64.deb"
test -s "$PACKAGE_DIR/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb"
printf 'fetched verified Epson Scan 2 packages into %s\n' "$PACKAGE_DIR"

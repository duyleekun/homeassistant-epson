#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-$ROOT_DIR/apps/sane_l3210}"
PACKAGE_DIR="$DEST_DIR/packages"
BUNDLE_URL="${EPSON_BUNDLE_URL:-https://sourceforge.net/projects/mxntrepo/files/sources/epsonscan2-bundle-6.7.92.0.x86_64.deb.tar.gz/download}"
BUNDLE_SHA256="a1997f557fa59f6f1b7278535f8700256cc0152689c56865a2c403990d98c242"
CORE_SHA256="1f941aed327270ce825841d0ef8e9244c35d278cfdc30b278a7a4e2e9ede12bf"
PLUGIN_SHA256="573661c4d18da5ae15f4d6b8f4f853921e0b8243b58634f499a6ee31649be0f3"
BUNDLE_NAME="epsonscan2-bundle-6.7.92.0.x86_64.deb.tar.gz"

check_sha256() {
  local expected="$1" path="$2" actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$path" | awk '{print $1}')"
  else
    actual="$(shasum -a 256 "$path" | awk '{print $1}')"
  fi
  [ "$actual" = "$expected" ]
}

mkdir -p "$PACKAGE_DIR"

if [ -f "$PACKAGE_DIR/epsonscan2_6.7.92.0-1_amd64.deb" ] \
  && [ -f "$PACKAGE_DIR/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb" ] \
  && check_sha256 "$CORE_SHA256" "$PACKAGE_DIR/epsonscan2_6.7.92.0-1_amd64.deb" \
  && check_sha256 "$PLUGIN_SHA256" "$PACKAGE_DIR/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb"; then
  printf 'using already staged Epson Scan 2 packages in %s\n' "$PACKAGE_DIR"
  exit 0
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl --fail --location --retry 3 --retry-all-errors --output "$tmp_dir/$BUNDLE_NAME" "$BUNDLE_URL"
check_sha256 "$BUNDLE_SHA256" "$tmp_dir/$BUNDLE_NAME"

tar -xzf "$tmp_dir/$BUNDLE_NAME" -C "$tmp_dir"
find "$tmp_dir" -type f -name 'epsonscan2_6.7.92.0-1_amd64.deb' -exec cp {} "$PACKAGE_DIR/" \;
find "$tmp_dir" -type f -name 'epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb' -exec cp {} "$PACKAGE_DIR/" \;

test -s "$PACKAGE_DIR/epsonscan2_6.7.92.0-1_amd64.deb"
test -s "$PACKAGE_DIR/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb"
printf 'fetched verified Epson Scan 2 packages into %s\n' "$PACKAGE_DIR"

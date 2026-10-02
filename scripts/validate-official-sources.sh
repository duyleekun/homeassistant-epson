#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSIONS="$ROOT_DIR/apps/cupsik/upstream-versions.env"

# GitHub's immutable commit archive is the checksum-verified source artifact
# corresponding to each pinned official upstream commit.
source "$VERSIONS"

verify_archive() {
  local name="$1" repository="$2" commit="$3" expected="$4"
  local archive="$(mktemp "/tmp/epson-${name}.XXXXXX")"
  curl --fail --silent --show-error --location \
    "https://github.com/${repository}/archive/${commit}.tar.gz" \
    --output "$archive"
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$archive" | awk '{print $1}')"
  else
    actual="$(shasum -a 256 "$archive" | awk '{print $1}')"
  fi
  [ "$actual" = "$expected" ]
  printf '%s source checksum verified\n' "$name"
}

verify_archive cups OpenPrinting/cups "$CUPS_COMMIT" "$CUPS_SHA256"
verify_archive libcupsfilters OpenPrinting/libcupsfilters "$LIBCUPS_FILTERS_COMMIT" "$LIBCUPS_FILTERS_SHA256"
verify_archive avahi avahi/avahi "$AVAHI_COMMIT" "$AVAHI_SHA256"
verify_archive cups-filters OpenPrinting/cups-filters "$CUPS_FILTERS_COMMIT" "$CUPS_FILTERS_SHA256"
verify_archive libppd OpenPrinting/libppd "$LIBPPD_COMMIT" "$LIBPPD_SHA256"

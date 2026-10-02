#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_file() {
  [ -f "$1" ] || { printf 'missing required file: %s\n' "$1" >&2; exit 1; }
}

require_file "$ROOT_DIR/hacs.json"
require_file "$ROOT_DIR/custom_components/epson_l3210/manifest.json"
require_file "$ROOT_DIR/custom_components/epson_l3210/config_flow.py"
require_file "$ROOT_DIR/apps/cupsik/Dockerfile"
require_file "$ROOT_DIR/apps/cupsik/upstream-versions.env"

grep -q '^name: Home Assistant Epson$' "$ROOT_DIR/repository.yaml"
grep -q 'github.com/duyleekun/homeassistant-epson$' "$ROOT_DIR/repository.yaml"
test ! -e "$ROOT_DIR/.gitmodules"

grep -q '^homeassistant_api: true$' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '^version: "0.8.1"$' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '6566/tcp' "$ROOT_DIR/apps/sane_l3210/config.yaml"
! grep -Eq '^(ingress|ingress_port|panel_icon|panel_title):' "$ROOT_DIR/apps/sane_l3210/config.yaml"
grep -q '^version: "2.0.4"$' "$ROOT_DIR/apps/cupsik/config.yaml"
grep -q '^ingress: true$' "$ROOT_DIR/apps/cupsik/config.yaml"
grep -q '^ingress_port: 631$' "$ROOT_DIR/apps/cupsik/config.yaml"

for source in \
  'https://github.com/OpenPrinting/cups.git' \
  'https://github.com/avahi/avahi.git' \
  'https://github.com/OpenPrinting/libcupsfilters.git' \
  'https://github.com/OpenPrinting/cups-filters.git' \
  'https://github.com/OpenPrinting/libppd.git'; do
  grep -q "$source" "$ROOT_DIR/apps/cupsik/Dockerfile"
done
grep -q 'CUPS_COMMIT=6ba0487abb05afc93d639f37676add8fd65d3756' "$ROOT_DIR/apps/cupsik/upstream-versions.env"
grep -q 'LIBCUPS_FILTERS_COMMIT=c4028517ba4a0d84e649e8e258508c5e90dde36e' "$ROOT_DIR/apps/cupsik/upstream-versions.env"
grep -q 'AVAHI_COMMIT=f060abee2807c943821d88839c013ce15db17b58' "$ROOT_DIR/apps/cupsik/upstream-versions.env"
grep -q 'CUPS_FILTERS_COMMIT=5a73330fbd0cde494d984141f9add1565aef8171' "$ROOT_DIR/apps/cupsik/upstream-versions.env"
grep -q 'LIBPPD_COMMIT=2b37a73c02126d1ba031270322b6c79034cc0d0f' "$ROOT_DIR/apps/cupsik/upstream-versions.env"

if rg -n -i 'romlisrl|zajac-grzegorz|cups-airprint|third_party/cups|patches/cupsik' \
    "$ROOT_DIR" --hidden -g '!.git/**' -g '!tests/validate-repository.sh' -g '!*.pyc' -g '!__pycache__/**'; then
  printf 'old third-party or removed scanner references remain\n' >&2
  exit 1
fi

if find "$ROOT_DIR/apps" -path '*/scanweb' -o -path '*/scanweb/*' | grep -q .; then
  printf 'removed scanner web service remains in an app tree\n' >&2
  exit 1
fi

tracked_forbidden="$(git -C "$ROOT_DIR" ls-files | grep -E '(^|/)(.*\.deb|.*\.so|__pycache__|.*\.pyc|.*\.(jpg|jpeg|tif|tiff|SF2))$' || true)"
[ -z "$tracked_forbidden" ] || {
  printf 'forbidden tracked files:\n%s\n' "$tracked_forbidden" >&2
  exit 1
}

python3 -m json.tool "$ROOT_DIR/hacs.json" >/dev/null
python3 -m json.tool "$ROOT_DIR/custom_components/epson_l3210/manifest.json" >/dev/null
python3 -m json.tool "$ROOT_DIR/custom_components/epson_l3210/strings.json" >/dev/null
python3 -m json.tool "$ROOT_DIR/custom_components/epson_l3210/translations/en.json" >/dev/null
python3 -m compileall -q "$ROOT_DIR/custom_components" "$ROOT_DIR/apps/sane_l3210/rootfs/usr/local/bin"

while IFS= read -r shell_file; do
  bash -n "$shell_file"
done < <(find "$ROOT_DIR/scripts" "$ROOT_DIR/apps" -type f \( -name '*.sh' -o -path '*/run' \) -print)

"$ROOT_DIR/apps/sane_l3210/tests/validate-queue-monitor.sh"
git -C "$ROOT_DIR" diff --check
printf 'repository validation passed\n'

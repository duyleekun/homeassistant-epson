# Home Assistant Epson Apps

Private Home Assistant app repository for the Epson L3210 scanner and the
separate CUPS/AirPrint service used by the printer.

## Apps

- `apps/sane_l3210`: native Epson Scan 2 web scanning through Home Assistant
  ingress, SANE network sharing, and dynamic USB-backed CUPS queue monitoring.
- `cupsik`: prepared from the pinned upstream CUPS/AirPrint submodule with a
  parent-owned patch for a Home Assistant ingress admin panel and localhost
  queue control.

The scanner and CUPS remain separate containers. CUPS continues to own IPP,
AirPrint, Bonjour, and the printer queue; the scanner app only monitors and
controls discovered USB-backed queues.

## Prepare A Home Assistant Host

For a long-term installation, use the GitHub repository as the app catalog and
the GHCR images published by `.github/workflows/publish-apps.yml`. Add
`https://github.com/duyleekun/homeassistant-epson` under **Settings > Apps >
App repositories**. Supervisor will pull the image named by each app's
`config.yaml`; it will not run the local staging script on its own.
Because this source repository is private, the GHCR packages must either be
made public or supplied through a registry-authenticated deployment before
Supervisor can pull them. The local staging path remains the recovery option.

The scanner image build downloads the Epson Scan 2 6.7.92.0 bundle from a
public download URL, verifies its SHA-256, and extracts the two `.deb` files.
The proprietary packages remain outside Git history. Override
`EPSON_BUNDLE_URL` only when using a trusted mirror with the same verified
bundle.

The upstream CUPS source is a Git submodule. On the Home Assistant host:

```bash
git submodule update --init --recursive
./scripts/prepare-local-apps.sh /addons
ha supervisor reload
```

The script stages `sane_l3210` and `cupsik` as separate Home Assistant apps.
This installation consumes local apps from `/local_apps`; use that destination
when deploying here. `/addons` remains supported for installations that use
the standard add-on source path. Set `USE_PUBLISHED_IMAGES=1` when staging a
host that should pull the public GHCR images instead of building locally.

The script fetches the tested Epson Scan 2 `.deb` packages when they are not
already staged. They are intentionally ignored and never committed. See
`scripts/fetch-epson-scan2.sh` and `apps/sane_l3210/packages/SHA256SUMS`.

## Migration Safety

Before replacing the existing CUPS app, back up `/share/epson-scan` and
`/app_configs/2c6aefcc_cupsik`. Preserve the existing `printers.conf`,
`cupsd.conf`, queue options, and Avahi behavior until both small CUPS and large
Mac AirPrint jobs have been verified.

The CUPS ingress panel is for administration only. TCP/UDP `631` remains
exposed for IPP, AirPrint, and Bonjour. CUPS authentication remains enabled;
Home Assistant ingress authentication does not replace CUPS authorization.

## Validation

```bash
apps/sane_l3210/tests/validate-queue-monitor.sh
git submodule update --init --recursive
git diff --submodule=diff --exit-code
```

Validate a real nonblank scan, CUPS test page, large Mac AirPrint job, USB
removal/resume, held-job release, and both ingress panels after deployment.

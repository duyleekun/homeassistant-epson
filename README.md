# Home Assistant Epson

Home Assistant apps and a HACS-compatible integration for an Epson L3210
scanner and printer.

## Apps

- `apps/sane_l3210`: native Epson Scan 2 and SANE network sharing, with a
  Home Assistant event bridge and dynamic USB-backed CUPS queue monitoring.
- `apps/cupsik`: a directly owned CUPS/AirPrint app built from pinned official
  OpenPrinting CUPS, Avahi, cups-filters, and libppd sources.
- `custom_components/epson_l3210`: the native Home Assistant UI, services,
  entities, events, image, and scan-history integration.

The scanner and CUPS remain separate containers. CUPS continues to own IPP,
AirPrint, Bonjour, and the printer queue; the scanner app only monitors and
controls discovered USB-backed queues.

## Prepare A Home Assistant Host

For a long-term installation, use the GitHub repository as the app catalog and
the GHCR images published by `.github/workflows/publish-apps.yml`. Add
`https://github.com/duyleekun/homeassistant-epson` under **Settings > Apps >
App repositories**. Supervisor will pull the image named by each app's
`config.yaml`; it will not run the local staging script on its own.
The local staging path remains the recovery option.

The scanner image build downloads the Epson Scan 2 6.7.92.0 bundle from a
public download URL, verifies its SHA-256, and extracts the two `.deb` files.
The proprietary packages remain outside Git history. Override
`EPSON_BUNDLE_URL` only when using a trusted mirror with the same verified
bundle.

On a Home Assistant host using local app sources:

```bash
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

Install the HACS integration into Home Assistant's `/config` volume with:

```bash
./scripts/install-integration.sh /config
```

Then restart Home Assistant and add **Epson L3210 Scanner** from Settings.
The scan button, settings, latest image, activity event, and previous scans
are exposed by Home Assistant. The scanner app listens on SANE port `6566`;
it no longer needs an unauthenticated web scanner endpoint.

## Migration Safety

Before replacing the existing CUPS app, back up `/share/epson-scan`,
`/app_configs/2c6aefcc_cupsik`, and `/app_configs/local_cupsik`. The migration
staging path `/share/epson-scan/cups-migration/local_cupsik` is copied into the
new `app_config` volume on first start when no queue exists. Preserve the existing `printers.conf`,
`cupsd.conf`, queue options, and Avahi behavior until both small CUPS and large
Mac AirPrint jobs have been verified.

The CUPS ingress panel is for administration only. TCP/UDP `631` remains
exposed for IPP, AirPrint, and Bonjour. CUPS authentication remains enabled;
Home Assistant ingress authentication does not replace CUPS authorization.

## Validation

```bash
apps/sane_l3210/tests/validate-queue-monitor.sh
tests/validate-repository.sh
```

Validate a real nonblank scan, CUPS test page, large Mac AirPrint job, USB
removal/resume, held-job release, and both ingress panels after deployment.

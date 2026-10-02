# Home Assistant Epson Scanner App

This repository contains the Home Assistant app for sharing an Epson L3210
scanner over SANE and bridging native Epson Scan 2 into Home Assistant.

## Features

- Native Epson Scan 2 scanning from the `epson_l3210.scan` action and scan
  button in the HACS integration.
- Physical two-button scans reported as Home Assistant activity events.
- Latest scan image and scan history exposed by the HACS integration.
- SANE network sharing on port `6566`.
- USB-backed CUPS queue monitoring.
- Dynamic discovery of USB CUPS queues from `lpstat`.
- Queue pause when the USB device disappears.
- Queue resume and release of jobs held while the device was offline.
- Epson's documented `usb-no-reattach-default` workaround applied to discovered USB queues.

The separate CUPS app provides AirPrint/Bonjour advertisement and owns the printer queue. This app only monitors the USB device and controls the queue through localhost CUPS.

The app keeps the tested native L3210 listener and SANE fallback. The scanner
web server has been removed; Home Assistant is the authenticated UI.

## Home Assistant UI

Install `custom_components/epson_l3210` with the repository-level deployment
script, restart Home Assistant, and add **Epson L3210 Scanner** from Settings.
The integration provides the scan button, resolution/color/prefix settings,
latest image, connection state, activity events, and a media-source folder for
previous scans. The app exposes only SANE on port `6566`.

## Local package staging

Epson Scan 2 packages and the patched private native libraries are intentionally excluded from Git. Stage these files before building the app:

```text
packages/epsonscan2_6.7.92.0-1_amd64.deb
packages/epsonscan2-non-free-plugin_1.0.0.6-1_amd64.deb
rootfs/opt/es2button/lib/libcommonutility.so
rootfs/opt/es2button/lib/libes2command.so
```

Do not publish or redistribute Epson binaries without checking their license terms. The current local staging files are the tested source of truth for this installation.

## Home Assistant deployment

Use the repository-level `scripts/prepare-local-apps.sh` to stage this app and
the separate CUPS app under `/addons`. Only SANE port `6566` is exposed for
network scanner clients.

The app maps `/share`; scan output and queue-monitor state are retained there
across rebuilds. The CUPS app configuration is separate and must not be
deleted during scanner deployment.

## Validation

Run the static checks before deployment:

```bash
tests/validate-repository.sh
```

Then verify a real scan, a small CUPS print, USB removal/resume, and a large Mac AirPrint print through the shared queue.

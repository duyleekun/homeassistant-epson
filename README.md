# Home Assistant Epson Scanner App

This repository contains the local Home Assistant app for sharing an Epson L3210 scanner over SANE and providing native Epson Scan 2 web scanning.

## Features

- Native Epson Scan 2 scanning through the web interface on port `8099`.
- A Home Assistant ingress sidebar panel named **Epson Scanner**.
- SANE network sharing on port `6566`.
- USB-backed CUPS queue monitoring.
- Dynamic discovery of USB CUPS queues from `lpstat`.
- Queue pause when the USB device disappears.
- Queue resume and release of jobs held while the device was offline.
- Epson's documented `usb-no-reattach-default` workaround applied to discovered USB queues.

The separate CUPS app provides AirPrint/Bonjour advertisement and owns the printer queue. This app only monitors the USB device and controls the queue through localhost CUPS.

The Epson physical panel-button scan event is not exposed reliably by the Linux driver on the L3210. Use the native web scanner for repeatable scans.

## Home Assistant UI

When installed from the repository through the Home Assistant app store, enable
the app, open its details page, and turn on **Show in sidebar**. The resulting
**Epson Scanner** panel uses Supervisor ingress, so it does not require
exposing the scanner web port to the LAN or entering a separate app login.
Direct access on port `8099` remains available for troubleshooting.

This is intentionally an app-level scanner UI rather than a Home Assistant
core `scanner` entity: Home Assistant does not provide a general document-scan
entity platform for Epson Scan 2. The app provides the native scan workflow,
while SANE clients continue to use port `6566`.

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

Home Assistant's documented remote-development path is `/addons`. Copy this
repository into the local app source path and rebuild it through Supervisor:

```bash
scp -r . root@homeassistant.local:/addons/sane_l3210
ssh root@homeassistant.local 'ha supervisor reload'
ssh root@homeassistant.local 'ha apps rebuild local_sane_l3210 --force'
ssh root@homeassistant.local 'ha apps start local_sane_l3210'
```

The older `/local_apps/sane_l3210` path may exist on older installations, but
`/addons/sane_l3210` is the source path Supervisor catalogs for local app
development.

The app maps `/share`; scan output and queue-monitor state are retained there across rebuilds. The CUPS app configuration is separate and must not be deleted during scanner deployment.

## Validation

Run the static checks before deployment:

```bash
tests/validate-queue-monitor.sh
```

Then verify a real scan, a small CUPS print, USB removal/resume, and a large Mac AirPrint print through the shared queue.

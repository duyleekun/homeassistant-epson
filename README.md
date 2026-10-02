# Home Assistant Epson Scanner App

This repository contains the local Home Assistant app for sharing an Epson L3210 scanner over SANE and providing native Epson Scan 2 web scanning.

## Features

- Native Epson Scan 2 scanning through the web interface on port `8099`.
- SANE network sharing on port `6566`.
- USB-backed CUPS queue monitoring.
- Dynamic discovery of USB CUPS queues from `lpstat`.
- Queue pause when the USB device disappears.
- Queue resume and release of jobs held while the device was offline.
- Epson's documented `usb-no-reattach-default` workaround applied to discovered USB queues.

The separate CUPS app provides AirPrint/Bonjour advertisement and owns the printer queue. This app only monitors the USB device and controls the queue through localhost CUPS.

The Epson physical panel-button scan event is not exposed reliably by the Linux driver on the L3210. Use the native web scanner for repeatable scans.

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

Home Assistant's local app repository is used for hardware testing. Copy this repository into the local app source path and rebuild it through Supervisor:

```bash
scp -r . root@homeassistant.local:/local_apps/sane_l3210
ssh root@homeassistant.local 'ha supervisor reload'
ssh root@homeassistant.local 'ha apps rebuild local_sane_l3210 --force'
ssh root@homeassistant.local 'ha apps start local_sane_l3210'
```

The app maps `/share`; scan output and queue-monitor state are retained there across rebuilds. The CUPS app configuration is separate and must not be deleted during scanner deployment.

## Validation

Run the static checks before deployment:

```bash
tests/validate-queue-monitor.sh
```

Then verify a real scan, a small CUPS print, USB removal/resume, and a large Mac AirPrint print through the shared queue.


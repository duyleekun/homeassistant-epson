# Epson Printer App

This Home Assistant app owns the CUPS/AirPrint runtime. It builds pinned
official sources instead of depending on a third-party Home Assistant app:

- OpenPrinting CUPS `2.4.19`
- Avahi `0.8`
- OpenPrinting libcupsfilters `2.1.1` (required by libppd and cups-filters)
- OpenPrinting cups-filters `2.0.1`
- OpenPrinting libppd `2.1.1`
- Debian's `printer-driver-escpr` for the Epson ESC/P-R PPD and filter

The immutable commit pins are in `upstream-versions.env` and are repeated as
Docker build arguments. The app keeps CUPS administration behind Home
Assistant ingress, while normal TCP/UDP `631` remains available for IPP,
AirPrint, and Bonjour.

The add-on configuration is stored in `/config/cups` inside the persistent
 app config volume. Existing `printers.conf`, queue options, and PPDs are
 copied forward only when missing. Before migration, place the preserved
 configuration under `/share/epson-scan/cups-migration/local_cupsik`; the
 initialization service copies it into the new app config volume only when no
 queue exists. Avahi also publishes the Epson IPP service directly so Bonjour
 discovery does not depend on a third-party app.

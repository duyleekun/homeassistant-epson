ARG BUILD_FROM=ghcr.io/hassio-addons/debian-base:7.6.2
FROM $BUILD_FROM

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        avahi-daemon \
        dbus \
        gcc \
        libboost-filesystem1.74.0 \
        libboost-program-options1.74.0 \
        libboost-system1.74.0 \
        libegl1 \
        libgl1 \
        libglib2.0-0 \
        libjpeg62-turbo \
        libpng16-16 \
        libqt5core5a \
        libqt5dbus5 \
        libqt5gui5 \
        libqt5network5 \
        libqt5printsupport5 \
        libqt5widgets5 \
        libtiff6 \
        libusb-1.0-0 \
        libusb-1.0-0-dev \
        psmisc \
        python3 \
        python3-websocket \
        cups-client \
        libc6-dev \
        usbutils \
        sane-utils \
        libsane \
        libsane-common \
        xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY packages /tmp/epson-packages
COPY rootfs /
COPY native-src /tmp/native-src

RUN apt-get update \
    && apt-get install -y --no-install-recommends /tmp/epson-packages/*.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/epson-packages \
    && rm -rf /etc/services.d/es2button \
    && cc -O2 -Wall -Wextra -o /usr/local/bin/l3210-button /tmp/native-src/l3210_button.c -lusb-1.0 \
    && rm -rf /tmp/native-src \
    && chmod a+x /etc/services.d/saned/run /etc/services.d/scan-bridge/run /etc/services.d/queue-monitor/run /etc/services.d/scanner-monitor/run /usr/local/bin/epson_scan_engine.py /usr/local/bin/epson_ha_bridge.py /usr/local/bin/epson_panel_scan.py /usr/local/bin/epson_status.py /usr/local/bin/l3210-button

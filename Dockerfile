ARG BUILD_FROM
FROM $BUILD_FROM

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        avahi-daemon \
        dbus \
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
        psmisc \
        python3 \
        cups-client \
        usbutils \
        sane-utils \
        libsane \
        libsane-common \
        xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY packages /tmp/epson-packages
COPY rootfs /

RUN apt-get update \
    && apt-get install -y --no-install-recommends /tmp/epson-packages/*.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/epson-packages \
    && chmod a+x /etc/services.d/saned/run /etc/services.d/scanweb/run /etc/services.d/queue-monitor/run /usr/local/bin/epson_scan_web.py /usr/local/bin/epson_panel_scan.py /usr/local/bin/es2button /usr/local/bin/l3210-button

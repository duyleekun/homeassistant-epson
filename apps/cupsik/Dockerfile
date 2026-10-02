ARG BUILD_FROM=ghcr.io/hassio-addons/debian-base:7.6.2

FROM debian:bookworm-slim AS cups-builder
ARG CUPS_COMMIT=6ba0487abb05afc93d639f37676add8fd65d3756
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake build-essential ca-certificates git libtool pkg-config \
    libavahi-client-dev libavahi-common-dev libdbus-1-dev libgnutls28-dev \
    libkrb5-dev libpam0g-dev libpaper-dev libsystemd-dev libusb-1.0-0-dev \
    zlib1g-dev libjpeg-dev libpng-dev libtiff-dev \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/OpenPrinting/cups.git /src/cups \
    && cd /src/cups \
    && git fetch --depth 1 origin "$CUPS_COMMIT" \
    && git checkout --detach "$CUPS_COMMIT" \
    && ./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
        --with-rundir=/run/cups --with-cups-user=lp --with-system-groups=lpadmin \
        --disable-static \
    && make -j"$(nproc)" \
    && make DESTDIR=/opt/stage install

FROM debian:bookworm-slim AS libcupsfilters-builder
ARG LIBCUPS_FILTERS_COMMIT=c4028517ba4a0d84e649e8e258508c5e90dde36e
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
COPY --from=cups-builder /opt/stage /opt/cups
RUN find /opt/cups -type f -name 'libcups.so.*' -print0 \
    | while IFS= read -r -d '' library; do \
        directory="$(dirname "$library")"; \
        [ -e "$directory/libcups.so" ] || ln -s "$(basename "$library")" "$directory/libcups.so"; \
      done
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake autopoint build-essential ca-certificates git gettext libtool pkg-config \
    libdbus-1-dev libexif-dev libfontconfig1-dev libglib2.0-dev libjpeg-dev \
    liblcms2-dev libpng-dev libpoppler-cpp-dev libqpdf-dev libtiff-dev ghostscript \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/OpenPrinting/libcupsfilters.git /src/libcupsfilters \
    && cd /src/libcupsfilters \
    && git fetch --depth 1 origin "$LIBCUPS_FILTERS_COMMIT" \
    && git checkout --detach "$LIBCUPS_FILTERS_COMMIT" \
    && NOCONFIGURE=1 ./autogen.sh \
    && PATH=/opt/cups/usr/bin:$PATH \
       PKG_CONFIG_PATH=/opt/cups/usr/lib/pkgconfig:/opt/cups/usr/lib64/pkgconfig:/opt/cups/usr/lib/x86_64-linux-gnu/pkgconfig \
       CPPFLAGS="-I/opt/cups/usr/include" \
       LDFLAGS="-L/opt/cups/usr/lib -L/opt/cups/usr/lib64 -L/opt/cups/usr/lib/x86_64-linux-gnu" \
       ./configure --prefix=/usr --disable-static --disable-mutool \
    && make -j"$(nproc)" \
    && make DESTDIR=/opt/stage install

FROM debian:bookworm-slim AS libppd-builder
ARG LIBPPD_COMMIT=2b37a73c02126d1ba031270322b6c79034cc0d0f
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
COPY --from=cups-builder /opt/stage /opt/cups
COPY --from=libcupsfilters-builder /opt/stage /opt/libcupsfilters
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake autopoint build-essential ca-certificates git gettext libtool pkg-config \
    ghostscript libcups2-dev libjpeg-dev libpng-dev libtiff-dev libzstd-dev poppler-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/OpenPrinting/libppd.git /src/libppd \
    && cd /src/libppd \
    && git fetch --depth 1 origin "$LIBPPD_COMMIT" \
    && git checkout --detach "$LIBPPD_COMMIT" \
    && NOCONFIGURE=1 ./autogen.sh \
    && PATH=/opt/cups/usr/bin:$PATH \
       PKG_CONFIG_PATH=/opt/cups/usr/lib/pkgconfig:/opt/cups/usr/lib64/pkgconfig:/opt/cups/usr/lib/x86_64-linux-gnu/pkgconfig:/opt/libcupsfilters/usr/lib/pkgconfig:/opt/libcupsfilters/usr/lib64/pkgconfig:/opt/libcupsfilters/usr/lib/x86_64-linux-gnu/pkgconfig \
       CPPFLAGS="-I/opt/cups/usr/include -I/opt/libcupsfilters/usr/include" \
       LDFLAGS="-L/opt/cups/usr/lib -L/opt/cups/usr/lib64 -L/opt/cups/usr/lib/x86_64-linux-gnu -L/opt/libcupsfilters/usr/lib -L/opt/libcupsfilters/usr/lib64 -L/opt/libcupsfilters/usr/lib/x86_64-linux-gnu" \
       ./configure --prefix=/usr --disable-static --disable-mutool --disable-pdftocairo --disable-acroread \
    && make -j"$(nproc)" \
    && make DESTDIR=/opt/stage install

FROM debian:bookworm-slim AS avahi-builder
ARG AVAHI_COMMIT=f060abee2807c943821d88839c013ce15db17b58
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake build-essential ca-certificates git libtool pkg-config \
    libcap-dev libdaemon-dev libdbus-1-dev libexpat1-dev libgcrypt20-dev \
    libevent-dev libglib2.0-dev libsystemd-dev intltool \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/avahi/avahi.git /src/avahi \
    && cd /src/avahi \
    && git fetch --depth 1 origin "$AVAHI_COMMIT" \
    && git checkout --detach "$AVAHI_COMMIT" \
    && NOCONFIGURE=1 ./autogen.sh \
    && ./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
        --disable-static --disable-gtk --disable-gtk3 --disable-qt4 \
        --disable-qt5 --disable-mono --disable-python --disable-python-dbus \
        --disable-autoipd --disable-manpages --disable-xmltoman \
        --disable-gdbm \
    && make -j"$(nproc)" \
    && make DESTDIR=/opt/stage install

FROM debian:bookworm-slim AS cups-filters-builder
ARG CUPS_FILTERS_COMMIT=5a73330fbd0cde494d984141f9add1565aef8171
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
COPY --from=cups-builder /opt/stage /opt/cups
COPY --from=libcupsfilters-builder /opt/stage /opt/libcupsfilters
COPY --from=libppd-builder /opt/stage /opt/libppd
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake autopoint build-essential ca-certificates git gettext libtool \
    ghostscript pkg-config libglib2.0-dev libjpeg-dev libpng-dev libtiff-dev \
    libqpdf-dev libpoppler-cpp-dev libfontconfig1-dev libfreetype6-dev \
    liblcms2-dev libexif-dev libqpdf-dev \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/OpenPrinting/cups-filters.git /src/cups-filters \
    && cd /src/cups-filters \
    && git fetch --depth 1 origin "$CUPS_FILTERS_COMMIT" \
    && git checkout --detach "$CUPS_FILTERS_COMMIT" \
    && NOCONFIGURE=1 ./autogen.sh \
    && PATH=/opt/cups/usr/bin:$PATH \
       PKG_CONFIG_PATH=/opt/cups/usr/lib/pkgconfig:/opt/cups/usr/lib64/pkgconfig:/opt/cups/usr/lib/x86_64-linux-gnu/pkgconfig:/opt/libcupsfilters/usr/lib/pkgconfig:/opt/libcupsfilters/usr/lib64/pkgconfig:/opt/libcupsfilters/usr/lib/x86_64-linux-gnu/pkgconfig:/opt/libppd/usr/lib/pkgconfig:/opt/libppd/usr/lib64/pkgconfig:/opt/libppd/usr/lib/x86_64-linux-gnu/pkgconfig \
       CPPFLAGS="-I/opt/cups/usr/include -I/opt/libcupsfilters/usr/include -I/opt/libppd/usr/include" \
       LDFLAGS="-L/opt/cups/usr/lib -L/opt/cups/usr/lib64 -L/opt/cups/usr/lib/x86_64-linux-gnu -L/opt/libcupsfilters/usr/lib -L/opt/libcupsfilters/usr/lib64 -L/opt/libcupsfilters/usr/lib/x86_64-linux-gnu -L/opt/libppd/usr/lib -L/opt/libppd/usr/lib64 -L/opt/libppd/usr/lib/x86_64-linux-gnu" \
       ./configure --prefix=/usr --disable-static --disable-mutool \
    && make -j"$(nproc)" \
    && make DESTDIR=/opt/stage install

FROM $BUILD_FROM
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    avahi-daemon dbus ghostscript libavahi-client3 libavahi-common3 \
    libcap2 libdaemon0 libdbus-1-3 libfontconfig1 libfreetype6 \
    libglib2.0-0 libgnutls30 libjpeg62-turbo liblcms2-2 libnss-mdns \
    libpam0g libpaper1 libpng16-16 libqpdf29 libsystemd0 libtiff6 \
    libusb-1.0-0 libxml2 libzstd1 printer-driver-escpr procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN getent group lpadmin >/dev/null || groupadd -r lpadmin

COPY --from=libppd-builder /opt/stage/ /
COPY --from=libcupsfilters-builder /opt/stage/ /
COPY --from=cups-builder /opt/stage/ /
COPY --from=avahi-builder /opt/stage/ /
COPY --from=cups-filters-builder /opt/stage/ /
COPY rootfs /

RUN chmod a+x \
      /etc/s6-overlay/s6-rc.d/initialization/run \
      /etc/s6-overlay/s6-rc.d/dbus-daemon/run \
      /etc/s6-overlay/s6-rc.d/avahi-daemon/run \
      /etc/s6-overlay/s6-rc.d/cups-server/run \
      /etc/s6-overlay/s6-rc.d/queue-repair/run

EXPOSE 631

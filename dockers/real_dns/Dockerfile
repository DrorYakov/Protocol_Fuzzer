FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    wget \
    make \
    gcc \
    xz-utils \
    libc6-dev

WORKDIR /app

RUN wget https://thekelleys.org.uk/dnsmasq/dnsmasq-2.75.tar.xz && \
    tar -xf dnsmasq-2.75.tar.xz && \
    rm dnsmasq-2.75.tar.xz

WORKDIR /app/dnsmasq-2.75

RUN make \
    CFLAGS="-Wall -Wno-address-of-packed-member -O1 -g -fsanitize=address -fno-omit-frame-pointer" \
    LDFLAGS="-fsanitize=address"

EXPOSE 5353/udp

CMD ["./src/dnsmasq", "-d", "-p", "5353", "--log-queries", "--no-daemon", "--no-resolv", "--no-hosts"]
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y gcc

WORKDIR /app

COPY vulnerable_dns.c .

RUN gcc vulnerable_dns.c -o vulnerable_dns \
    -fsanitize=address \
    -fno-stack-protector \
    -z execstack \
    -no-pie \
    -g

EXPOSE 5353/udp

CMD ["./vulnerable_dns"]
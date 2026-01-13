FROM ubuntu:22.04

RUN apt update && apt install -y gcc

WORKDIR /app
COPY vulnerable_ftp.c .

RUN gcc vulnerable_ftp.c -o ftp \
    -fno-stack-protector \
    -z execstack \
    -no-pie

EXPOSE 2121
CMD ["./ftp"]

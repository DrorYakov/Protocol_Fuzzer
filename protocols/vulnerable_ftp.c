#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 2121

int main() {
    // 🔴 Disable stdout buffering
    setvbuf(stdout, NULL, _IONBF, 0);

    int server_fd, client_fd;
    struct sockaddr_in addr;

    char recvbuf[1024];
    char user[64];   // vulnerable buffer

    printf("[+] FTP server starting on port %d\n", PORT);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 1);

    while (1) {
        printf("[*] Waiting for connection...\n");
        client_fd = accept(server_fd, NULL, NULL);
        printf("[+] Client connected\n");

        send(client_fd, "220 Vulnerable FTP Server\r\n", 27, 0);

        while (1) {
            memset(recvbuf, 0, sizeof(recvbuf));
            int r = recv(client_fd, recvbuf, sizeof(recvbuf)-1, 0);
            if (r <= 0) {
                printf("[-] Client disconnected\n");
                break;
            }

            printf("[>] Received %d bytes\n", r);

            if (strncmp(recvbuf, "USER ", 5) == 0) {
                printf("[!] USER command detected\n");
                printf("[!] Copying %ld bytes into 64-byte buffer\n",
                       strlen(recvbuf + 5));

                //  overflow
                strcpy(user, recvbuf + 5);

                send(client_fd, "331 Username OK\r\n", 17, 0);
            }
        }
        close(client_fd);
    }
}

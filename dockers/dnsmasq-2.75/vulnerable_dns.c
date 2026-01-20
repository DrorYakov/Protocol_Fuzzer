#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <stdint.h>
#include <ctype.h>

#define PORT 5454
#define BUFFER_SIZE 2048

// DNS Header Structure (RFC 1035)
struct DNS_HEADER {
    uint16_t id;          // identification number
    uint16_t flags;       // flags
    uint16_t q_count;     // number of question entries
    uint16_t ans_count;   // number of answer entries
    uint16_t auth_count;  // number of authority entries
    uint16_t add_count;   // number of resource entries
} __attribute__((packed));

// Function to convert domain name format (3www6google3com0) to string (www.google.com)
// Returns the length of the name in the packet
int parse_dns_name(unsigned char* reader, unsigned char* buffer, char* output_name) {
    unsigned char *name_ptr = reader;
    int i = 0, j = 0, p = 0;
    int name_len = 0;

    // Standard DNS name parsing loop
    while (*name_ptr != 0) {
        int label_len = *name_ptr;
        name_ptr++;
        for(j = 0; j < label_len; j++) {
            output_name[p++] = *name_ptr;
            name_ptr++;
        }
        output_name[p++] = '.';
    }
    output_name[p-1] = '\0'; // Remove trailing dot
    return (name_ptr - reader) + 1; // Return total length consumed including null byte
}

// VULNERABLE FUNCTION
// Simulates the logic error in Dnsmasq where response buffer size was miscalculated
void build_and_send_response(int sockfd, struct sockaddr_in client_addr, socklen_t addr_len, 
                             struct DNS_HEADER *req_header, char *qname, int qname_len) {
    
    printf("[*] Building response for query: %s (Len: %d)\n", qname, qname_len);

    // VULNERABILITY: 
    // The server allocates memory for the response packet.
    // It assumes a "standard" response size + a small buffer for the domain name.
    // Real CVE-2017-14491 involved incorrect arithmetic during DNSSEC/Pseudo-header construction.
    
    // Bug: We allocate 128 bytes regardless of the incoming domain name length.
    // If the attacker sends a domain name longer than ~100 bytes, this will overflow.
    int estimated_size = sizeof(struct DNS_HEADER) + 128; 
    
    char *response_packet = (char *)malloc(estimated_size);
    if (!response_packet) return;

    // 1. Copy the Header
    memcpy(response_packet, req_header, sizeof(struct DNS_HEADER));
    struct DNS_HEADER *resp_header = (struct DNS_HEADER *)response_packet;
    
    // Set response flags (QR=1, AA=1)
    resp_header->flags = htons(0x8180); 
    resp_header->ans_count = htons(1);

    // 2. Copy the Question Name (The Query) back into the response (Standard DNS behavior)
    char *ptr = response_packet + sizeof(struct DNS_HEADER);

    // --- HEAP OVERFLOW TRIGGER ---
    // We are copying 'qname_len' bytes into a buffer that might not be big enough 
    // if qname_len is very large (e.g., > 128).
    memcpy(ptr, qname, qname_len); 
    
    // (Simulation of adding the rest of the answer record...)
    ptr += qname_len;
    // ... logic to add Type/Class/TTL/RData ...

    printf("[+] Response built successfully (No crash).\n");
    
    // Send (in a real server)
    // sendto(sockfd, response_packet, ...);

    free(response_packet);
}

void process_packet(int sockfd, struct sockaddr_in client_addr, socklen_t addr_len, char *buffer, int len) {
    struct DNS_HEADER *dns = (struct DNS_HEADER *)buffer;
    
    // Basic validation
    if (len < sizeof(struct DNS_HEADER)) return;

    printf("\n--- New DNS Request ---\n");
    printf("Transaction ID: 0x%X\n", ntohs(dns->id));
    printf("Questions: %d\n", ntohs(dns->q_count));

    // Point to the question part
    unsigned char *qname_ptr = (unsigned char *)(buffer + sizeof(struct DNS_HEADER));
    char decoded_name[1024];
    
    // Note: In a real server we would parse the encoded name format (3www6google3com0)
    // For the vulnerability demonstration, we take the raw bytes representing the name structure.
    
    // Calculate raw name length roughly (search for null terminator of the qname)
    int qname_len = 0;
    while (qname_ptr[qname_len] != 0 && (sizeof(struct DNS_HEADER) + qname_len < len)) {
        qname_len++;
    }
    qname_len++; // Include the null terminator byte
    
    // Add Type and Class size (2+2 bytes) to the copy length
    int full_question_blob_len = qname_len + 4;

    // Trigger the response builder
    build_and_send_response(sockfd, client_addr, addr_len, dns, (char*)qname_ptr, full_question_blob_len);
}

int main() {
    int sockfd;
    char buffer[BUFFER_SIZE];
    struct sockaddr_in server_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(sockfd, (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }

    printf("Complex Vulnerable DNS Server listening on port %d\n", PORT);

    while (1) {
        int n = recvfrom(sockfd, (char *)buffer, BUFFER_SIZE, MSG_WAITALL, 
                         (struct sockaddr *)&client_addr, &addr_len);
        if (n > 0)
            process_packet(sockfd, client_addr, addr_len, buffer, n);
    }
    return 0;
}
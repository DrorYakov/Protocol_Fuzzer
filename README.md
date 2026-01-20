# Protocol Fuzzer Project 🛡️

A comprehensive security research project demonstrating **Protocol Fuzzing** (Black-Box Testing) techniques. This project implements custom fuzzers using the **Boofuzz** framework to detect critical vulnerabilities—such as Buffer Overflows and Logic Errors—in simulated FTP, DNS, and proprietary TCP servers.

## 👥 Authors

* **Shimon Khakshour** - [GitHub Profile](https://github.com/shimon2005)
* **Dror Yakov Hai** - [GitHub Profile](https://github.com/DrorYakov)

---

## 📖 Overview

The goal of this project is to simulate a realistic network environment containing vulnerable services and to develop automated attack tools (Fuzzers) capable of crashing them. Unlike standard functional testing, our Fuzzers send massive amounts of malformed and random data to edge cases, aiming to trigger unexpected behaviors.

We targeted three distinct server implementations:
1.  **Vulnerable FTP Server (C)** - Contains a Stack Buffer Overflow.
2.  **Math Server (Python)** - Contains a Logic Error (Division by Zero).
3.  **Vulnerable DNS Server (C)** - Contains a Heap Buffer Overflow (simulating **CVE-2017-14491** found in Dnsmasq).

---

## 🏗️ Architecture

The project environment is containerized using **Docker** to isolate the vulnerable services and ensure reproducible crashes without harming the host machine.

### The Vulnerable Services
| Service | Language | Port | Vulnerability Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| **FTP Server** | C | `2121` | Stack Buffer Overflow | Unsafe `strcpy` usage when handling the `USER` command. |
| **Math Server** | Python | `9090` | Denial of Service (DoS) | Logic error failing to handle division by zero. |
| **DNS Server** | C | `5454` | Heap Buffer Overflow | Miscalculated `malloc` size leading to `memcpy` overflow (CVE-2017-14491 simulation). |

---

## 🚀 Getting Started

### Prerequisites
* **Docker** & **Docker Compose**
* **Python 3.x**
* **Boofuzz** library (`pip install boofuzz`)

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/Protocol_Fuzzer.git](https://github.com/your-username/Protocol_Fuzzer.git)
    cd Protocol_Fuzzer
    ```

2.  **Build and Start the Vulnerable Environment:**
    We use Docker to compile the C servers with specific flags (e.g., `-fno-stack-protector`, `-z execstack`) to make them exploitable for demonstration purposes.
    ```bash
    docker-compose up --build
    ```
    *This command will start all three vulnerable servers on their respective ports.*

## 🛠️ Usage (Running the Fuzzers)

Each fuzzer is a standalone Python script designed to attack a specific protocol.

### 1. Attacking the FTP Server (Stack Overflow)
This fuzzer sends long strings to the `USER` command field.
```bash
python Fuzzer/ftp_fuzzer.py
``` 
Expected Result: The server crashes when receiving a username longer than 64 bytes. The fuzzer detects the socket disconnection, saves the crash packet, and the Docker container restarts.2. Attacking the Math Server (Logic Error)
This fuzzer sends binary packets with random opcodes and operands.

```Bash
python Fuzzer/math_fuzzer.py
```
Expected Result: The fuzzer eventually sends a "Division" opcode with 0 as the second operand. The server throws an unhandled ZeroDivisionError exception and terminates.


3. Attacking the DNS Server (Heap Overflow / CVE-2017-14491)
This fuzzer generates complex DNS UDP packets with varying domain name lengths.

``` Bash
python Fuzzer/dns_fuzzer.py
```
Expected Result: Sending a domain name exceeding the allocated buffer size (header + 128 bytes) triggers a Heap Buffer Overflow via memcpy. The AddressSanitizer (ASan) in the Docker container will report the memory violation and abort the server.

---

## 🔍 Vulnerability Deep Dive

### 💥 FTP Server: Stack Buffer Overflow
* **The Bug:** The server uses `strcpy(user, recvbuf + 5)` to copy the input into a fixed 64-byte buffer without checking the length.
* **The Exploit:** Sending >64 bytes overwrites the stack return address, crashing the program (and potentially allowing RCE in a real-world scenario).

### ➗ Math Server: Logic Denial of Service
* **The Bug:** The server performs `result = num_a // num_b` blindly.
* **The Exploit:** A packet with `num_b = 0` causes a runtime exception that kills the server process immediately.

### 🌐 DNS Server: Heap Buffer Overflow (CVE-2017-14491)
* **The Bug:** A simulation of a real vulnerability in Dnsmasq 2.75. The server calculates the response buffer size incorrectly:
    ```c
    int estimated_size = sizeof(struct DNS_HEADER) + 128; // Too small for long domains
    // ...
    memcpy(ptr, qname, qname_len); // Overflow occurs here
    ```
* **The Exploit:** The fuzzer constructs a valid DNS packet but extends the query name beyond the 128-byte safety margin, corrupting the heap metadata.

---

## 📊 Results

By using these fuzzing tools, we successfully:
* ✅ Automated the discovery of fatal crashes in all three servers.
* ✅ Generated crash reports and logs for analysis.
* ✅ Demonstrated the effectiveness of black-box testing in uncovering memory corruption and logic flaws that static analysis might miss.

## ⚖️ Disclaimer
This project is for **educational purposes only**. The vulnerabilities demonstrated here are intentional and exist within a controlled, isolated environment. Do not use these tools against targets without explicit permission.

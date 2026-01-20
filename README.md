# Protocol Fuzzer Project 🛡️

A comprehensive security-research project demonstrating **Protocol Fuzzing** (black-box testing) techniques. This repository implements custom fuzzers using the **Boofuzz** framework to detect critical vulnerabilities—such as buffer overflows and logic errors—in simulated FTP, DNS, and proprietary TCP servers.

---

## Authors

* **Shimon Khakshour** — [https://github.com/shimon2005](https://github.com/shimon2005)
* **Dror Yakov Hai** — [https://github.com/DrorYakov](https://github.com/DrorYakov)

---

## Overview

The goal of this project is to simulate a realistic network environment containing intentionally vulnerable services and to develop automated attack tools (fuzzers) capable of crashing them. Unlike functional tests, fuzzers send malformed and random inputs to protocol fields and edge cases to trigger unexpected behaviors.

We targeted three different services with distinct vulnerability classes:

1. **Vulnerable FTP Server (C)** — Stack buffer overflow in `USER` handling.
2. **Math Server (Python)** — Logic error that leads to an unhandled division-by-zero (DoS).
3. **Vulnerable DNS Server (C)** — Heap buffer overflow simulating CVE-2017-14491.

---

## Architecture

The environment is containerized with Docker to isolate services and ensure reproducible crashes without affecting the host.

### Services

| Service     | Language |   Port | Vulnerability Type    | Short Description                                                                          |
| ----------- | -------: | -----: | --------------------- | ------------------------------------------------------------------------------------------ |
| FTP Server  |        C | `2121` | Stack Buffer Overflow | Unsafe `strcpy` when copying the `USER` field into a 64‑byte buffer.                       |
| Math Server |   Python | `9090` | Logic Error (DoS)     | Performs integer division without validating the divisor (can be 0).                       |
| DNS Server  |        C | `5454` | Heap Buffer Overflow  | Incorrect response buffer size calculation; `memcpy` overflows for long qnames (CVE-like). |

All services run inside Docker containers. The C services are compiled with exploitation-friendly flags (e.g. `-fno-stack-protector`, `-z execstack`, AddressSanitizer enabled where noted) to make memory errors observable and reportable for educational purposes.

---

## Prerequisites

* Docker & Docker Compose
* Python 3.x
* `boofuzz` Python package (`pip install boofuzz`)

---

## Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/your-username/Protocol_Fuzzer.git
cd Protocol_Fuzzer
```

2. **Build and start the environment**

```bash
docker-compose up --build
```

This will compile the C servers and start all vulnerable services on their ports inside isolated containers.

> Note: The build intentionally disables some hardening features to make the vulnerabilities visible for study. Do **not** use these images or tools against systems you do not own or have explicit authorization to test.

---

## Running the Fuzzers

Each fuzzer is an independent Python script located in `Fuzzer/`. They are written with the **Boofuzz** framework and target the corresponding service.

### 1. FTP Fuzzer (Stack overflow)

Attacks the `USER` command by sending overly long username strings.

```bash
python Fuzzer/ftp_fuzzer.py
```

**Expected behavior:** Sending a username longer than 64 bytes corrupts the stack, crashing the server. The fuzzer detects the socket disconnection, saves the crashing packet, and Docker can be configured to restart the container so the experiment can continue.

### 2. Math Fuzzer (Logic error / DoS)

Sends binary packets with random opcodes and operands. One opcode performs integer division.

```bash
python Fuzzer/math_fuzzer.py
```

**Expected behavior:** The fuzzer will eventually send a division opcode with a zero divisor. The server raises `ZeroDivisionError` and the process terminates.

### 3. DNS Fuzzer (Heap overflow, CVE-like)

Generates UDP DNS queries with variable domain lengths to exercise parsing and copying logic.

```bash
python Fuzzer/dns_fuzzer.py
```

**Expected behavior:** A query with a domain name longer than the server's estimated buffer causes a heap overflow during `memcpy`. If AddressSanitizer (ASan) is enabled in the container, it will report the memory violation and abort the process.

---

## Vulnerability Deep Dives

### FTP Server — Stack Buffer Overflow

**Bug:** The server uses `strcpy(user, recvbuf + 5)` to copy the username into a fixed 64-byte buffer without bounds checking.

**Impact:** Sending `USER` with >64 bytes overwrites the stack return address and can crash the process or — in an exploitable configuration — allow code execution.

**Mitigations:** Use `strncpy`/`strlcpy` (with correct size), validate input lengths, enable compiler mitigations (stack canaries, ASLR, NX), and avoid unsafe C string functions.

---

### Math Server — Logic Denial of Service

**Bug:** The server computes `result = num_a // num_b` without validating `num_b`.

**Impact:** A packet with `num_b == 0` triggers an unhandled `ZeroDivisionError` that terminates the server process.

**Mitigations:** Validate inputs, handle exceptions gracefully, and implement rate-limiting / process supervision to reduce DoS impact.

---

### DNS Server — Heap Buffer Overflow (CVE-like)

**Bug:** The server underestimates the buffer needed for DNS responses:

```c
int estimated_size = sizeof(struct DNS_HEADER) + 128; // too small for long domains
// ...
memcpy(ptr, qname, qname_len); // overflow when qname_len > allocated
```

**Impact:** Copying a long qname overflows the heap area, corrupts heap metadata, and leads to crashes and possible arbitrary code execution in a real-world service. This reproduces the class of bug seen in CVE-2017-14491.

**Mitigations:** Properly calculate buffer sizes from input length, use safe allocation patterns, and enable runtime checks (ASan, fortify, hardened malloc).

---

## Results & Artifacts

* Crashes were automatically detected by the fuzzers.
* Crash packets are saved for triage and analysis.
* Docker container logs and ASan reports (when enabled) provide evidence and stack traces for each crash.

Use the saved crash cases and logs to triage, reproduce, and write minimal testcases or patches.

---

## Safety & Legal Disclaimer

This repository is strictly for educational use within a controlled environment. Do **not** point these fuzzers or vulnerable binaries at production systems or targets for which you do not have explicit authorization. Misuse may be illegal.

---

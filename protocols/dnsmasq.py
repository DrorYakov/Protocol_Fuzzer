#!/usr/bin/env python3
from boofuzz import *

TARGET_IP = "127.0.0.1"
TARGET_PORT = 53

def main():
    """
    DNS Protocol Fuzzer targeting structural vulnerabilities defined in RFC 1035.
    
    Implements strategy for attacking:
    1. Header logic (Transaction IDs, Flags, Counters).
    2. Label parsing (Length mismatches, Null bytes).
    3. Compression mechanism (Pointer loops, Out-of-bounds reads).
    """
    
    session = Session(
        target=Target(
            connection=SocketConnection(TARGET_IP, TARGET_PORT, proto='udp')
        ),
        sleep_time=0.1,
        check_interval=0.2
    )

    s_initialize("DNS_Packet")

    # --- DNS HEADER (12 Bytes) ---
    # Vulnerability: Transaction ID Spoofing & Memory Exhaustion
    # Fuzzing target: Check for state management bugs and collisions.
    s_word(0x1337, name="TransactionID", fuzzable=True)

    # Vulnerability: Flag Manipulation (Logic Bombs)
    # Breaking down the 16-bit flag field to target specific control bits.
    
    # QR (1 bit): Query/Response. Sending 'Response' (1) to a server expecting 'Query'.
    s_bit_field(0, width=1, name="QR") 
    
    # Opcode (4 bits): Critical target.
    # Values 15 or Reserved bits can trigger unhandled switch-cases or jump tables.
    s_bit_field(0, width=4, name="Opcode", fuzzable=True) 
    
    s_bit_field(0, width=1, name="AA") # Authoritative Answer
    s_bit_field(0, width=1, name="TC") # Truncated
    s_bit_field(1, width=1, name="RD") # Recursion Desired
    s_bit_field(0, width=1, name="RA") # Recursion Available
    
    # Z (3 bits): Reserved. MUST be 0.
    # Fuzzing target: Enabling debug modes or proprietary logic by setting these bits.
    s_bit_field(0, width=3, name="Z_Reserved", fuzzable=True) 
    
    s_bit_field(0, width=4, name="RCODE")

    # Vulnerability: Count Field Mismatches (Integer Overflows / Buffer Over-reads)
    # Intentionally causing a mismatch between these counts and the actual payload size.
    s_word(1, name="QDCOUNT", fuzzable=True) # Number of Questions
    s_word(0, name="ANCOUNT", fuzzable=True) # Number of Answers
    s_word(0, name="NSCOUNT", fuzzable=True) # Number of Authority Records
    s_word(0, name="ARCOUNT", fuzzable=True) # Number of Additional Records

    # --- QUESTION SECTION ---
    # Vulnerability: Label Parsing & Name Compression
    # Using blocks to allow the fuzzer to mutate the structure of domain names.
    
    if s_block_start("Question_Section"):
        
        # --- Label 1: "fuzz" ---
        # Vulnerability: Length Mismatch (Off-by-one).
        # We use s_size to define the length byte. Boofuzz will try to make this 
        # larger/smaller than the actual string, causing Heap Over-reads.
        s_size("Label1_Content", length=1, fuzzable=True)
        if s_block_start("Label1_Content"):
            s_string("fuzz", name="Label1_String", fuzzable=True)
        s_block_end("Label1_Content")

        # --- Label 2: "com" ---
        s_size("Label2_Content", length=1, fuzzable=True)
        if s_block_start("Label2_Content"):
            s_string("com", name="Label2_String", fuzzable=True)
        s_block_end("Label2_Content")

        # --- Terminator / Compression Pointer ---
        # Vulnerability: Compression Pointers (Infinite Loops / OOB Reads).
        # This byte is normally 0x00 (End of name).
        # Fuzzing this to 0xC0 triggers the compression logic.
        # Combined with the next byte, it creates a pointer offset.
        s_byte(0x00, name="Name_Terminator", fuzzable=True)

        # Query Type & Class
        s_word(1, name="QTYPE", fuzzable=False)  # A Record
        s_word(1, name="QCLASS", fuzzable=False) # IN Class
        
    s_block_end("Question_Section")

    session.connect(s_get("DNS_Packet"))
    
    print("[*] Starting DNS Protocol Fuzzer...")
    print("[*] Target: Structural integrity of Header and Name Parsing logic.")
    session.fuzz()

if __name__ == "__main__":
    main()
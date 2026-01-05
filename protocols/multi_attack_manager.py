#!/usr/bin/env python3
from boofuzz import *
import threading
import time

TARGET_IP = "127.0.0.1"
TARGET_PORT = 53

def define_attacks():
    """
    Defines the 4 attack vectors globally before execution.
    These definitions are read-only during runtime, making them thread-safe.
    """
    
    # --- Vector 1: Name Compression (Infinite Recursion) ---
    s_initialize("Attack_Compression")
    s_word(0x1337, name="TransID", fuzzable=False)
    s_word(0x0100, name="Flags", fuzzable=False)
    s_word(1, name="QDCOUNT", fuzzable=False)
    s_word(0, name="ANCOUNT", fuzzable=False)
    s_word(0, name="NSCOUNT", fuzzable=False)
    s_word(0, name="ARCOUNT", fuzzable=False)
    
    if s_block_start("Question_Compression"):
        s_size("Label_Len", length=1, fuzzable=False)
        s_string("attack", fuzzable=False)
        # The Attack: Pointer 0xC0 followed by a fuzzed offset to create loops
        s_byte(0xC0, name="Compression_Flag", fuzzable=False)
        s_byte(0x0C, name="Bad_Offset", fuzzable=True) 
    s_block_end("Question_Compression")

    # --- Vector 2: Count Fields (Buffer Over-read) ---
    s_initialize("Attack_Counts")
    s_word(0x1338, name="TransID", fuzzable=False)
    s_word(0x0100, name="Flags", fuzzable=False)
    # The Attack: Declare 1000 questions, send none (mismatch)
    s_word(1000, name="QDCOUNT_Mismatch", fuzzable=True) 
    s_word(0, name="ANCOUNT", fuzzable=False)
    s_word(0, name="NSCOUNT", fuzzable=False)
    s_word(0, name="ARCOUNT", fuzzable=False)

    # --- Vector 3: Labels (Heap Corruption) ---
    s_initialize("Attack_Labels")
    s_word(0x1339, name="TransID", fuzzable=False)
    s_word(0x0100, name="Flags", fuzzable=False)
    s_word(1, name="QDCOUNT", fuzzable=False)
    s_word(0, name="ANCOUNT", fuzzable=False)
    s_word(0, name="NSCOUNT", fuzzable=False)
    s_word(0, name="ARCOUNT", fuzzable=False)

    if s_block_start("Question_Label"):
        # The Attack: Length byte says X, string is Y (Boundary Violation)
        s_size("Label_Content", length=1, fuzzable=True) 
        if s_block_start("Label_Content"):
            s_string("fuzzme", name="Label_String", fuzzable=True)
        s_block_end("Label_Content")
        s_byte(0x00, name="Terminator", fuzzable=False)
    s_block_end("Question_Label")

    # --- Vector 4: Flags (Logic Bombs) ---
    s_initialize("Attack_Flags")
    s_word(0x1340, name="TransID", fuzzable=False)
    
    # The Attack: Fuzzing Reserved bits and Opcodes to trigger dead code
    s_bit_field(0, width=1, name="QR", fuzzable=False) 
    s_bit_field(0, width=4, name="Opcode", fuzzable=True) # Target: Invalid Opcodes
    s_bit_field(0, width=1, name="AA", fuzzable=False)
    s_bit_field(0, width=1, name="TC", fuzzable=False)
    s_bit_field(1, width=1, name="RD", fuzzable=False)
    s_bit_field(0, width=1, name="RA", fuzzable=False)
    s_bit_field(0, width=3, name="Z_Reserved", fuzzable=True) # Target: Reserved Bits
    s_bit_field(0, width=4, name="RCODE", fuzzable=False)

    s_word(1, name="QDCOUNT", fuzzable=False)
    s_word(0, name="ANCOUNT", fuzzable=False)
    s_word(0, name="NSCOUNT", fuzzable=False)
    s_word(0, name="ARCOUNT", fuzzable=False)
    
    if s_block_start("Question_Flags"):
        s_size("L_Len", length=1, fuzzable=False)
        s_string("test", fuzzable=False)
        s_byte(0x00, name="Term", fuzzable=False)
    s_block_end("Question_Flags")

def run_fuzzer_thread(request_name, thread_id):
    """
    Runs a separate fuzzing session for each thread.
    CRITICAL: Assigns a unique db_filename to prevent SQLite locking collisions.
    """
    unique_db = f"fuzz_results_thread_{thread_id}.db"
    
    session = Session(
        target=Target(
            connection=SocketConnection(TARGET_IP, TARGET_PORT, proto='udp')
        ),
        sleep_time=0.1,
        db_filename=unique_db, # Ensures thread safety for DB logging
        index_start=0,
        index_end=2000 # Iteration limit for demo
    )
    
    print(f"[*] [Thread-{thread_id}] Starting vector '{request_name}' (DB: {unique_db})")
    
    session.connect(s_get(request_name))
    session.fuzz()

if __name__ == "__main__":
    # 1. Initialize global protocol definitions
    define_attacks()
    
    # 2. Setup and launch threads
    vectors = ["Attack_Compression", "Attack_Counts", "Attack_Labels", "Attack_Flags"]
    threads = []
    
    print(f"[*] Launching Multi-Threaded DNS Fuzzer on {TARGET_IP}:{TARGET_PORT}")
    print("[*] Note: Parallel fuzzing uses unique DB files per thread.")

    for i, vector in enumerate(vectors):
        t = threading.Thread(target=run_fuzzer_thread, args=(vector, i+1))
        threads.append(t)
        t.start()
        # Short delay to prevent socket resource contention on startup
        time.sleep(0.5)

    # 3. Wait for all threads to complete
    for t in threads:
        t.join()

    print("[*] All attacks completed successfully.")
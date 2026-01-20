#!/usr/bin/env python3
from boofuzz import *

def main():
    target_ip = "127.0.0.1"
    target_port = 5454 

    session = Session(
        target=Target(
            connection=SocketConnection(target_ip, target_port, proto='udp')
        ),
        sleep_time=0.1, 
        restart_threshold=1, 
        ignore_connection_reset=True
    )

    s_initialize(name="DNS_Smart")

    # 1. DNS Header (Fixed Structure)
    s_word(0x1234, name="TransactionID", endian='>') 
    s_word(0x0100, name="Flags", endian='>')           # Standard Query
    s_word(0x0001, name="Questions", endian='>')       # 1 Question
    s_word(0x0000, name="AnswerRRs", endian='>')
    s_word(0x0000, name="AuthorityRRs", endian='>')
    s_word(0x0000, name="AdditionalRRs", endian='>')

    # 2. DNS Question Section (The Attack Surface)
    if s_block_start("Question"):
        
        s_size("fuzz_label", length=1, fuzzable=True) 
        s_string("fuzzme", name="fuzz_label", fuzzable=True)
        
        s_byte(0x03) # Length
        s_string("com")
        
        # Root Terminator
        s_byte(0x00)

        # Type A (Host Address)
        s_word(0x0001, name="Type", endian='>')
        # Class IN
        s_word(0x0001, name="Class", endian='>')
        
    s_block_end()

    session.connect(s_get("DNS_Smart"))

    print(f"[*] Starting Smart Fuzzer against Dnsmasq 2.75 on {target_ip}:{target_port}...")
    session.fuzz()

if __name__ == "__main__":
    main()
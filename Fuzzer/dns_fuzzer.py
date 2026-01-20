#!/usr/bin/env python3
from boofuzz import *

def main():
    target_ip = "127.0.0.1"
    target_port = 5454
    
    session = Session(
        target=Target(connection=SocketConnection(target_ip, target_port, proto='udp')),
        sleep_time=0.1,
    )

    s_initialize(name="DNS_Complex_Query")
    
    # 1. DNS Header (12 Bytes)
    s_word(0x1337, name="TransactionID", endian='>') 
    s_word(0x0100, name="Flags", endian='>')           # Standard Query, Recursion Desired
    s_word(0x0001, name="Questions", endian='>')       # 1 Question
    s_word(0x0000, name="AnswerRRs", endian='>')
    s_word(0x0000, name="AuthorityRRs", endian='>')
    s_word(0x0000, name="AdditionalRRs", endian='>')

    # 2. Question Section
    if s_block_start("Question_Section"):
        
        s_size("subdomain", length=1, fuzzable=True)
        s_string("fuzzme", name="subdomain", fuzzable=True)
        
        s_byte(0x03) # Length of 'com'
        s_string("com")
        
        s_byte(0x00) # Terminator

        # Type (A Record) and Class (IN)
        s_word(0x0001, name="Type", endian='>')
        s_word(0x0001, name="Class", endian='>')
    s_block_end()

    session.connect(s_get("DNS_Complex_Query"))
    print(f"[*] Starting Complex DNS Fuzzer on {target_ip}:{target_port}...")
    session.fuzz()

if __name__ == "__main__":
    main()
from boofuzz import *
import socket
import time
import sys

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8080

def check_crash(target, fuzz_data_logger, session, *args, **kwargs):
    """
    Callbacks function to verify server availability after each fuzzing iteration.
    
    Attempts to connect to the target; if connection fails, assumes a crash,
    logs the payload that caused the crash, and terminates the fuzzer.
    """ 
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((TARGET_IP, TARGET_PORT))
        s.close()
    except:
        print("\n[!] CRASH CONFIRMED! The server died due to Buffer Overflow.")
        # Saving the long packet that caused the crash
        with open(f"overflow_crash_{int(time.time())}.txt", "wb") as f:
            f.write(session.last_send)
        sys.exit(0)

def main():
    session = Session(
        target=Target(connection=SocketConnection(TARGET_IP, TARGET_PORT, proto='tcp')),
        sleep_time=0.1,
        post_test_case_callbacks=[check_crash]
    )

    s_initialize("OverflowRequest")

    # 1. the standard HTTP request headers (not fuzzed) 
    s_string("GET / HTTP/1.1", fuzzable=False)
    s_static("\r\n")
    s_string("Host: 127.0.0.1", fuzzable=False)
    s_static("\r\n")

    # 2. the payload header we want to fuzz 
    s_string("X-Small-Buffer", fuzzable=False) # The header name is fixed
    s_delim(": ", fuzzable=False)          # The delimiter is fixed

    # Here's the magic: we define a simple string, but we don't lock it (no fuzzable=False)
    # boofuzz will understand this is the only variable and start bombarding it with varying lengths:
    # 10 characters, 100 characters, 1000 characters, 5000 characters, etc.
    s_string("A", name="BufferField") 

    s_static("\r\n\r\n")

    session.connect(s_get("OverflowRequest"))
    
    print("[*] Starting Fuzzer...")
    print("[*] Strategy: Targeting 'X-Small-Buffer' with increasing lengths.")
    session.fuzz()

if __name__ == "__main__":
    """
    Initializes the Boofuzz session and defines the protocol structure.
    
    Sets 'X-Small-Buffer' as the injection point for fuzzing payloads
    to test the server's handling of variable-length inputs.
    """
    main()
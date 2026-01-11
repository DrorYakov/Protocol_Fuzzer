from boofuzz import *
import socket
import time
import sys

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8080

def check_crash(target, fuzz_data_logger, session, *args, **kwargs):
    try:
        # Check if server is alive
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((TARGET_IP, TARGET_PORT))
        s.close()
    except:
        print("\nCRASH DETECTED. Server is down.")
        
        # Save the packet that caused the crash
        filename = f"crash_overflow_{int(time.time())}.txt"
        with open(filename, "wb") as f:
            f.write(session.last_send)
        
        print(f"Crash packet saved to {filename}")
        sys.exit(0)

def main():
    # 'db_filename=None' prevents saving the run history to disk
    session = Session(
        target=Target(connection=SocketConnection(TARGET_IP, TARGET_PORT, proto='tcp')),
        sleep_time=0.1,
        db_filename=None, 
        post_test_case_callbacks=[check_crash]
    )

    s_initialize("OverflowRequest")

    # Static parts
    s_string("GET / HTTP/1.1", fuzzable=False)
    s_static("\r\n")
    s_string("Host: 127.0.0.1", fuzzable=False)
    s_static("\r\n")

    # Vulnerable part
    s_string("X-Small-Buffer", fuzzable=False)
    s_delim(": ", fuzzable=False)
    s_string("A", name="BufferField") # Fuzzer will expand this string

    s_static("\r\n\r\n")

    session.connect(s_get("OverflowRequest"))
    
    print("Starting Overflow Fuzzer...")
    session.fuzz()

if __name__ == "__main__":
    main()
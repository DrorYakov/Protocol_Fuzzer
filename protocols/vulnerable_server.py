from boofuzz import *
import socket
import time
import sys

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8080

def check_crash(target, fuzz_data_logger, session, *args, **kwargs):
    """בודק אם השרת מת אחרי השליחה"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((TARGET_IP, TARGET_PORT))
        s.close()
    except:
        print("\n[!] CRASH CONFIRMED! The server died due to Buffer Overflow.")
        # שמירת הפאקטה הארוכה שגרמה לקריסה
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

    # 1. חלקים קבועים (Fuzzer לא ייגע בהם)
    s_string("GET / HTTP/1.1", fuzzable=False)
    s_static("\r\n")
    s_string("Host: 127.0.0.1", fuzzable=False)
    s_static("\r\n")

    # 2. החלק שבו אנחנו רוצים להתמקד (The Target)
    s_string("X-Small-Buffer", fuzzable=False) # שם השדה קבוע
    s_delim(": ", fuzzable=False)          # המפריד קבוע

    # כאן הקסם: אנחנו מגדירים מחרוזת פשוטה, אבל לא נועלים אותה (אין fuzzable=False)
    # boofuzz יבין שזה המשתנה היחיד ויתחיל להפציץ אותו באורכים משתנים:
    # 10 תווים, 100 תווים, 1000 תווים, 5000 תווים וכו'.
    s_string("A", name="BufferField") 

    s_static("\r\n\r\n")

    session.connect(s_get("OverflowRequest"))
    
    print("[*] Starting Fuzzer...")
    print("[*] Strategy: Targeting 'X-Small-Buffer' with increasing lengths.")
    session.fuzz()

if __name__ == "__main__":
    main()
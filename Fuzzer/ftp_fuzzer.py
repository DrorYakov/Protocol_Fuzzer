from boofuzz import *
import subprocess
import time
import os

TARGET_IP = "127.0.0.1"
TARGET_PORT = 2121
CRASH_DIR = "crashes"

os.makedirs(CRASH_DIR, exist_ok=True)

def restart_server():
    print("[*] Restarting FTP server...")
    subprocess.run(
        ["docker", "restart", "ftp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1)

def after_test_case(target, fuzz_data_logger, session, *args, **kwargs):
    # ✔ real crash condition
    if session.last_recv is None:
        print("[!] REAL crash detected")

        filename = f"{CRASH_DIR}/crash_{int(time.time())}.bin"
        with open(filename, "wb") as f:
            f.write(session.last_send)

        print(f"[+] Saved crash input to {filename}")
        restart_server()

session = Session(
    target=Target(
        connection=TCPSocketConnection(
            TARGET_IP,
            TARGET_PORT
        )
    ),
    post_test_case_callbacks=[after_test_case]
)

s_initialize("ftp_user")

s_static("USER ")
s_string("anonymous", fuzzable=True, max_len=2000)  # חשוב!
s_static("\r\n")

session.connect(s_get("ftp_user"))

session.fuzz()

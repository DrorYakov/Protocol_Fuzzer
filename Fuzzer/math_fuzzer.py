from boofuzz import *
import socket
import sys
import time
import struct

TARGET_IP = "127.0.0.1"
TARGET_PORT = 9090

def check_crash(target, fuzz_data_logger, session, *args, **kwargs):
    try:
        # Check if server is alive
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((TARGET_IP, TARGET_PORT))
        s.close()
    except:
        print("\nCRASH DETECTED. Logic error triggered.")
        
        # Get the raw bytes that caused the crash
        raw_data = session.last_send
        filename = f"crash_math_{int(time.time())}.txt"
        
        # Create a readable text report
        with open(filename, "w") as f:
            f.write("=== CRASH REPORT ===\n")
            f.write(f"Timestamp: {time.ctime()}\n")
            f.write(f"Raw Hex: {raw_data.hex()}\n")
            f.write(f"Total Bytes: {len(raw_data)}\n")
            f.write("--------------------\n")
            f.write("Parsed Content:\n")
            
            # Try to decode the binary packet to show exactly what numbers caused it
            try:
                if len(raw_data) == 9:
                    opcode, a, b = struct.unpack('<Bii', raw_data)
                    f.write(f"Opcode:   {opcode}\n")
                    f.write(f"Operand A: {a}\n")
                    f.write(f"Operand B: {b}  <-- LIKELY CAUSE (If 0)\n")
                else:
                    f.write("Packet length mismatch (not 9 bytes), cannot parse structure.\n")
            except Exception as e:
                f.write(f"Parsing error: {e}\n")

        print(f"Crash details saved to text file: {filename}")
        sys.exit(0)

def main():
    session = Session(
        target=Target(connection=SocketConnection(TARGET_IP, TARGET_PORT, proto='tcp')),
        sleep_time=0.1,
        db_filename=None,
        post_test_case_callbacks=[check_crash]
    )

    s_initialize("MathPacket")
    
    # Define Binary Protocol [OP][A][B]
    s_byte(0x03, name="opcode", fuzzable=False)  # DIV operation - likely to trigger error
    s_dword(10, name="operand_a", endian='<', fuzzable=True)
    s_dword(2, name="operand_b", endian='<', fuzzable=True)

    session.connect(s_get("MathPacket"))
    
    print("Starting Binary Math Fuzzer...")
    session.fuzz()

if __name__ == "__main__":
    main()
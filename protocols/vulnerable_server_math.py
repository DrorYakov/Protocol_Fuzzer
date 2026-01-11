import socket
import struct
import sys

HOST = '0.0.0.0'
PORT = 9090

def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)
        print(f"Math Server running on {HOST}:{PORT}")
        print("Protocol: [OP:1][A:4][B:4]")

        while True:
            client_sock, _ = server_sock.accept()
            handle_client(client_sock)
    except KeyboardInterrupt:
        print("Server stopping")
    finally:
        server_sock.close()

def handle_client(sock):
    try:
        data = sock.recv(9)
        if len(data) < 9:
            return

        # Unpack: 1 byte char, 2 ints (Little Endian)
        opcode, num_a, num_b = struct.unpack('<Bii', data)
        result = 0

        if opcode == 0x01: # ADD
            result = num_a + num_b
        elif opcode == 0x02: # SUB
            result = num_a - num_b
        elif opcode == 0x03: # DIV
            # Logic Error: No check for zero
            result = num_a // num_b 

        print(f"Op: {opcode}, A: {num_a}, B: {num_b} -> Res: {result}")
        sock.sendall(struct.pack('<i', result))

    except ZeroDivisionError:
        print("CRITICAL ERROR: Division by zero. System crashing.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    start_server()
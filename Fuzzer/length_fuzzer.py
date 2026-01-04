import socket
import sys

HOST = '0.0.0.0'
PORT = 8080

def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)
        print(f"[*] Server running. I have a buffer limit of 256 bytes on 'X-Small-Buffer'.")

        while True:
            client_sock, _ = server_sock.accept()
            handle_client(client_sock)
    except KeyboardInterrupt:
        pass
    finally:
        server_sock.close()

def handle_client(sock):
    try:
        request = sock.recv(4096).decode('utf-8', errors='ignore')
        if not request:
            return

        for line in request.split('\r\n'):
            if line.startswith("X-Small-Buffer:"):
                value = line.split(":", 1)[1].strip()
                if len(value) > 256:
                    print(f"\n[!!!] BUFFER OVERFLOW! Received {len(value)} bytes, expected max 256.")
                    print("[!!!] Memory corrupted. System crashing...")
                    sys.exit(1)

        response = "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
        sock.sendall(response.encode())
        
    except SystemExit:
        raise # מעביר את הקריסה למעלה כדי לסגור את התוכנית
    except:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    start_server()
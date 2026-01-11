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
        print(f"Server running on {HOST}:{PORT}")
        print("Waiting for connections...")

        while True:
            client_sock, _ = server_sock.accept()
            handle_client(client_sock)
    except KeyboardInterrupt:
        print("Server stopping by user request")
    finally:
        server_sock.close()

def handle_client(sock):
    try:
        request = sock.recv(4096).decode('utf-8', errors='ignore')
        if not request:
            return

        # Simple parsing to find the specific header
        for line in request.split('\r\n'):
            if line.startswith("X-Small-Buffer:"):
                value = line.split(":", 1)[1].strip()
                
                # Vulnerability: Crash if value is > 256 bytes
                if len(value) > 256:
                    print(f"Buffer overflow detected ({len(value)} bytes). System crash.")
                    sys.exit(1) # Simulates a fatal crash

        # Send standard response
        response = "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
        sock.sendall(response.encode())
        
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    start_server()
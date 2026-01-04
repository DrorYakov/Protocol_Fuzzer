import socket
import sys

# Configuration
HOST = '0.0.0.0'
PORT = 8080  # Listening port


def start_server():
    """
    Starts a vulnerable HTTP server.

    Behavior:
    1. Listens on TCP port 8080.
    2. Accepts incoming HTTP requests.
    3. If the request contains the keyword 'FUZZ_CRASH', simulates a server crash.
    4. Otherwise, returns a standard HTTP 200 OK response.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow port reuse to avoid 'Address already in use' errors
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)
        print(f"[*] Vulnerable HTTP Server running on {HOST}:{PORT}")
        print("[*] Send 'FUZZ_CRASH' to kill this server.")

        while True:
            client_sock, addr = server_sock.accept()
            handle_client(client_sock)

    except KeyboardInterrupt:
        print("\n[*] Server stopping...")
    except RuntimeError as e:
        print(f"\n[!!!] SERVER CRASHED: {e}")
        sys.exit(1)
    finally:
        server_sock.close()


def handle_client(sock):
    """
    Handles a single client connection.
    Parses the input and triggers a crash if the vulnerability keyword is found.
    """
    try:
        request = sock.recv(4096).decode('utf-8', errors='ignore')

        if not request:
            sock.close()
            return

        # --- VULNERABILITY TRIGGER ---
        if "FUZZ_CRASH" in request:
            raise RuntimeError("Fatal Error: Buffer Overflow Simulated!")
        # -----------------------------

        # Standard HTTP Response
        http_response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 12\r\n"
            "\r\n"
            "Server Alive"
        )
        sock.sendall(http_response.encode('utf-8'))

    except Exception as e:
        # Re-raise the simulated crash to stop the main loop
        if "Simulated" in str(e):
            raise e
    finally:
        sock.close()


if __name__ == "__main__":
    start_server()
import socket
TARGET = "127.0.0.1"
PORT = 2121
payload = b'USER  anonymous\r\n'
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TARGET, PORT))
    s.send(payload)
    print("Payload sent.")
except Exception as e:
    print(e)

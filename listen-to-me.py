import socket
import keyboard
import time

def port_listener(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', port))
    sock.listen(1)

    print(f"Listening for keypress events on port {port}...")

    conn, addr = sock.accept()
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            key = data.decode()

            if len(key) == 1 and key.isalnum():
                keyboard.send(key)

if __name__ == "__main__":
    port = 65430
    port_listener(port)

import threading
import socket
import argparse
import sys

class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.connections = []
        self.host = host
        self.port = port
        self.lock = threading.Lock()  # Lock for thread-safe access
        self.shutdown_flag = threading.Event()  # Event to signal shutdown

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen(1)
        print("Listening at", sock.getsockname())

        while not self.shutdown_flag.is_set():  # Check shutdown flag
            try:
                sock.settimeout(1)  # Add timeout to avoid blocking indefinitely
                sc, sockname = sock.accept()
                print(f"Accepting a new connection from {sc.getpeername()} to {sc.getsockname()}")

                # Create a new thread
                server_socket = ServerSocket(sc, sockname, self)
                server_socket.start()

                # Add thread to active connections
                with self.lock:
                    self.connections.append(server_socket)
                print("Ready to receive message from", sc.getpeername())

            except socket.timeout:
                continue  # Timeout ensures that we can check for shutdown flag

        print("Server shutting down...")
        sock.close()

    def broadcast(self, message, source):
        with self.lock:
            for connection in self.connections:
                if connection.sockname != source:
                    connection.send(message)

    def remove_connection(self, connection):
        with self.lock:
            self.connections.remove(connection)

    def shutdown(self):
        self.shutdown_flag.set()  # Set the shutdown flag to stop the server
        with self.lock:
            for connection in self.connections:
                connection.close()  # Close all client connections

class ServerSocket(threading.Thread):
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server
        self.shutdown_flag = threading.Event()  # Event to signal shutdown

    def run(self):
        while not self.shutdown_flag.is_set():
            try:
                message = self.sc.recv(1024).decode('ascii')
                if message:
                    print(f"{self.sockname} says: {message}")
                    self.server.broadcast(message, self.sockname)
                else:
                    print(f"{self.sockname} has closed the connection")
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

        self.sc.close()
        self.server.remove_connection(self)

    def send(self, message):
        self.sc.sendall(message.encode('ascii'))

    def close(self):
        self.shutdown_flag.set()  # Signal this thread to stop
        self.sc.close()  # Close the socket

def exit_server(server):
    while True:
        ipt = input("Type 'q' to shut down the server: ")
        if ipt.lower() == "q":
            print("Shutting down the server...")
            server.shutdown()  # Signal the server to shut down
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom Server")
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')

    args = parser.parse_args()

    # Create and start server thread
    server = Server(args.host, args.p)
    server.start()

    # Listen for shutdown input
    exit_server(server)

    # Wait for the server thread to finish before exiting
    server.join()
    print("Server has been shut down.")

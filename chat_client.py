import threading
import socket
import argparse
import sys
import tkinter as tk
import traceback

class Send(threading.Thread):
    def __init__(self, sock, name, message_widget, text_input):
        super().__init__()
        self.sock = sock
        self.name = name
        self.message_widget = message_widget
        self.text_input = text_input

    def run(self):
        while True:
            message = self.text_input.get()
            if message.strip() == "QUIT":
                self.sock.sendall(f'Server: {self.name} has left the chat.'.encode('ascii'))
                break
            elif message:
                self.sock.sendall(f'{self.name}: {message}'.encode('ascii'))
            self.text_input.delete(0, tk.END)

        print('\nQuitting....')
        self.sock.close()
        sys.exit(0)

class Receive(threading.Thread):
    def __init__(self, sock, message_widget):
        super().__init__()
        self.sock = sock
        self.message_widget = message_widget

    def run(self):
        while True:
            try:
                message = self.sock.recv(1024).decode('ascii')
                if message:
                    self.message_widget.config(state='normal')
                    self.message_widget.insert(tk.END, message + '\n')
                    self.message_widget.yview(tk.END)  # Scroll to the bottom
                    self.message_widget.config(state='disabled')  # Make it read-only
                else:
                    print('\nConnection lost.')
                    break
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()
                break

        self.sock.close()
        sys.exit(0)

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None

    def start(self):
        print(f'Trying to connect to {self.host}:{self.port}.....')
        self.sock.connect((self.host, self.port))
        print(f'Successfully connected to {self.host}:{self.port}')

        self.name = input('Your name: ')
        print(f'Welcome, {self.name}! Getting ready to send and receive messages......')

        window = tk.Tk()
        window.title("ChatRoom")

        # Message display area
        self.message_widget = tk.Text(window, state='disabled', wrap=tk.WORD, height=15)
        self.message_widget.pack(expand=True, fill='both', padx=10, pady=10)

        # Text input area
        self.text_input = tk.Entry(window)
        self.text_input.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Send button
        send_button = tk.Button(window, text="Send", command=self.send_message)
        send_button.pack(pady=(0, 10))

        send_thread = Send(self.sock, self.name, self.message_widget, self.text_input)
        receive_thread = Receive(self.sock, self.message_widget)

        send_thread.start()
        receive_thread.start()

        self.sock.sendall(f'Server: {self.name} has joined the chat.'.encode('ascii'))
        print("Ready! Leave the chatroom anytime by typing 'QUIT'\n")

        window.mainloop()

    def send_message(self):
        message = self.text_input.get()
        if message.strip() == "QUIT":
            self.sock.sendall(f'Server: {self.name} has left the chat.'.encode('ascii'))
            self.text_input.delete(0, tk.END)
            self.sock.close()
            sys.exit(0)
        elif message:
            self.sock.sendall(f'{self.name}: {message}'.encode('ascii'))
            self.text_input.delete(0, tk.END)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom Client")
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    args = parser.parse_args()

    client = Client(args.host, args.p)
    client.start()

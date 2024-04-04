import socket
import sys
import threading


# Function to connect to the Chat Room Directory Server (CRDS)
def connect_to_crds():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))
        return client_socket
    except Exception as e:
        print(f"Error connecting to CRDS: {e}")
        return None

def receive_messages(client_socket, stop_event):
    """
    Continuously listens for messages from the server and prints them.
    """
    try:
        while not stop_event.is_set():
            response = client_socket.recv(1024).decode("utf-8")
            if response == "You have exited the chat.":
                break
            if not response:
                break  # Stop the loop if the server closes the connection or an empty response is received
            print(response)
    except Exception as e:
        print(f"Error receiving messages: {e}")
    finally:
        print("Stopped receiving messages.")

# Function to handle client commands
def handle_commands():
    connected = False
    client_socket = None
    name = ""
    while True:
        command = input("Enter command: ")
        if command.startswith("connect"):
            if connected:
                print("Already connected.")
                continue
            client_socket = connect_to_crds()
            if client_socket:
                print("Connected to CRDS.")
                connected = True
                continue
            else:
                print("Failed to connect to CRDS.")
                continue
        if not connected:
            print("Please connect to the server first.")
            continue

        if command.startswith("bye"):
            client_socket.close()
            break

        client_socket.send(command.encode("utf-8"))
        response = client_socket.recv(1024).decode("utf-8")
        print(response)

        if command.startswith("name"):
            name = command.split()[1]
            #print(f"Your name is set to: {name}")
        elif command.startswith("chat"):
            if not name:
                print("Please set your name first using 'name <your name>'")
                continue
            chat_room = command.split()[1]
            #print(f"Entering chat mode for chat room: {chat_room}")
            stop_event = threading.Event()
            receiver_thread = threading.Thread(target=receive_messages, args=(client_socket, stop_event))
            receiver_thread.start()
            try:
                while True:
                    message = input()
                    if message == "^E":
                        client_socket.send(message.encode("utf-8"))
                        break
                    client_socket.send(message.encode("utf-8"))
            finally:
                # Signal the receiver_thread to stop and wait for it to finish
                stop_event.set()
                receiver_thread.join()
                print("Exiting chat mode...")

# Main function
def main():
    handle_commands()

if __name__ == "__main__":
    main()

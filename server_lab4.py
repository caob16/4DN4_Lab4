import ipaddress
import socket
import threading

# Define constants
CRDP = 12345  # Chat Room Directory port
MULTICAST_RANGE = ('239.0.0.0', '239.255.255.255')

# Dictionary to store chat room directory
chat_room_directory = {}

# Dictionary to store client names
client_names = {}

# Dictionary to store clients in chat mode
clients_in_chat_mode = {}

def is_valid_multicast_address(address):
    # 定义多播地址的范围
    multicast_range_start = ipaddress.IPv4Address(MULTICAST_RANGE[0])
    multicast_range_end = ipaddress.IPv4Address(MULTICAST_RANGE[1])
    # 将传入的地址转换为IPv4Address对象
    addr = ipaddress.IPv4Address(address)
    # 检查地址是否在多播范围内
    return multicast_range_start <= addr <= multicast_range_end

def handle_client(client_socket, addr):
    """
    Function to handle client connections and requests.
    """
    try:
        print(f"Connection from {addr}")
        while True:
            request = client_socket.recv(1024).decode("utf-8").strip()
            if not request:
                break
            parts = request.split()
            command = parts[0]
            if command == "getdir":
                # Send chat room directory to client
                response = str(chat_room_directory)
                client_socket.send(response.encode("utf-8"))
            elif command == "makeroom":
                # Create a new chat room
                if len(parts) != 4:
                    client_socket.send("Usage: makeroom <chat room name> <address> <port>".encode("utf-8"))
                    continue
                chat_room_name, address, port = parts[1:]
                if chat_room_name in chat_room_directory:
                    client_socket.send("A chat room with the same name already exists.".encode("utf-8"))
                    continue

                address_already_used = False
                for existing_room in chat_room_directory.values():
                    if address == existing_room[0] and port == existing_room[1]:
                        address_already_used = True
                        break

                if address_already_used:
                    client_socket.send("A chat room with the same address and port already exists.".encode("utf-8"))
                    continue

                if is_valid_multicast_address(address) and 0 < int(port) < 65536:
                    chat_room_directory[chat_room_name] = (address, port)
                    client_socket.send("Chat room created successfully".encode("utf-8"))
                else:
                    client_socket.send("Invalid address/port".encode("utf-8"))
            elif command == "deleteroom":
                # Delete an existing chat room
                if len(parts) != 2:
                    client_socket.send("Usage: deleteroom <chat room name>".encode("utf-8"))
                    continue
                chat_room_name = parts[1]
                if chat_room_name in chat_room_directory:
                    del chat_room_directory[chat_room_name]
                    client_socket.send("Chat room deleted successfully".encode("utf-8"))
                else:
                    client_socket.send("Chat room does not exist".encode("utf-8"))
            elif command == "name":
                # Set client name
                if len(parts) != 2:
                    client_socket.send("Usage: name <your name>".encode("utf-8"))
                    continue
                client_name = parts[1]
                if client_name in client_names.values():
                    client_socket.send("This name is already taken. Please choose a different name.".encode("utf-8"))
                    continue
                client_names[client_socket] = client_name
                client_socket.send(f"Your name is set to: {client_name}".encode("utf-8"))
            elif command == "chat":
                # Enter chat mode
                if len(parts) != 2:
                    client_socket.send("Usage: chat <chat room name>".encode("utf-8"))
                    continue
                chat_room_name = parts[1]
                if chat_room_name not in chat_room_directory:
                    client_socket.send("Chat room does not exist".encode("utf-8"))
                    continue
                clients_in_chat_mode[client_socket] = chat_room_name
                client_socket.send(f"Entering chat mode for chat room: {chat_room_name}".encode("utf-8"))
            elif client_socket in clients_in_chat_mode:
                chat_room_name = clients_in_chat_mode[client_socket]
                # Forward message to all clients in the same chat room
                print("Request:", request)
                if request == "^E":
                    client_socket.send("You have exited the chat.".encode("utf-8"))
                    message = f"{client_names[client_socket]} has exited chat room {clients_in_chat_mode[client_socket]}"
                    del clients_in_chat_mode[client_socket]
                    for socket, room in clients_in_chat_mode.items():
                        if room == chat_room_name and socket != client_socket:
                            socket.send(message.encode("utf-8"))
                else:
                    message = f"{client_names[client_socket]}: {request}"
                    for socket, room in clients_in_chat_mode.items():
                        if room == chat_room_name and socket != client_socket:
                            socket.send(message.encode("utf-8"))
            elif command == "bye":
                # Close the client-to-CRDS connection
                print(f"Closing connection from {addr}")
                client_socket.send("Connection closed. Bye!".encode("utf-8"))
                break
            else:
                client_socket.send("Invalid command".encode("utf-8"))
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        print(f"Connection from {addr} closed.")
        if client_socket in clients_in_chat_mode:
            del clients_in_chat_mode[client_socket]
        if client_socket in client_names:
            del client_names[client_socket]
        client_socket.close()


def start_server():
    """
    Function to start the Chat Room Directory Server (CRDS).
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(('localhost', CRDP))
        server_socket.listen(5)
        print(f"Chat Room Directory Server listening on port {CRDP}...")
        while True:
            client_socket, addr = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        server_socket.close()


def main():
    """
    Main function to start the CRDS server.
    """
    start_server()


if __name__ == "__main__":
    main()

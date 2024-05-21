import Roles.Agent as agent
import Roles.Monitor as monitor
import re
import socket

def get_valid_port(message):
    while True:
        try:
            port = int(input(message))
            if 1023 < port < 49152:
                # Additional check if port is in use (using socket)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.bind(('localhost', port))
                    sock.close()
                    return port
                except OSError:
                    print(f"Port {port} is already in use. Please try a different one.")
            else:
                print("Invalid port number. Please enter a value between 1024 and 49151.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

def get_valid_ip():
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    while True:
        ip_address = input("Enter your target IP address (IPv4): ")
        if re.search(regex, ip_address):
            return ip_address
        else:
            print("Invalid IP address. Please enter a valid IPv4 address.")

def agent_init():
    print("################################")
    port = get_valid_port("Agent: Please enter a valid port number to start the connection (1024~49151):\nPort: ")
    print("Starting listening process...")
    agent_sender = agent.agent_sender("1.1.1.1", port)
    agent_sender.sender()

def monitor_init():
    print("################################")
    host_ip = get_valid_ip()
    port = get_valid_port("Monitor: Please enter your target port number (1024~49151):\nPort: ")
    print("Establishing connection...")
    monitor_receiver = monitor.monitor_receiver(host_ip, port)
    monitor_receiver.receiver()

if __name__ == "__main__":
    # Setup Terminal
    terminate = False

    print("################################")
    print("Welcome to Bernie's End-to-End Monitor Application!\n")

    while not terminate:
        role = input("Choose a role for your further usage (A for agent, M for monitor, E to terminate the application):\nRole: ").upper()

        match role.strip():
            case 'A':
                ans = input("You have chosen to be the agent, continue? (Y/N) ").upper()
                if ans.strip() == "Y":
                    agent_init()
                else:
                    pass  # Do nothing if user cancels
            case 'M':
                ans = input("You have chosen to be the monitor, continue? (Y/N) ").upper()
                if ans.strip() == "Y":
                    monitor_init()
                else:
                    pass  # Do nothing if user cancels
            case 'E':
                terminate = True
            case _:
                print("Invalid input. Please enter a legal command (A, M, E).")

    print("Application terminated.")
    print("################################")

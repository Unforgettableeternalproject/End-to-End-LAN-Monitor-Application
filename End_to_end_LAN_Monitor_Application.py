import Roles.Agent as agent
import Roles.Monitor as monitor
import re

def agent_Init():
    print("################################")
    port = 0

    while(not (port > 1023 and port < 49152)):
        filt = input("Agent: Please enter a valid port number to start the connection. (1024~49151)\nPort:") if port != 0 else input("Please enter a VALID port number. (1024~49151)\nPort:")
        port = int(filt) if filt.isnumeric() else -1

    print("Starting listening process...")
    Agent.sender(port)

def monitor_Init():
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

    print("################################")
    host_ip = 0
    port = 0
    first = True
    while(not re.search(regex, host_ip)):
        host_ip = input("Monitor: Please enter your target ip address. (IPv4)\nHost:") if first else input("Please enter a VALID ip address. (IPv4)\nHost:")
        first = False

    while(not (port > 1023 and port < 49152)):
        filt = input("Monitor: Please enter your target port number. (1024~49151)\nPort:") if port != 0 else input("Please enter a VALID port number. (1024~49151)\nPort:")
        port = int(filt) if filt.isnumeric() else -1

    print("Establishing connection...")
    Monitor.receiver(host_ip, port)

if __name__ == "__main__":
    # Setup Terminal
    terminate = False

    Agent = agent.agent_sender()
    Monitor = monitor.monitor_receiver()

    print("################################")
    print("Welcome to Bernie's End-to-End Monitor Application!\n")
    role = input("Choose a role for your further usage. (A for agent, M for monitor, E to terminate the application)\nRole:")
    
    while(not terminate):
        match(role):
            case 'A':
                ans = input("You have chosen to be as the agent, continue? (Y/N) ")
                if(ans == "Y"):
                    agent_Init()
                else:
                    role = input("Process aborted. Please enter new role or terminate the application (A, M, E):")
                    pass
            case 'M':
                ans = input("You have chosen to be as the monitor, continue? (Y/N) ")
                if(ans == "Y"):
                    monitor_Init()
                else:
                    role = input("Process aborted. Please enter new role or terminate the application (A, M, E):")
                    pass
                pass
            case 'E':
                terminate = True
            case _: # Invalid Input
                role = input("Invalid input, please enter legal command (A, M, E):")

    print("Application terminated.")
    print("################################")
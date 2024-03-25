import cv2
import numpy as np
import socket
import pyaudio
import threading
import logging
import select
import datetime

logging.basicConfig(filename='monitor.log', level=logging.DEBUG)  # Adjust filename and level as needed


class monitor_receiver:
    def __init__(self) -> None:
        logging.info(f"################################\nTimestamp: {datetime.datetime.now()}")
        pass

    # Function to receive video stream
    def receive_video(self, client_socket):
        cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)  # Create a resizable window

        data_received = False
        buffer_size = 8192  # Adjusted buffer size to accommodate chunks
        timeout = 1  # Timeout in seconds for select.select
        received_data = bytearray()

        while True:
            try:
                # Monitor socket for readability using select.select
                readable, writable, _ = select.select([client_socket], [], [], timeout)

                if readable:
                    # Data is available on the socket

                    # Receive data size
                    data_size_bytes = client_socket.recv(4)
                    if not data_size_bytes:
                        break  # Exit the loop if no data size received

                    # Acknowledge Receiving Data Size (Optional)
                    client_socket.sendall(b'ACK')  # Send acknowledgment (ACK)

                    # Calculate expected frame size
                    expected_data_size = int.from_bytes(data_size_bytes, byteorder='big') + 1  # Add 1 for header

                    # Receive data chunk by chunk
                    total_data_received = 0
                    while total_data_received < expected_data_size:
                        data = client_socket.recv(min(expected_data_size - total_data_received, buffer_size))
                        if not data:
                            logging.error(f"Error: Incomplete chunk received. Expected {expected_data_size}, received {total_data_received}")
                            break  # Handle incomplete chunk (optional: retry receiving)
                        received_data.extend(data)
                        total_data_received += len(data)

                    # Verify complete frame data received
                    if total_data_received == expected_data_size:
                        # Complete frame received
                        frame = cv2.imdecode(np.frombuffer(received_data, dtype=np.uint8), cv2.IMREAD_COLOR)

                        # **Optional Processing:** (Uncomment and modify as needed)
                        # gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        # blur = cv2.GaussianBlur(frame, (5, 5), 0)
                        # ... (apply other processing)

                        # Display the frame
                        cv2.imshow('Video Stream', frame)

                        # Handle keyboard input (optional)
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            break

                        # Reset buffer for next frame
                        received_data = bytearray()
                    else:
                        logging.warning(f"Received incomplete frame data. Expected {expected_data_size}, received {total_data_received}")

            except Exception as e:
                logging.error(f"Error receiving video: {e}")
                break

        cv2.destroyAllWindows()

    # Main function
    def receiver(self, hostIP, hostPort):
        host = hostIP  # Agent IP address
        port = hostPort  # Port to connect to

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
        except Exception as e:
            logging.error(f"Error encountered:{e}")
            return

        print("Connection successfully established! Receiving video from agent...")

        # Start video receiving thread
        video_thread = threading.Thread(target=self.receive_video, args=(client_socket,))
        video_thread.start()

        # Wait for thread to finish
        video_thread.join()

        client_socket.close()
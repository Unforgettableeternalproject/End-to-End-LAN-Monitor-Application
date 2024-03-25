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
        received_data = bytearray()  # Buffer to accumulate received data

        while True:
            try:
                # Monitor socket for readability using select.select
                readable, writable, _ = select.select([client_socket], [], [], timeout)

                if readable:
                    # Data is available on the socket

                    # Receive chunk size
                    data_size_bytes = client_socket.recv(4)
                    if not data_size_bytes:
                        break  # Exit the loop if no data size is received
                    chunk_size = int.from_bytes(data_size_bytes, byteorder='big')
                    logging.debug(f"Received chunk size: {chunk_size}")

                    # Receive data chunk
                    data = bytearray()
                    total_received_in_chunk = 0
                    while total_received_in_chunk < chunk_size:
                        packet = client_socket.recv(min(chunk_size - total_received_in_chunk, buffer_size))
                        if not packet:
                            logging.error(f"Error: Incomplete chunk received. Expected {chunk_size}, received {total_received_in_chunk}")
                            break  # Handle incomplete chunk (optional: retry receiving)
                        data.extend(packet)
                        total_received_in_chunk += len(packet)

                    # Verify chunk size and accumulate data
                    if total_received_in_chunk != chunk_size:
                        logging.error("Error: Received incomplete chunk")
                        continue

                    # **Data Type Handling:** Not required for video-only

                    # Check if total received data size indicates a complete frame
                    total_data_received = len(received_data)
                    frame_size_bytes = client_socket.recv(4)
                    if not frame_size_bytes:
                        break  # Exit loop if no frame size received

                    frame_size = int.from_bytes(frame_size_bytes, byteorder='big')

                    if total_data_received == frame_size:
                        # Complete frame received
                        frame = cv2.imdecode(np.frombuffer(received_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        # Process or display the frame
                        cv2.imshow('Video Stream', frame)
                        # ... (Rest of video processing logic)
                        received_data = bytearray()  # Reset buffer for next frame
                    else:
                        logging.warning(f"Received incomplete frame data. Expected {frame_size}, received {total_data_received}")

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
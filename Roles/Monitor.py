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

    def receive_video(self, client_socket):
        # Set custom window dimensions (width, height)
        window_width = 800
        window_height = 500
        cv2.namedWindow('Real-time Monitor', cv2.WINDOW_NORMAL)  # Create a resizable window
        cv2.resizeWindow('Real-time Monitor', window_width, window_height)  # Set custom size


        timeout = 1  # Timeout in seconds for select.select
        buffer_size = 8192  # Adjusted buffer size to accommodate chunks
        received_data = bytearray()
        expected_data_size = 0  # Initialize expected data size outside the loop

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

                    # Send acknowledgment for data size
                    client_socket.sendall(b'ACK')  # Send ACK for data size

                    # Calculate expected frame size
                    expected_data_size = int.from_bytes(data_size_bytes, byteorder='big')

                    # Receive data chunk by chunk
                    total_data_received = 0
                    while total_data_received < expected_data_size:
                        data_to_receive = min(expected_data_size - total_data_received, buffer_size)
                        data = client_socket.recv(data_to_receive)
                        if not data:
                            logging.error(f"Error: Connection closed or incomplete chunk received. Expected {expected_data_size}, received {total_data_received}")
                            break  # Handle connection closed or incomplete chunk (optional: retry receiving)
                        received_data.extend(data)
                        total_data_received += len(data)

                    # Verify complete frame data received
                    if total_data_received == expected_data_size:
                        # Complete frame received
                        try:
                            # Decode the frame using cv2.imdecode
                            frame = cv2.imdecode(np.frombuffer(received_data, dtype=np.uint8), cv2.IMREAD_COLOR)

                            # Display the frame
                            cv2.imshow('Real-time Monitor', frame)

                            # Handle keyboard input (optional)
                            key = cv2.waitKey(1) & 0xFF
                            if key == ord('q') or cv2.getWindowProperty('Real-time Monitor', cv2.WND_PROP_AUTOSIZE) == -1:
                                break

                            # Send acknowledgment for received frame (optional)
                            # client_socket.sendall(b'ACK')  # Send ACK for received frame (Optional)

                        except Exception as e:
                            logging.error(f"Error decoding frame: {e}")

                        # Reset buffer and variables for next frame
                        received_data = bytearray()
                        expected_data_size = 0  # Reset expected size for next frame
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
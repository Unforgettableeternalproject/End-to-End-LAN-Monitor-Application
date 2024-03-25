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
        logging.info(f"################################\nTimestamp: {datetime.datetime.now().timestamp()}")
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

                    # **Data Type Handling:**
                    # Extract data type from the first byte
                    data_type = data[0]
                    if data_type == b'V':  # Video data
                        received_data.extend(data[1:])  # Add video data (excluding header)

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
                            # ...
                            received_data = bytearray()  # Reset buffer for next frame
                        else:
                            logging.warning(f"Received incomplete frame data. Expected {frame_size}, received {total_data_received}")
                    else:
                        logging.warning(f"Unexpected data type received: {data_type}")

                    # ... (Rest of video processing logic)

            except Exception as e:
                logging.error(f"Error receiving video: {e}")
                break

        cv2.destroyAllWindows()

    # Function to receive audio stream
   # Function to receive audio stream
    def receive_audio(self, client_socket):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK)

        while True:
            try:
                # Receive data with data type identifier
                data = client_socket.recv(CHUNK + 1)  # Receive data size + data
                if not data:
                    break

                # Extract data type from the first byte
                data_type = data[0]
                if data_type == b'A':  # Audio data
                    audio_data = data[1:]  # Extract audio data (excluding header)
                    stream.write(audio_data)
                else:
                    logging.warning(f"Unexpected data type received in audio stream: {data_type}")

            except Exception as e:
                logging.error(f"Error encountered receiving audio:{e}")
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

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

        print("Connection successfully established! Receiving video and audio from agent...")

        # Start threads for receiving video and audio
        # (Commented out as you requested to ignore video)
        # video_thread = threading.Thread(target=self.receive_video, args=(client_socket,))
        audio_thread = threading.Thread(target=self.receive_audio, args=(client_socket,))
        # video_thread.start()
        audio_thread.start()

        # Wait for threads to finish
        # (Commented out as you requested to ignore video)
        # video_thread.join()
        audio_thread.join()

        client_socket.close()
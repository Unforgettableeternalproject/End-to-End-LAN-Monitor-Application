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

    def receive_video(self, client_socket, data_size):
        # Set custom window dimensions (width, height)
        window_width = 800
        window_height = 500
        cv2.namedWindow('Real-time Monitor', cv2.WINDOW_NORMAL)  # Create a resizable window
        cv2.resizeWindow('Real-time Monitor', window_width, window_height)  # Set custom size

        # Define buffer size (adjust as needed)
        buffer_size = 8192

        received_data = bytearray()
        total_data_received = 0

        while total_data_received < data_size:
            data_to_receive = min(data_size - total_data_received, buffer_size)
            data = client_socket.recv(data_to_receive)
            if not data:
                logging.error(f"Error: Connection closed or incomplete chunk received. Expected {data_size}, received {total_data_received}")
                break  # Handle connection closed or incomplete chunk (optional: retry receiving)
            received_data.extend(data)
            total_data_received += len(data)

            # Verify complete frame data received and handle user input/window closing
            if total_data_received == data_size:
                try:
                    # Decode the frame using cv2.imdecode
                    frame = cv2.imdecode(np.frombuffer(received_data, dtype=np.uint8), cv2.IMREAD_COLOR)

                    # Display the frame
                    cv2.imshow('Real-time Monitor', frame)

                    # Handle keyboard input (optional)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or cv2.getWindowProperty('Real-time Monitor', cv2.WND_PROP_AUTOSIZE) == -1: break

                except Exception as e:
                    logging.error(f"Error decoding frame: {e}")

        # Reset buffer for next frame
        received_data = bytearray()
        cv2.destroyAllWindows()

    def receive_audio(self, client_socket, data_size):
        # Define audio parameters (adjust as needed)
        CHUNK = 1024  # Audio data chunk size in bytes
        FORMAT = pyaudio.paInt16  # Audio format (16-bit signed integer)
        CHANNELS = 1  # Mono audio
        RATE = 44100  # Sampling rate (44.1kHz)

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Open an audio stream for playback
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

        # Buffer to store received audio data chunks
        received_data = bytearray()
        total_data_received = 0

        while total_data_received < data_size:
            data_to_receive = min(data_size - total_data_received, CHUNK)
            data = client_socket.recv(data_to_receive)
            if not data:
                logging.error(f"Error: Connection closed or incomplete chunk received. Expected {data_size}, received {total_data_received}")
                break  # Handle connection closed or incomplete chunk (optional: retry receiving)
            received_data.extend(data)
            total_data_received += len(data)

        # Verify complete audio data received
        if total_data_received == data_size:
            try:
                # Play the received audio data
                stream.write(received_data)

            except Exception as e:
                logging.error(f"Error playing audio: {e}")

        # Close PyAudio resources
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Reset buffer for next audio frame
        received_data = bytearray()

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

        # Define buffer size (adjust as needed)
        buffer_size = 8192

        while True:
            try:
                # Monitor socket for readability using select.select
                readable, writable, _ = select.select([client_socket], [], [], 1)  # Set a timeout if desired

                if readable:
                    # Data is available on the socket

                    # Receive packet header
                    header_data = client_socket.recv(4)  # Assuming header size is 4 bytes
                    if not header_data:
                        break  # Exit the loop if no header received

                # Extract data type and payload size from header
                    data_type = header_data.decode('utf-8')
                    data_size = int.from_bytes(client_socket.recv(4), byteorder='big')

                    # Receive data based on data type
                    if data_type == 'video':
                        self.receive_video(client_socket, data_size)  # Call video receive function
                    elif data_type == 'audio':
                        self.receive_audio(client_socket, data_size)  # Call audio receive function (not shown)
                    else:
                        logging.warning(f"Unknown data type received: {data_type}")

                    # Send acknowledgment (ACK) for received packet (sender implementation handles retransmission)
                    client_socket.sendall(b'ACK')

            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                break
            #cv2.destroyAllWindows()

        client_socket.close()
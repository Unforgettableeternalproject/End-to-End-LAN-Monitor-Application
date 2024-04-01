import cv2
import numpy as np
import socket
import pyaudio
import threading
import logging
import select
import datetime

logging.basicConfig(filename='monitor.log', level=logging.DEBUG)  # Adjust filename and level as needed
HEADER_SIZE = 9

class DataBuffer:
    def __init__(self, buffer_size):
        self.buffer = bytearray(buffer_size)
        self.head = 0  # Index of the first element in the buffer
        self.tail = 0  # Index of the next element to be inserted
        self.buffer_size = buffer_size
        self.lock = threading.Lock()  # Lock for thread-safe access

    def is_empty(self):
        return self.head == self.tail

    def is_full(self):
        return (self.tail + 1) % self.buffer_size == self.head

    def put(self, data):
        self.lock.acquire()
        while self.is_full():
            # Implement handling for buffer overflow (e.g., wait, drop data)
            pass
        self.buffer[self.tail] = data
        self.tail = (self.tail + 1) % self.buffer_size
        self.lock.release()

    def get(self):
        self.lock.acquire()
        while self.is_empty():
            # Implement handling for empty buffer (e.g., wait)
            pass
        data = self.buffer[self.head]
        self.head = (self.head + 1) % self.buffer_size
        self.lock.release()
        return data
  
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

        while True:
            try:
                # Monitor socket for readability using select.select
                readable, writable, _ = select.select([client_socket], [], [], 1)  # Set a timeout if desired
                print("Readable" if readable else "Not Readable")
                if readable:
                    # Data is available on the socket

                    # Receive packet header
                    header_data = client_socket.recv(HEADER_SIZE)
                    if not header_data:
                        break  # Exit the loop if no header received

                    # Extract data type and payload size from header
                    sequence_number = int.from_bytes(header_data[0:2], byteorder='big')
                    data_type_bytes = header_data[2:7]  # Assuming fixed data type field at position 2-6
                    data_type = data_type_bytes.rstrip(b'\0').decode('utf-8')  # Remove trailing null bytes
                    #data_type = header_data[2:3].decode('utf-8')  # Assuming 1-byte data type
                    data_size = int.from_bytes(header_data[7:9], byteorder='big')

                    logging.info(f"Sequence Number: {sequence_number}")
                    print(f"The received data type is {data_type}, also data size is {data_size}")
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
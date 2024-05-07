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
METADATA_SIZE = 2

class DataBuffer:
    def __init__(self, buffer_size):
        self.buffer = bytearray(buffer_size)
        self.head = 0 
        self.tail = 0 
        self.buffer_size = buffer_size
        self.lock = threading.Lock()
        self.space_available = threading.Condition(self.lock)
        self.data_available = threading.Condition(self.lock)

    def is_empty(self):
        return self.head == self.tail

    def is_full(self):
        return (self.tail + 1) % self.buffer_size == self.head

    def put(self, data):
        with self.space_available:
            while self.is_full():
                logging.warning("Buffer overflow! Waiting for space.")
                self.space_available.wait()
            for byte in data:
                self.buffer[self.tail] = byte
                self.tail = (self.tail + 1) % self.buffer_size
            self.data_available.notify()

    def get(self):
        with self.data_available:
            while self.is_empty():
                logging.warning("Buffer empty! Waiting for data.")
                self.data_available.wait()
            data = bytes(self.buffer)
            self.head = (self.head + 1) % self.buffer_size
            self.space_available.notify()
        return data
  
class monitor_receiver:
    def __init__(self) -> None:
        logging.info(f"################################\nTimestamp: {datetime.datetime.now()}")
        pass

    def receive_video(self, client_socket, video_buffer, data_size, total_chunks, sequence_number):
        try:
            chunk_size = 1024

            received_chunks = 0
            frame_data = bytearray()

            while received_chunks < total_chunks:
                # Receive video chunk from the sender
                chunk = client_socket.recv(chunk_size)

                # Send acknowledgment (ACK) for received packet (sender implementation handles retransmission)
                ack_data = sequence_number.to_bytes(2, byteorder='big')
                client_socket.sendall(ack_data)
                if not chunk:
                    break

                # Put received chunk into the frame data
                frame_data.extend(chunk)

                received_chunks += 1

            # Reconstruct and display the frame if all chunks for the frame have been received
            if received_chunks == total_chunks:
                received_chunks = 0
                frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                cv2.imshow('Real-time Monitor', frame)
                cv2.waitKey(1)


        except Exception as e:
            logging.error(f"Error receiving video: {e}")

    def receive_audio(self, client_socket, audio_buffer, data_size):
        received_data = 0
        
        while received_data < data_size:
          data_to_receive = min(data_size - received_data, audio_buffer.buffer_size)
          data = client_socket.recv(data_to_receive)
          if not data:
            logging.error(f"Error: Connection closed or incomplete chunk received. Expected {data_size}, received {received_data}")
            break
          received_data += len(data)

          # Put received data into the audio buffer
          audio_buffer.put(data)

        # Playback Thread (replace with actual implementation)
        def play_audio():
          # Define audio parameters (adjust as needed)
          CHUNK = 1024  # Audio data chunk size in bytes
          FORMAT = pyaudio.paInt16  # Audio format (16-bit signed integer)
          CHANNELS = 1  # Mono audio
          RATE = 44100  # Sampling rate (44.1kHz)

          # Initialize PyAudio
          audio = pyaudio.PyAudio()

          # Open an audio stream for playback
          stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

          while not audio_buffer.is_empty():
            try:
              # Get a chunk of audio data from the buffer
              audio_data = audio_buffer.get()

              # Play the audio data
              stream.write(audio_data)

            except Exception as e:
              logging.error(f"Error playing audio: {e}")
              break

          # Close PyAudio resources
          stream.stop_stream()
          stream.close()
          audio.terminate()

        # Start the playback thread
        playback_thread = threading.Thread(target=play_audio)
        playback_thread.start()

        # Wait for the playback thread to finish (optional)
        playback_thread.join()

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

        # Initialize video buffer and decoding thread
        video_buffer = DataBuffer(buffer_size=131071)

        while True:
            try:
                # Monitor socket for readability using select.select
                readable, _, _ = select.select([client_socket], [], [], 1)
                if readable:
                    # Data is available on the socket

                    # Receive packet header
                    header_data = client_socket.recv(HEADER_SIZE)
                    metadata = client_socket.recv(METADATA_SIZE)
                    if not header_data:
                        break  # Exit the loop if no header received

                    # Extract data type and payload size from header
                    sequence_number = int.from_bytes(header_data[0:2], byteorder='big')
                    data_type_bytes = header_data[2:7]  # Assuming fixed data type field at position 2-6
                    data_type = data_type_bytes.rstrip(b'\0').decode('utf-8')  # Remove trailing null bytes
                    data_size = int.from_bytes(header_data[7:9], byteorder='big')

                    total_chunks = int.from_bytes(metadata, byteorder='big')  # Extract total number of chunks

                    logging.info(f"Sequence Number: {sequence_number}")
                    print(f"The received data type is {data_type}, also data size is {data_size}")
                    print(total_chunks)
                    # Receive data based on data type
                    if data_type == 'video':
                        self.receive_video(client_socket, video_buffer, data_size, total_chunks, sequence_number)  # Call video receive function
                    elif data_type == 'audio':
                        # Ignored
                        pass
                    else:
                        logging.warning(f"Unknown data type received: {data_type}")

            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                break

        client_socket.close()
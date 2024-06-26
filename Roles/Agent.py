import cv2
import numpy as np
import socket
import threading
import logging
import datetime
import pyaudio

class agent_sender:
    def __init__(self):
        logging.basicConfig(filename='agent_sender.log', level=logging.DEBUG)  # Adjust filename and level as needed
        logging.info(f"################################\nTimestamp: {datetime.datetime.now().timestamp()}")
        self.sequence_number = 0  # Initialize sequence number
        self.expected_ack = 0  # Expected acknowledgment number

    def capture_video(self, client_socket):
        cap = cv2.VideoCapture(0)  # Open default camera

        try:
            while True:
                ret, frame = cap.read()
                if not ret: break

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            video_data = buffer.tobytes()

            # Send video data using send_data function with flow control
            self.send_data(client_socket, 'video', video_data)

        except Exception as e:
            logging.error(f"Error encountered in capturing video: {e}")

        finally:
            # Release resources
            cap.release()

    def capture_audio(self, client_socket):
        import pyaudio

        # Define audio parameters (adjust as needed)
        CHUNK = 1024  # Audio data chunk size in bytes
        FORMAT = pyaudio.paInt16  # Audio format (16-bit signed integer)
        CHANNELS = 1  # Mono audio
        RATE = 44100  # Sampling rate (44.1kHz)

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Open an audio stream for recording
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

        try:
            while True:
            # Read audio data from microphone
                data = stream.read(CHUNK)
            # Send audio data using send_data function with flow control
                self.send_data(client_socket, 'audio', data)

        except Exception as e:
            logging.error(f"Error encountered in capturing audio: {e}")

        finally:
            # Close PyAudio resources
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def send_data(self, client_socket, data_type, data):
        # Define packet header size (adjust as needed)
        HEADER_SIZE = 4

        # Generate unique sequence number
        sequence_number = self.get_next_sequence_number()

        # Create packet header
        header = (
            sequence_number.to_bytes(2, byteorder='big') +  # 2-byte sequence number
            data_type.encode('utf-8') +                     # Data type (video/audio)
            len(data).to_bytes(HEADER_SIZE - 2, byteorder='big')  # Payload size (optional)
        )

        # Combine header and data
        packet = header + data

        # Implement flow control with cumulative ACKs
        while sequence_number >= self.expected_ack:  # Loop until expected ACK is received
            # Send packet
            client_socket.sendall(packet)

            # Receive acknowledgment (blocking)
            ack_data = client_socket.recv(HEADER_SIZE)
            if not ack_data:
                logging.error("Connection closed by receiver.")
                break

            # Extract received acknowledgment number
            received_ack = int.from_bytes(ack_data, byteorder='big')

            # Update expected ACK based on received ACK
            self.expected_ack = min(received_ack + 1, sequence_number + 1)  # Handle potential packet loss

    def get_next_sequence_number(self):
        self.sequence_number = (self.sequence_number + 1) % (1 << 16)  # Wrap around after reaching max value (2^16 - 1)
        return self.sequence_number

    # Main function
    def sender(self, startingPort):
        host = '0.0.0.0'  # Server IP address
        port = startingPort  # Port to listen on

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)

        print("Agent is waiting for a connection...")

        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established. Streaming video and audio...")

        # Start threads for video and audio capture, passing the client socket
        video_thread = threading.Thread(target=self.capture_video, args=(client_socket,))
        audio_thread = threading.Thread(target=self.capture_audio, args=(client_socket,))

        # Start threads
        video_thread.start()
        audio_thread.start()

        # Wait for threads to finish
        video_thread.join()
        audio_thread.join()

        # Close connections and socket
        client_socket.close()
        server_socket.close()

        print("Streaming stopped.")

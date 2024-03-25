import cv2
import numpy as np
import socket
import pyaudio
import threading
import logging

logging.basicConfig(filename='monitor.log', level=logging.DEBUG)  # Adjust filename and level as needed

class monitor_receiver:
    def __init__(self) -> None:
        pass

    # Function to receive video stream
    def receive_video(self, client_socket):
        cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)  # Create a resizable window
        data_received = False  # Flag to track if data has been received
        buffer_size = 4096  # Adjust buffer size if needed

        while True:
            try:
                # Receive data size
                data_size_bytes = client_socket.recv(4)
                if not data_size_bytes:
                    break  # Exit the loop if no data size is received
                data_size = int.from_bytes(data_size_bytes, byteorder='big')
                logging.debug(f"Received data size: {data_size}")

                # Receive data
                data = bytearray()
                total_received = 0
                while total_received < data_size:
                    packet = client_socket.recv(min(data_size - total_received, buffer_size))
                    if not packet:
                        break
                    data.extend(packet)
                    total_received += len(packet)

                # Verify data size and decode frame
                if total_received != data_size:
                    logging.error("Error: Received incomplete data")
                    continue
                frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    logging.debug(f"Decoded frame: {frame.shape}")
                    cv2.imshow('Video Stream', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except Exception as e:
                logging.error("Error receiving video:", e)
                break

        cv2.destroyAllWindows()

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
                data = client_socket.recv(CHUNK)
                if not data:
                    break
                stream.write(data)
            except Exception as e:
                logging.error("Error encountered:", e)
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
            logging.error("Error encountered:", e)
            return

        print("Connection successfully established! Receiving video and audio from agent...")

        # Start threads for receiving video and audio
        video_thread = threading.Thread(target=self.receive_video, args=(client_socket,))
        audio_thread = threading.Thread(target=self.receive_audio, args=(client_socket,))
        video_thread.start()
        audio_thread.start()
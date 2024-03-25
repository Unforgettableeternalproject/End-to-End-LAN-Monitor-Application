import cv2
import numpy as np
import socket
import pyaudio
import threading

class agent_sender:
    def __init__(self) -> None:
        pass

    # Function to handle video streaming
    def send_video(self, client_socket):
        cap = cv2.VideoCapture(0)  # Open default camera (index 0)
        while True:
            ret, frame = cap.read()  # Read a frame from the camera
            if not ret:
                break
            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()
            # Send the size of the frame first
            client_socket.sendall(len(data).to_bytes(4, byteorder='big'))
            # Send the frame data
            client_socket.sendall(data)
        cap.release()

    # Function to handle audio streaming
    def send_audio(self, client_socket):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        while True:
            try:
                data = stream.read(CHUNK)
                client_socket.sendall(data)
            except:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

    # Main function
    def sender(self, startingPort):
        host = '0.0.0.0'  # Server IP address
        port = startingPort       # Port to listen on

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)

        print("Agent is waiting for a connection...")

        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established. Streaming video and audio...")

        # Start threads for video and audio streaming
        video_thread = threading.Thread(target=self.send_video, args=(client_socket,))
        audio_thread = threading.Thread(target=self.send_audio, args=(client_socket,))
        video_thread.start()
        audio_thread.start()

        video_thread.join()
        audio_thread.join()

        client_socket.close()
        server_socket.close()
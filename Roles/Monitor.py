import cv2
import numpy as np
import socket
import pyaudio
import threading

class monitor_receiver:
    def __init__(self) -> None:
        pass
    # Function to receive video stream
    def receive_video(self, client_socket):
        while True:
            # Receive the size of the frame
            data_size = int.from_bytes(client_socket.recv(4), byteorder='big')
            print("Received data size:", data_size)
            # Receive the frame data
            data = b''
            while len(data) < data_size:
                packet = client_socket.recv(min(data_size - len(data), 4096))
                if not packet:
                    break
                data += packet
            if not data:
                break
            print("Received frame data:", len(data))
            # Convert the received data to an image
            frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                print("Error decoding frame")
                continue
            print("Decoded frame:", frame.shape)
            # Display the frame
            cv2.imshow('Video Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    def receive_video_test(self, client_socket):
        while True:
            # Create a test image
            frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Black image (480x640 pixels)
            frame[240, :] = [0, 0, 255]  # Draw a red line in the middle

            # Display the test image
            cv2.imshow('Test Image', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
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
                print("Error encountered:", e)
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

    # Main function
    def receiver(self, hostIP, hostPort):
        host = hostIP    # Agent IP address
        port = hostPort  # Port to connect to

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
        except Exception as e:
            print("Error encountered:", e)
            return

        print("Connection successfully established! Receiving video and audio from agent...")

        # Start threads for receiving video and audio
        video_thread = threading.Thread(target=self.receive_video, args=(client_socket,))
        audio_thread = threading.Thread(target=self.receive_audio, args=(client_socket,))
        video_thread.start()
        audio_thread.start()

        video_thread.join()
        audio_thread.join()

        client_socket.close()
        cv2.destroyAllWindows()
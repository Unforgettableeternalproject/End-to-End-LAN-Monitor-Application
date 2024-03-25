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
        cap = cv2.VideoCapture(0)  # Open default camera

        try:
            while True:
                # Read a frame from the camera
                ret, frame = cap.read()
                if not ret:
                    break

                # Encode the frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                data = buffer.tobytes()

                # Break data into chunks (e.g., 4096 bytes)
                chunk_size = 4096
                chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

                # Send each chunk with its size prefix
                for chunk in chunks:
                    chunk_size = len(chunk)
                    client_socket.sendall(chunk_size.to_bytes(4, byteorder='big'))  # Send chunk size first
                    client_socket.sendall(chunk)  # Send the chunk data
        except Exception as e:
            print(f"Error encountered in sending video: {e}")

        finally:
            # Release resources
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
        running = True

        while running:
            try:
                data = stream.read(CHUNK)
                client_socket.sendall(data)
            except Exception as e:
                print(f"Error encountered in sending audio:{e}")
                running = False  # Set flag to stop the loop

        # Close stream and terminate PyAudio
        stream.stop_stream()
        stream.close()
        p.terminate()

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

        # Start threads for video and audio streaming
        video_thread = threading.Thread(target=self.send_video, args=(client_socket,))
        audio_thread = threading.Thread(target=self.send_audio, args=(client_socket,))
        video_thread.start()
        audio_thread.start()

        # Wait for threads to finish
        video_thread.join()
        audio_thread.join()

        # Close connections and sockets
        client_socket.close()
        server_socket.close()

import cv2
import numpy as np
import socket
import threading
import logging
import datetime

class agent_sender:
    def __init__(self):
        logging.basicConfig(filename='agent_sender.log', level=logging.DEBUG)  # Adjust filename and level as needed
        logging.info(f"################################\nTimestamp: {datetime.datetime.now().timestamp()}")

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

                # Prepend data type header to each chunk
                chunk_size = 4096
                chunks = [b'V' + data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]  # Header for every chunk

                # Send each chunk with its size prefix
                for chunk in chunks:
                    chunk_size = len(chunk)
                    client_socket.sendall(chunk_size.to_bytes(4, byteorder='big'))  # Send chunk size first
                    client_socket.sendall(chunk)  # Send the chunk data
        except Exception as e:
            logging.error(f"Error encountered in sending video: {e}")

        finally:
            # Release resources
            cap.release()

    # Main function
    def sender(self, startingPort):
        host = '0.0.0.0'  # Server IP address
        port = startingPort  # Port to listen on

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)

        print("Agent is waiting for a connection...")

        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established. Streaming video...")

        # Start thread for video streaming
        video_thread = threading.Thread(target=self.send_video, args=(client_socket,))
        video_thread.start()

        # Wait for thread to finish
        video_thread.join()

        # Close connections and sockets
        client_socket.close()
        server_socket.close()
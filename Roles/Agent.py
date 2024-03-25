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

                # Send data size and wait for acknowledgment (ACK)
                client_socket.sendall(len(data).to_bytes(4, byteorder='big'))  # Send total data size
                ack = client_socket.recv(4)  # Wait for ACK (4 bytes)
                if not ack or ack != b'ACK':
                    logging.error("Failed to receive acknowledgment. Retrying...")
                    continue  # Retry on missing or incorrect ACK

                # Send data
                client_socket.sendall(data)

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

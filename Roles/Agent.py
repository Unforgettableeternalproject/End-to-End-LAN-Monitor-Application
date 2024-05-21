import socket
import cv2
import numpy as np
import threading
import time
import logging

HEADER_SIZE = 9  # Adjusted header size
CHUNK_SIZE = 8192  # Adjust as needed

class agent_sender:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sequence_number = 0

    def get_next_sequence_number(self):
        self.sequence_number = (self.sequence_number + 1) % 65536
        return self.sequence_number

    def send_data(self, client_socket, data_type, data, is_header=False):
        # Generate unique sequence number
        sequence_number = self.get_next_sequence_number()

        data_type_bytes = data_type.encode('utf-8')[:5].ljust(5, b'\0')  # Pad to 5 bytes
        header = (
            sequence_number.to_bytes(2, byteorder='big') +
            data_type_bytes +
            len(data).to_bytes(2, byteorder='big')
        )

        # Combine header and data
        packet = header + data

        # Send packet
        client_socket.sendall(packet)

        if not is_header:
            # Implement acknowledgment (ACK) mechanism
            ack_received = False
            while not ack_received:
                try:
                    ack_data = client_socket.recv(2)
                    if not ack_data:
                        logging.error("Connection closed by receiver.")
                        break

                    received_ack = int.from_bytes(ack_data, byteorder='big')
                    if received_ack == sequence_number:
                        ack_received = True
                    else:
                        client_socket.sendall(packet)

                except Exception as e:
                    logging.error(f"Error receiving ACK: {e}")
                    break

    def capture_video(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Error opening video capture.")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.server_ip, self.server_port))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                _, buffer = cv2.imencode('.jpg', frame)
                video_data = buffer.tobytes()

                # Process the captured frame
                self.process_frame(client_socket, video_data)

                time.sleep(0.1)  # Adjust the sleep time as needed

        cap.release()
        cv2.destroyAllWindows()

    def process_frame(self, client_socket, video_data):
        total_chunks = (len(video_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        metadata = total_chunks.to_bytes(2, byteorder='big')  # Encode total number of chunks as metadata

        try:
            # Send header and metadata first
            self.send_data(client_socket, 'video_chunk', metadata, is_header=True)

            # Send the video chunks
            for i in range(0, len(video_data), CHUNK_SIZE):
                chunk = video_data[i:i + CHUNK_SIZE]
                self.send_data(client_socket, 'video_chunk', chunk)

        except Exception as e:
            logging.error(f"Error while sending video: {e}")

    def sender(self):
        video_thread = threading.Thread(target=self.capture_video)
        video_thread.start()
        video_thread.join()  # Adjust as needed for other data types (e.g., audio)

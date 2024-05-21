import socket
from telnetlib import IP
import threading
import logging
import cv2
import numpy as np
import select

HEADER_SIZE = 9
CHUNK_SIZE = 8192
METADATA_SIZE = 2

class DataBuffer:
    def __init__(self, buffer_size):
        self.buffer = bytearray(buffer_size)
        self.head = 0
        self.tail = 0
        self.chunk_count = 0
        self.buffer_size = buffer_size
        self.lock = threading.Lock()
        self.space_available = threading.Condition(self.lock)
        self.data_available = threading.Condition(self.lock)

    def is_empty(self):
        return self.head == self.tail

    def is_full(self):
        return (self.tail + 1) % self.buffer_size == self.head

    def is_complete_frame(self, total_chunks):
        return self.chunk_count == total_chunks

    def clear_all(self):
        self.head = 0
        self.tail = 0
        self.chunk_count = 0

    def put(self, data):
        with self.space_available:
            while self.is_full():
                logging.warning("Buffer overflow! Waiting for space.")
                self.space_available.wait()
            for byte in data:
                self.buffer[self.tail] = byte
                self.tail = (self.tail + 1) % self.buffer_size
            self.chunk_count += 1
            self.data_available.notify()

    def get(self, size):
        with self.data_available:
            while self.is_empty():
                logging.warning("Buffer empty! Waiting for data.")
                self.data_available.wait()
            data = self.buffer[:size]
            self.clear_all()
            self.space_available.notify()
        return data

class monitor_receiver:
    def __init__(self, host_ip, port):
        logging.basicConfig(filename='monitor.log', level=logging.DEBUG)
        self.host_ip = host_ip
        self.port = port
        self.expected_sequence_number = 0
        
    def receive_video(self, client_socket, video_buffer, total_chunks, sequence_number):
        try:
            while not video_buffer.is_complete_frame(total_chunks):
                chunk_data = client_socket.recv(CHUNK_SIZE)
                if not chunk_data:
                    break
                video_buffer.put(chunk_data)

            if video_buffer.is_complete_frame(total_chunks):
                frame_data = video_buffer.get(total_chunks * CHUNK_SIZE)
                frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow('Real-time Monitor', frame)
                    cv2.waitKey(1)
                else:
                    logging.error("Failed to decode frame.")

                # Send acknowledgment (ACK) for received packet (sender implementation handles retransmission)
                ack_data = sequence_number.to_bytes(2, byteorder='big')
                client_socket.sendall(ack_data)

        except Exception as e:
            logging.error(f"Error receiving video: {e}")

    def receiver(self):
        host = self.host_ip
        port = self.port

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
        except Exception as e:
            logging.error(f"Error encountered: {e}")
            return

        print("Connection successfully established! Receiving video and audio from agent...")

        video_buffer = DataBuffer(buffer_size=262142)

        while True:
            try:
                readable, _, _ = select.select([client_socket], [], [], 1)
                if readable:
                    header_data = client_socket.recv(HEADER_SIZE)
                    if not header_data:
                        break

                    sequence_number = int.from_bytes(header_data[0:2], byteorder='big')
                    data_type_bytes = header_data[2:7]
                    data_type = data_type_bytes.rstrip(b'\0').decode('utf-8')
                    data_size = int.from_bytes(header_data[7:9], byteorder='big')

                    if data_type == 'video_chunk':
                        metadata = client_socket.recv(METADATA_SIZE)
                        total_chunks = int.from_bytes(metadata, byteorder='big')
                        self.receive_video(client_socket, video_buffer, total_chunks, sequence_number)
                    elif data_type == 'audio':
                        # Handle audio data if needed
                        pass
                    else:
                        logging.warning(f"Unknown data type received: {data_type}")

            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                break

        client_socket.close()
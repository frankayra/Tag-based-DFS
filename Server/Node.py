# Function to hash a string using SHA-1 and return its integer representation

import hashlib, socket


def getShaRepr(data: str):
        return int(hashlib.sha1(data.encode()).hexdigest(), 16)
class NodeReference:
    def __init__(self, ip: str, port: int = 8001):
        self.id = 
        self.ip = ip
        self.port = port    
    
    
    # Internal method to send data to the referenced node
    def _send_data(self, op: int, data: str = None) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip, self.port))
                s.sendall(f'{op},{data}'.encode('utf-8'))
                return s.recv(1024)
        except Exception as e:
            print(f"Error sending data: {e}")
            return b''
    
    # Method to store a key-value pair in the current node
    def store_key(self, key: str, value: str):
        self._send_data(STORE_KEY, f'{key},{value}')
    
    def __str__(self) -> str:
        return f'{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)


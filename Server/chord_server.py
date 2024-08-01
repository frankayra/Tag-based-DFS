
import socket
import hashlib

M = 160

class ChordNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.id = create_node_id(ip, port)
        self.successor = self
        self.predecessor = None
        self.finger_table = [self] * M

    def find_successor(self, key):
        if self.id <= self.successor.id:
            if self.id < key <= self.successor.id:
                return self.successor
            else:
                return self.finger_table_closest_node(key).find_successor(key)
        else:
            if self.id < key or key <= self.successor.id:
                return self.successor
            else:
                return self.finger_table_closest_node(key).find_successor(key)

    def finger_table_closest_node(self, key):
        for i in range(M-1, -1, -1):
            if self.id < self.finger_table[i].id < key:
                return self.finger_table[i]
        return self

    def join(self, existing_node):
        if existing_node:
            self.successor = existing_node.find_successor(self.id)
        else:
            self.predecessor = self
            self.successor = self
            for i in range(M):
                self.finger_table[i] = self

    def stabilize(self):
        x = self.successor.predecessor
        if x and (self.id < x.id < self.successor.id):
            self.successor = x
        self.successor.notify(self)

    def notify(self, node):
        if not self.predecessor or (self.predecessor.id < node.id < self.id):
            self.predecessor = node

    def fix_fingers(self):
        for i in range(M):
            self.finger_table[i] = self.find_successor((self.id + 2**i) % (2**M))




def create_node_id(ip, port):
    hash_object = hashlib.sha1(f'{ip}:{port}'.encode())
    return int(hash_object.hexdigest(), 16) % (2 ** M)

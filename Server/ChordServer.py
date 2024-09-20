import time
import random
from hashlib import sha1
import socket
from concurrent import futures


import logging
import grpc


from gRPC import communication_pb2 as communication_messages
from gRPC import communication_pb2_grpc as communication
from DB import File_Tag_DB, Files_References_DB
from . import ClientAPIServer

class ChordServer(communication.ChordNetworkCommunicationServicer):
    def __init__(self, port:int = 50052, nodes_count:int = 8):
        pass

import time
import os
import asyncio
from pathlib import Path
from threading import Thread

import grpc

from gRPC import communication_pb2 as communication_messages
from gRPC import communication_pb2_grpc as communication
from DB import File_Tag_DB, Files_References_DB

class ChordNodeReference:
    def __init__(self, ip:str, port:int, id:int):
        self.id = id
        self.ip = ip
        self.port = port
    @property
    def uri_address(self):
        return f"{self.ip}:{self.port}"
    @property
    def hash_code(self):
        return int(sha1((self.ip + str(self.port)).encode('utf-8')).hexdigest(), 16)
    @property
    def grpc_format(self):
        return communication_messages.ChordNodeReference(id=self.id, ip=self.ip, port=self.port)
    
class ChordClient:
    def __init__(self, nodes_count:int = 8): pass








# Operaciones fundamentales de comunicacion
# ----------------------------------
    def succesor(self, node_reference:ChordNodeReference, searching_id, requested_operation, operation_id): 
        address = node_reference.uri_address
        with grpc.insecure_channel(address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            request_message = communication_messages.RingOperationRequest(requesting_node=node_reference.grpc_format, searching_id=searching_id, requested_operation=requested_operation, operation_id=operation_id)
            try:
                response = stub.succesor(request_message)
                return response.success
            except Exception as e:
                print(f"Error controlado en ChordClient: {e}")
                return None
    def proceed_with_operation(self, self_node_reference, requesting_node_reference:ChordNodeReference, searching_id, requested_operation, operation_id):
        # if node_reference == self.node_reference:               Esto no deberia ocurrir ya que sera chequeado en metodos antes de llamar a este, en ClientAPIServer.
        with grpc.insecure_channel(requesting_node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            request_message = communication_messages.OperationDescription(requested_operation=requested_operation, node_reference=self_node_reference, id_founded=searching_id, operation_id=operation_id)
            response = stub.proceed_with_operation(request_message)
            if not response.success:
                print("Se hizo una solicitud de operacion al servidor pero este no tenia operaciones pendientes")
    def RetakePendingOperation(self, node_reference, operation, info):
        """Se realiza esta operacion luego de que el servidor reciba una solicitud 'proceed_with_operation'. """
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            match operation:

                # CRUD
                case communication_messages.LIST:
                    return stub.list(info)
                case communication_messages.FILE_CONTENT:
                    return stub.file_content(info)
                case communication_messages.ADD_FILES:
                    return stub.add_files(info)
                case communication_messages.ADD_TAGS:
                    return stub.add_tags(info)
                case communication_messages.DELETE:
                    return stub.delete(info)
                case communication_messages.DELETE_TAGS:
                    return stub.delete_tags(info)

                # Replication y referencias
                case communication_messages.ADD_REFERENCES:
                    return stub.add_references(info)
                case communication_messages.DELETE_FILES_REFERENCES:
                    return stub.delete_files_references(info)

                # Actualizar Referencias y Replicas (Modificacion de Tags)
                case communication_messages.ADD_TAGS_TO_REFERED_FILES:
                    return stub.add_tags_to_refered_files(info)
                case communication_messages.DELETE_TAGS_FROM_REFERED_FILES:
                    return stub.delete_tags_from_refered_files(info)

                # Entrada de un nodo a la red
                case communication_messages.NODE_ENTRANCE_REQUEST:
                    return stub.node_entrance_request(info)

                # Actualizar finger tables
                case communication_messages.UPDATE_FINGER_TABLE:
                    return stub.update_finger_table(info)
                

# CRUD
# ----------------------------------
    # def list(self, stub, info): pass
    # def file_content(self, stub, info): pass
    # def add_files(self, stub, node_reference, info): pass
    # def add_tags(self, stub, node_reference, info): pass
    # def delete(self, stub, node_reference, info): pass
    # def delete_tags(self, stub, node_reference, info): pass
    

# Replication y referencias
# ----------------------------------
    def replicate(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.replicate(info)
    def send_raw_database_replica(self, stub, node_reference, info):
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.send_raw_database_replica(info)
    # def add_references(self, stub, node_reference, info): pass
    def delete_files_replicas(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.delete_files_replicas(info)
    # def delete_files_references(self, stub, node_reference, info): pass


# Actualizar Referencias y Replicas (Modificacion de Tags)
# ----------------------------------
    # def add_tags_to_refered_files(self, stub, node_reference, info): pass
    def add_tags_to_replicated_files(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.add_tags_to_replicated_files(info)
    # def delete_tags_from_refered_files(self, stub, node_reference, info): pass
    def delete_tags_from_replicated_files(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.delete_tags_from_replicated_files(info)


# Protocolo Heartbeat y AliveRequest (para replicas y nodos proximos respectivamente)
# ----------------------------------
    def heartbeat(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.heartbeat(info)
    def alive_request(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.alive_request(info)
    def unreplicate(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.unreplicate(info)


# Entrada de un nodo a la red
# ----------------------------------
    # def node_entrance_request(self, stub, node_reference, info): pass
    def i_am_your_next(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.i_am_your_next(info)
    def update_next(self, stub, node_reference, info):
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_next(info)
    def files_allotment_transfer(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.files_allotment_transfer(info)
    def update_replication_clique(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_replication_clique(info)


# Salida de un nodo de la red
# ----------------------------------
    def i_am_your_prev(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.i_am_your_prev(info)


# Actualizar finger tables
# ----------------------------------
    def update_finger_table(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_finger_table(info)
    def update_finger_table_forward(self, stub, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_finger_table_forward(info)


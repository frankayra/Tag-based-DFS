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
    def __hash__(self):
        return hash(f"{self.id}:{self.ip}:{self.port}")
    def __eq__(self, node):
        return isinstance(node, ChordNodeReference) and self.id == node.id and self.ip == node.ip and self.port == node.port
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



# Operaciones fundamentales de comunicacion
# ----------------------------------
    def succesor(self, requesting_node:ChordNodeReference, node_reference:ChordNodeReference, searching_id, requested_operation, operation_id): 
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de succesor")
        address = node_reference.uri_address
        with grpc.insecure_channel(address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            request_message = communication_messages.RingOperationRequest(requesting_node=requesting_node.grpc_format, searching_id=searching_id, requested_operation=requested_operation, operation_id=operation_id)
            # try:
            response = stub.succesor(request_message)
            return response.success
            # except Exception as e:
            #     print(f"Error controlado en ChordClient: {e}")
            #     return None
    def proceed_with_operation(self, self_node_reference:ChordNodeReference, requesting_node_reference:ChordNodeReference, searching_id, requested_operation, operation_id):
        print(f"📡 solicitud a {requesting_node_reference.ip}:{requesting_node_reference.port} de proceed_with_operation.")
        with grpc.insecure_channel(requesting_node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            request_message = communication_messages.OperationDescription(requested_operation=requested_operation, node_reference=self_node_reference.grpc_format, id_founded=searching_id, operation_id=operation_id)
            response = stub.proceed_with_operation(request_message)
            if not response.success:
                print("Se hizo una solicitud de operacion al servidor pero este no tenia operaciones pendientes")
    def RetakePendingOperation(self, node_reference, operation, info):
        """Se realiza esta operacion luego de que el servidor reciba una solicitud 'proceed_with_operation'. """
        print(f"📡 retomando operacion... Envio de la operacion {operation} a {node_reference.ip}:{node_reference.port}.")

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
                case communication_messages.UPDATE_FINGER_TABLE_FORWARD:
                    return stub.update_finger_table_forward(info)

                # Comprobaciones de red
                case communication_messages.JUST_CHECKING:
                    return node_reference, info
                

# CRUD
# ----------------------------------
    # def list(self, info): pass
    # def file_content(self, info): pass
    # def add_files(self, node_reference, info): pass
    # def add_tags(self, node_reference, info): pass
    # def delete(self, node_reference, info): pass
    # def delete_tags(self, node_reference, info): pass
    

# Replication y referencias
# ----------------------------------
    def replicate(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.replicate(info)
    def send_raw_database_replica(self, node_reference, info):
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.send_raw_database_replica(info)
    # def add_references(self, node_reference, info): pass
    def delete_files_replicas(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.delete_files_replicas(info)
    # def delete_files_references(self, node_reference, info): pass


# Actualizar Referencias y Replicas (Modificacion de Tags)
# ----------------------------------
    # def add_tags_to_refered_files(self, node_reference, info): pass
    def add_tags_to_replicated_files(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.add_tags_to_replicated_files(info)
    # def delete_tags_from_refered_files(self, node_reference, info): pass
    def delete_tags_from_replicated_files(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.delete_tags_from_replicated_files(info)


# Protocolo Heartbeat y AliveRequest (para replicas y nodos proximos respectivamente)
# ----------------------------------
    def heartbeat(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.heartbeat(info)
    def alive_request(self, node_reference): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.alive_request(communication_messages.Empty())
    def unreplicate(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.unreplicate(info)


# Entrada de un nodo a la red
# ----------------------------------
    def node_entrance_request(self, node_reference, info):
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de node_entrance_request")
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.node_entrance_request(info)

    def i_am_your_next(self, node_reference, info): 
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de i_am_your_next")
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.i_am_your_next(info)
    def update_next(self, node_reference, info):
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de update_next")
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_next(info)
    def files_allotment_transfer(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.files_allotment_transfer(info)
    def update_replication_clique(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_replication_clique(info)


# Salida de un nodo de la red
# ----------------------------------
    def i_am_your_prev(self, node_reference, info): 
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.i_am_your_prev(info)


# Actualizar finger tables
# ----------------------------------
    def update_finger_table(self, node_reference:ChordNodeReference, info): 
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de update_finger_table")
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_finger_table(info)
    def update_finger_table_forward(self, node_reference, info): 
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de update_finger_table_forward")
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.update_finger_table_forward(info)
    def send_me_your_next_list(self, node_reference):
        print(f"📡 solicitud a {node_reference.ip}:{node_reference.port} de send_me_your_next_list")
        with grpc.insecure_channel(node_reference.uri_address) as channel:
            stub = communication.ChordNetworkCommunicationStub(channel)
            return stub.send_me_your_next_list(communication_messages.Empty())

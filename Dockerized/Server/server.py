import random

import logging
from hashlib import sha1
import socket
import grpc
from concurrent import futures
import gRPC.communication_pb2 as communication_messages
import gRPC.communication_pb2_grpc as communication

from .DB import File_Tag_DB
class ChordNodeReference:
    def __init__(self, ip:str, port:int):
        self.id = 0
        self.ip = ip
        self.port = port
    @property
    def hash_code(self):
        return sha1((str(self.ip) + str(self.port)).encode('utf-8')).hexdigest()

class ChordNode(communication.ClientAPIServicer):
    def __init__(self, port:int, nodes_count:int):
        # self.id =                                                 # TODO
        ip = socket.gethostbyname(socket.gethostname())
        self.NodeReference = ChordNodeReference(ip, port)
        self.next:list[ChordNodeReference] = []
        self.prev = None
        self.finger_table:list[ChordNodeReference] = []
        self.nodes_count:int = nodes_count
        self.db_physical_files = File_Tag_DB('phisical_storage')
        self.db_replicas = File_Tag_DB('replicas')
        self.db_references = File_Tag_DB('references')
    
    def list(self, request, context):
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        files_list = []
        tag_query = [tag for tag in request.tags]
        selected_tag = random.choice(tag_query)
        selected_tag_hash_code = sha1(selected_tag.encode('utf-8')).hexdigest()
        recovered_files = self.db_physical_files.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)
        for file in recovered_files:
            file_name = file[0]
            file_hash = file[1]
            file_tags = file[2]
            yield communication_messages.FileGeneralInfo(title=file_name,
                                                            tag_list=file_tags,
                                                            location=communication_messages.FileLocation(file_hash=file_hash, 
                                                                                                            location_hash=selected_tag_hash_code))
    
    def fileContent(self, request, context):
        """FileLocation {file_hash:int, location_hash:int}    =>    FileContent {title:string, content:string}"""
        file_hash = request.file_hash
        file_location_hash = request.location_hash

        recovered_file = self.db_physical_files.RecoveryFileContent_ByInfo(file_hash)
        return communication_messages.FileContent(title=recovered_file.name, content=recovered_file.content)
    
    def addFiles(self, request, context):
        """FilesToAdd {files: FileContent[] {title: string, content: string}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        selected_tag = random.choice(request.tags)
        file_location_hash = sha1(selected_tag.encode('utf-8')).hexdigest()
        try:
            self.db_physical_files.AddFiles([(file.title, file.content) for file in request.files], request.tags)
            return communication_messages.OperationResult(success=True, message="Archivos añadidos satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los archivos")
    
    def addTags(self, request, context):
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        try:
            self.db_physical_files.AddTags(request.tag_query, request.operation_tags)
            return communication_messages.OperationResult(success=True, message="Tags añadidas satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los tags")
    
    def delete(self, request, context):
        """TagList {tags: string}    =>    OperationResult {success: bool, message: string}"""
        try:
            self.db_physical_files.DeleteFiles(tag_query=request.tags)
            return communication_messages.OperationResult(success=True, message="Archivos eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los archivos")


    
    def deleteTags(self, request, context):
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        try:
            self.db_physical_files.DeleteTags(tag_query=request.tags_query, tags=request.operation_tags)
            return communication_messages.OperationResult(success=True, message="Tags eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los tags")

    
    
def serve(port='50051'):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    communication.add_ClientAPIServicer_to_server(ChordNode(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
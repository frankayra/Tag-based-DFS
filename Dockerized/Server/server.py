import time
import sys
sys.path.append('../')
import random
from hashlib import sha1
import socket
from concurrent import futures


import logging
import grpc


import gRPC.communication_pb2 as communication_messages
import gRPC.communication_pb2_grpc as communication
from Server.DB import File_Tag_DB
class ChordNodeReference:
    def __init__(self, ip:str, port:int):
        self.id = 0
        self.ip = ip
        self.port = port
    @property
    def hash_code(self):
        return sha1((str(self.ip) + str(self.port)).encode('utf-8')).hexdigest()
# def Location_hash(tag: str, nodes_number: int) -> int:
#     return int(sha1(tag.encode('utf-8')).hexdigest(), 16) % nodes_number
# def File_hash(file_content: str) -> str:
#     return sha1(file_content.encode('utf-8')).hexdigest()
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
        # self.db_physical_files.File.delete().execute()
        # self.db_physical_files.FileTag.delete().execute()

        files_list = []
        tag_query = [tag for tag in request.tags]
        recovered_files = self.db_physical_files.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)

        try:
            first_file = next(recovered_files)
            file_name, file_hash, file_location_hash, file_tags = first_file[0], first_file[1], first_file[2], first_file[3]
            yield communication_messages.FileGeneralInfo(title=file_name,
                                                            tag_list=file_tags,
                                                            location=communication_messages.FileLocation(file_hash=file_hash, 
                                                                                                            location_hash=file_location_hash))
        except StopIteration:
            print("No se encontraron archivos")
            yield communication_messages.FileGeneralInfo(title="file_name not found",
                                                            tag_list=[],
                                                            location=communication_messages.FileLocation(file_hash='-1', 
                                                                                                            location_hash=-1))
            return
        for file in recovered_files:
            file_name = file[0]
            file_hash = file[1]
            file_location_hash = file[2]
            file_tags = file[3]
            # time.sleep(1)
            yield communication_messages.FileGeneralInfo(title=file_name,
                                                            tag_list=file_tags,
                                                            location=communication_messages.FileLocation(file_hash=file_hash, 
                                                                                                            location_hash=file_location_hash))

        ##### DEBUG #####
        print("\n-------- DEBUG MODE INFO--------")
        File, FileTag, Tag = self.db_physical_files.File, self.db_physical_files.FileTag, self.db_physical_files.Tag
        all_files = File.select(File.location_hash, File.name, File.file_hash)
        for file in all_files:
            print(f"file Hash: {file.file_hash}\n   |--> name: {file.name}\n   |--> location: {file.location_hash}\n   |--> tags: {[tag.tag.name for tag in file.tags]}\n")
        # self.db_physical_files.File.delete().execute()
        # self.db_physical_files.FileTag.delete().execute()
    def fileContent(self, request, context):
        """FileLocation {file_hash:int, location_hash:int}    =>    FileContent {title:string, content:string}"""
        file_hash = request.file_hash
        file_location_hash = request.location_hash
        
        recovered_file = self.db_physical_files.RecoveryFileContent_ByInfo(file_hash)
        if not recovered_file: return communication_messages.FileContent(title=None, content=None)
        return communication_messages.FileContent(title=recovered_file.name, content=recovered_file.content)
    
    def addFiles(self, request, context):
        """FilesToAdd {files: FileContent[] {title: string, content: string}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        # if self.prev and self.next:

        #     for tag in request.tags:
        #         tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
        #         if self.prev.id < tag_hash <= self.NodeReference.id:
                    
        #             break
        # return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos")
        
        selected_tag = random.choice(request.tags)
        files_location_hash = int(sha1(selected_tag.encode('utf-8')).hexdigest(), 16) % self.nodes_count
        try:
            add_files_message = self.db_physical_files.AddFiles([(file.title, file.content) for file in request.files], [tag for tag in request.tags], files_location_hash)
            return communication_messages.OperationResult(success=True, message=f"Archivos añadidos satisfactoriamente: {add_files_message}")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos solicitados: {e}")
    
    def addTags(self, request, context):
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        try:
            tag_query = [tag for tag in request.tags_query]
            operation_tags = [tag for tag in request.operation_tags]
            add_tags_message = self.db_physical_files.AddTags(tag_query, operation_tags)
            return communication_messages.OperationResult(success=True, message=add_tags_message)
            # return communication_messages.OperationResult(success=True, message="Tags añadidas satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los tags")
    
    def delete(self, request, context):
        """TagList {tags: string}    =>    OperationResult {success: bool, message: string}"""
        # try:
        tag_query = [tag for tag in request.tags]
        delete_message = self.db_physical_files.DeleteFiles(tag_query)
        return communication_messages.OperationResult(success=True, message=delete_message)
            # return communication_messages.OperationResult(success=True, message="Archivos eliminados satisfactoriamente")
        # except Exception:
        #     return communication_messages.OperationResult(success=False, message="Error al eliminar los archivos")


    
    def deleteTags(self, request, context):
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        try:
            tag_query = [tag for tag in request.tags_query]
            operation_tags = [tag for tag in request.operation_tags]
            self.db_physical_files.DeleteTags(tag_query=tag_query, tags=operation_tags)
            return communication_messages.OperationResult(success=True, message="Tags eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los tags")

    
    
def serve(port='50051'):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    communication.add_ClientAPIServicer_to_server(ChordNode(50051, 8), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
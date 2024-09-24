import time
import random
from hashlib import sha1
import socket
from concurrent import futures
from threading import Thread


import logging
import grpc


from gRPC import communication_pb2 as communication_messages
from gRPC import communication_pb2_grpc as communication
from DB import File_Tag_DB, Files_References_DB
from .ChordServer import ChordServer
from .ChordClient import ChordClient, ChordNodeReference


# def Location_hash(tag: str, nodes_number: int) -> int:
#     return int(sha1(tag.encode('utf-8')).hexdigest(), 16) % nodes_number
# def File_hash(file_content: str) -> str:
#     return sha1(file_content.encode('utf-8')).hexdigest()
class ClientAPIServer(communication.ClientAPIServicer):
    def __init__(self, port:int = 50051, nodes_count:int = 8):
        self.chord_server = ChordServer(self.check_for_ready_operation, port+1, nodes_count)
        self.chord_client = self.chord_server.chord_client

        self.pending_operations = self.chord_server.pending_operations
        self.ready_operations = self.chord_server.ready_operations
        
        self.active_threads = 0
    
    def list(self, request, context):
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        tag_query = [tag for tag in request.tags]
        self_id = self.chord_server.node_reference.id
        prev_id = self.chord_server.prev.id
        for tag in tag_query:
            tag_id = int(sha1(tag.encode("utf-8")).hexdigest(), 16) % self.chord_server.nodes_count
            if tag_id <= self_id and (prev_id < tag_id or prev_id > self_id):
                return self.chord_server.list(request, context)
            
        random_selected_tag = random.choice(tag_query)
        random_selected_tag_hash = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) % self.chord_server.nodes_count

        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16)                    # TODO verificar que el protocolo envie apropiadamente este id y retorne intacto de la operacion de successor()
        
        wait_for_results = self.PushPendingOperation(operation_id= operation_id, operation= communication_messages.LIST, info= communication_messages.TagList(tags=tag_query))
        self.chord_client.succesor(id=random_selected_tag_hash, node_reference=self.chord_server.node_reference, operation=communication_messages.LIST)
        results = wait_for_results()
        
        if isinstance(results, Exception):
            yield communication_messages.FileGeneralInfo(title=results.message,
                                                            tag_list=[],
                                                            location=communication_messages.FileLocation(file_hash='-1', 
                                                                                                            location_hash=-1))
            return

        for item in results:
            yield item        
        
    def fileContent(self, request, context):
        """FileLocation {file_hash:int, location_hash:int}    =>    FileContent {title:string, content:string}"""
        file_hash = request.file_hash
        file_location_hash = request.location_hash
        return self.chord_client.file_content(file_hash, file_location_hash)
    
    def addFiles(self, request, context):
        """FilesToAdd {files: FileContent[] {title: string, content: string}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        # if self.prev and self.next:

        #     for tag in request.tags:
        #         tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
        #         if self.prev.id < tag_hash <= self.NodeReference.id:
                    
        #             break
        # return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos")
        
        pass
    
    def addTags(self, request, context):
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        pass
    
    def delete(self, request, context):
        """TagList {tags: string}    =>    OperationResult {success: bool, message: string}"""
        pass


    
    def deleteTags(self, request, context):
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        pass

    
    
    # def RetakeOperation(self, operation, id, node_reference):
    #     (pending_op, info) = self.pending_operations.get(id, (None, None))
    #     if not pending_op or pending_op != operation:
    #        print("Se solicito una operacion que no estaba pendiente")
    #        return 
    #     return self.chord_client.RetakeOperation(node_reference, operation, info)
        

            
    def PushPendingOperation(self, operation_id, operation,  info, steaming = False):
            
        self.pending_operations[operation_id] = (operation, info)
        # result = self.chord_client.list(tag_query=[tag for tag in request.tags])
        checking_for_results_thread = Thread(target=self.check_for_ready_operation, args=(operation_id))
        def wait_for_results():
            checking_for_results_thread.start()
            self.active_threads += 1
            if self.active_threads > 1: print(f"active threads: {self.active_threads}")
            
            checking_for_results_thread.join()
            self.active_threads -= 1
            
            result = self.ready_operations[operation_id]
            del self.ready_operations[operation_id]
            return result
        return wait_for_results
            
        
        
    
    def serve(self, port='50051'):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        communication.add_ClientAPIServicer_to_server(self, server)
        server.add_insecure_port("[::]:" + port)
        server.start()
        print("Client API Server iniciado, escuchando en el puerto " + port)
        server.wait_for_termination()

    def check_for_ready_operation(self, id):
        result = None
        while(True):
            time.sleep(0.05)
            result = self.ready_operations.get(id, None)
            if result: return
    

if __name__ == '__main__':
    server = ClientAPIServer()
    API_thread = Thread(target=server.serve, args=())
    ChordServer_thread = Thread(target=server.chord_server.serve)

    API_thread.daemon = True
    ChordServer_thread.daemon = True

    API_thread.start()
    ChordServer_thread.start()
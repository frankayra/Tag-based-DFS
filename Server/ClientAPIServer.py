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


class ClientAPIServer(communication.ClientAPIServicer):
    def __init__(self, port:int = 50051, nodes_count:int = 8):
        self.chord_server = ChordServer(self.check_for_ready_operation, port+1, nodes_count)
        self.chord_client = self.chord_server.chord_client

        self.pending_operations = self.chord_server.pending_operations
        self.ready_operations = self.chord_server.ready_operations
        
        self.active_threads = 0
    

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
    

        
    def PushPendingOperation(self, operation_id, operation,  info):
            
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
        
        
    def belonging_id(self, searching_id):
        self_id = self.chord_server.node_reference.id
        prev_id = self.chord_server.prev.id
        # return searching_id <= self_id and (prev_id < searching or prev_id > self_id)
        return (prev_id < searching_id <= self_id) or (self_id < prev_id and (searching_id > prev_id or searching_id <= self_id))
        
    
    def list(self, request, context):
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        tag_query = [tag for tag in request.tags]
        for tag in tag_query:
            tag_id = int(sha1(tag.encode("utf-8")).hexdigest(), 16) % self.chord_server.nodes_count
            if self.belonging_id(tag_id):
                return self.chord_server.list(request, context)
            
        random_selected_tag = random.choice(tag_query)
        random_selected_tag_hash = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) % self.chord_server.nodes_count

        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16)                    # TODO verificar que el protocolo envie apropiadamente este id y retorne intacto de la operacion de successor()
        
        wait_for_results = self.PushPendingOperation(operation_id= operation_id, operation= communication_messages.LIST, info= request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.LIST, operation_id= operation_id)
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
        file_location_hash = request.location_hash

        if self.belonging_id(file_location_hash):
            return self.chord_server.file_content(request, context)

        file_hash = request.file_hash
        operation_id = int(sha1(file_hash.encode("utf-8")).hexdigest(), 16)

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.FILE_CONTENT, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=file_location_hash, requested_operation=communication_messages.FILE_CONTENT, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.FileContent(title=None, content=None)
        return results
    
    def addFiles(self, request, context):
        """FilesToAdd {files: FileContent[] {title: string, content: string}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        # if self.prev and self.next:
        tag_query = [tag for tag in request.tags]
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % self.chord_server.nodes_count

            if self.belonging_id(tag_id):
                return self.chord_server.add_files(communication_messages.FilesToAddWithLocation(files=request.files, tags=request.tags, location_hash=tag_id), context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % self.chord_server.nodes_count

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.ADD_FILES, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.ADD_FILES, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results
        
    def addTags(self, request, context):
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        tag_query = [tag for tag in request.tag_query]
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % self.chord_server.nodes_count

            if self.belonging_id(tag_id):
                return self.chord_server.add_tags(request, context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % self.chord_server.nodes_count

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.ADD_TAGS, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.ADD_TAGS, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results

    
    def delete(self, request, context):
        """TagList {tags: string}    =>    OperationResult {success: bool, message: string}"""
        tag_query = [tag for tag in request.tags]
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % self.chord_server.nodes_count

            if self.belonging_id(tag_id):
                return self.chord_server.delete(request, context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % self.chord_server.nodes_count

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.DELETE, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.DELETE, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results


    
    def deleteTags(self, request, context):
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        tag_query = [tag for tag in request.tag_query]
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % self.chord_server.nodes_count

            if self.belonging_id(tag_id):
                return self.chord_server.delete_tags(request, context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % self.chord_server.nodes_count

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.DELETE_TAGS, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.DELETE_TAGS, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results

    
    
if __name__ == '__main__':
    server = ClientAPIServer()
    API_thread = Thread(target=server.serve, args=())
    ChordServer_thread = Thread(target=server.chord_server.serve)

    API_thread.daemon = True
    ChordServer_thread.daemon = True

    API_thread.start()
    ChordServer_thread.start()
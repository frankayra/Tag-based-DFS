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
from ChordServer import ChordServer
from ChordClient import ChordClient, ChordNodeReference


class ClientAPIServer(communication.ClientAPIServicer):
    def __init__(self, ip = "localhost", port:int = 50051, nodes_count:int = 3, replication_factor = 3, next_alive_check_length = 3, server_to_request_entrance:ChordNodeReference = None):
        self.port=port
        self.chord_server = ChordServer(
                                        check_for_updates_func= self.check_for_ready_operation, 
                                        ip=ip,
                                        port= port+1, 
                                        nodes_count= nodes_count,
                                        replication_factor= replication_factor,
                                        next_alive_check_length= next_alive_check_length,
                                        server_to_request_entrance=server_to_request_entrance
                                        )
        self.chord_client = self.chord_server.chord_client

        self.pending_operations = self.chord_server.pending_operations
        self.ready_operations = self.chord_server.ready_operations
        
        self.active_threads = 0
        serve_thread = Thread(target=self.serve, daemon=True)
        serve_thread.start()
    

    

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
        communication.add_ClientAPIServicer_to_server(self, server)
        server.add_insecure_port("[::]:" + str(self.port))
        server.start()
        print("Client API Server iniciado, escuchando en el puerto " + str(self.port))
        server.wait_for_termination()

    def check_for_ready_operation(self, id):
        result = None
        start_time = time.time()
        waiting_time = 3
        while(True):
            time.sleep(0.05)
            result = self.chord_server.ready_operations.get(id, None)
            if result: return
            if time.time() - start_time > waiting_time: return
    

        
    def PushPendingOperation(self, operation_id, operation,  info):
            
        self.pending_operations[operation_id] = (operation, info)
        # result = self.chord_client.list(tag_query=[tag for tag in request.tags])
        print(f"operation id: {operation_id}")
        checking_for_results_thread = Thread(target=self.check_for_ready_operation, args=(operation_id,))
        def wait_for_results():
            checking_for_results_thread.start()
            self.active_threads += 1
            if self.active_threads > 1: print(f"active threads: {self.active_threads}")
            
            checking_for_results_thread.join()
            self.active_threads -= 1
            
            result = self.ready_operations[operation_id]
            del self.ready_operations[operation_id]
            print(f"result a la hora de chequear: {result}")
            return result
        return wait_for_results
        
        
    def belonging_id(self, searching_id):                                                                           # ✅
        if not self.chord_server.prev:
            print("El id pertenece, porque no tengo a mas nadie en el anillo")
            return True
        self_id = self.chord_server.node_reference.id
        prev_id = self.chord_server.prev.id
        # prev_id  <   searching_id   <=   self_id
        # return searching_id <= self_id and (prev_id < searching_id or prev_id > self_id)        # BUG Esto da un falso negativo en el caso de que este self_id con un id de los primeros y prev_id con uno de los ultimos, y caiga searching_id entre los dos pero del lado de prev_id, de los mayores ids.
        response = (prev_id < searching_id <= self_id) or (self_id < prev_id and (searching_id > prev_id or searching_id <= self_id))
        
        if response:    print(f"El id {searching_id} ((SI))esta en [{self.chord_server.prev.id}, {self.chord_server.node_reference.id}]")
        else:           print(f"El id {searching_id} ((NO)) esta en [{self.chord_server.prev.id}, {self.chord_server.node_reference.id}]")
        return response
    
    def list(self, request, context):
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        tag_query = [tag for tag in request.tags]
        print(f"tag query: {tag_query}")
        for tag in tag_query:
            tag_id = int(sha1(tag.encode("utf-8")).hexdigest(), 16) % (2**self.chord_server.nodes_count)
            if self.belonging_id(tag_id):
                results = self.chord_server.list(request, context)
                for file in results:
                    yield file
                return
            
        random_selected_tag = random.choice(tag_query)
        random_selected_tag_hash = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) % (2**self.chord_server.nodes_count)

        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) % 1000000                    # TODO verificar que el protocolo envie apropiadamente este id y retorne intacto de la operacion de successor()
        
        print(f"request del cliente: {request}")
        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.LIST, info=request)
        info = communication_messages.RingOperationRequest(requesting_node=self.chord_server.node_reference.grpc_format, searching_id=random_selected_tag_hash, requested_operation=communication_messages.LIST, operation_id=operation_id)
        # self.chord_client.succesor(requesting_node=self.chord_server.node_reference, node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.LIST, operation_id= operation_id)
        self.chord_server.succesor(info, context)
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
        operation_id = int(sha1(file_hash.encode("utf-8")).hexdigest(), 16) % 1000000

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.FILE_CONTENT, info=request)
        info = communication_messages.RingOperationRequest(requesting_node=self.chord_server.node_reference.grpc_format, searching_id=file_location_hash, requested_operation=communication_messages.FILE_CONTENT, operation_id=operation_id)
        self.chord_server.succesor(info, context)
        # self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=file_location_hash, requested_operation=communication_messages.FILE_CONTENT, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.FileContent(title=None, content=None)
        return results
    
    def addFiles(self, request, context):
        """FilesToAdd {files: FileContent[] {title: string, content: string}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        # if self.prev and self.next:

        tag_query = [tag for tag in request.tags]
        print(f"tag_query: {tag_query}")
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % (2**self.chord_server.nodes_count)

            if self.belonging_id(tag_id):
                return self.chord_server.add_files(communication_messages.FilesToAddWithLocation(files=request.files, tags=request.tags, location_hash=tag_id), context)
        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % (2**self.chord_server.nodes_count)

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.ADD_FILES, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.ADD_FILES, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results
        
    def addTags(self, request, context):
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        tag_query = [tag for tag in request.tags_query]
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % (2**self.chord_server.nodes_count)

            if self.belonging_id(tag_id):
                return self.chord_server.add_tags(request, context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % (2**self.chord_server.nodes_count)

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
            tag_id = tag_hash % (2**self.chord_server.nodes_count)

            if self.belonging_id(tag_id):
                return self.chord_server.delete(request, context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % (2**self.chord_server.nodes_count)

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.DELETE, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.DELETE, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results


    
    def deleteTags(self, request, context):
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        tag_query = [tag for tag in request.tags_query]
        for tag in tag_query:
            tag_hash = int(sha1(tag.encode('utf-8')).hexdigest(), 16)
            tag_id = tag_hash % (2**self.chord_server.nodes_count)

            if self.belonging_id(tag_id):
                return self.chord_server.delete_tags(request, context)

        random_selected_tag = random.choice(tag_query)
        operation_id = int(sha1(random_selected_tag.encode("utf-8")).hexdigest(), 16) 
        random_selected_tag_hash = operation_id % (2**self.chord_server.nodes_count)

        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.DELETE_TAGS, info=request)
        self.chord_client.succesor(node_reference=self.chord_server.node_reference, searching_id=random_selected_tag_hash, requested_operation=communication_messages.DELETE_TAGS, operation_id=operation_id)
        results = wait_for_results()

        if isinstance(results, Exception):
            return communication_messages.OperationResult(success=False, message=results.message)

        return results

    
    

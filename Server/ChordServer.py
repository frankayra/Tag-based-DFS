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
from . import ChordClient
from .ChordClient import ChordNodeReference


class ChordServer(communication.ChordNetworkCommunicationServicer):
    def __init__(self, check_for_updates_func, port:int = 50052, nodes_count:int = 8, docker_container_name = 'ds-server'):
        # self.id =                                                     # TODO
        self.check_for_updates_func = check_for_updates_func
        self.running_on_docker_container = False
        running_on_docker_container_input = input("Estas iniciando desde un contenedor Docker??(Si|No) ")
        match running_on_docker_container_input.casefold():
            case "si": self.running_on_docker_container = True
            case "no": self.running_on_docker_container = False
        ip = socket.gethostbyname(socket.gethostname()) if not running_on_docker_container else docker_container_name
        self.node_reference = ChordNodeReference(ip, port, 0)           # TODO hacer un metodo aparte para inicializar el nodo con un id
        self.next:list[ChordNodeReference] = []
        self.prev:ChordNodeReference = None
        self.finger_table:list[ChordNodeReference] = []
        self.nodes_count:int = nodes_count
        
        self.db_physical_files = File_Tag_DB('phisical_storage')
        self.db_replicas = File_Tag_DB('replicas')
        self.db_references = Files_References_DB('references')
        
        self.chord_client = ChordClient(nodes_count)
        self.pending_operations = {}
        self.ready_operations = {}

    def serve(self, port='50052'):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        communication.add_ChordNetworkCommunicationServicer_to_server(self, server)
        server.add_insecure_port("[::]:" + port)
        server.start()
        print("Chord Server iniciado, escuchando en el puerto " + port)
        server.wait_for_termination()

    def RetakePendingOperation(self, node_reference, operation, operation_id):
        (pending_op, info) = self.pending_operations.get(operation_id, (None, None))
        if not pending_op or pending_op != operation:
           print("Se solicito una operacion que no estaba pendiente")
           self.ready_operations[operation_id] = Exception(f"Error al realizar la operacion {str(operation).casefold()}, dicha operacion que no estaba pendiente")
           return 
        # NOTE Aqui no hay que esperar nada porque estamos ya esperando por el hilo
        # para meter el resltado en la bandeja de salida y asi ClientAPIServer lo toma y 
        # se lo envia al cliente.
        results = self.chord_client.RetakePendingOperation(node_reference, operation, info)
        # if operation == communication_messages.LIST:
        #     self.ready_operations[operation_id] = [item for item in results]
        # else:
        #     self.ready_operations[operation_id] = results

        # HACK Esto no se si hay que iterarlo y devolverlo o se puede devolver asi mismo sin iterar
        self.ready_operations[operation_id] = results
        
    def PushPendingOperation(self, operation_id, operation, info):
        self.pending_operations[operation_id] = (operation, info)

            









# Operaciones fundamentales de comunicacion
    def succesor(self, request, context): 
        next_node: ChordNodeReference = None
        self_id = self.node_reference.id
        requesting_node = ChordNodeReference(request.requesting_node.ip, request.requesting_node.port, request.requesting_node.id)
        if request.searching_id <= self_id:
            if self.prev.id < request.searching_id or self.prev.id > self_id:  # La segunda condicion garantiza que funcione el metodo cuando el id esta antes del primer id del anillo o luego del ultimo.
                # HACK Esto con el hilo asi no estoy del todo seguro que funciona. 
                continuing_with_operation_thread = Thread(target=self.chord_client.proceed_with_operation, args=(self.node_reference, requesting_node, request.searching_id, request.requested_operation, request.operation_id))
                continuing_with_operation_thread.start()
                return communication_messages.OperationReceived(success=True)
            

            
        for i in range(self.nodes_count-1, -1, -1):
            if request.searching_id < requesting_node.id and self_id >= requesting_node.id:    # Se solicito un id que era menor al id del nodo del anillo al que se le solicito.
                if self.finger_table[i].id > self_id or self.finger_table[i] < request.searching_id:
                    next_node = self.finger_table[i]
                    break
                continue
            if self.finger_table[i].id < request.searching_id:
                next_node = self.finger_table[i]
                break
        if not next_node:
            next_node = self.finger_table[0] # Esto garantiza que pueda haber salto cuando el nodo actual es el ultimo en el anillo.

        address = next_node.uri_address
        # HACK Esto con el hilo asi no estoy del todo seguro que funciona. 
        self.chord_client.succesor(next_node, request.searching_id, request.requested_operation, request.operation_id)
        continuing_with_operation_thread = Thread(target=self.chord_client.succesor, args=(next_node, request.searching_id, request.requested_operation, request.operation_id))
        continuing_with_operation_thread.start()
        return communication_messages.OperationReceived(success=True)
    def proceed_with_operation(self, request, context): 
        node_reference = ChordNodeReference(request.node_reference.ip, request.node_reference.port, request.node_reference.id)
        operation = request.requested_operation
        operation_id = request.operation_id

        continuing_with_operation_thread = Thread(target=self.RetakePendingOperation, args=(node_reference, operation, operation_id))
        continuing_with_operation_thread.start()
        return communication_messages.OperationReceived(success=True)


# CRUD
# ----------------------------------
    def list(self, request, context):  # TODO Modificar para obtener tambien la info de los archivos en la base de datos de referencias.
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        files_list = []
        tag_query = [tag for tag in request.tags]
        recovered_files = self.db_physical_files.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)
        recovered_files_references = self.db_references.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)

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
    def file_content(self, request, context):
        """FileLocation {file_hash:int, location_hash:int}    =>    FileContent {title:string, content:string}"""
        file_hash = request.file_hash
        recovered_file = self.db_physical_files.RecoveryFileContent_ByInfo(file_hash)
        if not recovered_file: return communication_messages.FileContent(title=None, content=None)
        return communication_messages.FileContent(title=recovered_file.name, content=recovered_file.content)
    def add_files(self, request, context): 
        """FilesToAdd {files: FileContent[] {title: string, content: string}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        selected_tag = random.choice(request.tags)
        files_location_hash = int(sha1(selected_tag.encode('utf-8')).hexdigest(), 16) % self.nodes_count
        try:
            add_files_message = self.db_physical_files.AddFiles([(file.title, file.content) for file in request.files], [tag for tag in request.tags], files_location_hash)
            return communication_messages.OperationResult(success=True, message=f"Archivos añadidos satisfactoriamente: {add_files_message}")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos solicitados: {e}")
    def add_tags(self, request, context):
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

    def delete_tags(self, request, context):
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        try:
            tag_query = [tag for tag in request.tags_query]
            operation_tags = [tag for tag in request.operation_tags]
            self.db_physical_files.DeleteTags(tag_query=tag_query, tags=operation_tags)
            return communication_messages.OperationResult(success=True, message="Tags eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los tags")
    

# Replication y referencias
# ----------------------------------
    def replicate(self, request, context): pass
    def send_raw_database_replica(self, request, context): pass
    def add_references(self, request, context): pass
    def delete_files_replicas(self, request, context): pass
    def delete_files_references(self, request, context): pass


# Actualizar Referencias y Replicas (Modificacion de Tags)
# ----------------------------------
    def add_tags_to_refered_files(self, request, context): pass
    def add_tags_to_replicated_files(self, request, context): pass
    def delete_tags_from_refered_files(self, request, context): pass
    def delete_tags_from_replicated_files(self, request, context): pass


# Protocolo Heartbeat y AliveRequest (para replicas y nodos proximos respectivamente)
# ----------------------------------
    def heartbeat(self, request, context): pass
    def alive_request(self, request, context): pass
    def unreplicate(self, request, context): pass


# Entrada de un nodo a la red
# ----------------------------------
    def node_entrance_request(self, request, context): pass
    def i_am_your_next(self, request, context): pass
    def update_next(self, request, context): pass
    def files_allotment_transfer(self, request, context): pass
    def update_replication_clique(self, request, context): pass


# Salida de un nodo de la red
# ----------------------------------
    def i_am_your_prev(self, request, context): pass


# Actualizar finger tables
# ----------------------------------
    def update_finger_table(self, request, context): pass
    def update_finger_table_forward(self, request, context): pass




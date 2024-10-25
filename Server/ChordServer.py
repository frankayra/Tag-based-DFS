import time
import random
from hashlib import sha1
import socket
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from concurrent import futures
from threading import Thread
import threading
import os
import platform
import atexit
from multiprocessing import Manager, Queue
import asyncio
import pickle


import docker
import grpc


from gRPC import communication_pb2 as communication_messages
from gRPC import communication_pb2_grpc as communication
from DB import File_Tag_DB, Files_References_DB
from ChordClient import ChordClient
from ChordClient import ChordNodeReference
from controlled_thread import ControlledThread




class ChordServer(communication.ChordNetworkCommunicationServicer):
    def __init__(self, check_for_updates_func, ip: str, port:int = 50052, nodes_count:int = 3, replication_factor = 3, next_alive_check_length = 3, docker_network_name = 'tag-based-dfs_ds-network', server_to_request_entrance:ChordNodeReference = None):
        self.next:list[ChordNodeReference] = []
        self.prev:ChordNodeReference = None
        self.finger_table:list[ChordNodeReference] = []
        self.nodes_count:int = nodes_count
        self.replication_factor = replication_factor
        self.next_alive_check_length = next_alive_check_length
        self.check_for_updates_func = check_for_updates_func
        self.chord_client = ChordClient()

        self.db_physical_files = File_Tag_DB('phisical_storage')
        self.db_references = Files_References_DB('references')
        
        self.pending_operations = {}
        self.ready_operations = {}
        self.ready_operations_locker = threading.Lock()

        # Heartbeat & Alilve Request
        # -------------------------------
        self.db_replicas = {}
        self.last_heartbeats = {}
        self.replication_forest: dict[ChordNodeReference, set] = {}
        self.any_changes_in_next_list = False
        self.NET_RECOVERY_TIME = 7*self.replication_factor
        
        
        # Resolucion del id
        # -------------------------------
        self.node_reference = ChordNodeReference(ip, port, -1)
        self.entrance_resolved = False
        # Se inicia el server antes de resolver la id por razones obvias, se necesitan recibir cosas desde el servidor que se le solicito entrada al anillo.
        ControlledThread(target=self.serve, args=(port,), name="ChordServer serve")
        claiming_id = random.randint(0, (2**nodes_count)-1)
        # claiming_id = 2
        print(f"reclamando el id: {claiming_id}")
        if server_to_request_entrance:
            info = communication_messages.NodeEntranceRequest(new_node_reference=self.node_reference.grpc_format, claiming_id=claiming_id)
            # entrance_request_thread = Thread(target=self.chord_client.node_entrance_request, args=(server_to_request_entrance, info), daemon=True)
            # entrance_request_thread.start()
            ControlledThread(self.chord_client.node_entrance_request, (server_to_request_entrance, info), "entrada de este nodo")
            while self.node_reference.id == -1:
                print("Esperando por respuesta para entrada a la red...")
                time.sleep(1)
                # operating_s = platform.system()
                # if operating_s == "Windows":
                #     os.system('cls')
                # else:
                #     os.system('clear')
            print(f" > id conseguido: {self.node_reference.id} ✅")
            self.entrance_resolved = True

        elif ip == "localhost":
            self.node_reference.id = claiming_id
            self.entrance_resolved = True
        else: 
            nodes_ips = self.discover_nodes(network_name=docker_network_name)
            if len(nodes_ips) == 0:
                print(f" > No se encontraron nodos en la red: Auto-asignando id: {claiming_id} ✅")
                self.node_reference.id = claiming_id
                self.entrance_resolved = True
            else:
                time.sleep(random.random()*5)
                if not self.entrance_resolved:
                    for n_ip in nodes_ips: print(f"Nodo descubierto: {n_ip}")
                    info = communication_messages.NodeEntranceRequest(new_node_reference=self.node_reference.grpc_format, claiming_id=claiming_id)
                    catched = False
                    for n_ip in nodes_ips:
                        server_to_request_entrance = ChordNodeReference(ip=n_ip, port=50052, id=-1)
                        try:
                            self.chord_client.node_entrance_request(server_to_request_entrance, info)
                            starting_time = time.time()
                            while True:
                                print("Esperando por respuesta para entrada a la red...")
                                if self.node_reference.id != -1:
                                    catched = True
                                    break
                                time.sleep(1)
                                if time.time() - starting_time > 4:
                                    break
                            if catched: 
                                print(f" > id conseguido: {self.node_reference.id} ✅")
                                self.entrance_resolved = True
                                break
                        except:
                            continue
                    if not catched:
                        self.node_reference.id = claiming_id
                        print(f" > Ninguno de los nodos descubiertos respondio validamente: Auto-asignando id: {claiming_id} ✅")
                        self.entrance_resolved = True

        ControlledThread(target=self.Manage_Heartbeats_AliveRequests, name="live_check")
        self.process_executor = ProcessPoolExecutor(max_workers=3)
        atexit.register(lambda: self.process_executor.shutdown(wait=True))

    def serve(self, port=50052):                                                                                    # ✅
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        communication.add_ChordNetworkCommunicationServicer_to_server(self, server)
        server.add_insecure_port("[::]:" + str(port))
        server.start()
        print("Chord Server iniciado, escuchando en el puerto " + str(port))
        server.wait_for_termination()
    def discover_nodes(self, network_name='bridge'):
        try:
            docker_host = os.getenv('DOCKER_HOST', 'tcp://host.docker.internal:2375')
            client = docker.DockerClient(base_url=docker_host)
        except docker.errors.DockerException as e1:
            try:
                client = docker.DockerClient(base_url='tcp://host.docker.internal:2375')
            except docker.errors.DockerException as e2:
                try:
                    docker_host = os.getenv('DOCKER_HOST', 'unix://var/run/docker.sock')
                    client = docker.DockerClient(base_url=docker_host)
                except docker.errors.DockerException as e3:
                    print("errores por doquier:")
                    print(f"---------Error 1: {e1}")
                    print(f"\n ---------Error 2: {e2}")
                    print(f"\n ---------Error 3: {e3}")
        try:
            network = client.networks.get(network_name)
            containers = network.attrs['Containers']

            # Obtener la IP del contenedor actual
            current_container_name = socket.gethostname()
            current_container = client.containers.get(current_container_name)
            current_container_ip = None
            if network_name in current_container.attrs['NetworkSettings']['Networks']:
                current_container_ip = current_container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']
        except Exception as e:
            print("La red especificada no se encontro. Estas son las redes disponibles")
            for net in client.networks.list():
                print(f"------{net.name}------")
                containers = net.attrs['Containers']
                for container_id, container_info in containers.items():
                    print(f"ID: {container_id}")
                    print(f"Nombre: {container_info['Name']}")
                    print(f"IP: {container_info['IPv4Address']}")
                    print("-" * 20)

            print(f"Error encontrando la red: {e}")
            return []

        nodes = []
        for container_id, container_info in containers.items():
            container_ip = container_info['IPv4Address'].split('/')[0]  # Obtener solo la IP
            if container_ip != current_container_ip:
                nodes.append(container_ip)

        return nodes
    
    def RetakePendingOperation(self, node_reference, operation, operation_id):                                      # ✅
        print("🔗 Entre en RetakePendingOperation")

        # (pending_op, info) = self.pending_operations.get(operation_id, (None, None))
        (pending_op, info) = self.pending_operations.pop(operation_id, (None, None))
        if not info or pending_op != operation:
            print("Se solicito una operacion que no estaba pendiente")
            print(f"operation_ID: {operation_id}")
            print(f"pending_op: {pending_op}")
            print(f"operation: {operation}")
            with self.ready_operations_locker:
                self.ready_operations[operation_id] = Exception(f"Error al realizar la operacion {str(operation).casefold()}, dicha operacion que no estaba pendiente")
            return 
        # del self.pending_operations[operation_id]

        # NOTE Aqui no hay que esperar nada porque ya el hilo principal espera por la respuesta
        # final del servidor.
        # Al recibir la respuesta se sigue el proceso no como cualquier otro metodo iterativo
        # no concurrente ni paralelo para meter el resltado en la bandeja de salida y asi ClientAPIServer 
        # lo toma y se lo envia al cliente.
        # ⛔⛔⛔ print(f"Se va a enviar la siguiente estructura al otro servidor(info): {info}")
            # print(f"Threads activos: {threading.active_count()}")
            # print(f"Se va a enviar la siguiente estructura al otro servidor(info): {info}")
        
        # try:
        #     active_threads = threading.active_count()
        #     print(f"Hilos activos: {active_threads}")
        #     while active_threads >=9:
        #         time.sleep(0.1)
        #     print(f"info: {info}")
        # except Exception as e:
        #     print(e)

        results = self.chord_client.RetakePendingOperation(node_reference, operation, info)
        # print(f"results(ya se recepciono en el servidor recepcionista): {results}")
        with self.ready_operations_locker:
            self.ready_operations[operation_id] = results
        # print(f"pase el envio y estoy en RetakePendingOperation de nuevo: {results}")
    def PushPendingOperation(self, operation_id, operation, info):                                                  # ✅
        print("🔗 Entre en push_pending_operation")

        self.pending_operations[operation_id] = (operation, info)
        def wait_for_results():
            results_ready = self.check_for_updates_func(operation_id)

            results = self.ready_operations.get(operation_id, None)
            if not results_ready:
                print(f"No se recupero el resultado de la operacion '{operation}' en el tiempo esperado")
                return
            # del self.ready_operations[operation_id]
            print(f"Operacion Realizada: {operation}   => Resultados: {results}")
            # if function_to_apply_to_results != print:
            #     function_to_apply_to_results(results)
        def start_thread():
            ControlledThread(target=wait_for_results, name="wait_for_results")
        return start_thread

    def belonging_id(self, searching_id):                                                                           # ✅
        if not self.prev:
            print("El id pertenece, porque no tengo a mas nadie en el anillo")
            return True
        self_id = self.node_reference.id
        prev_id = self.prev.id
        # prev_id  <   searching_id   <=   self_id
        # return searching_id <= self_id and (prev_id < searching_id or prev_id > self_id)        # BUG Esto da un falso negativo en el caso de que este self_id con un id de los primeros y prev_id con uno de los ultimos, y caiga searching_id entre los dos pero del lado de prev_id, de los mayores ids.
        response = (prev_id < searching_id <= self_id) or (self_id < prev_id and (searching_id > prev_id or searching_id <= self_id))
        
        if response:    print(f"El id {searching_id} ((SI))esta en [{self.prev.id}, {self.node_reference.id}]")
        else:           print(f"El id {searching_id} ((NO)) esta en [{self.prev.id}, {self.node_reference.id}]")
        return response
    def id_in_between(self, base_id, id_to_be_surpassed, base_id_offset):                                           # ✅
        # return base_id_offset >= id_to_be_surpassed or base_id_offset < base_id     # BUG Esto se parte en el caso de que esten base_id_offset y base_id en el final del anillo, y id_to_be_suprpassed este por el principio, este caso da verdadero por la primera condicion y este ejemplo seria un falso positivo.
        return (base_id < id_to_be_surpassed <= base_id_offset) or (base_id_offset < base_id and (id_to_be_surpassed > base_id or id_to_be_surpassed <= base_id_offset))
    def gap(self, id_prev, id_next):                                                                                # ✅
        return id_next - id_prev if id_next-id_prev >= 0 else id_next + (2**self.nodes_count - id_prev) # suma de los 2 trozitos.
    def apply_offset(self, base_id, offset):                                                                        # ✅
        return (base_id + offset + (2**self.nodes_count)) % (2**self.nodes_count)










# Operaciones fundamentales de comunicacion
    def succesor(self, request, context):                                                                           # ✅
        print("🔹 Entre en sucesor")
        next_node: ChordNodeReference = None
        self_id = self.node_reference.id
        requesting_node = ChordNodeReference(request.requesting_node.ip, request.requesting_node.port, request.requesting_node.id)

        # Vemos si el sucesor que se esta buscando es el nodo actual, si es asi, paramos aqui la busqueda y se envia al nodo solicitante un a solicitud para que prosiga con la operacion para la que se buscaba el responsable del id en cuestion
        if self.belonging_id(request.searching_id):
            # HACK Esto con el hilo asi no estoy del todo seguro que funciona. 
            requesting_node = ChordNodeReference(ip=request.requesting_node.ip, port=request.requesting_node.port, id=request.requesting_node.id)
            # ControlledThread(target=self.chord_client.proceed_with_operation, args=(self.node_reference, requesting_node, request.searching_id, request.requested_operation, request.operation_id), name=f"procced_with_operation a: ({requesting_node.id}) -> {requesting_node.ip}:{requesting_node.port}")
            self.process_executor.submit(self.chord_client.proceed_with_operation, self.node_reference, requesting_node, request.searching_id, request.requested_operation, request.operation_id)
            return communication_messages.OperationReceived(success=True)
            
        # print("succesor: El id no pertenece a este nodo")
            
        for i in range(len(self.finger_table)-1, -1, -1):
            # Se busca un id pa lante en el anillo, pero esta detras, hay que dar la vuelta entera. 
            # Fijarse que esto no es una comparacion a ver si un id esta intermedio, esto se comprueba porque en el "if" de abajo, toma de manera greedy el primer nodo de la finger table 
            #   que se encuentre de atras para adelante que sea menor que el id que se busca, pero esto no avanza todo lo que se puede en todos los casos. En particular en el caso de que el id 
            #   que se busca, se encuentre en primera instancia detras del nodo que lo busca, en este caso se tiene que dar una vuelta completa por el anillo, y en este caso hay que tomar
            #   siempre el nodo mas avanzado en el anillo (mas alante en la finger table tambien), que a su vez sea menor que el id que buscamos. 
            # Si se tenia este caso de un nodo buscando un id que le queda detras, y el i-esimo nodo de la finger table resulta tener mayor id que el id que se busca, pues 'continue' para seguir
            #   buscando en el resto de nodos en la finger table (que tienen menor id)

            # if request.searching_id < requesting_node.id <= self_id :    
            #     if self.finger_table[i].id > self_id or self.finger_table[i].id < request.searching_id: # Seleccionando el nodo i-esimo de la finger table, es viable, o sea, se avanzara hacia encontrar el id que se busca (sin pasarse).
            #         next_node = self.finger_table[i]
            #         break
            #     continue
            # if self.finger_table[i].id < request.searching_id:
            #     next_node = self.finger_table[i]
            #     break

            if self.id_in_between(self_id, self.finger_table[i].id, request.searching_id):
                next_node = self.finger_table[i]
                break

        if not next_node:
            if len(self.finger_table) == 0: 
                requesting_node = ChordNodeReference(ip=request.requesting_node.ip, port=request.requesting_node.port, id=request.requesting_node.id)
                # ControlledThread(target=self.chord_client.proceed_with_operation, args=(self.node_reference, requesting_node, request.searching_id, request.requested_operation, request.operation_id), name=f"procced_with_operation a: ({requesting_node.id}) -> {requesting_node.ip}:{requesting_node.port}")
                self.process_executor.submit(self.chord_client.proceed_with_operation, self.node_reference, requesting_node, request.searching_id, request.requested_operation, request.operation_id)
                return communication_messages.OperationReceived(success=True)
            next_node = self.finger_table[0] # Esto garantiza que pueda haber salto cuando el nodo siguiente al actual es el nodo responsable del id que se busca ya que este ultimo por lo tanto tiene un id mayor y no sera escogido para ser el siguiente por el algoritmo.

        address = next_node.uri_address
        # HACK Esto con el hilo asi no estoy del todo seguro que funciona. 
        # self.chord_client.succesor(next_node, request.searching_id, request.requested_operation, request.operation_id)
        # ControlledThread(target=self.chord_client.succesor, args=(requesting_node, next_node, request.searching_id, request.requested_operation, request.operation_id), name=f"sucesor a: ({next_node.id}) -> {next_node.ip}:{next_node.port}")
        self.process_executor.submit(self.chord_client.succesor, requesting_node, next_node, request.searching_id, request.requested_operation, request.operation_id)
        return communication_messages.OperationReceived(success=True)
    def proceed_with_operation(self, request, context):                                                             # ✅
        print("🔹 Entre en proceed_with_operation")

        node_reference = ChordNodeReference(request.node_reference.ip, request.node_reference.port, request.node_reference.id)
        operation = request.requested_operation
        operation_id = request.operation_id

        ControlledThread(target=self.RetakePendingOperation, args=(node_reference, operation, operation_id), name="RetakePendingOperation desde proceed_with_operation")
        return communication_messages.OperationReceived(success=True)


# CRUD
# ----------------------------------
    def list(self, request, context):                                                                               # ✅
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        print("🔹 Entre en list")
        
        files_list = []
        tag_query = [tag for tag in request.tags]
        recovered_files = self.db_physical_files.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)
        recovered_files_references = self.db_references.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)

        empty_file_list = True
        for file in recovered_files:
            empty_file_list = False
            file_name = file[0]
            file_hash = file[1]
            file_location_hash = file[2]
            file_tags = file[3]
            file = communication_messages.FileGeneralInfo(title=file_name,
                                                            tag_list=file_tags,
                                                            location=communication_messages.FileLocation(file_hash=file_hash, 
                                                                                                            location_hash=file_location_hash))
            # print(f"archivo recuperado: {file}")
            files_list.append(file)
        for file in recovered_files_references:
            empty_file_list = False
            file_name = file[0]
            file_hash = file[1]
            file_location_hash = file[2]
            file_tags = file[3]
            file = communication_messages.FileGeneralInfo(title=file_name,
                                                            tag_list=file_tags,
                                                            location=communication_messages.FileLocation(file_hash=file_hash, 
                                                                                                            location_hash=file_location_hash))
            # print(f"archivo recuperado: {file}")
            files_list.append(file)

        if empty_file_list:
            print("No se encontraron archivos")
            return communication_messages.FileGeneralInfoss(files_general_info=[])
        return communication_messages.FileGeneralInfoss(files_general_info=files_list)
    def file_content(self, request, context):                                                                       # ✅
        """FileLocation {file_hash:int, location_hash:int}    =>    FileContent {title:string, content:string}"""
        print("🔹 Entre en file_content")
        file_hash = request.file_hash
        recovered_file = self.db_physical_files.RecoveryFileContent_ByInfo(file_hash)
        if not recovered_file: return communication_messages.FileContent(title=None, content=None)
        return communication_messages.FileContent(title=recovered_file.name, content=recovered_file.content)
    def add_files(self, request, context):                                                                          # ✅
        """FilesToAddWithLocation {files: FileContent[] {title: string, content: string}, tags: string[], location_hash: int}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en add-files")
        try:
            add_files_message = self.db_physical_files.AddFiles([(file.title, file.content) for file in request.files], [tag for tag in request.tags], request.location_hash)
            return communication_messages.OperationResult(success=True, message=f"Archivos añadidos satisfactoriamente: {add_files_message}")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos solicitados: {e}")
    def add_tags(self, request, context):                                                                           # ✅
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en add-tags")
        try:
            tag_query = [tag for tag in request.tags_query]
            operation_tags = [tag for tag in request.operation_tags]
            add_tags_message = self.db_physical_files.AddTags(tag_query, operation_tags)
            return communication_messages.OperationResult(success=True, message=add_tags_message)
            # return communication_messages.OperationResult(success=True, message="Tags añadidas satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los tags")
    def delete(self, request, context):                                                                             # ✅
        """TagList {tags: string}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en delete")
        try:
            tag_query = [tag for tag in request.tags]
            delete_message = self.db_physical_files.DeleteFiles(tag_query)
            return communication_messages.OperationResult(success=True, message=delete_message)
            # return communication_messages.OperationResult(success=True, message="Archivos eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los archivos")

    def delete_tags(self, request, context):                                                                        # ✅
        """TagQuery {tags_query: string[], operation_tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en delete-tags")
        try:
            tag_query = [tag for tag in request.tags_query]
            operation_tags = [tag for tag in request.operation_tags]
            self.db_physical_files.DeleteTags(tag_query=tag_query, tags=operation_tags)
            return communication_messages.OperationResult(success=True, message="Tags eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los tags")
    

# Replication y referencias
# ----------------------------------
    def replicate(self, request, context):
        """FilesToReplicate {files: FilesToAdd {files: FileContent[] {title: atring, content: string}, tags: string[]}, location_hash: int, main_replica_node_reference: ChordNodeReference {id: int, ip: string, port: int}}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en replicate")
        try:
            chord_node_reference = ChordNodeReference(ip=request.main_replica_node_reference.ip, port=request.main_replica_node_reference.port, id=request.main_replica_node_reference.id)
            if self.db_replicas.get(chord_node_reference, None):
                add_files_message = self.db_replicas[chord_node_reference].AddFiles([(file.title, file.content) for file in request.files.files], [tag for tag in request.files.tags], request.location_hash)
            else:
                self.db_replicas[chord_node_reference] = (File_Tag_DB(f"phisical_storage-{chord_node_reference.id}-{self.node_reference.id}")
                                                    , Files_References_DB(f"references-{chord_node_reference.id}-{self.node_reference.id}"))
                add_files_message = self.db_replicas[chord_node_reference].AddFiles([(file.title, file.content) for file in request.files.files], [tag for tag in request.files.tags], request.location_hash)
            return communication_messages.OperationResult(success=True, message=f"Archivos añadidos satisfactoriamente: {add_files_message}")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos solicitados: {e}")
    def send_raw_database_replica(self, request, context): 
        """RawDatabases {db_phisical: bytes, db_references: bytes, main_replica_node_reference: ChordNodeReference {...}}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en send_raw_database_replica")
        main_replica_node_reference = ChordNodeReference(ip=request.main_replica_node_reference.ip, port=request.main_replica_node_reference.port, id=request.main_replica_node_reference.id)
        physical_storage_name = f"phisical_storage-{main_replica_node_reference.id}-{self.node_reference.id}"
        references_name = f"references-{main_replica_node_reference.id}-{self.node_reference.id}"
        try:
            converted_db = (pickle.loads(request.db_phisical), pickle.loads(request.db_references))
            with open(physical_storage_name, "wb") as file:
                file.write(converted_db[0])
            with open(references_name, "wb") as file:
                file.write(converted_db[1])
        except Exception as e:
            print("Error la conversion de bytes a clase de la base de datos")
            return communication_messages.OperationResult(success=False, message="Error al convertir la replica solicitada")

        physical_storage_db = File_Tag_DB(physical_storage_name)
        references_db = Files_References_DB(references_name)

        if main_replica_node_reference == self.node_reference:
            self.db_physical_files.JoinDatabase(physical_storage_db)
            self.db_references.JoinDatabase(references_db)
        else:
            if not self.replication_forest[main_replica_node_reference]:
                self.replication_forest[main_replica_node_reference] = set()
            self.db_replicas[main_replica_node_reference][0].JoinDatabase(physical_storage_db)
            self.db_replicas[main_replica_node_reference][1].JoinDatabase(references_db)
            # NOTE No se añaden nodos al clique de replicacion porque ya de esto se encarga el metodo 'i_am_your_next' con la nueva lista next.
        return communication_messages.OperationResult(success=True, message="Replica recibida satisfactoriamente")
    def add_references(self, request, context): 
        """FilesReferencesToAdd {location_hash: int, files_references: FileReference[] {title: string, file_hash: int}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en add_references")
        try:
            add_references_message = self.db_references.AddFiles(files=[(file.title, file.file_hash) for file in request.files_references], 
                                                                tags=[tag for tag in request.tags],
                                                                location_hash=request.location_hash)
            return communication_messages.OperationResult(success=True, message=add_references_message)
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Hubo un error al añadir las referencias: add_references_message")

    def delete_files_replicas(self, request, context):
        """FilesToUpdateRquest {
            args: UpdateRequestArguments {
                files: optional FilesReferences {
                    files_references: FileReference[] {
                        title: string, file_hash: int
                    }
                }, 
                tag_list: optional TagList {
                    tags: string[]
                }
            }, 
            node_reference: ChordNodeReference: {
                id: int, 
                ip: string, 
                port: int
            }
        }    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en delete_files_replicas")
        chord_node_reference = ChordNodeReference(ip=request.node_reference.ip, port=request.node_reference.port, id=request.node_reference.id)
        try:
            if self.db_replicas.get(chord_node_reference, None):
                tag_query = [tag for tag in request.args.tag_list]
                delete_message = self.db_replicas[chord_node_reference].DeleteFiles(tag_query=tag_query)
                return communication_messages.OperationResult(success=True, message=delete_message)
            return communication_messages.OperationResult(success=True, message="No habia replica en este server del nodo solicitado")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message="Hubo un error en la eliminacion de las replicas")

            
    def delete_files_references(self, request, context):
        """UpdateRequestArguments {
            files: optional FilesReferences {
                files_references: FileReference[] {
                    title: string, file_hash: int
                }
            }, 
            tag_list: optional TagList {
                tags: string[]
            }
        }    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en delete_files_references")
        try:
            tag_query = [tag for tag in request.tag_list]
            delete_message = self.db_references.DeleteFiles(tag_query=tag_query)
            return communication_messages.OperationResult(success=True, message=delete_message)
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar las referencias")


# Actualizar Referencias y Replicas (Modificacion de Tags)
# ----------------------------------
    def add_tags_to_refered_files(self, request, context):
        """UpdateTagsRequest {
            args: UpdateRequestArguments {
                files: optional FilesReferences {
                    files_references: FileReference[] {
                        title: string,
                        file_hash: int
                    }
                },
                tag_list: optional TagList {
                    tags: string[]
                }
            },
            operation_tags: string[]
            node_reference: optional ChordNodeReference {
                ip: string,
                port: int,
                id: int,
            }
        }    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en add_tags_to_refered_files")
        try:
            tag_query = [tag for tag in request.args.tag_list.tags]
            operation_tags = [tag for tag in request.operation_tags]
            add_tags_message = self.db_references.AddTags(tag_query, operation_tags)
            return communication_messages.OperationResult(success=True, message=add_tags_message)
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los tags")

    def add_tags_to_replicated_files(self, request, context):
        """Fijarse en la estructura de arriba"""
        print("🔹 Entre en add_tags_to_replicated_files")
        try:
            chord_node_reference = ChordNodeReference(ip=request.node_reference.ip, port=request.node_reference.port, id=request.node_reference.id)
            tag_query = [tag for tag in request.args.tag_list.tags]
            operation_tags = [tag for tag in request.operation_tags]
            if self.db_replicas.get(chord_node_reference, None):
                add_tags_message = self.db_replicas[chord_node_reference].AddTags(tag_query, operation_tags)
                return communication_messages.OperationResult(success=True, message=add_tags_message)
            return communication_messages.OperationResult(success=True, message="No habia replica en este server del nodo solicitado")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los tags")

    def delete_tags_from_refered_files(self, request, context):
        """Fijarse en la estructura de arriba"""
        print("🔹 Entre en delete_tags_from_refered_files")
        try:
            tag_query = [tag for tag in request.args.tag_list.tags]
            operation_tags = [tag for tag in request.operation_tags]
            delete_tags_message = self.db_references.DeleteTags(tag_query, operation_tags)
            return communication_messages.OperationResult(success=True, message=delete_tags_message)
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los tags")

    def delete_tags_from_replicated_files(self, request, context):
        """Fijarse en la estructura de arriba"""
        print("🔹 Entre en delete_tags_from_replicated_files")
        try:
            
            if self.db_replicas.get(chord_node_reference, None):
                chord_node_reference = ChordNodeReference(ip=request.node_reference.ip, port=request.node_reference.port, id=request.node_reference.id)
                tag_query = [tag for tag in request.args.tag_list.tags]
                operation_tags = [tag for tag in request.operation_tags]
                delete_tags_message = self.db_replicas[chord_node_reference].DeleteTags(tag_query, operation_tags)
                return communication_messages.OperationResult(success=True, message=delete_tags_message)
            return communication_messages.OperationResult(success=True, message="No habia replica en este server del nodo solicitado")
            
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los tags")


# Protocolo Heartbeat y AliveRequest (para replicas y nodos proximos respectivamente)
# ----------------------------------
    def heartbeat(self, request, context):
        """ChordNodeReference {ip: string, port: int, id: int}    =>    Empty {}"""
        print("🔹 Entre en heartbeat")
        chord_node_reference = ChordNodeReference(ip=request.ip, port=request.port, id=request.id)
        self.last_heartbeats[chord_node_reference] = time.time()
        return communication_messages.Empty()
        
    def alive_request(self, request, context): 
        if self.any_changes_in_next_list:
            self.any_changes_in_next_list = False
            info = communication_messages.LiveAnswer(   any_changes=True, 
                                                        next_nodes_list=communication_messages.ChordNodeReferences(
                                                            references=[communication_messages.ChordNodeReference(id=n.id, ip=n.ip, port=n.port) for n in self.next]))
            return info
        return communication_messages.LiveAnswer(any_changes=False)
    def unreplicate(self, request, context): 
        """{ ChordNodeReference{...}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en unreplicate")
        # chord_node_reference = ChordNodeReference(ip=request.main_replica_node_reference.ip, port=request.main_replica_node_reference.port, id=request.main_replica_node_reference.id)
        chord_node_reference = ChordNodeReference(ip=request.ip, port=request.port, id=request.id)
        if self.db_replicas.pop(chord_node_reference, None) and self.replication_forest.pop(chord_node_reference, None):
            return communication_messages.OperationResult(success=True, message=f"Replica eliminada satisfactoriamente")
        return communication_messages.OperationResult(success=False, message=f"Error al eliminar la replica {e}")


# Entrada de un nodo a la red
# ----------------------------------
    def node_entrance_request(self, request, context):                                                              # ✅
        print("🔹 Entre en node_entrance_request")
        if not self.entrance_resolved:
            self.entrance_resolved = True
            self.node_reference.id = random.randint(0, (2**self.nodes_count)-1)
        # Verificando si se puede dar de alta al nuevo nodo aqui mismo.
        # ----------------------------------
        # Verificando si el nodo esta dentro de los ids que el nodo actual maneja y este puede ponerlo como su anterior, integrandolo a la red.
        # Fijarse que aqui tambien se filtra, o entra, cuando el id que se reclama coincide con el del nodo actual. En este caso se sigue buscando
        #   otro id libre en la red segun mi algoritmo de encontrar id libre para un nuevo nodo.
        if self.belonging_id(request.claiming_id):
            if request.claiming_id != self.node_reference.id or (not self.prev):
                entrance_node_reference = ChordNodeReference(ip=request.new_node_reference.ip, port=request.new_node_reference.port, id=request.claiming_id)

                # Aqui le asignamos un id al otro lado del anillo (a distancia igual a la mitad del tamaño del anillo que es 2**self.nodes_count / 2 o lo que es lo mismo 2**(self.nodes_count -1))
                #   en caso de que el nodo este queriendo entrar al mismo con un id igual al nodo actual y no tengamos a mas nadie en el anillo ademas del nodo actual. En otro caso se le da el mismo id, por simplicidad.
                # Fijarse que esta condicion se puede cumplir si se entro en el if por la condicion de 'not self.prev'.
                assigned_id = request.claiming_id if request.claiming_id != self.node_reference.id else self.apply_offset(self.node_reference.id, 2**(self.nodes_count -1))
                ControlledThread(target=self.Manage_Node_Entrance, args=(entrance_node_reference, assigned_id), name="Manage_Node_Entrance desde node_entrance_request")
                return communication_messages.OperationResult(success=True, message="Se encontro un hueco para el nuevo nodo")
            
        next_node = None
        new_claiming_id = 0
        gap = self.gap(self.node_reference.id, self.next[0].id)
        if gap > 1:
            next_node = self.next[0]
            new_claiming_id = self.apply_offset(self.node_reference.id, int(gap/2))
        else:
            for i in range(1, len(self.next)):
                gap = self.gap(self.next[i-1].id, self.next[i].id)
                if gap > 1:
                    next_node = self.next[i]
                    new_claiming_id = self.apply_offset(self.next[i-1].id, int(gap/2))
                    break

        # Redireccionando la operacion de 'node_entrance_request' para el siguiente nodo
        # -----------------------------------------
        # Caso en que habiamos encontrado en next[] un intervalo o espacio vacio, y vamos a enviar la solicitud hacia el nodo siguiente, responsable del id escogido en dicho espacio vacio.
        if next_node:
            info = communication_messages.NodeEntranceRequest(new_node_reference=request.new_node_reference, claiming_id=new_claiming_id)
            ControlledThread(target=self.chord_client.node_entrance_request, args=(next_node, info), name=f"node_entrance_request del nodo ({request.new_node_reference.id}) -> {request.new_node_reference.ip}:{request.new_node_reference.port} traspasada a ({next_node.id}) -> {next_node.ip}:{next_node.port}")
            return communication_messages.OperationResult(success=True, message="Seguimos buscando un hueco para el nuevo nodo")
        
        # Caso en que no se encontro id libre en next[] y se procede a seguir con el algoritmo para encontrar hueco libre, ahora buscando un id random
        #   que inteligentemente no este en el intervalo de ids del nodo actual hasta el id del ultimo nodo de next[] (next[-1]).
        if self.node_reference.id < self.next[len(self.next)-1].id: # Esto pasa cuando el id de next[-1] no ha dado un salto en el final del anillo.
            if self.next[len(self.next)-1].id == 2**self.nodes_count -1: # Esto es cuando el ultimo nodo de next[] tiene id igual al ultimo id posible del anillo, en este caso no es necesario tener en cuenta el intervalo de next[-1] al final del anillo.
                new_claiming_id = random.randint(0, self.node_reference.id)
            else:
                new_claiming_id = random.choice([random.randint(0, self.node_reference.id), random.randint(self.next[len(self.next)-1].id +1, 2**self.nodes_count)])
        else: 
            new_claiming_id = random.randint(self.next[len(self.next)-1] +1, self.node_reference.id)
        
        operation_id = random.randint(1, 10000)
        info = communication_messages.NodeEntranceRequest(new_node_reference=request.new_node_reference, claiming_id=new_claiming_id)
        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.NODE_ENTRANCE_REQUEST, info=info)
        info = communication_messages.RingOperationRequest(requesting_node=self.node_reference.grpc_format, searching_id=new_claiming_id, requested_operation=communication_messages.NODE_ENTRANCE_REQUEST, operation_id=operation_id)
        ControlledThread(target=self.succesor, args=(info, context), name=f"sucesor a: mi mismo")
        wait_for_results()
        return communication_messages.OperationResult(success=True, message="Seguimos buscando un hueco para el nuevo nodo")
        




    def i_am_your_next(self, request, context):                                                                     # ✅
        """IAmYourNextRequest    =>    OperationReceived"""
        print("🔹 Entre en i_am_your_next")
        
        # Actualizamos el id del nodo actual con la id que se asigno en el proceso de busqueda del anillo, asi como la lista next[] y prev
        self.next.clear()
        for node in request.next_list.references:
            self.next.append(ChordNodeReference(ip=node.ip, port=node.port, id=node.id))
        self.prev = ChordNodeReference(ip=request.prev.ip, port=request.prev.port, id=request.prev.id)
        self.node_reference.id = request.assigned_id

        # Actualizando la finger table
        self.Update_FingerTable_WithNextList()
        

        # Enviamos la referencia del nodo actual al nuevo nodo prev para que actualice su lista next[]
        info = self.node_reference.grpc_format
        ControlledThread(target=self.chord_client.update_next, args=(self.prev, info), name=f"update_next a: mi nodo previo")
        

        # Pedimos al nuevo nodo proximo (next[0]) que le envie al nodo actual los archivos que le tocan
        # operation_id = random.randint(1, 10000000000000)
        # info = communication_messages.Empty()
        # for node in self.next:
        #     self.chord_client.update_replication_clique(node, )
        
        
        return communication_messages.OperationReceived(success=True)






        
    def update_next(self, request, context):                                                                        # ✅
        print("🔹 Entre en update_next")

        if len(self.next) >= self.next_alive_check_length:
            self.next.pop()
        self.next.insert(0, ChordNodeReference(ip=request.ip, port=request.port, id=request.id))
        
        # Actualizando la finger table
        self.Update_FingerTable_WithNextList()
        
        return communication_messages.OperationReceived(success=True)
    def files_allotment_transfer(self, request, context):
        """FilesAllotmentTransferRequest {files: FileToTransfer[] {file: FileContent {title: string, content: string}, tags: string[]}, location: FileLocation {file_hash: string, location_hash: int}}    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en files_allotment_transfer")
        try:
            for file in request.files:
                self.db_physical_files.SaveFile(file.file.title, file.file.content, request.location.location_hash, *[tag for tag in file.tags])
                self.db_references.SaveFile(file.file.title, file.file.file_hash, request.location.location_hash, *[tag for tag in file.tags])
            return communication_messages.OperationResult(success=True, message=f"Archivos transferidos satisfactoriamente: {add_files_message}")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al transferir los archivos solicitados: {e}")
    def update_replication_clique(self, request, context):
        """UpdateReplicationCliqueRequest { old_leader: ChordNodeReference, new_leader: ChordNodeReference, clique: ChordNodeReferences }    =>    OperationResult {success: bool, message: string}"""
        print("🔹 Entre en update_replication_clique")
        try:
            old_leader = ChordNodeReference(ip=request.old_leader.ip, port=request.old_leader.port, id=request.old_leader.id)
            new_leader = ChordNodeReference(ip=request.new_leader.ip, port=request.new_leader.port, id=request.new_leader.id)
            clique = [ChordNodeReference(ip=node.ip, port=node.port, id=node.id) for node in request.clique.references]
            if old_leader.id == new_leader.id: # Se detecto una baja DESDE la replica principal. Simplemente se quiere actualizar el clique
                self.replication_forest[new_leader] = set(clique)
            elif self.id_in_between(new_leader.id, old_leader.id, self.node_reference.id): # old_leader.id > new_leader.id --> Esta entrando un nodo.
                self.replication_forest[new_leader] = set(clique)
                self.Change_Replica_Leader(old_leader, new_leader)
            elif self.id_in_between(old_leader.id, new_leader.id, self.node_reference.id): # old_leader.id < new_leader.id --> Se esta manejando la baja de un nodo
                self.replication_forest.pop(old_leader)
                self.Join_Replica_Leader(new_leader, old_leader)
                
            
            return communication_messages.OperationResult(success=True, message="Clique de replicacion actualizada satisfactoriamente")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al actualizar la clique de replicacion: {e}")
        


# Salida de un nodo de la red
# ----------------------------------
    def i_am_your_prev(self, request, context):
        print("🔹 Entre en i_am_your_prev")
        try:
            response = self.chord_client.alive_request(self.prev)
            print(f"El nodo ({request.id}) esta solicitando ser mi prev, pero ({self.prev.id}) aun esta vivo)")
        except grpc.RpcError:
            self.prev = ChordNodeReference(ip=request.ip, port=request.port, id=request.id)
            print(f"El nodo ({request.id}) es mi nuevo prev")
        return communication_messages.OperationReceived(success=True)


# Actualizar finger tables
# ----------------------------------
    def update_finger_table(self, request, context):                                                                # ✅
        print(f"🔹 Entre en update_finger_table. Meter a {request.node_reference.id}")

        # Constants
        updates_so_far = request.updates_so_far
        new_node_id = request.node_reference.id
        pivot_id = self.apply_offset(new_node_id, -request.interval_gap)
        self_id = self.node_reference.id
        gap_beginning = self.apply_offset(pivot_id, -(2**(updates_so_far -1))) if updates_so_far > 0 else pivot_id
        just_forward_updates = False
        
        print("paso 1 superado")
        
        # Comprobando si ya se hicieron todos los saltos hacia atras actualizando las finger tables.
        if updates_so_far >= self.nodes_count: 
            if self.node_reference == request.node_reference:
                just_forward_updates = True                                     # NOTE Esto se hace porque puede que hayan quedado nodos unos pasitos delante que apunten al intevalo [pivot_id, new_node_id]. Esto solo puede pasar si el nodo actual es el nodo nuevo(que ya tiene id asignado y por ende podemos compararlo).
            else: return communication_messages.OperationResult(success=True)   #   Esta es la unica forma que tenemos de dejar que la funcion ejecute la parte de update_finger_table_forward y retorne despues. De otra manera se retorna aqui mismo porque no hay mas nada que se pueda actualizar en ninguna tabla, ni siquiera en la del nodo actual
        print("paso 2 superado")

        # Modificando la finger table en concordancia para cambiar las que apunten al rango (pivot_id, new_node_id], añadiendo si es necesario un nuevo lugar
        # -----------------------------------------------------
        if not just_forward_updates:                                            # NOTE Si esto esta activo significa que el nodo actual es el nodo entrante en el anillo, no podemos ponerlo a el mismo en su finger table, por ende tenemos nada que actualizar aqui
            for i in range(self.nodes_count):
                if i >= len(self.finger_table):
                    if self.id_in_between(pivot_id, self.apply_offset(self_id, 2**i), new_node_id) and self_id != new_node_id:
                        print(f"Agregando a ({new_node_id}) a la finger table")
                        self.finger_table.append(ChordNodeReference(ip=request.node_reference.ip, port=request.node_reference.port, id=request.node_reference.id))
                    else: break
                elif self.id_in_between(pivot_id, self.apply_offset(self_id, 2**i), new_node_id):
                    self.finger_table[i] = ChordNodeReference(ip=request.node_reference.ip, port=request.node_reference.port, id=request.node_reference.id)
        print("paso 3 superado")
        
        # Chequeando hacia alante con pasos pequeños
        # -----------------------------------------------------
        # Aprovechando que se tienen las referencias en next[] de algunos nodos que puedan apuntar al intervalo de interes
        info = communication_messages.UpdateFingerTableRequest(node_reference=request.node_reference, interval_gap=request.interval_gap)
        for i in range(len(self.next)):
            next_id = self.next[i].id
            if (updates_so_far == 0 or 
                next_id == pivot_id or                                      # el i-esimo indice es pivot(el anterior al nuevo nodo). Este nodo
                self.gap(gap_beginning, next_id) > request.interval_gap or  # no hay posibilidad de que next[i] apunte al intervalo (pivot, new_node]
                updates_so_far>0 and self.id_in_between(self_id, self.apply_offset(pivot_id, -(2**(updates_so_far -1))), next_id)       # ya habiamos pasado por ahi actualizando
            ): break                                                        # Aqui no incluyo la condicion de que next_id este en el intervalo de interes, porque es imposible, recordar que cuando la condicion only_forward_updates esta activa significa que el nodo actual es el nuevo, y aqui se estan analizando sus proximos...
            ControlledThread(target=self.chord_client.update_finger_table_forward, args=(self.next[i], info), name=f"update_finger_table_forward a: next[{i}]: ({self.next[i].id}) -> {self.next[i].ip}:{self.next[i].port}")
        print("paso 4 superado")

        # Verificando si existe algun otro nodo mas adelante de next, que aun pueda apuntar al intervalo. wl el while lo que hace es basicamente iterar por los nodos
        #   en la lista de los nodos siguientes del nodo actual, e ir actualizando todas sus finger_tables, terminando de actualizar nodos en el momento que se alcance
        #   un nodo con id que quede a una distancia mayor que 'interval_gap' CONTANDO DESDE 'gap_beginning'. Si por casualidad se acaba la lista de nodos proximos y aun 
        #   queda diferencia con 'interval_gap', se le pide la lista de nodos al ultimo de los nodos en su lista de siguientes y se sigue actualizando la finger table de
        #   los mismos, asi sucesivamente.

        next_list = self.next
        next_list_len = len(self.next)
        while self.gap(gap_beginning, next_list[next_list_len-1].id) < request.interval_gap: # Si el nodo actual es pivot, a su vez es gap_beginning, y la distancia de pivot a su proximo nodo(que es el nuevo) ES INTERVAL_GAP!!!, por ende, nunca entrara en este while :)
            response = self.chord_client.send_me_your_next_list(next_list[next_list_len-1])
            next_list = [ChordNodeReference(id=node.id, ip=node.ip, port=node.port) for node in response.references]
            next_list_len = len(next_list)
            for node_ref in next_list:
                next_id = node_ref.id
                if (next_id == pivot_id or                                          # el i-esimo indice es pivot(el anterior al nuevo nodo). Este nodo
                    self.gap(gap_beginning, next_id) > request.interval_gap or      # no hay posibilidad de que next[i] apunte al intervalo (pivot, new_node]
                    (updates_so_far>0 and self.id_in_between(self_id, self.apply_offset(pivot_id, -(2**(updates_so_far -1))), next_id)) # ya habiamos pasado por ahi actualizando
                ): break
                ControlledThread(target=self.chord_client.update_finger_table_forward, args=(node_ref, info), name=f"update_finger_table_forward en una lista recibida, a: ({next_id})")
        print("paso 5 superado")

        if just_forward_updates: return communication_messages.OperationResult(success=True)    # Si el paso logaritmico hacia atras 
        # Chequeando hacia atras con pasos logaritmicos
        # -----------------------------------------------------
        # Saltando los ids que pertenezcan al nodo actual, o sea, los ids hacia atras en pasos logaritmicos de los que se sigue haciendo cargo el nodo actual. 
        #   Esto lo hago para evitar enviar solicitudes innecesarias a la red como un succesor y que lo reciba el propio nodo actual, cosas asi.
        next_id=None
        while updates_so_far <= self.nodes_count:
            if updates_so_far == self.nodes_count:
                return communication_messages.OperationReceived(success=True)
            next_id = self.apply_offset(pivot_id, -(2**(updates_so_far)))
            if self.id_in_between(self_id, next_id, pivot_id):   # next_id, o sea, el candidato a proximo nodo a actualizar, dio la vuelta entera al anillo, y cayo incluso fuera del intervalo de interes, que el responsable de este id es pivot, y este ya en este punto actualizo su finger table.
                return communication_messages.OperationReceived(success=True)
            # if self.id_in_between(self_id, next_id, new_node_id):   # next_id, o sea, el candidato a proximo nodo a actualizar, dio la vuelta entera al anillo, y cayo dentro del intervalo de interes, que el responsable de este id es new_node y este no tiene que actualizar su finger table y agregarse el mismo. O en un intervalo donde ya pasamos actualizando. Por eso pongo el intervalo entre el nodo actual y el nodo nuevo
            #     return communication_messages.OperationReceived(success=True)               # FIXME aqui puede pasar que no haya que actualizar el nodo a distancia logaritmica exactamente, pero si nodos a unos pasos hacia delante del mismo 
            if not self.belonging_id(next_id):
                break
            updates_so_far +=1

        if self.gap(next_id, pivot_id) >= 2**self.nodes_count: # doble capa de comprobacion para saber que no nos pasamos de distancia, tal vez esto nunca sucede.
            return communication_messages.OperationReceived(success=True)
        # Enviando la solicitud al proximo nodo
        operation_id = random.randint(1, 10000)
        info = communication_messages.UpdateFingerTableRequest(node_reference=request.node_reference, updates_so_far=updates_so_far+1, interval_gap=request.interval_gap)
        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.UPDATE_FINGER_TABLE, info=info)
        # succesor_thread = Thread(target=self.chord_client.succesor, args=(self.node_reference, next_id, next_id, communication_messages.UPDATE_FINGER_TABLE), daemon=True)
        info = communication_messages.RingOperationRequest(
            requesting_node= self.node_reference.grpc_format,
            searching_id= next_id,
            requested_operation= communication_messages.UPDATE_FINGER_TABLE,
            operation_id= operation_id
        )
        ControlledThread(target=self.succesor, args=(info, context), name="sucesor a: mi mismo")
        wait_for_results() # Esto al final lo que hace es printear el resultado de la operacion de 'update_finger_table' que se le hace al proximo nodo
        
        print("paso 6 superado")
        return communication_messages.OperationReceived(success=True)
        
                
    def update_finger_table_forward(self, request, context):                                                        # ✅
        print("🔹 Entre en update_finger_table_forward")

        new_node = request.node_reference
        interval_gap = request.interval_gap
        self_id = self.node_reference.id
        pivot_id = self.apply_offset(new_node.id, -interval_gap)
        for i in range(len(self.finger_table)):
            if self.id_in_between(pivot_id, self.finger_table[i].id, new_node.id):
                self.finger_table[i] = ChordNodeReference(ip=new_node.ip, port=new_node.port, id=new_node.id)
        return communication_messages.OperationReceived()

    def send_me_your_next_list(self, request, context):                                                             # ✅
        print("🔹 Entre en send_me_your_next_list")

        next_list= [communication_messages.ChordNodeReference(id=n.id, ip=n.ip, port=n.port) for n in self.next[:max(0, len(self.next) - 1)]] # En caso de que el nodo actual no tenga a nadie en next, aqui habra una lista vacia y mas adelante se agregara el mismo para enviarselo al nodo entrante
        return communication_messages.ChordNodeReferences(references=next_list)













# Metodos aunxiliares de los oficiales para evitar reguero
# ----------------------------------

    def Update_FingerTable_WithNextList(self, force=False):                                                                      # ✅
        print("🔗 Entre en Update_FingerTable_WithNextList")
        self_id = self.node_reference.id
        next_index = 0
        stop_updating = False
        for i in range(self.nodes_count):
            if stop_updating: break
            while not stop_updating:
                if i >= len(self.finger_table):
                    if self.id_in_between(self_id, self.apply_offset(self_id, 2**i), self.next[next_index].id):
                        print(f"Agregando a ({self.next[next_index].id}) a la finger table")
                        self.finger_table.append(self.next[next_index])
                        break
                    else: 
                        next_index += 1
                        # stop_updating = True
                        # continue
                elif ((force and self.id_in_between(self_id, self.apply_offset(self_id, 2**i), self.next[next_index].id)) or      # Si se fuerza la actualizacion, se actualiza la finger table con el nodo que corresponda, sin importar si mejora o no el nodo que ya estaba en la finger table
                        self.id_in_between(self.apply_offset(self_id, 2**i), self.next[next_index].id, self.finger_table[i].id)): # Esto comprueba que: 1) next[next_index] pueda ser responsable del id correspondiente del i-esimo puesto en la finger table y 2) que mejore el id del nodo que hasta el momento estaba
                    self.finger_table[i] = self.next[next_index]
                    break
                else: next_index += 1
                if next_index >= len(self.next):
                    stop_updating = True
# Replicas
    def Change_Replica_Leader(old_leader: ChordNodeReference, new_leader: ChordNodeReference):
        print("🔗 Entre en Change_Replica_Leader")
        self.db_replicas[new_leader] = (File_Tag_DB(f"phisical_storage-{new_leader.id}-{self.node_reference.id}")
                                                    , Files_References_DB(f"references-{new_leader.id}-{self.node_reference.id}"))
        replica_db = self.db_replicas.get(old_leader, None)
        result = []
        if replica_db:
            physical_storage = replica_db[0]
            references = replica_db[1]
            top_id = new_leader.id
            physical_files = physical_storage.File.select().where(physical_storage.File.location_hash <= top_id)
            references_files = references.File.select().where(references.File.location_hash <= top_id)
            for file in physical_files:
                physical_storage.SaveFile(file["name"], file["content"], file["location_hash"], *file["tags"])
            for file in references_files:
                references.SaveFile(file["name"], file["file_hash"], file["location_hash"], *file["tags"])
            return True
    def Join_Replica_Leader(new_leader: ChordNodeReference, old_leader: ChordNodeReference):
        print("🔗 Entre en Join_Replica_Leader")
        replica_db = self.db_replicas.pop(old_leader, None)
        if replica_db:
            self.db_replicas[new_leader][0].JoinDatabase(replica_db[0])
            self.db_replicas[new_leader][1].JoinDatabase(replica_db[1])
            replica_db.close[0]()
            replica_db.close[1]()
            
            return True
        return False
    def Change_Files_From_DB_to_Replicas(self, new_main_replica_node, pop_files=True):
        print("🔗 Entre en Change_Files_From_DB_to_Replicas")
        top_id = new_main_replica_node.id
        files_to_transfer = self.db_physical_files.File.select().where(self.db_physical_files.File.location_hash <= top_id) # La condicion de '''self.db_references.File.location_hash > bottom_id, ''' no es necesaria porque los archivos del nodo actual estan asignados aqui por tal motivo.
        files_references_to_transfer = self.db_references.File.select().where(self.db_references.File.location_hash <= top_id) 
        result = {"files": [], "references": []}
        # assert not self.db_replicas.get(new_main_replica_node, None)
        self.db_replicas[new_main_replica_node] = (File_Tag_DB(f"phisical_storage-{new_main_replica_node.id}-{self.node_reference.id}")
                                                    , Files_References_DB(f"references-{new_main_replica_node.id}-{self.node_reference.id}"))
        replica_physical_storage = self.db_replicas[new_main_replica_node][0]
        replica_references = self.db_replicas[new_main_replica_node][1]
        for file in files_to_transfer:
            result["files"].append({"name": file.name, "content": file.content, "file_hash": file.file_hash, "location_hash": file.location_hash, "tags": [tag.tag.name for tag in file.tags]})
            replica_physical_storage.SaveFile(file["name"], file["content"], file["location_hash"], *[tag.tag.name for tag in file["tags"]])
            if pop_files: file.delete_instance()

        for file in files_references_to_transfer:
            result["references"].append({"name": file.name, "file_hash": file.file_hash, "location_hash": file.location_hash, "tags": [tag.tag.name for tag in file.tags]})
            replica_references.SaveFile(file["name"], file["file_hash"], ile["location_hash"], *[tag.tag.name for tag in file["tags"]])
            if pop_files: file.delete_instance()
        return result

    def Change_Files_From_Replica_to_DB(self, main_replica_node_reference):
        print("🔗 Entre en Change_Files_From_Replica_to_DB")
        replication_db = self.Extract_ReplicaFiles_Fragment(main_replica_node_reference, pop_replica=True)
        if replication_db:
            for file in replication_db["files"]:
                self.db_physical_files.SaveFile(file["name"], file["content"], file["location_hash"], *[tag.tag.name for tag in file["tags"]])
            for file in replication_db["references"]:
                self.db_references.SaveFile(file["name"], file["file_hash"], file["location_hash"], *[tag.tag.name for tag in file["tags"]])
            return True
        return False
    def Extract_ReplicaFiles_Fragment(self, main_replica_node: ChordNodeReference, pop_replica=False):
        print("🔗 Entre en Extract_ReplicaFiles_Fragment")
        replication_db = self.db_replicas.pop(main_replica_node, (None, None)) if pop_replica else self.db_replicas.get(main_replica_node, (None, None))
        if replication_db[0] and replication_db[1]: # [0] es las replicas y [1] es las referencias
            files_to_transfer = replication_db[0].File.select()
            files_references_to_transfer = replication_db[1].File.select()
            result = {"files": [], "references": []}
            for file in files_to_transfer:
                result["files"].append({"name": file.name, "content": file.content, "location_hash": file.location_hash, "tags": [tag.tag.name for tag in file.tags]})
            for file in files_references_to_transfer:
                result["references"].append({"name": file.name, "file_hash": file.file_hash, "location_hash": file.location_hash, "tags": [tag.tag.name for tag in file.tags]})
        else: return None
        return result
                
    

    def AddFiles_To_Replica(self, main_replica_node: ChordNodeReference, files: list[dict[str, object]]):
        print("🔗 Entre en AddFiles_To_Replica")
        replication_db = self.db_replicas.get(main_replica_node, None)
        result_log = ""
        if replication_db[0] and replication_db[1]:
            for file in files:
                result_log += replication_db[0].SaveFile(file["name"], file["content"], file["location_hash"], *file["tags"])
        return result_log

    def AddReferences_To_Replica(self, main_replica_node: ChordNodeReference, files_references: list[dict[str, object]]):
        print("🔗 Entre en AddReferences_To_Replica")
        replication_db = self.db_replicas.get(main_replica_node, None)
        result_log = ""
        if replication_db[0] and replication_db[1]:
            for file in files_references:
                replication_db[1].SaveFile(file["name"], file["file_hash"], file["location_hash"], *file["tags"])
        return result_log
    
    def AddTags_To_Replica(self, main_replica_node:ChordNodeReference, tag_query: list[str], tag_list: list[str]):
        print("🔗 Entre en AddTags_To_Replica")
        result_log = ""
        replication_db = self.db_replicas.get(main_replica_node, None)
        if replication_db[0] and replication_db[1]: # [0] es las replicas y [1] es las referencias
            result_log += replication_db[0].AddTags(tag_query, tag_list)
            result_log += replication_db[1].AddTags(tag_query, tag_list)
        return result_log

                
                
    def DeleteFiles_From_Replica(self, main_replica_node: ChordNodeReference, tag_query: list[str]):
        print("🔗 Entre en DeleteFiles_From_Replica")
        replication_db = self.db_replicas.get(main_replica_node, None)
        # if not replication_db: 
        #     return ("No habia replica en este server del nodo solicitado")
        result_log = ""
        if replication_db[0] and replication_db[1]: # [0] es las replicas y [1] es las referencias
            result_log += replication_db[0].DeleteFiles(tag_query)
            result_log += replication_db[1].DeleteFiles(tag_query)
        return result_log
        # self.db_physical_files.File.delete().execute()
        # self.db_physical_files.FileTag.delete().execute()
    def DeleteTags_From_Replica(self, main_replica_node:ChordNodeReference, tag_query: list[str], tag_list: list[str]):
        print("🔗 Entre en DeleteTags_From_Replica")
        result_log = ""
        replication_db = self.db_replicas.get(main_replica_node, None)
        if replication_db[0] and replication_db[1]: # [0] es las replicas y [1] es las referencias
            result_log += replication_db[0].DeleteTags(tag_query, tag_list)
            result_log += replication_db[1].DeleteTags(tag_query, tag_list)
        return result_log
    
        



    
# Referencias
    def Change_Files_From_DB_to_References(self, new_main_replica: ChordNodeReference, pop_files=True):
        print("🔗 Entre en Change_Files_From_DB_to_References")
        files_to_transfer = self.db_physical_files.File.select().where(self.db_physical_files.File.location_hash <= new_main_replica.id)
        result = []
        for file in files_to_transfer:
            result.append({"name": file.name, "content": file.content, "location_hash": file.location_hash, "tags": [tag.tag.name for tag in file.tags]})
            if pop_files: file.delete_instance()
        return result
    def Extract_Files_From_References(self, top_id: int, pop_reference=False):
        print("🔗 Entre en Extract_Files_From_References")
        references_db = self.db_references.File.select().where(self.db_references.File.location_hash <= top_id)

        result = []
        for file in references_db:
            result.append({"name": file.name, "content": file.content, "location_hash": file.location_hash, "tags": [tag.tag.name for tag in file.tags]})
            if pop_reference: file.delete_instance()
        return result
    def AddFiles_To_References(self, files: list[dict[str, object]]):
        print("🔗 Entre en AddFiles_To_References")
        result_log = ""
        for file in files:
            result_log += self.db_references.SaveFile(file["name"], file["file_hash"], file["location_hash"], *file["tags"])
        return result_log
    def AddTags_To_References(self, tag_query: list[str], tag_list: list[str]):
        print("🔗 Entre en AddTags_To_References")
        result_log = ""
        result_log += self.db_references.AddTags(tag_query, tag_list)
        return result_log
    def DeleteTags_From_References(self, tag_query: list[str], tag_list: list[str]):
        print("🔗 Entre en DeleteTags_From_References")
        result_log = ""
        result_log += self.db_references.DeleteTags(tag_query, tag_list)
        return result_log
    def DeleteFiles_From_References(self, tag_query: list[str]):
        print("🔗 Entre en DeleteFiles_From_References")
        result_log = ""
        result_log += self.db_references.DeleteFiles(tag_query)
        return result_log
    

    # Replicacion y Comprobacion de vida
    def Manage_Heartbeats_AliveRequests(self):
        heat_factor = 1
        async def alive_request():
            print("Alive check started")
            while True:
                await asyncio.sleep(10 / heat_factor)
                no_problem = False
                for i, node in enumerate(self.next):
                    if no_problem: break
                    for _ in range(3):
                        try:
                            response = self.chord_client.alive_request(node)
                            if i == 0:
                                if not response.any_changes:
                                    no_problem = True
                                    break
                                print("Actualizando lista de next...")
                                assert response.HasField('next_nodes_list')
                                self.next.clear()
                                for node in response.next_nodes_list.references:
                                    self.next.append(ChordNodeReference(id=node.id, ip=node.ip, port=node.port))
                                self.any_changes_in_next_list = True
                                break
                            print("Se detecto un nodo que no responde, intentando recuperar datos...")
                            new_next_list = self.chord_client.send_me_your_next_list(node)
                            print("Actualizando lista de next...")
                            self.next.clear()
                            for n in new_next_list.references:
                                self.next.append(ChordNodeReference(id=n.id, ip=n.ip, port=n.port))
                            self.chord_client.i_am_your_prev(node, self.node_reference.grpc_format)
                            # Actualizando la finger table
                            self.Update_FingerTable_WithNextList(force=True)

                            self.any_changes_in_next_list = True
                            no_problem = True
                            break
                        except grpc.RpcError: 
                            # time.sleep(random.randint(1, 3)/heat_factor)
                            await asyncio.sleep(1/heat_factor)
                if not no_problem: 
                    print("No hay respuesta de los nodos proximos. La red esta temporalmente caida")
                    # self.Recover_Network()

                # Revisando los ultimos heartbeats
                for node, last_heartbeat in self.last_heartbeats.items():
                    if not self.is_alive(node):
                        print(f"El nodo ({node.id}) no responde a los heartbeats, se procede a eliminarlo")
                        self.Manage_Node_Failure(node)
                
        async def heartbeat():
            print("Heartbeat signals started")
            while True:
                await asyncio.sleep(10 / heat_factor)
                nodes_set = set()
                for replication_clique in self.replication_forest.values():
                    nodes_set.update(replication_clique)
                for node in nodes_set:
                    for _ in range(2):
                        try:
                            self.chord_client.heartbeat(node, self.node_reference.grpc_format)
                            break
                        except grpc.RpcError:
                            await asyncio.sleep(1)
        async def run_em():
            await asyncio.gather(alive_request(), heartbeat())
        asyncio.run(run_em())


    # Manejo de entrada y salida de nodos.
    def Manage_Node_Entrance(self, entrance_node_reference: ChordNodeReference, assigned_id):  # TODO Añadir las operaciones 'files_allotment_transfer', 'update_replication_clique' y 'unreplicate' y luego transferir sus archivos de almacenamiento a referencias.
        print("🔗 Entre en Manage_Node_Entrance")

        # -- Operaciones involucradas: 'i_am_your_next', 'update_finger_table', 'files_allotment_transfer', 'update_replication_clique', 'unreplicate'
        # 1) Comunicar con el nodo entrante para proveerle la info de entrada a la red: el id que le fue asignado, su lista de nodos proximos y su nodo anterior. Este ultimo sera el nodo actual en caso que sea el unico en la red.
        #   NOTE: El nodo actual no se encarga de hacer saber a 'prev' que entro un nuevo nodo que sera su proximo, ya que de esto se encargara este ultimo por su cuenta.
        # 2) Se comienza con el proceso de actualizacion de las finger tables, comenzando por el nodo previo al actual, el cual sera el nuevo 'prev' del nodo entrante.
        # 3) Cambiar los datos que tienen un id del que pueda ser responsable el nodo entrante, de la base de datos fisica hacia una nueva base de datos de replica creada en este paso tambien, con el nodo entrante como lider.
        # 4) Mandar los datos correpondientes al nodo entrante.
        # 5) Añadir el nodo entrante como lider en un nuevo clique en replication_forest con los mismos nodos que el clique del nodo actual, exluendo el nodo de mas adelante en el anillo, si ya se cumplia con el factor de replicacion.
        # 6) Transmitir, hacia los nodos del clique del que es replica principal, este cambio de lider para los datos en el intervalo del que es responsable el nuevo nodo. Aqui incluso se hace esta operacion al nodo que se desreplicara, 
        #   porque la operacion 'unreplicate' que se realizara mas adelante sobre este nodo, recibe la referencia de un nodo para quitarlo de sus replicas, y si aun no esta en sus replicas no podra realizar dicha operacion. Ademas de todas 
        #   formas se tiene que hacer la operacion de recuperacion de datos en el nodo que se desreplicara (para cambiar de lider los datos), y de esta forma se sigue haciendo una sola vez y al mismo tiempo queda de manera limpia. 
        #   En plan: 1) Cambia de lider 2) Elimina la replica del lider nuevo
        # 7) Excluir el nodo de mas adelante del anillo de los datos mencionados en el paso anterior o sea, aplicar la operacion de desreplicacion, a menos que no se haya alcanzado el factor de replicacion aun.
        #   NOTE: No se modifican los cliques a los que pertenece el nodo actual ya que esta responsabilidad recae en la verificacion de cambios en la lista next en el metodo 'Manage_Hearbeats_AliveRequests'.
        #   NOTE: El nodo actual ni siquiera le envia al nodo nuevo el clique de replicacion suyo propio, este puede deducirlo por si mismo dada la lista next que se le envio en el paso 1)
        # 8) Asignar el nodo entrante como 'prev' del nodo actual.

        # 1) ----------------------------------------
        next_list = [n.grpc_format for n in self.next[:max(0, min(len(self.next), self.next_alive_check_length -1))]] # En caso de que el nodo actual no tenga a nadie en next, aqui habra una lista vacia y mas adelante se agregara el mismo para enviarselo al nodo entrante
        next_list.insert(0, self.node_reference.grpc_format)
        prev = self.prev.grpc_format if self.prev else self.node_reference.grpc_format
        info = communication_messages.IAmYourNextRequest(next_list=communication_messages.ChordNodeReferences(references=next_list), 
                                                            prev=prev,
                                                            assigned_id=assigned_id)
        response = self.chord_client.i_am_your_next(entrance_node_reference, info) # En este metodo realizamos las llamadas sincronas y secuenciales porque hace falta dar un seguimiento de las operaciones.
        if not response.success: return

        
        # 2) ----------------------------------------
        if self.prev:
            pivot_id = self.prev.id
            interval_gap = self.gap(pivot_id, assigned_id)
            info = communication_messages.UpdateFingerTableRequest(node_reference=entrance_node_reference.grpc_format,
                                                                        updates_so_far=0, remaining_updates=self.nodes_count, interval_gap=interval_gap)
            self.chord_client.update_finger_table(node_reference=self.prev, info=info)
        # else: # Si el nodo actual es el unico en la red, ahora su proximo y su anterior es el mismo, y es el nodo que esta entrando en la red.
            # self.next.append(entrance_node_reference)  # NOTE No se actualiza la lista next[] porque ya de eso se encarga update_next, que en este caso se mandaria para este mismo nodo cuando se le envie al nodo entrante la solicitud de i_am_your_next porque el nodo actual es su prev ademas de ser su sucesor

        entrance_node_reference.id = assigned_id
        self.prev = entrance_node_reference


        # 3) ----------------------------------------
        # if self.replication_factor > 0: # FIXME agregar esto. Si el factor de replicacion es 0, no se deberia mantener replica en el nodo actual.
        files_to_transfer = self.Change_Files_From_DB_to_Replicas(new_main_replica_node=entrance_node_reference, pop_files=True)


        # 4) ----------------------------------------
        physical_storage_files = files_to_transfer["files"]
        files_references = files_to_transfer["references"]
        self.chord_client.files_allotment_transfer( 
                                                    node_reference=entrance_node_reference, 
                                                    info= communication_messages.FilesAllotmentTransferRequest(
                                                        files= [communication_messages.FileToTransfer(
                                                            file=communication_messages.FileContent(
                                                                title= file["name"],
                                                                content= file["content"],
                                                            ),
                                                            tags= file["tags"],
                                                            location= communication_messages.FileLocation(
                                                                file_hash= file["file_hash"],
                                                                location_hash= file["location_hash"]
                                                            )
                                                        ) for file in physical_storage_files]
                                                    )
                                                )

        # 5) ----------------------------------------
        self.replication_forest[entrance_node_reference] = self.replication_forest[self.node_reference].copy()


        # 6) ----------------------------------------
        for node in self.replication_forest[entrance_node_reference]:
            info = communication_messages.UpdateReplicationCliqueRequest(
                new_leader=entrance_node_reference.grpc_format, 
                old_leader=self.node_reference.grpc_format, 
                clique=communication_messages.ChordNodeReferences(
                    references=[n.grpc_format for n in self.replication_forest[entrance_node_reference]] + [self.node_reference.grpc_format]
                )
            )
            self.chord_client.update_replication_clique(node, info)
        
        # NOTE No es necesario actualizar la lista next de los nodos que ya estaban en la red porque ya eso se hace cuando se inserta un nodo nuevo paulatinamente con el LiveAnswer.



        # 7) ----------------------------------------
        if len(self.replication_forest[self.node_reference]) -1 >= self.replication_factor: 
            node_to_unreplicate = self.last_node_in_replication_clique(entrance_node_reference)
            if node_to_unreplicate == self.node_reference:
                del self.replication_forest[entrance_node_reference]
            else:
                self.chord_client.unreplicate(node_reference=node_to_unreplicate, info=entrance_node_reference.grpc_format)
                self.replication_forest[entrance_node_reference] -= { node_to_unreplicate }
            

        # 8) ----------------------------------------
        self.prev = entrance_node_reference

    def Manage_Node_Failure(self, failed_node: ChordNodeReference):
        """Funcion que maneja cuando un nodo falla, se encarga tanto de las replicas como de las referencias"""
        print("🔗 Entre en Manage_Node_Failure")



        # Actualizando la lista de next[] y prev
        if self.prev == failed_node:
            self.prev = None
        if failed_node in self.next:
            self.next.remove(failed_node)
            self.any_changes_in_next_list = True
            # Actualizando la finger table
            self.Update_FingerTable_WithNextList()
        # Actualizando las replicas y referencias
        if failed_node in self.replication_forest.keys(): # Si el nodo que fallo era el nodo principal de uno de los cliques de replicacion presentes en el nodo actual, o lo que es lo mismo, QUEDABA DETRAS en el anillo
            
            # Protocolo de votacion para elegir un nuevo nodo principal
            self_responsability = True
            for node in self.replication_forest[failed_node]:
                if self.id_in_between(failed_node.id, node.id, self.node_reference.id) and self.is_alive(node): # Si existe un nodo del clique de replicacion que tiene un id menor al del nodo actual, este sera el nuevo nodo principal y el nodo actual se despreocupa del procedimiento restante.
                    self_responsability = False
                    break
            
            # El nodo actual pasara a ser la nueva referencia principal del clique de replicacion
            if self_responsability:

                # Obtenemos los datos replica de los archivos del nodo fallido
                files_to_replicate_db = self.db_replicas.get(failed_node, None)


                # NOTE No se tiene que agregar ningun nodo nuevo al clique. Lo que se hace es:
                # -- Operaciones involucradas: 'update_replication_clique', 'replicate'
                # 1) Cambiar de lider a las replicas del nodo fallido en los nodos que estaban en su clique de replicacion
                # 2) Replicar los datos del nodo fallido a los nodos que no estaban en el clique del nodo fallido pero si en el clique del nodo actual
                # 3) Borrar el clique de replicacion del nodo fallido.
                # 4) Cambiar los datos replica del nodo fallido en el nodo actual, para el almacenamiento en la BD fisicos.

                # 1)-------------------------------------
                for n in self.replication_forest[failed_node]:
                    for i in range(2):
                        if not self.is_alive(n):
                            await asyncio.sleep(1/heat_factor)
                            continue
                        try:
                            info = communication_messages.UpdateReplicationCliqueRequest(
                                new_leader=self.node_reference.grpc_format, 
                                old_leader=failed_node.grpc_format, 

                                clique=communication_messages.ChordNodeReferences(
                                    references=[n_i.grpc_format for n_i in self.replication_forest[self.node_reference]]
                                )
                            )
                            self.chord_client.update_replication_clique(n, info)
                            break
                        except grpc.RpcError:
                            print(f"Manage_Node_Failure: fallo {i+1} en la actualizacion de cliques ")
                            pass

                # 2)-------------------------------------
                for n in filter(lambda n_i: n_i not in self.replication_forest[failed_node], self.replication_forest[self.node_reference]):
                    for i in range(2):
                        if not self.is_alive(n):
                            await asyncio.sleep(1/heat_factor)
                            continue
                        try:
                            physical_db_file, references_db_file = None, None
                            with open(files_to_replicate_db[0].name +".db", 'rb') as file:
                                physical_db_file = file.read()
                            with open(files_to_replicate_db[1].name +".db", 'rb') as file:
                                references_db_file = file.read()

                            physical_db_bytes = pickle.dumps(physical_db_file)
                            references_db_bytes = pickle.dumps(references_db_file)

                            info = communication_messages.RawDatabases(
                                db_phisical=physical_db_bytes, 
                                db_references=references_db_bytes, 
                                main_replica_node_reference= self.node_reference.grpc_format,
                            ) 
                            self.chord_client.send_raw_database_replica(n, info)
                            break
                        except grpc.RpcError:
                            print(f"Manage_Node_Failure: fallo {i+1} en la actualizacion de replicas")
                            pass
                        

                # 3)-------------------------------------
                del self.replication_forest[failed_node]

                # 4)-------------------------------------
                Change_Files_From_Replica_to_DB(failed_node)
                del self.db_replicas[failed_node]
        elif failed_node in self.replication_forest[self.node_reference]: # El nodo del fallo no se le guarda replica en este nodo, o lo que es lo mismo, EL NODO DEL FALLO QUEDA DELANTE EN EL ANILLO(GUARDA UNA REPLICA DEL NODO ACTUAL)
            # NOTE en este caso no se hace protocolo de voltacion porque ya se sabe en este punto que el nodo que fallo esta en el clique de replicacion
            # del nodo actual, y esta delante en el anillo, por ende, el nodo actual solo se encargara de su propia replica en el nodo fallido, replicando 
            # un nodo mas hacia delante en el anillo, y actualizando el clique de replicacion del nodo actual.
            # -- Operaciones involucradas: 'update_replication_clique', 'replicate'
            # 1) Buscar un nuevo nodo replica del nodo actual. No replicar en caso de que no hayan nodos disponibles, o sea, que todos los nodos del anillo guarden replica del nodo actual.
            # 2) Replicar en el nuevo nodo replica con una lista de archivos vacia. Solo para que se cree la base de datos.
            # 3) Mandar la base de datos pura hacia la nueva replica.
            # 4) Actualizar el clique de replicacion del nodo actual, quitando al nodo fallido y agregando el nuevo nodo replica.
            # 5) Actualizar el clique de replicacion de todos los nodos del clique con los cambios pertinentes.

            # 1)-------------------------------------
            new_replica_node = None
            for n in self.next:
                if n not in self.replication_forest[self.node_reference] and self.is_alive(n):
                    new_replica_node = n
                    break
            if not new_replica_node:
                print("No hay nodos disponibles para replicar")
                return
            
            # 2)-------------------------------------
            info = communication_messages.FilesToReplicate(
                files= communication_messages.FilesToAdd(
                    files=[],
                    tags=[]
                ),
                location_hash= -1,
                main_replica_node_reference= self.node_reference.grpc_format
            )
            self.chord_client.replicate(new_replica_node, info)

            # 3)-------------------------------------
            physical_db_file, references_db_file = None, None
            with open("phisical_storage.db", 'rb') as file:
                physical_db_file = file.read()
            with open("references.db", 'rb') as file:
                references_db_file = file.read()

            physical_db_bytes = pickle.dumps(physical_db_file)
            references_db_bytes = pickle.dumps(references_db_file)
            
            info = communication_messages.RawDatabases(
                db_phisical=physical_db_bytes, 
                db_references=references_db_bytes, 
                main_replica_node_reference= self.node_reference.grpc_format,
            ) 
            self.chord_client.send_raw_database_replica(new_replica_node, info)
            
            # 4)-------------------------------------
            self.replication_forest[self.node_reference] -= {failed_node}
            self.replication_forest[self.node_reference] |= {new_replica_node}

            # 5)-------------------------------------
            for n in self.replication_forest[self.node_reference]:
                info = communication_messages.UpdateReplicationCliqueRequest(
                    new_leader=self.node_reference.grpc_format, 
                    old_leader=self.node_reference.grpc_format, 
                    clique=communication_messages.ChordNodeReferences(
                        references=[n_i.grpc_format for n_i in self.replication_forest[self.node_reference]]
                    ) 
                )
                self.chord_client.update_replication_clique(n, info)
            



        
        
    def is_alive(self, node: ChordNodeReference, heat_factor=1):
        # print("🔗 Entre en is_alive")
        if node not in last_heartbeats.keys():
            print("Se intento verificar la actividad de un nodo que no se tiene registrado")
            return False
        if time.time() - last_heartbeats[node] <= NET_RECOVERY_TIME: return True
        for _ in range(3):
            try:
                self.chord_client.alive_request(node)
                return True
            except grpc.RpcError:
                asyncio.sleep(1/heat_factor)
                continue
        return False
    def last_node_in_replication_clique(self, main_replica: ChordNodeReference):
        # print("🔗 Entre en last_node_in_replication_clique")
        if len(self.replication_forest) or main_replica not in self.replication_forest.keys():
            return None
        from_main_replica_to_max = sorted(filter(lambda n_i: main_replica.id < n_i.id, self.replication_forest[main_replica] | self.node_reference), key=lambda n: n.id)
        from_min_to_main_replica = sorted(filter(lambda n_i: main_replica.id > n_i.id, self.replication_forest[main_replica] | self.node_reference), key=lambda n: n.id)
        if from_min_to_main_replica: return from_min_to_main_replica[-1]
        else: return from_main_replica_to_max[-1]
    def Recover_Network(self):
        print("🔗 Entre en Recover_Network")
        # Actualizando la lista de next[] y prev
        self.next.clear()
        self.prev = None
        # Actualizando la finger table
        self.Update_FingerTable_WithNextList()
        # Actualizando las replicas y referencias
        for node in self.db_replicas.keys():
            self.chord_client.unreplicate(node)
        self.db_replicas.clear()
        self.db_references.Clear()
        # Actualizando los archivos fisicos
        # self.db_references.Clear_Physical_Files()
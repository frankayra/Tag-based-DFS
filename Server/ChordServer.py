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
    def __init__(self, check_for_updates_func, port:int = 50052, nodes_count:int = 3, replication_factor = 3, docker_container_name = f'ds-server'):
        # self.id = 0                                                     # TODO
        self.check_for_updates_func = check_for_updates_func
        self.running_on_docker_container = False
        running_on_docker_container_input = input("Estas iniciando desde un contenedor Docker??(Si|No) ")
        match running_on_docker_container_input.casefold():
            case "si": self.running_on_docker_container = True
            case "no": self.running_on_docker_container = False
        ip = socket.gethostbyname(socket.gethostname()) if not running_on_docker_container else docker_container_name
        self.node_reference = ChordNodeReference(ip, port, self.id)           # TODO hacer un metodo aparte para inicializar el nodo con un id
        self.next:list[ChordNodeReference] = []
        self.prev:ChordNodeReference = None
        self.finger_table:list[ChordNodeReference] = []
        self.nodes_count:int = nodes_count
        self.next_list_size = 0
        self.replication_factor = replication_factor
        
        self.db_physical_files = File_Tag_DB('phisical_storage')
        self.db_replicas = File_Tag_DB('replicas')
        self.db_references = Files_References_DB('references')
        
        self.chord_client = ChordClient(nodes_count)
        self.pending_operations = {}
        self.ready_operations = {}
        self.replication_forest = {}
        

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
        del self.pending_operations[operation_id]
        # NOTE Aqui no hay que esperar nada porque ya el hilo principal espera por la respuesta
        # final del servidor.
        # Al recibir la respuesta se sigue el proceso no como cualquier otro metodo iterativo
        # no concurrente ni paralelo para meter el resltado en la bandeja de salida y asi ClientAPIServer 
        # lo toma y se lo envia al cliente.
        results = self.chord_client.RetakePendingOperation(node_reference, operation, info)
        # if operation == communication_messages.LIST:
        #     self.ready_operations[operation_id] = [item for item in results]
        # else:
        #     self.ready_operations[operation_id] = results

        # HACK Esto no se si hay que iterarlo y devolverlo o se puede devolver asi mismo sin iterar
        self.ready_operations[operation_id] = results
    def PushPendingOperation(self, operation_id, operation, info, function_to_apply_to_results = print):
        self.pending_operations[operation_id] = (operation, info)
        def wait_for_results():
            self.check_for_updates_func(operation_id)
            results = self.ready_operations[operation_id]
            del self.ready_operations[operation_id]
            print(f"Operacion Realizada: {operation}   => Resultados: {results}")
            if function_to_apply_to_results != print:
                function_to_apply_to_results(results)
        checking_for_results_thread = Thread(target=wait_for_results)
        def start_thread():
            checking_for_results_thread.start()
        return start_thread

    def belonging_id(self, searching_id):
        if not self.prev:
            return True
        self_id = self.node_reference.id
        prev_id = self.prev.id
        # prev_id  <   searching_id   <=   self_id
        # return searching_id <= self_id and (prev_id < searching_id or prev_id > self_id)        # BUG Esto da un falso negativo en el caso de que este self_id con un id de los primeros y prev_id con uno de los ultimos, y caiga searching_id entre los dos pero del lado de prev_id, de los mayores ids.
        return (prev_id < searching_id <= self_id) or (self_id < prev_id and (searching_id > prev_id or searching_id <= self_id))
    def id_in_between(self, base_id, id_to_be_surpassed, base_id_offset):
        # return base_id_offset >= id_to_be_surpassed or base_id_offset < base_id     # BUG Esto se parte en el caso de que esten base_id_offset y base_id en el final del anillo, y id_to_be_suprpassed este por el principio, este caso da verdadero por la primera condicion y este ejemplo seria un falso positivo.
        return (base_id < id_to_be_surpassed <= base_id_offset) or (base_id_offset < base_id and (id_to_be_surpassed > base_id or id_to_be_surpassed <= base_id_offset))
    def gap(self, id_prev, id_next):
        return id_next - id_prev if id_next-id_prev >= 0 else id_next + (2**self.nodes_count - id_prev) # suma de los 2 trozitos.
    def apply_offset(self, base_id, offset):
        return (base_id + offset + (2**self.nodes_count)) % (2**self.nodes_count)










# Operaciones fundamentales de comunicacion
    def succesor(self, request, context):               # ✅
        next_node: ChordNodeReference = None
        self_id = self.node_reference.id
        requesting_node = ChordNodeReference(request.requesting_node.ip, request.requesting_node.port, request.requesting_node.id)

        # Vemos si el sucesor que se esta buscando es el nodo actual, si es asi, paramos aqui la busqueda y se envia al nodo solicitante un a solicitud para que prosiga con la operacion para la que se buscaba el responsable del id en cuestion
        if self.belonging_id(request.searching_id):
            # HACK Esto con el hilo asi no estoy del todo seguro que funciona. 
            continuing_with_operation_thread = Thread(target=self.chord_client.proceed_with_operation, args=(self.node_reference, requesting_node, request.searching_id, request.requested_operation, request.operation_id))
            continuing_with_operation_thread.start()
            return communication_messages.OperationReceived(success=True)
            

            
        for i in range(self.nodes_count-1, -1, -1):
            # Se busca un id pa lante en el anillo, pero esta detras, hay que dar la vuelta entera. 
            # Fijarse que esto no es una comparacion a ver si un id esta intermedio, esto se comprueba porque en el "if" de abajo, toma de manera greedy el primer nodo de la finger table 
            #   que se encuentre de atras para adelante que sea menor que el id que se busca, pero esto no avanza todo lo que se puede en todos los casos. En particular en el caso de que el id 
            #   que se busca, se encuentre en primera instancia detras del nodo que lo busca, en este caso se tiene que dar una vuelta completa por el anillo, y en este caso hay que tomar
            #   siempre el nodo mas avanzado en el anillo (mas alante en la finger table tambien), que a su vez sea menor que el id que buscamos. 
            # Si se tenia este caso de un nodo buscando un id que le queda detras, y el i-esimo nodo de la finger table resulta tener mayor id que el id que se busca, pues 'continue' para seguir
            #   buscando en el resto de nodos en la finger table (que tienen menor id)
            if request.searching_id < requesting_node.id <= self_id :    
                if self.finger_table[i].id > self_id or self.finger_table[i].id < request.searching_id: # Seleccionando el nodo i-esimo de la finger table, es viable, o sea, se avanzara hacia encontrar el id que se busca (sin pasarse).
                    next_node = self.finger_table[i]
                    break
                continue
            if self.finger_table[i].id < request.searching_id:
                next_node = self.finger_table[i]
                break
        if not next_node:
            next_node = self.finger_table[0] # Esto garantiza que pueda haber salto cuando el nodo siguiente al actual es el nodo responsable del id que se busca ya que este ultimo por lo tanto tiene un id mayor y no sera escogido para ser el siguiente por el algoritmo.

        address = next_node.uri_address
        # HACK Esto con el hilo asi no estoy del todo seguro que funciona. 
        # self.chord_client.succesor(next_node, request.searching_id, request.requested_operation, request.operation_id)
        continuing_with_operation_thread = Thread(target=self.chord_client.succesor, args=(next_node, request.searching_id, request.requested_operation, request.operation_id))
        continuing_with_operation_thread.start()
        return communication_messages.OperationReceived(success=True)
    def proceed_with_operation(self, request, context):         # TODO Verificar si esto funciona bien tambien para las operaciones que son pusheadas u ordenadas desde el propio ChordServer
        node_reference = ChordNodeReference(request.node_reference.ip, request.node_reference.port, request.node_reference.id)
        operation = request.requested_operation
        operation_id = request.operation_id

        continuing_with_operation_thread = Thread(target=self.RetakePendingOperation, args=(node_reference, operation, operation_id))
        continuing_with_operation_thread.start()
        return communication_messages.OperationReceived(success=True)


# CRUD
# ----------------------------------
    def list(self, request, context):                   # ✅
        """TagList {tags: string[]}    =>    FileGeneralInfo {title: string, tag_list: strin[], location: FileLocation {file_hash:int, location_hash: int}}"""
        files_list = []
        tag_query = [tag for tag in request.tags]
        recovered_files = self.db_physical_files.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)
        recovered_files_references = self.db_references.RecoveryFilesInfo_ByTagQuery(tag_query, include_tags=True)

        for item in recovered_files:
            files_list.append(item)
        for item in recovered_files_references:
            files_list.append(item)

        try:
            first_file = next(files_list)
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
        for file in files_list:
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
    def file_content(self, request, context):           # ✅
        """FileLocation {file_hash:int, location_hash:int}    =>    FileContent {title:string, content:string}"""
        file_hash = request.file_hash
        recovered_file = self.db_physical_files.RecoveryFileContent_ByInfo(file_hash)
        if not recovered_file: return communication_messages.FileContent(title=None, content=None)
        return communication_messages.FileContent(title=recovered_file.name, content=recovered_file.content)
    def add_files(self, request, context):              # ✅
        """FilesToAddWithLocation {files: FileContent[] {title: string, content: string}, tags: string[], location_hash: int}    =>    OperationResult {success: bool, message: string}"""
        try:
            add_files_message = self.db_physical_files.AddFiles([(file.title, file.content) for file in request.files], [tag for tag in request.tags], location_hash)
            return communication_messages.OperationResult(success=True, message=f"Archivos añadidos satisfactoriamente: {add_files_message}")
        except Exception as e:
            return communication_messages.OperationResult(success=False, message=f"Error al añadir los archivos solicitados: {e}")
    def add_tags(self, request, context):               # ✅
        """TagQuery {tag_query: string[], operation_tags}    =>    OperationResult {success: bool, message: string}"""
        try:
            tag_query = [tag for tag in request.tags_query]
            operation_tags = [tag for tag in request.operation_tags]
            add_tags_message = self.db_physical_files.AddTags(tag_query, operation_tags)
            return communication_messages.OperationResult(success=True, message=add_tags_message)
            # return communication_messages.OperationResult(success=True, message="Tags añadidas satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al añadir los tags")
    def delete(self, request, context):                 # ✅
        """TagList {tags: string}    =>    OperationResult {success: bool, message: string}"""
        try:
            tag_query = [tag for tag in request.tags]
            delete_message = self.db_physical_files.DeleteFiles(tag_query)
            return communication_messages.OperationResult(success=True, message=delete_message)
            # return communication_messages.OperationResult(success=True, message="Archivos eliminados satisfactoriamente")
        except Exception:
            return communication_messages.OperationResult(success=False, message="Error al eliminar los archivos")

    def delete_tags(self, request, context):            # ✅
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
    def replicate(self, request, context):
        """FilesToReplicate {files: FilesToAdd {files: FileContent[] {title: atring, content: string}}, location_hash: int, main_replica_node_reference: ChordNodeReference {id: int, ip: string, port: int}}    =>    OperationResult {success: bool, message: string}"""
        pass
    def send_raw_database_replica(self, request, context): 
        """RawDatabases {db_phisical: bytes, db_references: bytes}    =>    OperationResult {success: bool, message: string}"""
        pass
    def add_references(self, request, context): 
        """FilesReferencesToAdd {location_hash: int, files_references: FileReference[] {title: string, file_hash: int}, tags: string[]}    =>    OperationResult {success: bool, message: string}"""
        pass
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
        pass
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
    def node_entrance_request(self, request, context):  # ✅

        # Verificando si se puede dar de alta al nuevo nodo aqui mismo.
        # ----------------------------------
        # Verificando si el nodo esta dentro de los ids que el nodo actual maneja y este puede ponerlo como su anterior, integrandolo a la red.
        # Fijarse que aqui tambien se filtra, o entra, cuando el id que se reclama coincide con el del nodo actual. En este caso se sigue buscando
        #   otro id libre en la red segun mi algoritmo de encontrar id libre para un nuevo nodo.
        if self.belonging_id(request.claiming_id):
            if request.claiming_id != self.node_reference.id or not self.prev:
                entrance_node_reference = request.new_node_reference


                continuing_operation_thread = Thread(target=self.Resolve_NodeEntrance, args=(entrance_node_reference, request.claiming_id))
                continuing_operation_thread.start()
                return communication_messages.OperationResult(success=True, message="Se encontro un hueco para el nuevo nodo")
            
        next_node = None
        new_claiming_id = 0
        gap = self.gap(self.node_reference.id, self.next[0].id)
        if gap > 1: 
            next_node = self.next[0]
            new_claiming_id = self.apply_offset(self.node_reference.id, int(gap/2))
        else:
            for i in range(1, self.next_list_size):
                gap = self.gap(self.next[i-1], self.next[i].id)
                if gap > 1:
                    next_node = self.next[i]
                    new_claiming_id = self.apply_offset(next_node.id, int(gap/2))
                    break

        # Redireccionando la operacion de 'node_entrance_request' para el siguiente nodo
        # -----------------------------------------
        # Caso en que habiamos encontrado en next[] un intervalo o espacio vacio, y vamos a enviar la solicitud hacia el nodo siguiente, responsable del id escogido en dicho espacio vacio.
        if next_node:
            info = communication_messages.NodeEntranceRequest(new_node_reference=request.new_node_reference, claiming_id=new_claiming_id)
            continuing_operation_thread = Thread(target=self.chord_client.node_entrance_request, args=(next_node, info))
            continuing_operation_thread.start()
            return communication_messages.OperationResult(success=True, message="Seguimos buscando un hueco para el nuevo nodo")
        
        # Caso en que no se encontro id libre en next[] y se procede a seguir con el algoritmo para encontrar hueco libre, ahora buscando un id random
        #   que inteligentemente no este en el intervalo de ids del nodo actual hasta el id del ultimo nodo de next[] (next[-1]).
        if self.node_reference.id < self.next[self.next_list_size-1]: # Esto pasa cuando el id de next[-1] no ha dado un salto en el final del anillo.
            if self.next[self.next_list_size-1].id == 2**self.nodes_count -1: # Esto es cuando el ultimo nodo de next[] tiene id igual al ultimo id posible del anillo, en este caso no es necesario tener en cuenta el intervalo de next[-1] al final del anillo.
                new_claiming_id = random.randint(0, self.node_reference.id)
            else:
                new_claiming_id = random.choice([random.randint(0, self.node_reference.id), random.randint(self.next[self.next_list_size-1].id +1, 2**self.nodes_count)])
        else: 
            new_claiming_id = random.randint(self.next[self.next_list_size-1] +1, self.node_reference.id)
        new_claiming_id
        info = communication_messages.NodeEntranceRequest(new_node_reference=request.new_node_reference, claiming_id=new_claiming_id)
        continuing_operation_thread = Thread(target=self.chord_client.node_entrance_request, args=(next_node, info))
        continuing_operation_thread.start()
        return communication_messages.OperationResult(success=True, message="Seguimos buscando un hueco para el nuevo nodo")
        




    def i_am_your_next(self, request, context):         # ✅
        """IAmYourNextRequest    =>    OperationReceived"""
        
        # Actualizamos el id del nodo actual con la id que se asigno en el proceso de busqueda del anillo, asi como la lista next[] y prev
        self.next.clear()
        for node in request.next_list:
            self.next.append(ChordNodeReference(ip=node.ip, port=node.port, id=node.id))
        self.prev = ChordNodeReference(ip=request.prev.ip, port=request.prev.port, id=request.prev.id)
        self.node_reference.id = request.assigned_id

        # Enviamos la referencia del nodo actual al nuevo nodo prev para que actualice su lista next[]
        info = self.node_reference.grpc_format
        update_prev_thread = Thread(target=self.chord_client.update_next, args=info)
        update_prev_thread.start()

        # Pedimos al nuevo nodo proximo (next[0]) que le envie al nodo actual los archivos que le tocan
        # operation_id = random.randint(1, 10000000000000)
        # info = communication_messages.Empty()
        # for node in self.next:
        #     self.chord_client.update_replication_clique(node, )
        
        
        return communication_messages.OperationReceived(success=True)







        
    # def update_next(self, request, context): pass
    def files_allotment_transfer(self, request, context): pass
    def update_replication_clique(self, request, context): pass


# Salida de un nodo de la red
# ----------------------------------
    def i_am_your_prev(self, request, context): pass


# Actualizar finger tables
# ----------------------------------
    def update_finger_table(self, request, context):                # ✅
        # Constants
        updates_so_far = request.updates_so_far
        new_node_id = request.node_reference.id
        pivot_id = self.apply_offset(new_node_id, -request.interval_gap)
        self_id = self.node_reference.id
        gap_beginning = self.apply_offset(pivot_id, -(2**updates_so_far))

        # Ya se hicieron todos los saltos hacia atras actualizando
        if updates_so_far >= self.nodes_count: return communication_messages.OperationReceived(success=True)

        # Chequeando las referencias de la finger table del nodo actual, y cambiando las que apunten al rango (pivot_id, new_node_id]
        # -----------------------------------------------------
        for i in range(len(self.finger_table)):
            if self.id_in_between(pivot_id, self.apply_offset(self_id, 2**i), new_node_id):
                self.finger_table[i] = ChordNodeReference(ip=request.node_reference.ip, port=request.node_reference.port, id=request.node_reference.id)
        
        # Chequeando hacia alante con pasos pequeños
        # -----------------------------------------------------
        # Aprovechando que se tienen las referencias en next[] de algunos nodos que puedan apuntar al intervalo de interes
        info = communication_messages.UpdateFingerTableRequest(node_reference=request.node_reference, interval_gap=request.interval_gap)
        for i in range(self.next_list_size):
            next_id = self.next[i].id
            if (next_id == pivot_id or # el i-esimo indice es pivot(el anterior al nuevo nodo). Este nodo
                (updates_so_far>0 and self.id_in_between(self_id, pivot_id - 2**(updates_so_far -1), next_id)) or # ya habiamos pasado por ahi actualizando
                self.gap(gap_beginning, next_id) > request.interval_gap): # no hay posibilidad de que next[i] apunte al intervalo (pivot, new_node]
                break
            update_finger_table_forward_thread = Thread(target=self.chord_client.update_finger_table_forward, args=(info))
            update_finger_table_forward_thread.start()

        # Verificando si existe algun otro nodo mas adelante de next, que aun pueda apuntar al intervalo. wl el while lo que hace es basicamente iterar por los nodos
        #   en la lista de los nodos siguientes del nodo actual, e ir actualizando todas sus finger_tables, terminando de actualizar nodos en el momento que se alcance
        #   un nodo con id que quede a una distancia mayor que 'interval_gap' CONTANDO DESDE 'gap_beginning'. Si por casualidad se acaba la lista de nodos proximos y aun 
        #   queda diferencia con 'interval_gap', se le pide la lista de nodos al ultimo de los nodos en su lista de siguientes y se sigue actualizando la finger table de
        #   los mismos, asi sucesivamente.
        next_list = self.next
        next_list_len = self.next_list_size
        while self.gap(gap_beginning, next_list[next_list_len-1].id) <= request.interval_gap:
            response = self.chord_client.send_me_your_next_list(next_list[next_list_len-1])
            next_list = [ChordNodeReference(id=node.id, ip=node.ip, port=node.port) for node in response]
            next_list_len = len(next_list)
            for item in next_list:
                next_id = item.id
                if (next_id == pivot_id or # el i-esimo indice es pivot(el anterior al nuevo nodo). Este nodo
                    (updates_so_far>0 and self.id_in_between(self_id, pivot_id - 2**(updates_so_far -1), next_id)) or # ya habiamos pasado por ahi actualizando
                    self.gap(gap_beginning, next_id) > request.interval_gap): # no hay posibilidad de que next[i] apunte al intervalo (pivot, new_node]
                    break
                update_finger_table_forward_thread = Thread(target=self.chord_client.update_finger_table_forward, args=(info))
                update_finger_table_forward_thread.start()

        # Chequeando hacia atras con pasos logaritmicos
        # -----------------------------------------------------
        # Saltando los ids que pertenezcan al nodo actual, o sea, los ids hacia atras en pasos logaritmicos de los que se sigue haciendo cargo el nodo actual. 
        #   Esto lo hago para evitar enviar solicitudes innecesarias a la red como un succesor y que lo reciba el propio nodo actual, cosas asi.
        while True:
            next_id = self.apply_offset(pivot_id, -(2**(updates_so_far +1)))
            if next_id == new_node_id:
                return communication_messages.OperationReceived(success=True)               # FIXME aqui puede pasar que no haya que actualizar el nodo a distancia logaritmica exactamente, pero si nodos a unos pasos hacia delante del mismo como por ejemplo en un anillo con 4 nodos, donde si se tira para atras -(2**2) ids, obtenemos el mismo nodo desde es que estamos intentando actualizar los demas, pero el de -(2**2) +1, que tambien puede referenciar al nodo actual, no estaria siendo actualizado.
            if not self.belonging_id(next_id):
                break
            updates_so_far +=1
        
        # Enviando la solicitud al proximo nodo
        operation_id = random.randint(1, 10000000000000)
        info = communication_messages.UpdateFingerTableRequest(node_reference=request.node_reference, updates_so_far=updates_so_far+1, interval_gap=request.interval_gap)
        wait_for_results = self.PushPendingOperation(operation_id=operation_id, operation=communication_messages.UPDATE_FINGER_TABLE, info=info)
        succesor_thread = Thread(target=self.chord_client.succesor, args=(self.node_reference, next_id, communication_messages.UPDATE_FINGER_TABLE))
        succesor_thread.start()
        wait_for_results() # Esto al final lo que hace es printear el resultado de la operacion de 'update_finger_table' que se le hace al proximo nodo
        
        return communication_messages.OperationReceived(success=True)
        
                
    def update_finger_table_forward(self, request, context):        # ✅
        new_node = request.node_reference
        interval_gap = request.interval_gap
        self_id = self.node_reference.id
        pivot_id = self.apply_offset(new_node.id, -interval_gap)
        for i in range(len(self.finger_table)):
            if self.id_in_between(pivot_id, self.finger_table[i].id, new_node.id):
                self.finger_table[i] = ChordNodeReference(ip=new_node.ip, port=new_node.port, id=new_node.id)
        return communication_messages.OperationReceived()

    def send_me_your_next_list(self, request, context):             # ✅
        next_list= [communication_messages.ChordNodeReference(id=n.id, ip=n.ip, port=n.port) for n in self.next[:max(0, self.next_list_size - 1)]] # En caso de que el nodo actual no tenga a nadie en next, aqui habra una lista vacia y mas adelante se agregara el mismo para enviarselo al nodo entrante
        return communication_messages.ChordNodeReferences(references=next_list)













# Metodos aunxiliares de los oficiales para evitar reguero
# ----------------------------------
    def Resolve_NodeEntrance(self, entrance_node_reference: ChordNodeReference, assigned_id):  # TODO Añadir las operaciones 'files_allotment_transfer', 'update_replication_clique' y 'unreplicate' y luego transferir sus archivos de almacenamiento a referencias.
        # if self.prev == None or self.next_list_size == 0:      # TODO

        # Enviandole al nodo entrante, la informacion de entrada a la red, como el id que se fue asignado, asi como sus nodos proximos y su nodo anterior en el anillo.
        next_list = [communication_messages.ChordNodeReference(n.id, n.ip, n.port) for n in self.next[:max(0, self.next_list_size - 1)]] # En caso de que el nodo actual no tenga a nadie en next, aqui habra una lista vacia y mas adelante se agregara el mismo para enviarselo al nodo entrante
        next_list.insert(0, self.node_reference)
        prev = self.prev.grpc_format if self.prev else self.node_reference.grpc_format
        info = communication_messages.IAmYourNextRequest(next_list=communication_messages.ChordNodeReferences(references=next_list), 
                                                            prev=prev,
                                                            assigned_id=assigned_id)
        response = self.chord_client.i_am_your_next(entrance_node_reference, info) # En este metodo realizamos las llamadas sincronas y secuenciales porque hace falta dar un seguimiento de las operaciones.
        if not response.success: return
        if not self.prev: # Si el nodo actual es el unico en la red, ahora su proximo y su anterior es el mismo, y es el nodo que esta entrando en la red.
            self.prev = entrance_node_reference
            self.next.append(entrance_node_reference)

        # Le pedimos a prev que actualice su finger table, y que siga el con las actualizaciones, segun mi algoritmo de actualizacion de fingers tables.
        pivot_id = self.prev.id
        interval_gap = self.gap(pivot_id, entrance_node_reference.id)
        info = communication_messages.UpdateFingerTableRequest(node_reference=communication_messages.ChordNodeReference(id=entrance_node_reference.id, ip=entrance_node_reference.ip, port=entrance_node_reference.port),
                                                                    updates_so_far=0, remaining_updates=self.nodes_count, interval_gap=interval_gap)
        # HACK No se si con esto sera suficiente o correcto
        self.chord_client.update_finger_table(node_reference=self.prev, info=info)

        # Realizando las operaciones:'files_allotment_transfer', 'update_replication_clique' y 'unreplicate'
        # ----------------------------------------

        # 'files_allotment_transfer'
        # files_to_transfer = self.ChangeFiles_FromPhisical_to_Replicated()
        # info = communication_messages.FilesAllotmentTransferRequest(files=files_to_transfer)
        # self.chord_client.files_allotment_transfer(node_reference=entrance_node_reference, info=info)

        # 'update_replication_clique'
        # for node in self.replication_forest.keys:
        #     del self.replication_forest[replication]
        #     replication_array.clear()
        # self.chord_client.update_replication_clique
            
        # 'unreplicate'
        # Bla bla bla bla



        # Actualizando los datos del nodo actual
        if self.next_list_size == 0: 
            self.next.append(entrance_node_reference)
            self.next_list_size +=1
        self.prev = entrance_node_reference




    def ChangeFiles_FromPhisical_to_Replicated(self, bottom_id, top_id): pass
        # TODO Usar un array deesta estructura para devolver la respuesta communication_messages.FileToTransfer()
    def DeleteFiles_FromReplicated(self, bottom_id, top_id): pass

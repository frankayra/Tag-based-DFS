from threading import Thread, Event
import time
import re
import platform
import os
import sys
import socket



import docker


from ChordServer import ChordServer
from ChordClient import ChordClient, ChordNodeReference
from ClientAPIServer import ClientAPIServer


if __name__ == '__main__':
    parameters = sys.argv
    server_to_request_entrance = None
    nodes_count = 3
    replication_factor = 2
    next_alive_check_length = 2
       
    if len(parameters) == 2:
        if parameters[1] == "localhost":
            ip = "localhost"
            port = 50051
        elif parameters[1] == "localgest":
            ip = "localhost"
            server_to_request_entrance = ChordNodeReference(ip="localhost", port=50052, id=-1) 

            # Autodescubrimiento de puertos
            # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            #     s.settimeout(1)
            #     for test_port in range(50051, 50200):

            #         try:
            #             s.connect(("localhost", test_port)) # s.bind((host, puerto))
            #             print(f"puerto {test_port} ocupado")
            #         except socket.error:
            #             port = test_port
            #             break

            port = 50053
    elif len(parameters) == 3:
        port = int(parameters[1])
        entrance_request_address = parameters[2]
        exp = r'^(?P<ip>[\w\.]+):(?P<port>[\d]+)$'
        coincidence = re.match(exp, entrance_request_address)
        if coincidence:
            ip = "localhost"
            server_to_request_entrance = ChordNodeReference(ip=coincidence.group('ip'), port=coincidence.group('port'), id=-1) 
                
    api_server = ClientAPIServer(ip, port, nodes_count, replication_factor, next_alive_check_length, server_to_request_entrance)




    
    # nodes_count = int(input("Cantidad de bits de identificador: "))
    # replication_factor = int(input("factor de replicacion: "))
    # while(replication_factor > 2**nodes_count):
    #     print("El factor de replicacion no deberia ser mayor que la cantidad de nodos de la red")
    #     replication_factor = int(input("factor de replicacion: "))

    # port = int(input("Puerto para la Api (Tener en cuenta que tambien se usa internamente [el puerto que escojas  +1] asi que debe estar libre): "))
    # entrance_request_address = input("Provee la direccion de un nodo del anillo para entrar a traves de el. Debe ser en el formato ip:puerto. Si quieres que se cree un nuevo anillo, solo deja en blanco este campo: ")
    # exp = r'^(?P<ip>[\w\.]+):(?P<port>[\d]+)$'
    # coincidence = re.match(exp, entrance_request_address)
    # server_to_request_entrance = None
    # if coincidence:
    #     server_to_request_entrance = ChordNodeReference(ip=coincidence.group('ip'), port=coincidence.group('port'), id=-1) 
    
    

    ######### Propiedades globales ##########
    # nodes_count = 3
    # replication_factor = 2
    # next_alive_check_length = 2

    ######### Primer Nodo ##########
    # port = 50051
    # server_to_request_entrance = None

    ######### Nodo entrante ##########
    # port = 50053
    # server_to_request_entrance = ChordNodeReference("localhost", 50052, -1)



    
    
    # api_server = ClientAPIServer(port, nodes_count, replication_factor, next_alive_check_length, server_to_request_entrance)













    
    time.sleep(5)
    try:
        while True:
            # operating_s = platform.system()
            # if operating_s == "Windows":
            #     os.system('cls')
            # else:
            #     os.system('clear')
            print(f"mi id es: {api_server.chord_server.node_reference.id}")
            print("proximos: ", [f"{n.id}--> {n.ip}:{n.port} " for n in api_server.chord_server.next])
            if api_server.chord_server.prev:
                print("anterior: ", f"{api_server.chord_server.prev.id}--> {api_server.chord_server.prev.ip}:{api_server.chord_server.prev.port}")
            time.sleep(20)  # Mantener el hilo principal activo
    except KeyboardInterrupt:
        print("Interrupción recibida. Saliendo del programa.")

















    # running_on_docker_container_input = input("Estas iniciando desde un contenedor Docker??(Si|No) ")
    # match running_on_docker_container_input.casefold():
    #     case "si": ip = docker_container_name
    #     case "no": ip = socket.gethostbyname(socket.gethostname())

        # # Señalizar a los hilos que deben detenerse
        # stop_threads.set()  
        # # Esperar a que los hilos terminen
        # API_thread.join(timeout=1)          
        # ChordServer_thread.join(timeout=1)
        # print("Programa finalizado de manera ordenada.")

# def running_on_docker():
#     client = docker.from_env()
#     network_name = "ds-network"
#     try:
#         # Obtener la red especificada
#         network = client.networks.get(network_name)
        
#         # Obtener los contenedores conectados a la red
#         containers = network.containers
#         print(f"Contenedores en la red '{network_name}':")
#         for container in containers:
#             print(f"- {container.name} ({container.short_id})")
#             name = contenedor.name
#             networks = info.get('NetworkSettings', {}).get('Networks', {})
#             ip_address = networks.get(network_name, {}).get('IPAddress', 'N/A')
#         return containers
#     except docker.errors.NotFound:
#         print(f"La red '{network_name}' no existe.")
#         return []
from threading import Thread, Event
import time
import docker

from ChordServer import ChordServer
from ChordClient import ChordClient, ChordNodeReference
from ClientAPIServer import ClientAPIServer


if __name__ == '__main__':
    
    nodes_count = int(input("Cantidad de bits de identificador: "))
    port = int(input("Puerto para la Api (Tener en cuenta que tambien se usa internamente [el puerto que escojas  +1] asi que debe estar libre): "))
        
    
    # running_on_docker_container_input = input("Estas iniciando desde un contenedor Docker??(Si|No) ")
    # match running_on_docker_container_input.casefold():
    #     case "si": ip = docker_container_name
    #     case "no": ip = socket.gethostbyname(socket.gethostname())
    
    api_server = ClientAPIServer(port, nodes_count)
    API_thread = Thread(target=api_server.serve, daemon=True)
    ChordServer_thread = Thread(target=api_server.chord_server.serve, args=(port +1,), daemon=True)

    # API_thread.daemon = True
    # ChordServer_thread.daemon = True


    API_thread.start()
    time.sleep(1)
    ChordServer_thread.start()
    try:
        while True:
            time.sleep(0.1)  # Mantener el hilo principal activo
    except KeyboardInterrupt:
        print("Interrupción recibida. Saliendo del programa.")

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
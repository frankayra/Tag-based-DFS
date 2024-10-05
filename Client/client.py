
import time
import os
# import sys
# sys.path.append('../')
import asyncio
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
import grpc

from gRPC import communication_pb2 as communication_messages
from gRPC import communication_pb2_grpc as communication

from parser import exec_command, RunPrompt

######################### TERMINAL SERVER #########################
async def actions(action: str, arg1_list, arg2_list):
    address = 'ds-server:50051' if running_on_docker_container else 'localhost:50051'
    with grpc.insecure_channel(address) as channel:
        stub = communication.ClientAPIStub(channel)
        match action:
            case 'add':
                files=[]
                for file_name in arg1_list:
                    if not Path(file_name).exists():
                        print(f"Cliente: No se encontro la ruta al archivo: '{file_name}'.")
                        continue
                    with open(file_name, 'rb') as file:
                        file_content = file.read()
                        files.append(communication_messages.FileContent(title=file_name, content=file_content))
                response = stub.addFiles(communication_messages.FilesToAdd(files=files, tags=arg2_list), timeout=2)
                return f'response.success: {response.success}\nresponse.message: {response.message}'
            case 'add-tags':
                response = stub.addTags(communication_messages.TagQuery(tags_query=arg1_list, operation_tags=arg2_list), timeout=2)
                return f'response.success: {response.success}\nresponse.message: {response.message}'
            case 'delete':
                response = stub.delete(communication_messages.TagList(tags=arg1_list), timeout=2)

                return f'response.success: {response.success}\nresponse.message: {response.message}'
            case 'delete-tags':
                response = stub.deleteTags(communication_messages.TagQuery(tags_query=arg1_list, operation_tags=arg2_list), timeout=2)
                return f'response.success: {response.success}\nresponse.message: {response.message}'

               
                
            case 'list':
                print("Listing...")
                response = stub.list(communication_messages.TagList(tags=arg1_list), timeout=2)

                result = ""
                for file_info in response:
                    if file_info.location.file_hash == "-1":
                        return "no files found"
                    cache[file_info.location.file_hash] = (file_info.title, file_info.location.location_hash)
                    result+=f"{file_info.location.file_hash} -> \"{file_info.title}\"      {file_info.tag_list}\n"
                return result
                
            case 'file-content':
                file_name, location_hash = cache[arg1_list[0]]
                
                if not file_name:
                    return "No se ha recuperado tal archivo, para acceder a el tene que haber sido recuperado en esta sesion"

                response = stub.fileContent(communication_messages.FileLocation(file_hash=arg1_list[0], location_hash=location_hash), timeout=2)
                if not response.title and not response.content:
                    return f"\nNo se encontro el archivo especificado('{file_name}'), este fue movido o eliminado de la BD."
                return f"\n   📰: \"{response.title}\" \n{response.content}"

            case 'cache':
                os.system('cls')
                print("\n\nCache --------------------------------")
                for (file_hash, file_name, file_location_hash) in cache:
                    print(f"  | > file hash: {file_hash}    name: {file_name}    location hash: {file_location_hash}")
                print("    -----------------------------------\n")
                return ""
            case 'clear-cache':
                cache.clear()
                return "Cache cleared successfully"
            case _:
                return "No se reconoce el comando"
            

async def RunTerminalClient():
    global cache
    global running_on_docker_container
    running_on_docker_container_input = input("Estas iniciando desde un contenedor Docker??(Si|No) ")
    match running_on_docker_container_input.casefold():
        case "si": running_on_docker_container = True
        case "no": running_on_docker_container = False
    cache = Cache()
    def wrapped_actions(action:str, arg1_list, arg2_list):

        try:
            return actions(action, arg1_list, arg2_list)
        except grpc._channel._MultiThreadedRendezvous as e:
            # Captura esta excepcion especifica de gRPC
            print(f"Se produjo una excepción de gRPC: {e}")
        except Exception as e:
            return "Hubo problemas encontrando respuesta en los servers"

    await RunPrompt(commands={
        'add': wrapped_actions,
        'list': wrapped_actions,
        'delete': wrapped_actions,
        'add-tags': wrapped_actions,
        'delete-tags': wrapped_actions,
        "file-content": wrapped_actions,
        'cache': wrapped_actions,
        'clear-cache': wrapped_actions,
    })
class Cache:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.files_hashs = []
        self.files_locations_hashs = {}
        self.files_names_hashs = {}
    def __getitem__(self, file_hash:str):
        return (self.files_names_hashs.get(file_hash, None), self.files_locations_hashs.get(file_hash, None))
    def __setitem__(self, file_hash:str, file_name_location_tuple:tuple) -> None:
        file_name, file_location_hash = file_name_location_tuple[0], file_name_location_tuple[1]
        if file_hash in self.files_hashs:
            if file_name == self.files_names_hashs[file_hash]: return
        else: self.files_hashs.append(file_hash)
        self.files_locations_hashs[file_hash] = file_location_hash
        self.files_names_hashs[file_hash] = file_name
        if len(self.files_hashs) > self.capacity:
            file_hash_to_remove = self.files_hashs.pop(0)
            del self.files_locations_hashs[file_hash_to_remove]
            del self.files_names_hashs[file_hash_to_remove]
    def __len__(self):
        return len(self.cache)
    def __iter__(self):
        return ((file_hash, self.files_names_hashs[file_hash], self.files_locations_hashs[file_hash]) for file_hash in self.files_hashs)
    def delete_item(self, file_hash):
        if file_hash in self.files_hashs:
            file_name = self.files_names_hashs[file_hash]
            del self.files_hashs[file_hash]
            del self.files_names_hashs[file_hash]
            del self.files_locations_hashs[file_hash]
            print(f"cache actualizada")
        else:
            print()
    def clear(self):
        self.files_hashs.clear()
        self.files_names_hashs.clear()
        self.files_locations_hashs.clear()


if __name__ == '__main__':
    print("---------------------------------------------- Nueva ejecucion")
    asyncio.run(RunTerminalClient())
    # actions('add', ['Dockerfile'], ['archivo', 'docker', 'proyecto'])
    # actions('list', ['archivo'], [])
    pass



















######################### FLASK SERVER #########################
# app = Flask(__name__)
# CORS(app)
# @app.route('/')
# def index():
#     pass


# @app.route('/add?q=<query>')
# def add(tag_query):
#     files = request.headers['files']
#     print()
#     pass
# @app.route('/list')
# def list_():
#     pass
# @app.route('/delete')
# def delete():
#     pass
# @app.route('/add-tags')
# def add_tags():
#     pass
# @app.route('/delete-tags')
# def delete_tags():
#     pass

# @app.route('/', methods=['GET'])
# def home():
#     # Simulando la comunicación con el cliente gRPC
#     channel = grpc.insecure_channel('localhost:50051')
#     stub = communication.CommunicationStub(channel)
#     return jsonify({'mensaje': 'Hola desde F-T-system'})

# def run():
#     with grpc.insecure_channel('localhost:50051') as channel:
#         stub = communication.ClientAPIStub(channel)
#         response = stub.GetMessage(communication_messages.Empty())
#         return jsonify({'mensaje': response.message})
#     with grpc.insecure_channel('localhost:50051') as channel:
#         stub = greet_pb2_grpc.GreeterStub(channel)
#         response = stub.SayHello(greet_pb2.HelloRequest(name='world'))
#     print("Greeter client received: " + response.message)
 
# if __name__ == '__main__':
#     # app.run(debug=True, host="0.0.0.0", port=3000)
#     pass
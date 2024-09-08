

from flask import Flask, jsonify
from flask_cors import CORS
import grpc

# import sys
# sys.path.append('../')
from gRPC import communication_pb2 as communication_messages
from gRPC import communication_pb2_grpc as communication
from parser import exec_command, RunPrompt

######################### TERMINAL SERVER #########################

def actions(action: str, arg1_list, arg2_list):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = communication.ClientAPIStub(channel)
        match action:
            case 'add':
                files=[]
                for file_name in arg1_list:
                    with open(file_name, 'rb') as file:
                        file_content = file.read()
                        communication_messages.FileContent(title=file_name, content=file_content)
                response = stub.addFiles(communication_messages.FilesToAdd(files=files, tags=arg2_list))
                return f'response.success: {response.success}\nresponse.message: {response.message}'
            case 'add-tags':
                response = stub.addTags(communication_messages.TagQuery(tags_query=arg1_list, operation_tags=arg2_list))
                return f'response.success: {response.success}\nresponse.message: {response.message}'
            case 'delete':
                response = stub.delete(communication_messages.TagList(tags=arg1_list))
                return f'response.success: {response.success}\nresponse.message: {response.message}'
            case 'delete-tags':
                response = stub.addTags(communication_messages.TagQuery(tags_query=arg1_list, operation_tags=arg2_list))
                return f'response.success: {response.success}\nresponse.message: {response.message}'

                
                
            case 'list':
                response = stub.list(communication_messages.TagList(tags=arg1_list))
                for file_info in response:
                    files_locations_hashs[file_info.location.file_hash] = file_info.location.location_hash
                    return f"{file_info.location.file_hash} -> \"{file_info.title}\"      {file_info.tag_list}"
            case 'file-content':
                location_hash=files_locations_hashs.get(arg1_list[0], None)
                if not location_hash:
                    return "No se ha recuperado tal archivo, para acceder a el tene que haber sido recuperado en esta sesion"

                response = stub.fileContent(communication_messages.FileLocation(file_hash=arg1_list[0], location_hash=location_hash))
                return f"\n   > \"{response.title}\" \n{response.content}"
                    
            case _:
                return "No se reconoce el comando"
            


def RunTerminalServer():
    global files_locations_hashs
    files_locations_hashs = {}
    RunPrompt(commands={
        'add': actions,
        'list': actions,
        'delete': actions,
        'add-tags': actions,
        'delete-tags': actions
    })






















######################### FLASK SERVER #########################
app = Flask(__name__)
CORS(app)
@app.route('/')
def index():
    pass


@app.route('/add?q=<query>')
def add(tag_query):
    files = request.headers['files']
    print()
    pass
@app.route('/list')
def list_():
    pass
@app.route('/delete')
def delete():
    pass
@app.route('/add-tags')
def add_tags():
    pass
@app.route('/delete-tags')
def delete_tags():
    pass

@app.route('/', methods=['GET'])
def home():
    # Simulando la comunicación con el cliente gRPC
    channel = grpc.insecure_channel('localhost:50051')
    stub = communication.CommunicationStub(channel)
    return jsonify({'mensaje': 'Hola desde F-T-system'})

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = communication.ClientAPIStub(channel)
        response = stub.GetMessage(communication_messages.Empty())
        return jsonify({'mensaje': response.message})
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = greet_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(greet_pb2.HelloRequest(name='world'))
    print("Greeter client received: " + response.message)
 
if __name__ == '__main__':
    # app.run(debug=True, host="0.0.0.0", port=3000)
    pass
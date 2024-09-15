import re
from DB.queries import File_Tag_DB


def exec_command(prompt:str, actions:dict):
    """Separa la expresion inicial en varias expresiones hasta desglosarlo en listas de elementos y en elementos."""
    exp = r'^(?P<command>[\w\-]+)\s+(?P<rest>.*)'
    exp_args = r'(?P<arg1_list>[\w_\.\|]+) (\s?)+ (?P<arg2_list>[\w_\|]+)?'
    exp_list = r'(?P<tag>[\w_\.]+)\| | \|?(?P<tag1>[\w_\.]+)'

    match = re.match(exp, prompt, re.VERBOSE)
    args_match = re.match(exp_args, match.group('rest'), re.VERBOSE)
    if not args_match.group('arg1_list'):
        return "Formato incorrecto"
    arg1_match = re.finditer(exp_list, args_match.group('arg1_list'), re.VERBOSE)
    arg2_match = re.finditer(exp_list, args_match.group('arg2_list'), re.VERBOSE) if args_match.group('arg2_list') else None

    def fill_list(iterator, filling_list:list):
        for item in iterator:
            if item.group('tag'):
                if item.group('tag1'): raise Exception("Formato incorrecto")
                filling_list.append(item.group('tag'))
            elif item.group('tag1'):
                filling_list.append(item.group('tag1'))

    if not match:
        return "Formato incorrecto"
    
    arg1_list = []
    arg2_list = []
    fill_list(arg1_match, arg1_list)
    if arg2_match : fill_list(arg2_match, arg2_list)
    
    try:
        command = match.group('command')
        result_function = actions.get(command)
        return result_function(command, arg1_list, arg2_list)
        # return result_function(arg1_list, arg2_list)
    except Exception as e:
        print(f"arg1_list: {arg1_list}")
        print(f"arg2_list: {arg2_list}")
        return f"Formato incorrecto: {e}"
    
def actions(action: str, arg1_list, arg2_list):
    match action:
        case 'add':
            files=[]
            for file_name in arg1_list:
                with open(file_name, 'rb') as file:
                    file_content = file.read()
                    files.append((file_name, file_content))
            response = DB.AddFiles(files, arg2_list, "lasldalsd")
        case 'add-tags':
            response = DB.AddTags(arg1_list, arg2_list)
            return response
        case 'delete':
            response = DB.DeleteFiles(arg1_list)
            
        case 'delete-tags':
            response = DB.DeleteTags(arg1_list, arg2_list)
            return response
            
        case 'list':
            response = DB.RecoveryFilesInfo_ByTagQuery(tag_query=arg1_list, include_tags=True)
            result = f"{[file for file in response]}"
            return result
        case 'file-content':
            response = DB.RecoveryFileContent_ByInfo(arg1_list)
            return response

        #     response = 
        #     return f"\n   > \"{response.title}\" \n{response.content}"
                
        case _:
            return "No se reconoce el comando"
        


def RunPrompt(commands: dict):
    # DB.StartDB()
    print("Consola de comandos\n" + 
            "Comandos permitidos:\n" +
            "- add file-list tag-list\n" +
            "- delete tag-query\n" +
            "- list tag-query\n" +
            "- add-tags tag-query tag-list\n" +
            "- delete-tags tag-query tag-list\n" +
            "- file-content file-hash location-hash")
    while 1:
        command = input(">>> ")
        print(exec_command(command, commands))
if __name__ == "__main__":
    global DB
    DB = File_Tag_DB('database')
    RunPrompt(commands={
        'add': actions,
        'list': actions,
        'delete': actions,
        'add-tags': actions,
        'delete-tags': actions,
        "file-content": actions
    })

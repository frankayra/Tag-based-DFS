import re

def exec_command(prompt:str, actions:dict):
    # Divide la expresion del comando en varias
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
        result_function = actions.get(match.group('command'))
        return result_function(arg1_list, arg2_list)
    except Exception as e:
        return f"Formato incorrecto: {e}"

    # match match.group('command'):
    #     case 'delete':
    #         return delete_tags(arg1_list)
    #     case 'list':
    #         return list_(arg1_list)
    #     case 'add':
    #         if not arg2_match: return "Formato incorrecto"
    #         fill_list(arg2_match, arg2_list)
    #         return add(arg1_list, arg2_list)
    #     case 'add-tags':
    #         if not arg2_match: return "Formato incorrecto"
    #         fill_list(arg2_match, arg2_list)
    #         return add_tags(arg1_list, arg2_list)
    #     case 'delete-tags':
    #         if not arg2_match: return "Formato incorrecto"
    #         fill_list(arg2_match, arg2_list)
    #         return delete_tags(arg1_list, arg2_list)
    #     case _:
    #         return "Formato incorrecto"

def add(files_list, tags_list):
    print(f"argumento 1: {files_list}\n argumento 2: {tags_list}")
    pass
def delete(tag_query):
    print(f"argumento 1: {tag_query}")
    pass
def list_(tag_query):
    print(f"argumento 1: {tag_query}")
    pass
def add_tags(tag_query, tags_list):
    print(f"argumento 1: {tag_query}\n argumento 2: {tags_list}")
    pass
def delete_tags(tag_query, tags_list):
    print(f"argumento 1: {tag_query}\n argumento 2: {tags_list}")
    pass

print("Consola de comandos\n" + 
        "Comandos permitidos:\n" +
        "- add file-list tag-list\n" +
        "- delete tag-query\n" +
        "- list tag-query\n" +
        "- add-tags tag-query tag-list\n" +
        "- delete tag-query tag-list\n")
commands = {
    "add": add,
    "delete": delete,
    "list": list_,
    "add-tags": add_tags,
    "delete-tags": delete_tags,
}
while 1:
    command = input(">>> ")
    exec_command(command, commands)
command_example_1 = "add file_1.txt|resource_2do.pdf"
command_example_2 = "add file1.txt fotos_con_mi_madre|Vacaciones"
command_example_3 = ""
command_example_4 = ""
command_example_5 = ""
command_example_6 = ""
command_example_7 = ""
command_example_8 = ""
command_example_9 = ""
command_example_10 = ""
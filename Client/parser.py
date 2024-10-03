import re
# from DB import queries
# from DB import File, FileTag, Tag
# from DB import DB


async def exec_command(prompt:str, actions:dict):
    """Separa la expresion inicial en varias expresiones hasta desglosarlo en listas de elementos y en elementos."""
    exp = r'^(?P<command>[\w\-]+)\s+(?P<rest>.*)'
    exp_args = r'(?P<arg1_list>[\w_\.\|]+) (\s?)+ (?P<arg2_list>[\w_\|]+)?'
    exp_list = r'(?P<tag>[\w_\.]+)\| | \|?(?P<tag1>[\w_\.]+)'

    match = re.match(exp, prompt, re.VERBOSE)
    if not match:
        "Funciones sin argumentos"
        command_exp = r'^(?P<command>[\w_\-]+)'
        comm_match = re.match(command_exp, prompt, re.VERBOSE)
        if not comm_match: return "No se recibio comando alguno"
        command = comm_match.group('command')
        result_function = actions.get(command, None)
        if not result_function: return f"No esta definida una accion para el comando '{command}'"
        try:
            return await result_function(command, None, None)
        except Exception as e:
            return f"Hubo un error dentro de la funcion, ó: No se recibio ningun argumento cuando la operacion a ejecutar lo(s) requeria"
    args = match.group('rest')
    args_match = re.match(exp_args, args, re.VERBOSE)

    arg1_match = re.finditer(exp_list, args_match.group('arg1_list'), re.VERBOSE)
    arg2_match = re.finditer(exp_list, args_match.group('arg2_list'), re.VERBOSE) if args_match.group('arg2_list') else None

    def fill_list(iterator, filling_list:list):
        for item in iterator:
            if item.group('tag'):
                if item.group('tag1'): raise Exception("Formato incorrecto")
                filling_list.append(item.group('tag'))
            elif item.group('tag1'):
                filling_list.append(item.group('tag1'))

    arg1_list = []
    arg2_list = []
    fill_list(arg1_match, arg1_list)
    if arg2_match : fill_list(arg2_match, arg2_list)
    
    command = match.group('command')
    result_function = actions.get(command)
    return await result_function(command, arg1_list, arg2_list)
    

async def RunPrompt(commands: dict):
    # DB.StartDB()
    print("Consola de comandos\n" + 
            "Comandos permitidos:\n" +
            "- add file-list tag-list\n" +
            "- delete tag-query\n" +
            "- list tag-query\n" +
            "- add-tags tag-query tag-list\n" +
            "- delete-tags tag-query tag-list\n" +
            "- file-content file-hash location-hash\n" + 
            "- cache\n" + 
            "- clear-cache")

    try:
        while 1:
            command = input(">>> ")
            print(await exec_command(command, commands))
    except EOFError or KeyboardInterrupt:
        print("Interrupción del usuario")
        # try:
        # except Exception as e:
        #     print(f"Error controlado proveniente del parser (desconocido).")
# if __name__ == "__main__":
#     RunPrompt(commands = {
#         "add": queries.AddFiles,
#         "delete": queries.DeleteFiles,
#         "list": queries.RecoverFiles_ByTagQuery,
#         "add-tags": queries.AddTags,
#         "delete-tags": queries.DeleteTags,
# })
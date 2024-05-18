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

def RunPrompt(commands: dict):
    print("Consola de comandos\n" + 
            "Comandos permitidos:\n" +
            "- add file-list tag-list\n" +
            "- delete tag-query\n" +
            "- list tag-query\n" +
            "- add-tags tag-query tag-list\n" +
            "- delete tag-query tag-list\n")

    while 1:
        command = input(">>> ")
        exec_command(command, commands)
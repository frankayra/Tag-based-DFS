import re
from DB import queries
from DB import File, FileTag, Tag
from DB import DB


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
        result_function = actions.get(match.group('command'))
        return result_function(arg1_list, arg2_list)
    except Exception as e:
        return f"Formato incorrecto: {e}"
    

def RunPrompt(commands: dict):
    DB.StartDB()
    print("Consola de comandos\n" + 
            "Comandos permitidos:\n" +
            "- add file-list tag-list\n" +
            "- delete tag-query\n" +
            "- list tag-query\n" +
            "- add-tags tag-query tag-list\n" +
            "- delete-tags tag-query tag-list\n")

    while 1:
        command = input(">>> ")
        print(exec_command(command, commands))
if __name__ == "__main__":
    RunPrompt(commands = {
        "add": queries.AddFiles,
        "delete": queries.DeleteFiles,
        "list": queries.RecoverFiles_ByTagQuery,
        "add-tags": queries.AddTags,
        "delete-tags": queries.DeleteTags,
})

######################## TESTING ########################
# def test_Saving_Files():
#     db = StartDB()
#     with open("tests/texto.txt", 'rb') as file:
#         file_content = file.read()
#         SaveFile(file_name="texto.txt", file_content=file_content)
#         recovery_content = File.get(name="texto.txt").file_content
#         self.assertEqual(file_content, recovery_content)
#     db.close()
# def test_Multiple_Files():
#     db = StartDB()
#     curr_dir = os.getcwd()+ '\\tests'
#     test_files = {}
#     for f in [fil for fil in os.listdir(curr_dir) if (os.path.isfile(os.path.join(curr_dir, fil)) and os.path.splitext(fil)[1] == ".txt")]:
#         print(f)
#         with open(os.path.join(curr_dir, f), 'rb') as file:
#             file_content = file.read()
#             test_files[f] = file_content
#     AddFiles(*["Fotos_con_mi_madre", "vacaciones", "viajes", "playa", "familia"], **test_files)
#     db.close()
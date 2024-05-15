import re

def exec_command(command:str):
    exp = r'(?P<command>\w+)\s+((?P<param1>\w+)\s+)?(?P<param2>\w+)?'
    command = 'add tag_query'
    match = re.match(exp, command)
    print(f'comando: {match.group('command')}')
    print(f'param1: {match.group('param1')}')
    print(f'param2: {match.group('param2')}')
exec_command("lalala")
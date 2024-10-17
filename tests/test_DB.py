import unittest
from Server.DB import *
import os
import peewee

def Change_to_test_dir(test_dir:str):
    def decorador_mediador(f):
        def result_func(*args, **kwargs):
            cur_dir = os.getcwd()
            os.chdir(test_dir)
            result = f(*args, **kwargs) 
            os.chdir(cur_dir)
            return result
        return result_func
    return decorador_mediador


class TestDB(unittest.TestCase):
    # @Change_to_test_dir('tests')
    def test_Saving_Files(self):
        db = StartDB()
        with open("tests/texto.txt", 'rb') as file:
            file_content = file.read()
            SaveFile(file_name="texto.txt", file_content=file_content)
            recovery_content = File.get(name="texto.txt").file_content
            self.assertEqual(file_content, recovery_content)
        db.close()
    # @Change_to_test_dir('tests')
    def test_Multiple_Files(self):
        db = StartDB()
        curr_dir = os.getcwd()+ '\\tests'
        test_files = {}
        for f in [fil for fil in os.listdir(curr_dir) if (os.path.isfile(os.path.join(curr_dir, fil)) and os.path.splitext(fil)[1] == ".txt")]:
            print(f)
            with open(os.path.join(curr_dir, f), 'rb') as file:
                file_content = file.read()
                test_files[f] = file_content
        AddFiles(*["Fotos_con_mi_madre", "vacaciones", "viajes", "playa", "familia"], **test_files)
        db.close()



            
if __name__ == '__main__':
    unittest.main()
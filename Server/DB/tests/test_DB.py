import unittest
from Server.DB import *

class TestDB(unittest.TestCase):

    def test_Saving_File(self):
        with open("texto.txt", 'rb') as file:
            self.assertTrue(SaveFile(file_name="texto.txt", file_content=file))

if __name__ == '__main__':
    unittest.main()
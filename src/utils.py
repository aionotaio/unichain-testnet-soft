import random
from typing import Optional, Union

import ujson


class Utils:
    @staticmethod
    def read_json(path: str, encoding: Optional[str] = None) -> Union[list, dict]:
        with open(path, 'r', encoding=encoding) as f:
            contents = f.read()
            return ujson.loads(contents)

    @staticmethod
    def read_file(path: str, encoding: Optional[str] = None) -> str:
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    
    @staticmethod
    def read_strings_from_file(path: str) -> list:
        strings = []
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    strings.append(line)
        return strings

    @staticmethod
    def get_random_name_and_symbol(file1_path: str, file2_path: str) -> tuple:
        with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
            names = f1.readlines()
            symbols = f2.readlines()
        
        paired_list = list(zip(names, symbols))
        name, symbol = random.choice(paired_list)
    
        return name.strip(), symbol.strip()
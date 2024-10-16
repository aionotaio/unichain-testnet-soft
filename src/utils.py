import asyncio
import random
from typing import Optional, Union

import aiofiles
import ujson


class Utils:
    @staticmethod
    async def read_json(path: str, encoding: Optional[str] = None) -> Union[list, dict]:
        async with aiofiles.open(path, 'r', encoding=encoding) as f:
            contents = await f.read()
            return ujson.loads(contents)

    @staticmethod
    async def read_file(path: str, encoding: Optional[str] = None) -> str:
        async with aiofiles.open(path, 'r', encoding=encoding) as f:
            return await f.read()
    
    @staticmethod
    async def read_strings_from_file(path: str) -> list:
        strings = []
        async with aiofiles.open(path, 'r') as f:
            async for line in f:
                line = line.strip()
                if line:
                    strings.append(line)
        return strings

    @staticmethod
    async def get_random_name_and_symbol(file1_path: str, file2_path: str) -> tuple:
        async with aiofiles.open(file1_path, 'r') as f1, aiofiles.open(file2_path, 'r') as f2:
            names = await f1.readlines()
            symbols = await f2.readlines()
        
        paired_list = list(zip(names, symbols))
        name, symbol = random.choice(paired_list)
    
        return name.strip(), symbol.strip()

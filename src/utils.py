import asyncio
import random
import os
import sys
from pathlib import Path
from typing import Optional, Union

import aiofiles
import ujson


if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

ABIS_DIR = os.path.join(ROOT_DIR, 'abis')
FILES_DIR = os.path.join(ROOT_DIR, 'files')
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

ETHBRIDGE_ABI = os.path.join(ABIS_DIR, 'ethbridge.json')
WETH_ABI = os.path.join(ABIS_DIR, 'weth.json')

ERC721_ABI = os.path.join(ABIS_DIR, 'erc721contract.json')
ERC721_BYTECODE = os.path.join(DATA_DIR, 'erc721bytecode.txt')

ERC20_ABI = os.path.join(ABIS_DIR, 'erc20contract.json')
ERC20_BYTECODE = os.path.join(DATA_DIR, 'erc20bytecode.txt')

NAMES_PATH = os.path.join(DATA_DIR, 'token_names.txt')
SYMBOLS_PATH = os.path.join(DATA_DIR, 'token_symbols.txt')

PRIVATE_KEYS_PATH = os.path.join(FILES_DIR, 'private_keys.txt')
PROXIES_PATH = os.path.join(FILES_DIR, 'proxies.txt')
LOGS_PATH = os.path.join(LOGS_DIR, 'logs.txt')


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
    
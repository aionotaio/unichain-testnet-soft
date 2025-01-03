import os
import sys
from pathlib import Path


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

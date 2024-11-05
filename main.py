import random
import time
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from src.client import Client
from src.models import ethereum_sepolia, unichain_sepolia
from src.utils import Utils
from config import PRIVATE_KEYS_PATH, LOGS_PATH, ETHBRIDGE_ABI, WETH_ABI, ERC721_ABI, ERC721_BYTECODE, NAMES_PATH, SYMBOLS_PATH, MAX_THREADS


logger.add(sink=LOGS_PATH, format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", level="INFO", rotation="100 MB")

def bridge_eth(client_eth, bridge_value):
    logger.info(f'{client_eth.wallet_address} | Attempting to bridge {bridge_value / 10 ** 18:.18f} ETH...')
    return execute_with_delay(client_eth.bridge_eth(
        contract_address='0xea58fcA6849d79EAd1f26608855c2D6407d54Ce2',
        value=bridge_value,
        abi_path=ETHBRIDGE_ABI
    ), random.randint(25, 50))

def wrap_eth(client_uni, wrap_value):
    logger.info(f'{client_uni.wallet_address} | Attempting to wrap {wrap_value / 10 ** 18:.18f} ETH...')
    return execute_with_delay(client_uni.wrap_eth(
        contract_address='0x4200000000000000000000000000000000000006',
        value=wrap_value,
        abi_path=WETH_ABI
    ), random.randint(3, 15))

def mint_nft(client_uni, contract_address):
    logger.info(f'{client_uni.wallet_address} | Attempting to mint NFT through smart contract {contract_address}')
    return execute_with_delay(client_uni.mint_nft(
        contract_address=contract_address, 
        abi_path=ERC721_ABI
    ), random.randint(10, 15))

def deploy_with_return_res(client_uni, name, symbol):
    try:
        logger.info(f'{client_uni.wallet_address} | Attempting to deploy ERC721 token smart contract in {client_uni.network.name}')
        return client_uni.deploy_erc721_contract(
            token_name=name,
            token_symbol=symbol,
            abi_path=ERC721_ABI,
            bytecode_path=ERC721_BYTECODE
        )
    except Exception as e:
        logger.error(f'Error deploying contract: {e}')
        return None

def execute_with_delay(task, delay):
    time.sleep(delay)
    return task

def wait_for_positive_balance(client_uni):
    while True:
        balance = client_uni.get_balance()
        if balance > 0:
            logger.info(f'{client_uni.wallet_address} | Balance is positive: {balance / 10 ** 18} ETH')
            break
        logger.info(f'{client_uni.wallet_address} | Waiting for positive balance in {client_uni.network.name}...')
        time.sleep(10)

def process_client(private_key):
    client_eth = Client(private_key=private_key, network=ethereum_sepolia)
    client_uni = Client(private_key=private_key, network=unichain_sepolia)

    eth_balance = client_eth.w3.eth.get_balance(client_eth.wallet_address)
    uni_balance = client_uni.w3.eth.get_balance(client_uni.wallet_address)

    if uni_balance == 0 and eth_balance > 0:
        max_bridge_value = eth_balance * 0.5
        bridge_value = round(random.uniform(0, max_bridge_value), 2)
        bridge_value = int(bridge_value)
        bridge_eth(client_eth, bridge_value)
    
    wait_for_positive_balance(client_uni)

    if uni_balance > 0:
        max_wrap_value = uni_balance * 0.05
        wrap_value = round(random.uniform(0, max_wrap_value), 5)
        print(wrap_value)
        wrap_value = int(wrap_value)
        if random.choice([True, False]):
            wrap_eth(client_uni, wrap_value)
            name, symbol = Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
            deploy_task = deploy_with_return_res(client_uni, name, symbol)

            if deploy_task is not None:
                mint_nft(client_uni, deploy_task)
        else:
            name, symbol = Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
            deploy_task = deploy_with_return_res(client_uni, name, symbol)

            if deploy_task is not None:
                mint_nft(client_uni, deploy_task)
            wrap_eth(client_uni, wrap_value)

def main():
    private_keys = Utils.read_strings_from_file(PRIVATE_KEYS_PATH)

    logger.info('Starting...')

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_client, private_key) for private_key in private_keys]
        for future in futures:
            future.result()
    logger.info('Finished.')

if __name__ == '__main__':
    main()
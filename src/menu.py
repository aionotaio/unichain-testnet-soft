import random
import asyncio
from typing import Optional

from loguru import logger

from src.utils import Utils
from src.client import Client
from src.vars import NAMES_PATH, SYMBOLS_PATH
from src.models import ethereum_sepolia, unichain_sepolia
from config import BRIDGE_PARAMS, DELAY_BETWEEN_ACC, WRAP_PARAMS, SHUFFLE_WALLETS

from src.wrap import WrapManager
from src.erc_20 import ERC20Manager
from src.morkie import MorkieManager
from src.bridge import BridgeManager
from src.erc_721 import ERC721Manager
from src.random_interactions import RandomManager


class Menu:
    def __init__(self):
        self.wrap_manager = WrapManager()
        self.erc20_manager = ERC20Manager()
        self.bridge_manager = BridgeManager()
        self.erc721_manager = ERC721Manager()
        self.random_manager = RandomManager()
        self.morkie_manager = MorkieManager()

    @staticmethod
    def open_menu():
        print('''
█░█ █▄░█ █ █▀▀ █░█ ▄▀█ █ █▄░█   ▀█▀ █▀▀ █▀ ▀█▀ █▄░█ █▀▀ ▀█▀   █▀ █▀█ █▀▀ ▀█▀
█▄█ █░▀█ █ █▄▄ █▀█ █▀█ █ █░▀█   ░█░ ██▄ ▄█ ░█░ █░▀█ ██▄ ░█░   ▄█ █▄█ █▀░ ░█░

█▄▄ █▄█   ▄▀█ █ █▀█ █▄░█ █▀█ ▀█▀ ▄▀█ █ █▀█
█▄█ ░█░   █▀█ █ █▄█ █░▀█ █▄█ ░█░ █▀█ █ █▄█\n''')
        
        print('''1. Bridge ETH from Ethereum Sepolia to Unichain Sepolia.
2. Wrap ETH in Unichain Sepolia.
3. Deploy an ERC-721 contract in Unichain Sepolia + interact with it.
4. Deploy an ERC-20 contract in Unichain Sepolia + interact with it.
5. Mint an Unicorn NFT from morkie.xyz.
6. Mint an Europa NFT from morkie.xyz.                
7. Random interaction
8. Quit\n''')
        
        choice = int(input('Choose an option (1-8): '))
        return choice

    def shuffle_wallets(self, private_keys: list, proxies: list = None) -> tuple[list, list, list]:
        indices = list(range(len(private_keys)))
        if SHUFFLE_WALLETS:
            random.shuffle(indices)
            private_keys = [private_keys[i] for i in indices]
            if proxies:
                proxies = [proxies[i % len(proxies)] for i in indices]
        return private_keys, proxies, indices
    
    async def handle_choice(self, choice: int, private_keys_list: list, proxies_list: list) -> Optional[bool]:
        private_keys, proxies, shuffled_indices = self.shuffle_wallets(private_keys_list, proxies_list)
    
        if choice == 1:
            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_eth = Client(private_key, ethereum_sepolia, proxy)
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    result = await self.bridge_manager.bridge_eth(client_eth, client_uni, BRIDGE_PARAMS, account_index)
            
                    if isinstance(result, Exception) or result is False:
                        logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge failed with error: {result}.')
                    elif result is None:
                        logger.warning(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge completed with no result.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge completed successfully.')
                    
                    return result
            
                except Exception as e:
                    logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Error processing account: {e}.')
                    return False

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                task = asyncio.create_task(process_account(private_key, i))
                account_tasks.append(task)
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)

            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 2:
            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    result = await self.wrap_manager.wrap_eth(client_uni, WRAP_PARAMS, account_index)
            
                    if isinstance(result, Exception) or result is False:
                        logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap failed with error: {result}.')
                    elif result is None:
                        logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap completed with no result.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap completed successfully.')
                    
                    return result
            
                except Exception as e:
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Error processing account: {e}.')
                    return False

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                task = asyncio.create_task(process_account(private_key, i))
                account_tasks.append(task)
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)

            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 3:
            second_choice = int(input('Enter an integer number of how many contracts you want to deploy: '))

            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    account_results = []

                    for contract_index in range(second_choice):
                        name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                        contract_address = await self.erc721_manager.deploy_erc721(client_uni, name, symbol, account_index, is_first_tx=(contract_index==0))
                       
                        if isinstance(contract_address, Exception) or contract_address is False:
                            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 contract deployment {contract_index+1} failed with error: {contract_address}.')
                        elif contract_address is None:
                            logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 contract deployment {contract_index+1} completed with no result.')
                        else:
                            logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 contract deployment {contract_index+1} completed successfully.')
                        
                        if contract_address:
                            account_results.append((contract_index, contract_address))
                            mint_result = await self.erc721_manager.mint_nft(client_uni, contract_address, account_index)
                    
                            if isinstance(mint_result, Exception) or mint_result is False:
                                logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Mint NFT with contract {contract_index+1} failed with error: {mint_result}.')
                            elif mint_result is None:
                                logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | Mint NFT with contract {contract_index+1} completed with no result.')
                            else:
                                logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Mint NFT with contract {contract_index+1} completed successfully.')
            
                    return account_results
            
                except Exception as e:
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Error processing account: {e}.')
                    return []

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                account_tasks.append(asyncio.create_task(
                    process_account(private_key, i))
                )
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)

            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 4:
            second_choice = int(input('Enter an integer number of how many contracts you want to deploy: '))

            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    account_results = []
            
                    for contract_index in range(second_choice):
                        name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                        contract_address = await self.erc20_manager.deploy_erc20(client_uni, name, symbol, account_index, is_first_tx=(contract_index==0))
                
                        if isinstance(contract_address, Exception) or contract_address is False:
                            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 contract deployment {contract_index+1} failed with error: {contract_address}.')
                        elif contract_address is None:
                            logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 contract deployment {contract_index+1} completed with no result.')
                        else:
                            logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 contract deployment {contract_index+1} completed successfully.')
                
                        if contract_address:
                            account_results.append((contract_index, contract_address))
                            interact_result = await self.erc20_manager.interact_with_contract(client_uni, contract_address, account_index)
                    
                            if isinstance(interact_result, Exception) or interact_result is False:
                                logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Interact with contract {contract_index+1} failed with error: {interact_result}.')
                            elif interact_result is None:
                                logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | Interact with contract {contract_index+1} completed with no result.')
                            else:
                                logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Interact with contract {contract_index+1} completed successfully.')
            
                    return account_results
            
                except Exception as e:
                    logger.error(f'Error processing account {account_index+1}: {e}.')
                    return []

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                task = asyncio.create_task(process_account(private_key, i))
                account_tasks.append(task)
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)

            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 5:
            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    result = await self.morkie_manager.mint_unicorn_nft(client_uni, account_index)
            
                    if isinstance(result, Exception) or result is False:
                        logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Minting Unicorn NFT failed with error: {result}.')
                    elif result is None:
                        logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | Minting Unicorn NFT completed with no result.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Minting Unicorn NFT completed successfully.')
                    
                    return result
            
                except Exception as e:
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Error processing account: {e}.')
                    return False

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                task = asyncio.create_task(process_account(private_key, i))
                account_tasks.append(task)
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)

            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 6:
            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    result = await self.morkie_manager.mint_europa_nft(client_uni, account_index)
            
                    if isinstance(result, Exception) or result is False:
                        logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Minting Europa NFT failed with error: {result}.')
                    elif result is None:
                        logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | Minting Europa NFT completed with no result.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Minting Europa NFT completed successfully.')
                    
                    return result
            
                except Exception as e:
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Error processing account: {e}.')
                    return False

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                task = asyncio.create_task(process_account(private_key, i))
                account_tasks.append(task)
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)

            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 7:
            async def process_account(private_key: str, i: int):
                try:
                    account_index = shuffled_indices[i]
                    proxy = proxies[i % len(proxies)] if proxies else None
                    client_uni = Client(private_key, unichain_sepolia, proxy)
            
                    result = await self.random_manager.random_interactions(client_uni, account_index)
            
                    if isinstance(result, Exception) or result is False:
                        logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Random interactions failed with error: {result}.')
                    elif result is None:
                        logger.warning(f'Account {account_index+1} | {client_uni.wallet_address} | Random interactions completed with no result.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Random interactions completed successfully.')
            
                    return result
            
                except Exception as e:
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Error processing account: {e}.')
                    return False

            account_tasks = []
            for i, private_key in enumerate(private_keys):
                task = asyncio.create_task(process_account(private_key, i))
                account_tasks.append(task)
        
                if i < len(private_keys) - 1:
                    delay = random.randint(DELAY_BETWEEN_ACC[0], DELAY_BETWEEN_ACC[1])
                    logger.info(f'Waiting {delay} seconds before starting next account...')
                    await asyncio.sleep(delay)
            
            if account_tasks:
                await asyncio.gather(*account_tasks, return_exceptions=True)

        elif choice == 8:
            logger.info('Exiting...')
            return None
        
        else:
            logger.error('Please enter a number from 1 to 9.')

        logger.info('Finished.')

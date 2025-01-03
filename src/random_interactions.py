import random
from typing import Optional

from loguru import logger

from src.utils import Utils
from src.client import Client
from src.wrap import WrapManager
from src.erc_20 import ERC20Manager
from src.erc_721 import ERC721Manager
from config import RANDOM_CONFIG, WRAP_PARAMS
from src.vars import NAMES_PATH, SYMBOLS_PATH


class RandomManager:
    def __init__(self) -> None:
        self.wrap_manager = WrapManager()
        self.erc20_manager = ERC20Manager()
        self.erc721_manager = ERC721Manager()

    async def random_interactions(self, client_uni: Client, account_index: int) -> Optional[bool]:
        try:
            erc721_count = random.randint(RANDOM_CONFIG['max_actions']['erc721_count'][0], RANDOM_CONFIG['max_actions']['erc721_count'][1])
            erc20_count = random.randint(RANDOM_CONFIG['max_actions']['erc20_count'][0], RANDOM_CONFIG['max_actions']['erc20_count'][1])
            wrap_count = random.randint(RANDOM_CONFIG['max_actions']['wrap_count'][0], RANDOM_CONFIG['max_actions']['wrap_count'][1])
        
            for i in range(erc721_count):
                name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Deploying ERC-721 contract {i+1}/{erc721_count}...')
            
                contract_address = await self.erc721_manager.deploy_erc721(client_uni, name, symbol, account_index, is_first_tx=(i==0 and erc721_count > 0))
            
                if isinstance(contract_address, Exception):
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 Deploy {i+1} failed with error: {contract_address}.')
                elif contract_address:
                    logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 Deploy {i+1} completed successfully.')

                    logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Starting mint for ERC-721 contract {i+1}.')
                    mint_result = await self.erc721_manager.mint_nft(client_uni, contract_address, account_index)
                
                    if isinstance(mint_result, Exception):
                        logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 Mint {i+1} failed with error: {mint_result}.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-721 Mint {i+1} completed successfully.')
        
            for i in range(erc20_count):
                name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Deploying ERC-20 contract {i+1}/{erc20_count}...')
            
                contract_address = await self.erc20_manager.deploy_erc20(client_uni, name, symbol, account_index, is_first_tx=(i==0 and erc721_count == 0))
            
                if isinstance(contract_address, Exception):
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 Deploy {i+1} failed with error: {contract_address}.')
                elif contract_address:
                    logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 Deploy {i+1} completed successfully.')

                    logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Starting interaction with ERC-20 contract {i+1}...')
                    interact_result = await self.erc20_manager.interact_with_contract(client_uni, contract_address, account_index)
                
                    if isinstance(interact_result, Exception):
                        logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 Interaction {i+1} failed with error: {interact_result}.')
                    else:
                        logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | ERC-20 Interaction {i+1} completed successfully.')

            for i in range(wrap_count):
                logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap {i+1}/{wrap_count}...')
            
                result = await self.wrap_manager.wrap_eth(client_uni, WRAP_PARAMS, account_index)
            
                if isinstance(result, Exception):
                    logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap {i+1} failed with error: {result}.')
                else:
                    logger.success(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap {i+1} completed successfully.')

            return True

        except Exception as e:
            logger.error(f'Account {account_index+1} | Error during random interactions: {e}.')
            return None
        
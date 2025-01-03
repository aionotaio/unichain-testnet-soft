from typing import Optional, Union

from loguru import logger

from src.utils import Utils
from src.client import Client
from src.manager import Manager
from src.vars import WETH_ABI
from config import WRAP_PARAMS


class WrapManager:  
    async def wrap_eth(self, client_uni: Client, wrap_params: dict, account_index: int) -> bool:
        balance = await client_uni.w3.eth.get_balance(client_uni.wallet_address)
        
        if not Manager.is_balance_sufficient(balance, wrap_params["min_balance"]):
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap cancelled: balance is less than minimum required.')
            return False
        
        wrap_amount = self.calculate_wrap_amount(client_uni, balance, wrap_params, account_index)

        if wrap_amount is False:
            return False
        
        if balance < wrap_amount:
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap cancelled: balance is less than amount to wrap.')
            return False

        return await self.execute_wrap(client_uni, wrap_amount, account_index)
    
    @staticmethod
    def calculate_wrap_amount(client_uni: Client, balance: int, wrap_params: dict, account_index: int) -> Union[bool, int]:
        if wrap_params["amount"] is not False and wrap_params["percent"] is not False:
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap cancelled: both amount and percent are set. One of them must be set to False.')
            return False
        
        if wrap_params["amount"] is not False:
            return Manager.calculate_amount(client_uni, wrap_params["amount"], account_index)
        elif wrap_params["percent"] is not False:
            return Manager.calculate_percent_amount(client_uni, balance, wrap_params["percent"], account_index)
        else:
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Wrap cancelled: both amount and percent are set to False. Cannot proceed with bridging.')
            return False
    
    async def execute_wrap(self, client_uni: Client, wrap_amount: int, account_index: int) -> Optional[bool]:
        try:
            wrap_fixed_amount = Utils.round_to_significant_digits(wrap_amount / 10 ** 18, 3)
            
            logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Attempting to wrap {wrap_fixed_amount} ETH...')
            
            result = await client_uni.wrap_eth(
                contract_address='0x4200000000000000000000000000000000000006',
                value=wrap_amount,
                abi_path=WETH_ABI,
                account_index=account_index
            )

            await Manager.wait_for_positive_balance(client_uni, account_index, WRAP_PARAMS['timeout'])

            return result
        except Exception as e:
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Error during wrapping ETH: {e}.')
            return False
        
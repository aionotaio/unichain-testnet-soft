from typing import Optional, Union

from loguru import logger

from src.utils import Utils
from src.client import Client
from src.manager import Manager
from config import BRIDGE_PARAMS
from src.vars import ETHBRIDGE_ABI


class BridgeManager:  
    async def bridge_eth(self, client_eth: Client, client_uni: Client, bridge_params: dict, account_index: int) -> bool:
        balance = await client_eth.w3.eth.get_balance(client_eth.wallet_address)
        
        if not Manager.is_balance_sufficient(balance, bridge_params["min_balance"]):
            logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge cancelled: balance is less than minimum required.')
            return False
        
        bridge_amount = self.calculate_bridge_amount(client_eth, balance, bridge_params, account_index)

        if bridge_amount is False:
            return False
        
        if balance < bridge_amount:
            logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge cancelled: balance is less than amount to bridge.')
            return False

        return await self.execute_bridge(client_eth, client_uni, bridge_amount, account_index)
    
    @staticmethod
    def calculate_bridge_amount(client_eth: Client, balance: int, bridge_params: dict, account_index: int) -> Union[bool, int]:
        if bridge_params["amount"] is not False and bridge_params["percent"] is not False:
            logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge cancelled: both amount and percent are set. One of them must be set to False.')
            return False
        
        if bridge_params["amount"] is not False:
            return Manager.calculate_amount(client_eth, bridge_params["amount"], account_index)
        elif bridge_params["percent"] is not False:
            return Manager.calculate_percent_amount(client_eth, balance, bridge_params["percent"], account_index)
        else:
            logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Bridge cancelled: both amount and percent are set to False. Cannot proceed with bridging.')
            return False
    
    async def execute_bridge(self, client_eth: Client, client_uni: Client, bridge_amount: int, account_index: int) -> Optional[bool]:
        try:
            bridge_fixed_amount = Utils.round_to_significant_digits(bridge_amount / 10 ** 18, 3)
            
            logger.info(f'Account {account_index+1} | {client_eth.wallet_address} | Attempting to bridge {bridge_fixed_amount} ETH...')
            
            result = await client_eth.bridge_eth(
                contract_address='0xea58fcA6849d79EAd1f26608855c2D6407d54Ce2',
                value=bridge_amount,
                abi_path=ETHBRIDGE_ABI,
                account_index=account_index
            )

            await Manager.wait_for_positive_balance(client_uni, account_index, BRIDGE_PARAMS['timeout'])

            return result
        except Exception as e:
            logger.error(f'Account {account_index+1} | {client_eth.wallet_address} | Error during bridging ETH: {e}.')
            return False
        
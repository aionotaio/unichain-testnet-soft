import time
import random
import asyncio
from decimal import Decimal
from typing import Optional, Union

from loguru import logger

from src.utils import Utils
from src.client import Client


class Manager:
    @staticmethod
    async def wait_for_positive_balance(client: Client, account_index: int, timeout: int) -> bool:
        start_time = time.time()
        while True:
            balance = await client.get_balance()
            
            if balance > 0:
                logger.info(f'Account {account_index+1} | {client.wallet_address} | Balance is positive: {balance / 10 ** 18} ETH.')
                return True
            
            if time.time() - start_time > timeout:
                logger.error(f'Account {account_index+1} | {client.wallet_address} | Error: Timeout waiting for positive balance after {timeout} seconds.')
                return False
            
            logger.info(f'Account {account_index+1} | {client.wallet_address} | Waiting for positive balance in {client.network.name}...')
            await asyncio.sleep(10)

    @staticmethod
    def is_balance_sufficient(balance: int, min_balance: Union[bool, float]) -> bool:
        return min_balance is False or balance > int(min_balance * 10 ** 18)

    @staticmethod
    def calculate_amount(client: Client, amount: Union[int, float, tuple], account_index: int) -> Optional[int]:
        if isinstance(amount, (int, float)):
            return int(amount * 10 ** 18)
        elif isinstance(amount, tuple) and len(amount) == 2:
            return Manager.calculate_random_amount(amount)
        else:
            logger.error(f'Account {account_index+1} | {client.wallet_address} | Operation cancelled: amount is set to {type(amount)} type. Should be int, float or tuple.')
            return False

    @staticmethod
    def calculate_random_amount(amount_range: tuple) -> int:
        min_amount, max_amount = amount_range
        unformatted_amount = random.uniform(min_amount, max_amount)
        formatted_amount = Utils.round_to_significant_digits(unformatted_amount, 3)
        return int(Decimal(formatted_amount) * 10 ** 18)

    @staticmethod
    def calculate_percent_amount(client: Client, balance: int, percent: Union[int, tuple], account_index: int) -> Optional[int]:
        if isinstance(percent, int):
            return Manager.calculate_fixed_percent_amount(balance, percent)
        elif isinstance(percent, tuple) and len(percent) == 2:
            return Manager.calculate_random_percent_amount(balance, percent)
        else:
            logger.error(f'Account {account_index+1} | {client.wallet_address} | Operation cancelled: percent is set to {type(percent)} type. Should be int or tuple.')
            return False

    @staticmethod
    def calculate_fixed_percent_amount(balance: int, percent: int) -> int:
        percent_value = percent / 100
        unformatted_amount = (balance / 10 ** 18) * percent_value
        formatted_amount = Utils.round_to_significant_digits(unformatted_amount, 3)
        return int(Decimal(formatted_amount) * 10 ** 18)

    @staticmethod
    def calculate_random_percent_amount(balance: int, percent_range: tuple) -> int:
        min_percent, max_percent = percent_range
        min_amount = (balance / 10 ** 18) * (min_percent / 100)
        max_amount = (balance / 10 ** 18) * (max_percent / 100)
        unformatted_amount = random.uniform(min_amount, max_amount)
        formatted_amount = Utils.round_to_significant_digits(unformatted_amount, 3)
        return int(Decimal(formatted_amount) * 10 ** 18)
    
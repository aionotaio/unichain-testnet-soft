import asyncio
import random
from typing import Optional, Union

from web3 import AsyncWeb3
from loguru import logger

from src.utils import Utils
from src.models import Network, TokenAmount


class Client:
    def __init__(self, private_key: str, network: Network, proxy: str = None):
        self.private_key = private_key
        self.network = network
        self.proxy = proxy
        if proxy:
            self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(endpoint_uri=self.network.rpc, request_kwargs={"proxy": f"http://{proxy}"}))
        else:
            self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(endpoint_uri=self.network.rpc))
        self.wallet_address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)
        self.nonce_lock = asyncio.Lock()

    async def get_balance(self) -> int:
        return await self.w3.eth.get_balance(self.wallet_address)

    async def get_transaction_count(self) -> int:
        async with self.nonce_lock:
            return await self.w3.eth.get_transaction_count(self.wallet_address)
        
    async def send_transaction(self, to_: str = None, data: str = None, value: int = None, tx_params: dict = None) -> Optional[str]:
        if not tx_params:
            tx_params = {
                'from': self.wallet_address,
                'gasPrice': await self.w3.eth.gas_price,
                'nonce': await self.get_transaction_count(),
                'chainId': await self.w3.eth.chain_id
            }

            if to_:
                tx_params['to'] = AsyncWeb3.to_checksum_address(to_)

            if data:
                tx_params['data'] = data

            if value:
                tx_params['value'] = value

            try:
                estimate_gas = await self.w3.eth.estimate_gas(tx_params)
                tx_params['gas'] = int(estimate_gas * 1.1)
            
            except Exception as e:
                logger.warning(f'{self.wallet_address} | Error estimating gas: {e}')
                return None
        
        else:
            tx_params = tx_params
        
        try:
            sign = self.w3.eth.account.sign_transaction(tx_params, self.private_key)
            return await self.w3.eth.send_raw_transaction(sign.rawTransaction)
        
        except Exception as e:
            if 'nonce too low' in str(e):
                tx_params['nonce'] += 1
                return await self.send_transaction(tx_params=tx_params)
            elif 'replacement transaction underpriced' in str(e):
                tx_params['nonce'] += 1
                return await self.send_transaction(tx_params=tx_params)
            elif 'already known' in str(e):
                tx_params['nonce'] += 1
                return await self.send_transaction(tx_params=tx_params)
            
            logger.warning(f'{self.wallet_address} | Error sending transaction: {e}')
            return None

    async def send_transaction_with_abimethod(self, contract, method: str, *args, value: Optional[int] = None) -> Optional[str]:
        tx_params = {
            'to': contract.address,
            'from': self.wallet_address,
            'data': contract.encode_abi(method, args=args),
            'gasPrice': await self.w3.eth.gas_price,
            'nonce': await self.get_transaction_count(),
            'chainId': await self.w3.eth.chain_id
        }
        
        if value:
            tx_params['value'] = value
        
        try:
            estimate_gas = await self.w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimate_gas * 1.1) 
        
        except Exception as e:
            logger.warning(f'{self.wallet_address} | Error estimating gas: {e}')
            return None
        
        return await self.send_transaction(tx_params=tx_params)

    async def bridge_eth(self, contract_address: str, value: Union[TokenAmount, int], abi_path: str, account_index: int) -> Optional[bool]:       
        args = [self.wallet_address, 200000, '0x7375706572627269646765']
        bridge_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=bridge_abi)

        tx = await self.send_transaction_with_abimethod(contract, 'bridgeETHTo', *args, value=value)
        if tx:
            await self.verif_tx(tx, account_index)
            return True

    async def wrap_eth(self, contract_address: str, value: Union[TokenAmount, int], abi_path: str, account_index: int) -> Optional[bool]:
        bal = await self.get_balance()
        if bal <= value:
            logger.warning(f'{self.wallet_address} | Wrap cancelled: balance is less than amount to wrap.')
            return None

        weth_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=weth_abi)

        tx = await self.send_transaction_with_abimethod(contract=contract, method='deposit', value=value)
        if tx:
            await self.verif_tx(tx, account_index)
            return True

    async def deploy_contract(self, account_index: int, name: str, symbol: str, abi_path: str, bytecode_path: str, increase_gas: float = 1.1) -> Optional[str]:
        contract_abi = await Utils.read_json(abi_path)
        contract_bytecode = await Utils.read_file(bytecode_path)
        contract = self.w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

        tx_params = {
            'chainId': await self.w3.eth.chain_id,
            'from': self.wallet_address,
            'nonce': await self.get_transaction_count(),
            'gasPrice': await self.w3.eth.gas_price
        }

        try:
            estimate_gas = await contract.constructor(name, symbol).estimate_gas({'from': self.wallet_address})
            tx_params['gas'] = int(estimate_gas * increase_gas)
        
        except Exception as e:
            logger.warning(f'{self.wallet_address} | Error estimating gas: {e}')
            return None

        construct_tx = await contract.constructor(name, symbol).build_transaction(tx_params)
        tx = await self.send_transaction(tx_params=construct_tx)

        if tx:
            if await self.verif_tx(tx, account_index):
                tx_receipt = await self.w3.eth.wait_for_transaction_receipt(tx, timeout=200)
                return tx_receipt.contractAddress
            
            logger.warning(f'{self.wallet_address} | Contract deployment failed.')
            return None

    async def mint_nft(self, contract_address: str, abi_path: str, account_index: int) -> Optional[bool]:
        contract_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=contract_abi)

        tx = await self.send_transaction_with_abimethod(contract, 'createCollectible')
        if tx:
            return await self.verif_tx(tx, account_index)
        return None

    async def random_interact_with_contract(self, contract_address: str, abi_path: str, account_index: int) -> Optional[bool]:
        contract_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=contract_abi)

        values = [10000, 50000, 100000, 250000, 500000, 1000000]
        available_methods = ['mint', 'burn', 'pause']
        args = []

        random_method = random.choice(available_methods)
        
        if random_method == 'mint':
            random_value = random.choice(values)
            args = [self.wallet_address, random_value * 10 ** 18]
        elif random_method == 'burn':
            random_value = random.choice(values)
            args = [random_value * 10 ** 18]
        
        tx = await self.send_transaction_with_abimethod(contract, random_method, *args)
        
        if tx:
            return await self.verif_tx(tx, account_index)
        return None

    async def mint_morkie_nft(self, contract_address: str, account_index: int) -> Optional[bool]:
        formatted_address = self.wallet_address.lower().replace('0x', '')

        tx_params = {
            'chainId': await self.w3.eth.chain_id,
            'data': f'0x84bb1e42000000000000000000000000{formatted_address}0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'from': self.wallet_address,
            'to': contract_address,
            'nonce': await self.get_transaction_count(),
            'gasPrice': await self.w3.eth.gas_price,
            'value': 0
        }

        try:
            gas_estimate = await self.w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(gas_estimate * 1.1)
        except Exception as e:
            if '2' in str(e):
                logger.info(f'Account {account_index+1} | {self.wallet_address} | Already have NFT from morkie.xyz')
            else:
                logger.error(f'Account {account_index+1} | {self.wallet_address} | Error estimating gas: {e}')
            return None

        tx = await self.send_transaction(tx_params=tx_params)
        if tx:
            return await self.verif_tx(tx, account_index)
        return None
        
    async def verif_tx(self, tx_hash: str, account_index: int) -> bool:
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if data.get('status') == 1:
                logger.debug(f'Account {account_index+1} | {self.wallet_address} | Successful tx: {self.network.explorer}/tx/{tx_hash.hex()}')
                return True 
            else:
                logger.warning(f'Account {account_index+1} | {self.wallet_address} | Failed tx: {self.network.explorer}/tx/{data["transactionHash"].hex()}')
                return False
        except Exception as e:
            logger.warning(f'Account {account_index+1} | {self.wallet_address} | Unexpected error in <verif_tx> function: {e}')
            return False

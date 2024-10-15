import asyncio
from typing import Optional, Union

from web3 import AsyncWeb3
from loguru import logger

from src.utils import Utils
from src.models import Network, TokenAmount


class Client:
    def __init__(self, private_key: str, network: Network):
        self.private_key = private_key
        self.network = network
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(endpoint_uri=self.network.rpc))
        self.wallet_address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)

    async def get_balance(self) -> int:
        return await self.w3.eth.get_balance(self.wallet_address)

    async def send_transaction(self, tx_params: dict) -> Optional[str]:
        try:
            sign = self.w3.eth.account.sign_transaction(tx_params, self.private_key)
            return await self.w3.eth.send_raw_transaction(sign.rawTransaction)
        except Exception as e:
            if 'nonce too low' in str(e):
                logger.warning(f'{self.wallet_address} | Nonce too low. Retrying with updated nonce...')
                tx_params['nonce'] += 1
                return await self.send_transaction(tx_params)
            logger.error(f'{self.wallet_address} | Error sending transaction: {e}')
            return None

    async def send_transaction_with_abimethod(self, contract, method: str, *args, value: Optional[int] = None) -> Optional[str]:
        tx_params = {
            'to': contract.address,
            'data': contract.encode_abi(method, args=args),
            'value': value,
            'gasPrice': await self.w3.eth.gas_price,
            'nonce': await self.w3.eth.get_transaction_count(self.wallet_address),
            'chainId': await self.w3.eth.chain_id
        }

        try:
            estimate_gas = await self.w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimate_gas * 1.1) 
        except Exception as e:
            logger.error(f'{self.wallet_address} | Error estimating gas: {e}')
            return None

        return await self.send_transaction(tx_params)

    async def bridge_eth(self, contract_address: str, value: Union[TokenAmount, int], abi_path: str) -> Optional[bool]:
        bal = await self.get_balance()
        if bal <= value:
            logger.warning(f'{self.wallet_address} | Bridge cancelled: balance is less than amount to bridge.')
            return None

        bridge_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=bridge_abi)

        tx = await self.send_transaction_with_abimethod(contract, 'bridgeETHTo', self.wallet_address, 200000, '0x7375706572627269646765', value=value)
        if tx:
            await self.verif_tx(tx)
            return True

    async def wrap_eth(self, contract_address: str, value: Union[TokenAmount, int], abi_path: str) -> Optional[bool]:
        bal = await self.get_balance()
        if bal <= value:
            logger.warning(f'{self.wallet_address} | Wrapping cancelled: balance is less than amount to wrap.')
            return None

        weth_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=weth_abi)

        tx = await self.send_transaction_with_abimethod(contract, 'deposit', value=value)
        if tx:
            await self.verif_tx(tx)
            return True

    async def deploy_erc721_contract(self, token_name: str, token_symbol: str, abi_path: str, bytecode_path: str, increase_gas: float = 1.1) -> Optional[str]:
        contract_abi = await Utils.read_json(abi_path)
        contract_bytecode = await Utils.read_file(bytecode_path)
        contract = self.w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

        tx_params = {
            'chainId': await self.w3.eth.chain_id,
            'from': self.wallet_address,
            'nonce': await self.w3.eth.get_transaction_count(self.wallet_address),
            'gasPrice': await self.w3.eth.gas_price
        }

        try:
            estimate_gas = await contract.constructor(token_name, token_symbol).estimate_gas({'from': self.wallet_address})
            tx_params['gas'] = int(estimate_gas * increase_gas)
        except Exception as e:
            logger.error(f'{self.wallet_address} | Error estimating gas: {e}')
            return None

        tx = await self.send_transaction(tx_params)
        if tx:
            if await self.verif_tx(tx):
                tx_receipt = await self.w3.eth.wait_for_transaction_receipt(tx, timeout=200)
                logger.success(f'{self.wallet_address} | Contract deployment successful: {tx_receipt.contractAddress}')
                return tx_receipt.contractAddress
            logger.error(f'{self.wallet_address} | Contract deployment failed.')
            return None

    async def mint_nft(self, contract_address: str, abi_path: str) -> Optional[bool]:
        contract_abi = await Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=AsyncWeb3.to_checksum_address(contract_address), abi=contract_abi)

        tx = await self.send_transaction_with_abimethod(contract, 'createCollectible')
        if tx:
            return await self.verif_tx(tx)
        return None

    async def verif_tx(self, tx_hash: str) -> bool:
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if data.get('status') == 1:
                logger.success(f'{self.wallet_address} | Transaction was successful: {tx_hash.hex()}. Explorer: {self.network.explorer}')
                return True
            else:
                logger.error(f'{self.wallet_address} | Transaction failed: {data["transactionHash"].hex()}. Explorer: {self.network.explorer}')
                return False
        except Exception as e:
            logger.error(f'{self.wallet_address} | Unexpected error in <verif_tx> function: {e}')
            return False

    async def get_max_priority_fee_per_gas(self, block: dict) -> int:
        block_number = block['number']
        latest_block_transaction_count = await self.w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_lst = []

        for i in range(latest_block_transaction_count):
            try:
                transaction = await self.w3.eth.get_transaction_by_block(block_number, i)
                if 'maxPriorityFeePerGas' in transaction:
                    max_priority_fee_per_gas_lst.append(transaction['maxPriorityFeePerGas'])
            except Exception:
                continue

        if not max_priority_fee_per_gas_lst:
            return await self.w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_lst.sort()
            return max_priority_fee_per_gas_lst[len(max_priority_fee_per_gas_lst) // 2]
        
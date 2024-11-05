from typing import Optional, Union

from web3 import Web3
from loguru import logger

from src.utils import Utils
from src.models import Network, TokenAmount


class Client:
    def __init__(self, private_key: str, network: Network):
        self.private_key = private_key
        self.network = network
        self.w3 = Web3(Web3.HTTPProvider(endpoint_uri=self.network.rpc))  # Изменяем на синхронный HTTPProvider
        self.wallet_address = Web3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)

    def get_balance(self) -> int:
        return self.w3.eth.get_balance(self.wallet_address)

    def send_transaction(self, tx_params: dict) -> Optional[str]:
        try:
            sign = self.w3.eth.account.sign_transaction(tx_params, self.private_key)
            return self.w3.eth.send_raw_transaction(sign.rawTransaction)
        except Exception as e:
            if 'nonce too low' in str(e):
                logger.warning(f'{self.wallet_address} | Nonce too low. Retrying with updated nonce...')
                tx_params['nonce'] += 1
                return self.send_transaction(tx_params)
            if 'replacement transaction underpriced' in str(e):
                logger.warning(f'{self.wallet_address} | Replacement transaction underpriced. Retrying with updated nonce...')
                tx_params['nonce'] += 1
                return self.send_transaction(tx_params)
            logger.error(f'{self.wallet_address} | Error sending transaction: {e}')
            return None

    def send_transaction_with_abimethod(self, contract, method: str, *args, value: Optional[int] = None) -> Optional[str]:
        tx_params = {
            'to': contract.address,
            'data': contract.encode_abi(method, args=args),
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
            'chainId': self.w3.eth.chain_id
        }
        if value:
            tx_params['value'] = value
        try:
            estimate_gas = self.w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimate_gas * 1.1) 
        except Exception as e:
            logger.error(f'{self.wallet_address} | Error estimating gas: {e}')
            return None
        return self.send_transaction(tx_params)

    def bridge_eth(self, contract_address: str, value: Union[TokenAmount, int], abi_path: str) -> Optional[bool]:
        bal = self.get_balance()
        if bal <= value:
            logger.warning(f'{self.wallet_address} | Bridge cancelled: balance is less than amount to bridge.')
            return None

        bridge_abi = Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=bridge_abi)

        tx = self.send_transaction_with_abimethod(contract, 'bridgeETHTo', self.wallet_address, 200000, '0x7375706572627269646765', value=value)
        if tx:
            self.verif_tx(tx)
            return True

    def wrap_eth(self, contract_address: str, value: Union[TokenAmount, int], abi_path: str) -> Optional[bool]:
        bal = self.get_balance()
        if bal <= value:
            logger.warning(f'{self.wallet_address} | Wrapping cancelled: balance is less than amount to wrap.')
            return None

        weth_abi = Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=weth_abi)

        tx = self.send_transaction_with_abimethod(contract, 'deposit', value=value)
        if tx:
            self.verif_tx(tx)
            return True
        
    def deploy_erc721_contract(self, token_name: str, token_symbol: str, abi_path: str, bytecode_path: str, increase_gas: float = 1.1) -> Optional[str]:
        contract_abi = Utils.read_json(abi_path)
        contract_bytecode = Utils.read_file(bytecode_path)
        contract = self.w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

        tx_params = {
            'chainId': self.w3.eth.chain_id,
            'from': self.wallet_address,
            'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
            'gasPrice': self.w3.eth.gas_price
        }

        try:
            estimate_gas = contract.constructor(token_name, token_symbol).estimate_gas({'from': self.wallet_address})
            tx_params['gas'] = int(estimate_gas * increase_gas)
        except Exception as e:
            logger.error(f'{self.wallet_address} | Error estimating gas: {e}')
            return None

        tx = self.send_transaction(tx_params)
        if tx:
            if self.verif_tx(tx):
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx, timeout=200)
                logger.success(f'{self.wallet_address} | Contract deployment successful: {tx_receipt.contractAddress}')
                return tx_receipt.contractAddress
            logger.error(f'{self.wallet_address} | Contract deployment failed.')
            return None

    def mint_nft(self, contract_address: str, abi_path: str) -> Optional[bool]:
        contract_abi = Utils.read_json(abi_path)
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=contract_abi)

        tx = self.send_transaction_with_abimethod(contract, 'createCollectible')
        if tx:
            return self.verif_tx(tx)
        return None

    def verif_tx(self, tx_hash: str) -> bool:
        try:
            data = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if data.get('status') == 1:
                logger.success(f'{self.wallet_address} | Transaction was successful: {tx_hash.hex()}. Explorer: {self.network.explorer}')
                return True
            else:
                logger.error(f'{self.wallet_address} | Transaction failed: {data["transactionHash"].hex()}. Explorer: {self.network.explorer}')
                return False
        except Exception as e:
            logger.error(f'{self.wallet_address} | Unexpected error in <verif_tx> function: {e}')
            return False

    def get_max_priority_fee_per_gas(self, block: dict) -> int:
        block_number = block['number']
        latest_block_transaction_count = self.w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_lst = []

        for i in range(latest_block_transaction_count):
            try:
                transaction = self.w3.eth.get_transaction_by_block(block_number, i)
                if 'maxPriorityFeePerGas' in transaction:
                    max_priority_fee_per_gas_lst.append(transaction['maxPriorityFeePerGas'])
            except Exception:
                continue

        if not max_priority_fee_per_gas_lst:
            return self.w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_lst.sort()
            return max_priority_fee_per_gas_lst[len(max_priority_fee_per_gas_lst) // 2]
        
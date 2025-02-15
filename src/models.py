from typing import Union
from decimal import Decimal

from config import RPCS


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


class Network:
    def __init__(self, name: str, rpc: str, chain_id: int, coin_symbol: str, explorer: str, decimals: int = 18):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.coin_symbol = coin_symbol
        self.decimals = decimals
        self.explorer = explorer

    def __str__(self):
        return self.name


ethereum_sepolia = Network(
    name='Sepolia',
    rpc=RPCS['ethereum_sepolia'],
    chain_id=11155111,
    coin_symbol='ETH',
    explorer='https://sepolia.etherscan.io'
)

unichain_sepolia = Network(
    name='Unichain Sepolia',
    rpc=RPCS['unichain_sepolia'],
    chain_id=1301,
    coin_symbol='ETH',
    explorer='https://sepolia.uniscan.xyz'
)

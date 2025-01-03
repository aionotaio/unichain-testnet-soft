from typing import Optional

from loguru import logger

from src.client import Client


class MorkieManager():
    async def mint_unicorn_nft(self, client_uni: Client, account_index: int) -> Optional[bool]:
        balance = await client_uni.w3.eth.get_balance(client_uni.wallet_address)
        
        if balance <= 0:
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Mint cancelled: zero balance.')
            return False
        
        try:
            logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Attempting to mint an Unicorn NFT from morkie.xyz...')
            
            result = await client_uni.mint_morkie_nft(
                contract_address='0x99F4146B950Ec5B8C6Bc1Aa6f6C9b14b6ADc6256',
                account_index=account_index,
            )

            return result
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error during minting Unicorn NFT: {e}.')
            return False

    async def mint_europa_nft(self, client_uni: Client, account_index: int) -> Optional[bool]:
        balance = await client_uni.w3.eth.get_balance(client_uni.wallet_address)
        
        if balance <= 0:
            logger.error(f'Account {account_index+1} | {client_uni.wallet_address} | Mint cancelled: zero balance.')
            return False
        
        try:
            logger.info(f'Account {account_index+1} | {client_uni.wallet_address} | Attempting to mint an Europa NFT from morkie.xyz...')
            
            result = await client_uni.mint_morkie_nft(
                contract_address='0x2188DA4AE1CAaFCf2fBFb3ef34227F3FFdc46AB6',
                account_index=account_index,
            )
            
            return result
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error during minting Europa NFT: {e}.')
            return False

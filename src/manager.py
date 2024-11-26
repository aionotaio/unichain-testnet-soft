import random
import asyncio

from loguru import logger

from src.client import Client
from src.models import ethereum_sepolia, unichain_sepolia
from src.utils import Utils, ETHBRIDGE_ABI, WETH_ABI, ERC721_ABI, ERC721_BYTECODE, ERC20_ABI, ERC20_BYTECODE, NAMES_PATH, SYMBOLS_PATH
from config import bridge_amount, wrap_amount, delay


class Manager:
    @staticmethod
    async def bridge_eth(client_eth: Client, bridge_amount=None):
        if bridge_amount == None:
            eth_balance = await client_eth.w3.eth.get_balance(client_eth.wallet_address)
            max_bridge_amount = (eth_balance / 10 ** 18) * (random.randint(1, 50) / 100)
            formatted_amount = float(f"{max_bridge_amount:.5f}")
            bridge_amount = int(formatted_amount * 10 ** 18)
        else:
            bridge_amount = int(bridge_amount * 10 ** 18)

        try:
            logger.info(f'{client_eth.wallet_address} | Attempting to bridge {format(bridge_amount / 10 ** 18, ".18f").rstrip("0").rstrip(".")} ETH...')

            return await client_eth.bridge_eth(
                contract_address='0xea58fcA6849d79EAd1f26608855c2D6407d54Ce2',
                value=bridge_amount,
                abi_path=ETHBRIDGE_ABI
            )
        except Exception as e:
            logger.error(f'{client_eth.wallet_address} | Error bridging ETH: {e}')
            return None
    
    @staticmethod
    async def wrap_eth(client_uni: Client, wrap_amount=None):
        if wrap_amount == None:
            uni_balance = await client_uni.w3.eth.get_balance(client_uni.wallet_address)
            max_wrap_amount = (uni_balance / 10 ** 18) * (random.randint(1, 50) / 100)
            formatted_amount = float(f"{max_wrap_amount:.5f}")
            wrap_amount = int(formatted_amount * 10 ** 18)
        else:
            wrap_amount = int(wrap_amount * 10 ** 18)
    
        try:
            logger.info(f'{client_uni.wallet_address} | Attempting to wrap {format(wrap_amount / 10 ** 18, ".18f").rstrip("0").rstrip(".")} ETH...')
    
            return await client_uni.wrap_eth(
                contract_address='0x4200000000000000000000000000000000000006',
                value=wrap_amount,
                abi_path=WETH_ABI
            )
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error wrapping ETH: {e}')
            return None
    
    @staticmethod
    async def deploy_erc721(client_uni: Client, name: str, symbol: str):
        try:
            logger.info(f'{client_uni.wallet_address} | Attempting to deploy ERC-721 contract in {client_uni.network.name}')
            
            return await client_uni.deploy_contract(
                name=name,
                symbol=symbol,
                abi_path=ERC721_ABI,
                bytecode_path=ERC721_BYTECODE
            )
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error deploying contract: {e}')
            return None

    @staticmethod
    async def mint_nft(client_uni: Client, contract_address: str):
        try:
            logger.info(f'{client_uni.wallet_address} | Attempting to mint NFT with contract {contract_address}')
        
            return await client_uni.mint_nft(
                contract_address=contract_address, 
                abi_path=ERC721_ABI
            )
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error interacting contract: {e}')
            return None
    
    @staticmethod
    async def mint_morkie_nft(client_uni: Client):
        try:
            logger.info(f'{client_uni.wallet_address} | Attempting to mint a Unicorn NFT from morkie.xyz')
        
            return await client_uni.mint_morkie_nft(
                contract_address='0x99F4146B950Ec5B8C6Bc1Aa6f6C9b14b6ADc6256',
            )
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error interacting contract: {e}')
            return None
    
    @staticmethod
    async def deploy_erc20(client_uni: Client, name: str, symbol: str):
        try:
            logger.info(f'{client_uni.wallet_address} | Attempting to deploy ERC-20 contract in {client_uni.network.name}')
            
            return await client_uni.deploy_contract(
                name=name,
                symbol=symbol,
                abi_path=ERC20_ABI,
                bytecode_path=ERC20_BYTECODE
            )
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error deploying contract: {e}')
            return None
    
    @staticmethod
    async def interact_with_contract(client_uni: Client, contract_address: str):
        try:
            logger.info(f'{client_uni.wallet_address} | Attempting to interact with ERC-20 contract {contract_address}')
        
            return await client_uni.random_interact_with_contract(
                contract_address=contract_address,
                abi_path=ERC20_ABI
            )
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error interacting contract: {e}')
            return None
        
    @staticmethod
    async def random_interactions(client_uni: Client):
        wrap_eth_calls = random.randint(0, 3)
        deploy_erc721_calls = random.randint(0, 3)
        deploy_erc20_calls = random.randint(0, 3)

        tasks = []

        try:
            for _ in range(wrap_eth_calls):
                tasks.append(asyncio.create_task(Manager.wrap_eth(client_uni)))

            for _ in range(deploy_erc721_calls):
                name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                deploy_task = asyncio.create_task(Manager.deploy_erc721(client_uni, name, symbol))
            
                tasks.append(deploy_task)
            
                tasks.append(asyncio.create_task(Manager.mint_nft(client_uni, await deploy_task)))

            for _ in range(deploy_erc20_calls):
                name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                deploy_task = asyncio.create_task(Manager.deploy_erc20(client_uni, name, symbol))
            
                tasks.append(deploy_task)
            
                tasks.append(asyncio.create_task(Manager.interact_with_contract(client_uni, await deploy_task)))
            
            tasks.append(asyncio.create_task(Manager.mint_morkie_nft(client_uni)))

            random.shuffle(tasks)

            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f'{client_uni.wallet_address} | Error doing random interactions: {e}')
            return None

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
5. Mint a Unicorn NFT from morkie.xyz.
6. Random interaction
7. Quit\n''')
        
        choice = int(input('Choose an option (1-7): '))
        return choice
    
    @staticmethod
    async def handle_choice(choice: int, private_keys: list, proxies: list):
        tasks = []

        if choice == 1:
            print('''\n1. Bridge a certain amount (change in config.py).
2. Bridge a random amount.\n''')
            
            second_choice = int(input('Choose an option (1-2): '))
            
            if second_choice == 1:
                logger.info('Starting to bridge certain amount ETH...')
                    
                for private_key in private_keys:
                    if proxies:
                        proxy_index = private_keys.index(private_key) % len(proxies)
                        proxy = proxies[proxy_index]
                    else:
                        proxy = None
                    
                    client_eth = Client(private_key, ethereum_sepolia, proxy)
                    tasks.append(asyncio.create_task(Manager.bridge_eth(client_eth, bridge_amount)))
                    await asyncio.sleep(random.randint(delay[0], delay[1]))

            elif second_choice == 2:
                logger.info('Starting to bridge random amount ETH...')
                
                for private_key in private_keys:
                    if proxies:
                        proxy_index = private_keys.index(private_key) % len(proxies)
                        proxy = proxies[proxy_index]
                    else:
                        proxy = None
                    
                    client_eth = Client(private_key, ethereum_sepolia, proxy)
                    tasks.append(asyncio.create_task(Manager.bridge_eth(client_eth)))
                    await asyncio.sleep(random.randint(delay[0], delay[1]))
        elif choice == 2:
            print('''\n1. Wrap a certain amount (change in config.py).
2. Wrap a random amount.\n''')
            
            second_choice = int(input('Choose an option (1-2): '))
            
            if second_choice == 1:
                logger.info('Starting to wrap certain amount ETH...')
                
                for private_key in private_keys:
                    if proxies:
                        proxy_index = private_keys.index(private_key) % len(proxies)
                        proxy = proxies[proxy_index]
                    else:
                        proxy = None
                    
                    client_uni = Client(private_key, unichain_sepolia, proxy)
                    tasks.append(asyncio.create_task(Manager.wrap_eth(client_uni, wrap_amount)))
                    await asyncio.sleep(random.randint(delay[0], delay[1]))
            elif second_choice == 2:
                logger.info('Starting to wrap random amount ETH...')
                
                for private_key in private_keys:
                    if proxies:
                        proxy_index = private_keys.index(private_key) % len(proxies)
                        proxy = proxies[proxy_index]
                    else:
                        proxy = None
                    
                    client_uni = Client(private_key, unichain_sepolia, proxy)
                    tasks.append(asyncio.create_task(Manager.wrap_eth(client_uni)))
                    await asyncio.sleep(random.randint(delay[0], delay[1]))
        elif choice == 3:
            logger.info('Starting to deploy an ERC-721 contract...')
            
            deploy_tasks = []
            
            for private_key in private_keys:
                if proxies:
                    proxy_index = private_keys.index(private_key) % len(proxies)
                    proxy = proxies[proxy_index]
                else:
                    proxy = None
                
                client_uni = Client(private_key, unichain_sepolia, proxy)
                name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                deploy_tasks.append(asyncio.create_task(Manager.deploy_erc721(client_uni, name, symbol)))
                await asyncio.sleep(random.randint(delay[0], delay[1]))     
        
            results = await asyncio.gather(*deploy_tasks)

            for i, deploy_result in enumerate(results):
                if deploy_result is not None:
                    if proxies:
                        proxy_index = i % len(proxies)
                        proxy = proxies[proxy_index]
                    else:
                        proxy = None
                    
                    client_uni = Client(private_keys[i], unichain_sepolia, proxy)
                    tasks.append(asyncio.create_task(Manager.mint_nft(client_uni, deploy_result)))
                    await asyncio.sleep(random.randint(delay[0], delay[1]))
        elif choice == 4:
            logger.info('Starting to deploy an ERC-20 contract...')
            
            deploy_tasks = []
            
            for private_key in private_keys:
                if proxies:
                    proxy_index = private_keys.index(private_key) % len(proxies)
                    proxy = proxies[proxy_index]
                else:
                    proxy = None
                
                client_uni = Client(private_key, unichain_sepolia, proxy)
                name, symbol = await Utils.get_random_name_and_symbol(NAMES_PATH, SYMBOLS_PATH)
                deploy_tasks.append(asyncio.create_task(Manager.deploy_erc20(client_uni, name, symbol)))
                await asyncio.sleep(random.randint(delay[0], delay[1]))
        
            results = await asyncio.gather(*deploy_tasks)

            for i, deploy_result in enumerate(results):
                if deploy_result is not None:
                    if proxies:
                        proxy_index = i % len(proxies)
                        proxy = proxies[proxy_index]
                    else:
                        proxy = None
                    
                    client_uni = Client(private_keys[i], unichain_sepolia, proxy)
                    tasks.append(asyncio.create_task(Manager.interact_with_contract(client_uni, deploy_result)))
                    await asyncio.sleep(random.randint(delay[0], delay[1]))
        elif choice == 5:
            logger.info('Starting to mint a Unicorn NFT from morkie.xyz...')

            for private_key in private_keys:
                if proxies:
                    proxy_index = private_keys.index(private_key) % len(proxies)
                    proxy = proxies[proxy_index]
                else:
                    proxy = None
                client_uni = Client(private_key, unichain_sepolia, proxy)
                tasks.append(asyncio.create_task(Manager.mint_morkie_nft(client_uni)))
                await asyncio.sleep(random.randint(delay[0], delay[1]))
        elif choice == 6:
            logger.info('Starting random interactions...')
            
            for private_key in private_keys:
                if proxies:
                    proxy_index = private_keys.index(private_key) % len(proxies)
                    proxy = proxies[proxy_index]
                else:
                    proxy = None
                client_uni = Client(private_key, unichain_sepolia, proxy)
                tasks.append(asyncio.create_task(Manager.random_interactions(client_uni)))
                await asyncio.sleep(random.randint(delay[0], delay[1]))
        elif choice == 7:
            pass
        else:
            logger.error('Print a number from 1 to 6.')
        
        await asyncio.gather(*tasks)

        logger.info('Finished.')

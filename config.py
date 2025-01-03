BRIDGE_PARAMS = {
    "min_balance": False, 
    "amount": False, 
    "percent": (5, 10),
    "timeout": 120 
}

WRAP_PARAMS = {
    "min_balance": False, 
    "amount": False, 
    "percent": (5, 10)
}

RANDOM_CONFIG = {
    'max_actions': {
        'erc721_count': (1, 1),
        'erc20_count': (1, 1),
        'wrap_count': (1, 1)
    }
}

RPCS = {
    "ethereum_sepolia": 'https://ethereum-sepolia-rpc.publicnode.com',
    "unichain_sepolia": 'https://sepolia.unichain.org/'
}

DELAY_BETWEEN_TX = (5, 12)
DELAY_BETWEEN_ACC = (10, 20)
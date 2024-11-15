# Unichain Testnet Soft

## Functionality
- Bridge from Ethereum Sepolia to Unichain Sepolia
- Wrap ETH in Unichain Sepolia
- Deploy an ERC-721 contract in Unichain Sepolia + interact with it
- Deploy an ERC-20 contract in Unichain Sepolia + interact with it
- Making random interactions in Unichain Sepolia

## Settings
- `files/private_keys.txt` - Private keys. 1 line = 1 private key

## config.py
- `bridge_amount` - Amount in ETH you want to bridge from Ethereum Sepolia to Unichain Sepolia
- `wrap_amount` - Amount in ETH you want to wrap in Unichain Sepolia

### Follow: https://t.me/touchingcode

## Run
- Python version: 3.10+

- Installing virtual env: \
`pip install virtualenv` \
`cd <project_dir>` \
`python -m venv venv`

- Activating: 
    - Mac/Linux - `source venv/bin/activate` 
    - Windows - `.\venv\Scripts\activate` 

- Installing dependencies: \
`pip install -r requirements.txt`

- Run main script: \
`python main.py`

## Results
- `logs/logs.txt` - Logs

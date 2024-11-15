import asyncio

from loguru import logger

from src.utils import Utils, PRIVATE_KEYS_PATH, LOGS_PATH
from src.manager import Manager


logger.add(sink=LOGS_PATH, format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", level="INFO", rotation="100 MB")

async def main():
    choice = Manager.open_menu()
    private_keys = await Utils.read_strings_from_file(PRIVATE_KEYS_PATH)
    
    await Manager.handle_choice(choice, private_keys)

if __name__ == '__main__':
    asyncio.run(main())

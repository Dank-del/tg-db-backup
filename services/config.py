import os
from dotenv import load_dotenv
from telethon import TelegramClient


class ConfigService:
    API_ID: int = int()
    API_HASH: str = ""
    BOT_TOKEN: str = ""
    TELETHON_CLIENT: TelegramClient = None
    OWNER_ID: int = int()

    def __init__(self):
        load_dotenv()
        self.API_ID = int(os.getenv("API_ID", "0"))
        self.API_HASH = os.getenv("API_HASH", "")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.OWNER_ID = int(os.getenv("OWNER_ID", "0"))

        if not self.API_ID or not self.API_HASH or not self.BOT_TOKEN:
            raise ValueError("API_ID, API_HASH, and BOT_TOKEN must be set in environment variables.")
        
        if not self.OWNER_ID:
            raise ValueError("OWNER_ID must be set in environment variables and be a valid integer.")
        
        self.TELETHON_CLIENT = TelegramClient('bot', self.API_ID, self.API_HASH)
        
    async def initialize_client(self):
        await self.TELETHON_CLIENT.start(bot_token=self.BOT_TOKEN)
        

config_service = ConfigService()

    
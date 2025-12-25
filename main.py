from services.config import config_service
import logging, asyncio
from handlers.start import StartCommand

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

async def main():
    print("Hello from tg-db-backup!")
    await config_service.initialize_client()
    me = await config_service.TELETHON_CLIENT.get_me()
    logger.info(f"Logged in as {me.first_name} (id: {me.id}, username: @{me.username})") 
    
    # Register commands
    start_command = StartCommand(config_service.TELETHON_CLIENT)
    start_command.register()
    
    await config_service.TELETHON_CLIENT.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

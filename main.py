from services.config import config_service
from services.database_config import DatabaseConfigParser
from services.backup_service import BackupService
import logging, asyncio, schedule

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

async def main():
    print("Hello from tg-db-backup!")
    await config_service.initialize_client()
    me = await config_service.TELETHON_CLIENT.get_me()
    logger.info(f"Logged in as {me.first_name} (id: {me.id}, username: @{me.username})") 
    
    db_parser = DatabaseConfigParser('config.yaml')
    backup_service = BackupService(config_service, db_parser)
    
    databases = db_parser.parse()
    for db in databases:
        if db['schedule']:
            job = db_parser.create_schedule_job(db['schedule'])
            job.do(lambda db=db: asyncio.create_task(backup_service.backup_database(db)))
    
    async def schedule_loop():
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
    
    # Register commands
    from handlers.start import StartCommand
    start_command = StartCommand(config_service.TELETHON_CLIENT, db_parser)
    start_command.register()
    
    from handlers.backup import BackupCommand
    backup_command = BackupCommand(config_service.TELETHON_CLIENT, backup_service, db_parser)
    backup_command.register()
    
    await asyncio.gather(
        config_service.TELETHON_CLIENT.run_until_disconnected(),
        schedule_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())

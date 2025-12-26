import os
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from services.config import ConfigService
from services.database_config import DatabaseConfigParser
from services.db_providers.postgresql import PostgreSQLBackup


class BackupService:
    """
    A service class for managing database backups, supporting multiple database protocols.
    This class handles the backup process for various databases by parsing configurations,
    performing backups using protocol-specific handlers, and sending the backup files
    to specified Telegram channels. It ensures cleanup of temporary files after upload.
    Attributes:
        config_service (ConfigService): Service for configuration management, including
            the Telethon client for Telegram interactions.
        db_parser: Parser object responsible for extracting database configurations.
        backup_handlers (dict): Dictionary mapping protocol names (e.g., "postgresql")
            to their respective backup handler instances.
    Methods:
        __init__(config_service, db_parser):
            Initializes the BackupService with the given configuration service and database parser.
            Args:
                config_service (ConfigService): The configuration service instance.
                db_parser: The database parser instance.
        backup_all_databases():
            Asynchronously backs up all databases parsed from the configuration.
            This method iterates through the list of databases and triggers backup for each
            that has a valid URL or database name.
        backup_database(db_config, progress_message=None):
            Asynchronously backs up a single database based on the provided configuration.
            Args:
                db_config (Dict[str, Any]): Dictionary containing database configuration,
                    including 'protocol', 'url', 'database', and 'channel_id'.
                progress_message (Optional[Any]): Optional message object for updating
                    upload progress in Telegram.
            Raises:
                NotImplementedError: If no backup handler is available for the specified protocol.
        _send_to_channel(channel_id, filename, progress_message=None):
            Private method to send a backup file to a Telegram channel.
            Args:
                channel_id (str): The ID of the Telegram channel to send the file to.
                filename (str): Path to the backup file to be sent.
                progress_message (Optional[Any]): Optional message for progress updates.
            The method generates a caption with the database name and timestamp, and
            optionally reports upload progress. The file is removed after sending.
    """
    def __init__(self, config_service, db_parser):
        self.config_service: ConfigService = config_service
        self.db_parser: DatabaseConfigParser = db_parser
        self.backup_handlers = {
            "postgresql": PostgreSQLBackup(),
        }

    async def backup_all_databases(self):
        databases = self.db_parser.parse()
        for db in databases:
            if db["url"] or db["database"]:
                await self.backup_database(db)

    async def backup_database(self, db_config: Dict[str, Any], progress_message: Optional[Any] = None):
        handler = self.backup_handlers.get(db_config["protocol"])
        if not handler:
            raise NotImplementedError(
                f"Backup for {db_config['protocol']} not implemented"
            )
        filename = await handler.backup(db_config)
        try:
            await self._send_to_channel(db_config["channel_id"], filename, progress_message)
        finally:
            os.remove(filename)

    async def _send_to_channel(self, channel_id: str, filename: str, progress_message: Optional[Any] = None):
        if channel_id:
            timestamp = datetime.now().isoformat()
            db_name = filename.split('_')[0] if '_' in filename else 'backup'
            caption = f"Backup of {db_name} at {timestamp}"
            
            if progress_message:
                loop = asyncio.get_event_loop()
                last_update = [0]
                def progress(current, total):
                    if total > 0:
                        percent = (current / total) * 100
                        if percent - last_update[0] >= 10:
                            last_update[0] = percent
                            loop.create_task(progress_message.edit(f"Upload progress: {percent:.1f}%"))
                await self.config_service.TELETHON_CLIENT.send_file(channel_id, filename, caption=caption, progress_callback=progress)
            else:
                await self.config_service.TELETHON_CLIENT.send_file(channel_id, filename, caption=caption)

import os
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from services.config import ConfigService
from services.db_providers.postgresql import PostgreSQLBackup


class BackupService:
    def __init__(self, config_service, db_parser):
        self.config_service: ConfigService = config_service
        self.db_parser = db_parser
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

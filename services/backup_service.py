import os
import subprocess
from typing import Dict, Any
from datetime import datetime

from services.config import ConfigService


class BackupService:
    def __init__(self, config_service, db_parser):
        self.config_service: ConfigService = config_service
        self.db_parser = db_parser

    async def backup_all_databases(self):
        databases = self.db_parser.parse()
        for db in databases:
            if db["url"] or db["database"]:
                await self.backup_database(db)

    async def backup_database(self, db_config: Dict[str, Any]):
        if db_config["protocol"] == "postgresql":
            await self._backup_postgresql(db_config)
        else:
            raise NotImplementedError(
                f"Backup for {db_config['protocol']} not implemented"
            )

    async def _backup_postgresql(self, db_config: Dict[str, Any]):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{db_config['database'] or 'backup'}_{timestamp}.sql"
        cmd = [
            "pg_dump",
            "--host",
            db_config["host"],
            "--port",
            db_config["port"],
            "--username",
            db_config["user"],
            "--dbname",
            db_config["database"],
            "--file",
            filename,
        ]
        env = os.environ.copy()
        if db_config["password"]:
            env["PGPASSWORD"] = db_config["password"]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")
        try:
            await self._send_to_channel(db_config["channel_id"], filename)
        finally:
            os.remove(filename)

    async def _send_to_channel(self, channel_id: str, filename: str):
        if channel_id:
            timestamp = datetime.now().isoformat()
            db_name = filename.split('_')[0] if '_' in filename else 'backup'
            caption = f"Backup of {db_name} at {timestamp}"
            await self.config_service.TELETHON_CLIENT.send_file(channel_id, filename, caption=caption)

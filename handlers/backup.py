from common.base_command import BaseCommand
from typing import List, Dict, Any


class BackupCommand(BaseCommand):
    command_name = "backup"
    description = "Perform an immediate backup of a specified database."
    aliases = ["bkp"]

    def __init__(self, client, backup_service, db_parser):
        super().__init__(client)
        self.backup_service = backup_service
        self.db_parser = db_parser

    async def execute(self, event, args: List[str]):
        if not args:
            await event.respond("Usage: /backup <database_name>")
            return
        db_name = args[0]
        databases = self.db_parser.parse()
        db_config = next((db for db in databases if db['database'] == db_name), None)
        if not db_config:
            await event.respond(f"Database '{db_name}' not found in configuration.")
            return
        try:
            await self.backup_service.backup_database(db_config)
            await event.respond(f"Backup of '{db_name}' completed successfully.")
        except Exception as e:
            await event.respond(f"Backup of '{db_name}' failed: {str(e)}")
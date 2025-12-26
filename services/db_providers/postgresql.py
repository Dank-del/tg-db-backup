import os
import subprocess
from typing import Dict, Any
from datetime import datetime
from common.db_backup import DatabaseBackup


class PostgreSQLBackup(DatabaseBackup):
    """A backup provider for PostgreSQL databases.

    This class implements the DatabaseBackup interface to perform asynchronous backups
    of PostgreSQL databases using the pg_dump command-line tool. It generates a timestamped
    SQL dump file containing the database schema and data.
    """
    async def backup(self, db_config: Dict[str, Any]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        return filename

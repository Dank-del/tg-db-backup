from typing import Dict, Any
import abc

class DatabaseBackup(abc.ABC):
    @abc.abstractmethod
    async def backup(self, db_config: Dict[str, Any]) -> str:
        pass
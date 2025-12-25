import yaml
from urllib.parse import urlparse
from typing import List, Dict, Optional, Union, Any
import schedule


class DatabaseConfigParser:
    """
    A class to parse the config.yaml file for database configurations.
    Supports both full SQL database URL strings and individual component specifications.
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.databases: List[Dict[str, Optional[Union[str, Dict[str, Any]]]]] = []

    def parse(self) -> List[Dict[str, Optional[Union[str, Dict[str, Any]]]]]:
        """
        Parses the YAML configuration file and returns a list of database configurations.
        Each configuration is a dictionary with keys: protocol, host, port, user, password, database, channel_id, schedule.
        The schedule can be a string or a dict.
        """
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)

        self.databases = []
        for db in data.get('databases', []):
            if 'url' in db and db['url']:
                parsed_db = self._parse_url(db['url'])
            else:
                parsed_db = {
                    'protocol': db.get('protocol', 'postgresql'),
                    'host': db.get('host', 'localhost'),
                    'port': str(db.get('port', 5432)),
                    'user': db.get('user'),
                    'password': db.get('password'),
                    'database': db.get('database'),
                }
            parsed_db['channel_id'] = db.get('channel_id')
            if parsed_db['channel_id'] and isinstance(parsed_db['channel_id'], str):
                try:
                    parsed_db['channel_id'] = int(parsed_db['channel_id'])
                except ValueError:
                    pass
            parsed_db['schedule'] = db.get('schedule')
            self.databases.append(parsed_db)

        return self.databases

    def _parse_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Parses a database URL string into components.
        """
        parsed = urlparse(url)
        return {
            'protocol': parsed.scheme,
            'host': parsed.hostname,
            'port': str(parsed.port) if parsed.port else None,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/') if parsed.path else None,
        }

    def get_databases(self) -> List[Dict[str, Optional[Union[str, Dict[str, Any]]]]]:
        """
        Returns the parsed list of database configurations.
        """
        return self.databases

    def create_schedule_job(self, sched_dict: Dict[str, Any]) -> schedule.Job:
        """
        Creates a schedule.Job from a schedule dict.
        Supported keys: every (int), unit (str like 'day', 'hour'), at (str like '10:00')
        """
        if not sched_dict:
            raise ValueError("Schedule dict is empty")

        job = schedule.every(sched_dict.get('every', 1))
        unit = sched_dict.get('unit', 'day')
        job = getattr(job, unit)
        if 'at' in sched_dict:
            job = job.at(sched_dict['at'])
        return job
from common.base_command import BaseCommand


class StartCommand(BaseCommand):
    command_name = "start"
    description = "Start the bot and get a welcome message."
    aliases = ["begin", "initiate"]

    def __init__(self, client, db_parser):
        super().__init__(client)
        self.db_parser = db_parser

    async def execute(self, event, args):
        databases = self.db_parser.parse()
        status = "Welcome! The bot is active.\n\nConfigured Databases:\n"
        for i, db in enumerate(databases, 1):
            status += f"{i}. {db['database'] or 'Unnamed'} ({db['protocol']}) - Channel: {db['channel_id'] or 'None'}\n"
            if db['schedule']:
                sched = db['schedule']
                status += f"   Schedule: Every {sched.get('every', 1)} {sched.get('unit', 'day')}"
                if 'at' in sched:
                    status += f" at {sched['at']}"
                status += "\n"
            else:
                status += "   Schedule: None\n"
        await event.respond(status)

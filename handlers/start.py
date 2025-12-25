from common.base_command import BaseCommand


class StartCommand(BaseCommand):
    command_name = "start"
    description = "Start the bot and get a welcome message."
    aliases = ["begin", "initiate"]

    async def execute(self, event, args):
        await event.respond("Welcome! The bot is now active and ready to use.")

from abc import ABC, abstractmethod
from typing import Optional, List, Any
from telethon import TelegramClient, events
from telethon.events import NewMessage
import re
import logging
from services.config import config_service

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """
    Base class for creating custom Telegram bot commands.

    Subclasses should override the `execute` method and optionally
    customize the `command_name`, `description`, and other properties.
    """

    # Default command prefixes
    COMMAND_PREFIXES = ["/", "!"]

    def __init__(self, client: TelegramClient):
        self.client = client
        self._command_name = getattr(self, "command_name", None)
        self._description = getattr(self, "description", "No description provided")
        self._aliases = getattr(self, "aliases", [])
        self._prefixes = getattr(self, "prefixes", self.COMMAND_PREFIXES)

    @property
    def command_name(self) -> Optional[str]:
        """
        The command name without prefix.
        Override in subclasses or set as class attribute.
        """
        return self._command_name

    @property
    def description(self) -> str:
        """Command description for help text"""
        return self._description

    @property
    def aliases(self) -> List[str]:
        """Alternative command names (without prefixes)"""
        return self._aliases

    @property
    def min_args(self) -> int:
        """Minimum number of arguments required for this command"""
        return getattr(self, "min_args", 0)

    @property
    def usage(self) -> str:
        """Usage message for the command"""
        cmd = getattr(self, 'matched_command', self.command_name)
        if hasattr(self, "usage"):
            return self.usage.format(command=cmd)
        if self.min_args > 0:
            args_str = " ".join([f"<arg{i+1}>" for i in range(self.min_args)])
            return f"Usage: /{cmd} {args_str}"
        return f"Usage: /{cmd}"

    @property
    def prefixes(self) -> List[str]:
        """Command prefixes to support (e.g., ['/', '!'])"""
        return self._prefixes

    @property
    def pattern(self) -> str:
        """
        Auto-generated regex pattern that matches all prefixes + command names (including aliases).
        """
        if not self.command_name:
            raise ValueError(
                f"Command {self.__class__.__name__} must define a command_name"
            )
        escaped_prefixes = [re.escape(prefix) for prefix in self.prefixes]

        prefix_pattern = "|".join(escaped_prefixes)
        commands = [self.command_name] + self.aliases
        command_pattern = "|".join(re.escape(cmd) for cmd in commands)

        return rf"(?i)(^|\s)({prefix_pattern})({command_pattern})(\s|$)"

    def matches(self, text: str):
        """Check if the given text matches this command's pattern"""
        if not self.pattern:
            return None
        return re.match(self.pattern, text, re.IGNORECASE)

    def parse_args(self, text: str) -> List[str]:
        """
        Parse command arguments from message text.
        Extracts text after the command.
        """
        match = re.search(self.pattern, text)
        if not match:
            return []

        command_end = match.end()
        remaining = text[command_end:].strip()

        if remaining:
            args = []
            current_arg = ""
            in_quotes = False
            quote_char = None

            for char in remaining:
                if not in_quotes and char in ('"', "'"):
                    in_quotes = True
                    quote_char = char
                elif in_quotes and char == quote_char:
                    in_quotes = False
                    quote_char = None
                elif not in_quotes and char.isspace():
                    if current_arg:
                        args.append(current_arg)
                        current_arg = ""
                else:
                    current_arg += char

            if current_arg:
                args.append(current_arg)

            return args

        return []

    async def can_execute(self, event: NewMessage.Event) -> bool:
        """
        Check if this command can be executed in the current context.
        Override in subclasses to add permissions, context checks, etc.
        """
        return event.sender_id == config_service.OWNER_ID

    @abstractmethod
    async def execute(self, event: NewMessage.Event, args: List[str]) -> Any:
        """
        Execute the command logic.
        Must be implemented by subclasses.

        Args:
            event: The NewMessage event
            args: Parsed command arguments

        Returns:
            Any: Command result (optional)
        """
        pass

    async def handle_error(self, event: NewMessage.Event, error: Exception) -> None:
        """
        Handle errors that occur during command execution.
        Override in subclasses for custom error handling.
        """
        logger.error(f"Error executing command {self.command_name}: {error}")
        try:
            await event.reply(f"❌ Error executing command: {str(error)}")
        except Exception as reply_error:
            logger.error(f"Failed to send error reply: {reply_error}")

    async def __call__(self, event: NewMessage.Event) -> None:
        """
        Main handler method called by the event system.
        Don't override this - override execute() instead.
        """
        try:
            match_obj = self.matches(event.raw_text)
            if not match_obj:
                return

            if not await self.can_execute(event):
                return

            self.matched_command = match_obj.group(3)
            args = self.parse_args(event.raw_text)
            if len(args) < self.min_args:
                await event.reply(self.usage.format(command=self.matched_command))
                return

            await self.execute(event, args)

        except Exception as e:
            await self.handle_error(event, e)

    def get_event_handler(self) -> events.NewMessage:
        """
        Get the event handler for this command.
        Use this to register the command with the client.
        """
        return events.NewMessage(func=self)

    def register(self, client: Optional[TelegramClient] = None) -> None:
        """
        Register this command with a Telegram client.
        If no client is provided, uses the client from __init__.
        """
        client = client or self.client
        if not client:
            raise ValueError("No client provided for command registration")

        client.add_event_handler(self, self.get_event_handler())
        logger.info(f"Registered command: {self.command_name}")

    def unregister(self, client: Optional[TelegramClient] = None) -> None:
        """
        Unregister this command from a Telegram client.
        """
        client = client or self.client
        if not client:
            return

        client.remove_event_handler(self, self.get_event_handler())
        logger.info(f"Unregistered command: {self.command_name}")

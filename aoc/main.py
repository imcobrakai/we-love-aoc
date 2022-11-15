import logging
import os

import discord
from discord.ext import commands

DESCRIPTION = """
Hey Everyone! Use me to Check your Rank!!
"""

EXTENSIONS = (
    "internal_commands", 
    "cogs.hacksquad",
)


class AocBot(commands.AutoShardedBot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=os.getenv("PREFIX") or "!",
            description=DESCRIPTION,
            intents=discord.Intents.all(),
        )
    
    async def setup_hook(self) -> None:
        for extension in EXTENSIONS:
            try:
                await self.load_extension(
                    f"aoc.{extension}"
                )
            except Exception:
                logging.exception(f"Could not load {extension} due to an error")
from aoc.main import AocBot

from .core import Aoc


async def setup(bot: AocBot):
    cog = Aoc(bot)
    await bot.add_cog(cog)

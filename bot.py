import contextlib
import os

from aoc.main import AocBot

with contextlib.suppress(ImportError):
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()

bot = AocBot()

bot.run(os.getenv("TOKEN"))

from dotenv import load_dotenv

load_dotenv()

# This example requires the 'message_content' intent.

import discord
import os

from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)

@bot.command()
async def test2(ctx, *args):
    res = " ".join(args)
    await ctx.send(res if res is not None else "Hello")

@bot.command()
async def test3(ctx, *, kwarg):
    await ctx.send(kwarg)

@bot.command(name="list")
async def _list(ctx):
    print("This is the list of the commands")

@bot.command()
async def guild(ctx):
    res = f"""
Guild Name: {ctx.guild}
Message : {ctx.message}
Sender : {ctx.author}
"""
    await ctx.send(res)

@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(a + b)

import random

class Slapper(commands.Converter):
    async def convert(self, ctx, arg):
        to_slap = random.choice(ctx.guild.members)
        print(ctx.guild.members)
        return f"{ctx.author} slapped {to_slap} because {arg}"

@bot.command()
async def slap(ctx, *, arg : Slapper):
    await ctx.send(arg)




bot.run(os.getenv('TOKEN'))
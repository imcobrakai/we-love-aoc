import logging
import random
from typing import List, TypedDict

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from rapidfuzz import process

from aoc.cogs.aoc.utils import Requester
from aoc.main import AocBot

from .utils import HACKSQUAD_COLOR, AocContributor, Requester, ResponseError

SOME_RANDOM_ASS_QUOTES = [
    "Seriously... If you're gonna win, can you... give me one of your shirt?",
    "Hacktoberfest's nice. Hacksquad's better.",
    "I like #memes. No seriously, it's too good.",
    "btw i use arch",
    "Wait. Open Source is just for the free T-shirt? Always has been.",
    "I'm number #0 in the leaderboard bro! Who can win against me, the great HackSquad bot??",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "E.",
    "I see no God up here. OTHER THAN ME!",
    "I have no idea what I'm doing...",
    "I am a NFT.",
    'Why is this variable called "SOME_RANDOM_ASS_QUOTES"? I\'m legit NOT LYING!',
    "What a Wonderful World",
    "Nevo David is awesome, don't you think?",
    "Thank you, Nevo David, HellFire, sravan, Santosh, Midka, and Capt. Pred for making me alive :)",
    "imma just .pop the line where I say nevo david is awesome... but he's so handsome tho...",
    "Hey Mods, can you be a huge freaking favor? Can you literally start banning anyone that does spammy PRs? David can you tell them.",
    "Yes, all of those quotes are not funny. Made by someone not funny.",
    "I'm not an AI, I'm just a randomly picked, stupid string!",
    "skill issue!",
]


class Aoc(commands.Cog):
    def __init__(self, bot: AocBot) -> None:
        self.bot = bot

    @app_commands.command(description="Ping pong")
    # @app_commands.describe()
    async def ping(self, interaction: Interaction) -> None:
        await interaction.response.send_message("Pong!")

    @staticmethod
    def hero_embed_formatter(contributor: AocContributor) -> discord.Embed:
        name = f"AOC Contributor: {contributor['name']}" or "Name not found"

        embed = discord.Embed(
            title=f"{name}",
            color=HACKSQUAD_COLOR,
        )
        embed.add_field(
            name="GitHub",
            value=f"[{contributor['github']}](https://github.com/{contributor['github']})",
        )
        embed.add_field(name="Total PRs", value=contributor["total_pulls"])

        embed.set_thumbnail(url=contributor["avatar_url"])
        embed.set_footer(
            text=f"About: {contributor['bio'] or 'No bio'}",
            icon_url="https://avatars.githubusercontent.com/u/116383341?v=4",
        )

        return embed

    @app_commands.command()
    @app_commands.describe(page="The page to show.")
    async def leaderboard(
        self, interaction: Interaction, *, page: app_commands.Range[int, 1, None] = 1
    ):
        """
        Show the leaderboard of HackSquad 2022!
        """
        if page <= 0:
            await interaction.response.send_message("The page cannot be negative or 0.")
            return
        await interaction.response.defer()

        page -= 1

        class MinifiedPartialTeam(TypedDict):
            place: int
            name: str
            score: int
            slug: str

        results = await Requester().fetch_leaderboard()
        results.sort(key=lambda x: x["score"], reverse=True)

        teams: List[MinifiedPartialTeam] = [
            MinifiedPartialTeam(
                place=place, name=result["name"], score=result["score"], slug=result["slug"]
            )
            for place, result in enumerate(results, 1)
        ]

        list_of_teams = [teams[x : x + 10] for x in range(0, len(teams), 10)]

        # sourcery skip: min-max-identity
        if page >= len(list_of_teams):
            # Last page
            page = len(list_of_teams) - 1

        teams = list_of_teams[page]
        embed = discord.Embed(
            title="Leaderboard - HackSquad 2022",
            color=HACKSQUAD_COLOR,
            url="https://hacksquad.dev/leaderboard",
        )

        embed.description = "\n".join(
            f"`{team['place']}` : [`{team['name']}`](https://hacksquad.dev/team/{team['slug']}) with a score of **{team['score']}** PRs  (Slug: `{team['slug']}`)"
            for team in teams
        )

        embed.set_footer(
            text=f"Page {page + 1}/{len(list_of_teams)}\n{random.choice(SOME_RANDOM_ASS_QUOTES)}",
            icon_url="https://i.imgur.com/kDynel4.png",
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command()
    async def hero(self, interaction: discord.Interaction, *, hero: str):
        """
        Show the details of an hero that have contributed to Novu.
        """
        await interaction.response.defer()

        contributor = await Requester().fetch_contributor(hero)

        await interaction.followup.send(embed=self.hero_embed_formatter(contributor))

    @hero.autocomplete("hero")
    async def hero_autocomplete(
        self, _: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        result = await Requester().fetch_contributors_mini()
        return [
            app_commands.Choice(name=contributor["github"], value=contributor["github"])
            for contributor in result
            if current.lower() in contributor["github"].lower()
        ][:25]

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CommandInvokeError) and isinstance(
            error.original, ResponseError
        ):
            if error.original.code == 404:
                await interaction.followup.send(
                    "Could not find what you're looking for :( Try again!"
                )
            else:
                await interaction.followup.send(
                    f"An unexpected error happened with the HackSquad API: Status code: {error.original.code}"
                )
            return
        logging.exception(error)
        await interaction.followup.send(f"Unexpected error:\n\n```py\n{error}\n```")

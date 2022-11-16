import logging
import random
from typing import List, TypedDict

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from aoc.cogs.aoc.utils import Requester
from aoc.main import AocBot

from .utils import AOC_COLOR, AocContributor, Requester, ResponseError

SOME_RANDOM_ASS_QUOTES = [
    "Seriously... If you're gonna win, can you... give me one of your shirt?",
    "I like #memes. No seriously, it's too good.",
    "btw i use arch",
    "Wait. Open Source is just for the free T-shirt? Always has been.",
    "I'm number #0 in the leaderboard bro! Who can win against me, the great AOC bot??",
    "I see no God up here. OTHER THAN ME!",
    "I have no idea what I'm doing...",
    "I am a NFT.",
    "What a Wonderful World",
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
        temp_name = contributor['name'] if contributor['name'] is not None else "No Name"
        name = f"AOC Contributor: {temp_name}" or "Name not found"

        embed = discord.Embed(
            title=f"{name}",
            color=AOC_COLOR,
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
        Show the leaderboard of AOC 2022!
        """
        if page <= 0:
            await interaction.response.send_message("The page cannot be negative or 0.")
            return
        await interaction.response.defer()

        page -= 1

        class PartialContributor(TypedDict):
            place: int
            name: str
            score: int

        results = await Requester().fetch_leaderboard()
        results.sort(key=lambda x: x["score"], reverse=True)

        contributors: List[PartialContributor] = [
            PartialContributor(
                place=place, name=result["name"], score=result["score"]
            )
            for place, result in enumerate(results, 1)
        ]

        list_of_contributors = [contributors[x : x + 10] for x in range(0, len(contributors), 10)]

        # sourcery skip: min-max-identity
        if page >= len(list_of_contributors):
            # Last page
            page = len(list_of_contributors) - 1

        contributors = list_of_contributors[page]
        embed = discord.Embed(
            title="Leaderboard - Automn of Code 2022",
            color=AOC_COLOR,
            # url="https://hacksquad.dev/leaderboard",
        )

        embed.description = "\n".join(
            f"`{contrib['place']}` : [`{contrib['name']}`](https://github.com/{contrib['name']}) with a score of **{contrib['score']}** PRs"
            for contrib in contributors
        )

        embed.set_footer(
            text=f"Page {page + 1}/{len(list_of_contributors)}\n{random.choice(SOME_RANDOM_ASS_QUOTES)}",
            icon_url="https://avatars.githubusercontent.com/u/116383341?v=4",
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command()
    async def hero(self, interaction: discord.Interaction, *, hero: str):
        """
        Show the details of the hero who have contributed to AOC.
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
                    f"An unexpected error happened with the GitHub API: Status code: {error.original.code}"
                )
            return
        logging.exception(error)
        await interaction.followup.send(f"Unexpected error:\n\n```py\n{error}\n```")

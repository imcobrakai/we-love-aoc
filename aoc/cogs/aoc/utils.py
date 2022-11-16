import ast
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TypedDict

import aiohttp
from dateutil.parser import isoparse
from discord import Color

from aoc.utils.objects import Singleton

from .config import ORGANIZATION, g, headers

HACKSQUAD_COLOR = Color.from_rgb(255, 0, 149)


class ResponseError(Exception):
    """Something went wrong with the response"""

    code: int

    def __init__(self, status_code: int) -> None:
        self.code = status_code

class AocContributor(TypedDict):
    github: str
    name: Optional[str]
    avatar_url: str
    total_pulls: Optional[int]
    bio: Optional[str]
    # merged_pulls: Optional[int]

class AocContributorMini(TypedDict):
    github: str

class RequesterCachedAttribute(TypedDict):
    cached_at: datetime
    data: Any
    allowed_time: Optional[timedelta]


class Requester(Singleton):
    _cache: Dict[str, RequesterCachedAttribute] = {}
    _cache_team: Dict[str, RequesterCachedAttribute] = {}

    async def get_user_status(self, user):
        print("-------------------------------------------------------------------------------")
        return g.search_issues(query=f"is:pull-request author:{user} org:{ORGANIZATION}").totalCount

    async def get_list(self):
        contributors = dict()
        org = await g.get_organization(ORGANIZATION)
        repos = await org.get_repos()
        for repo in repos:
            prs = await repo.get_pulls(state="closed")
            for pr in prs:
                if pr.is_merged():
                    user = pr.user.login
                    contributors[user] = contributors.get(user, 0) + 1

        contributors = sorted(contributors.items(), key = lambda x : x[0].lower())
        contributors = sorted(contributors, key= lambda x : x[1], reverse=True)
        res = ""
        for key, value in contributors:
            res += f"{key} - {value}\n"
        return contributors

    async def _make_request(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise ResponseError(response.status)
                return await response.json()

    def _allow_cache_use(self, entry_name: str) -> bool:
        if not self._cache.get(entry_name):
            return False

        cached_at = self._cache[entry_name]["cached_at"]

        if allowed_cache_time := self._cache[entry_name]["allowed_time"]:
            invalid_at = cached_at + allowed_cache_time
        else:
            invalid_at = cached_at + timedelta(minutes=30)

        # Cached data is invalid if it's been there since 30 minutes
        return invalid_at >= datetime.now()

    # async def fetch_leaderboard(self) -> List[PartialTeam]:
    #     if self._allow_cache_use("leaderboard"):
    #         return self._cache["leaderboard"]["data"]

    #     result = await self._make_request("https://www.hacksquad.dev/api/leaderboard")

    #     final_result = [
    #         PartialTeam(
    #             place=None,
    #             id=info["id"],
    #             name=info["name"],
    #             score=info["score"],
    #             slug=info["slug"],
    #         )
    #         for info in result["teams"]
    #     ]
    #     self._cache["leaderboard"] = {
    #         "cached_at": datetime.now(),
    #         "data": final_result,
    #         "allowed_time": None,
    #     }
    #     return final_result

   
    async def fetch_contributor(self, github: str) -> AocContributor:
        url = f"https://api.github.com/search/issues?q=is:pull-request +author:{github} +org:{ORGANIZATION}"
        prs = await self._make_request(url)
        count = prs['total_count']
        url = f'https://api.github.com/users/{github}'
        contrib = await self._make_request(url)
        if contrib is None:
            raise ResponseError(404)

        return AocContributor(
            github=contrib["login"],
            name=contrib.get("name"),
            avatar_url=contrib["avatar_url"],
            total_pulls=count,
            bio=contrib["bio"],
        )
    async def fetch_contributors_mini(self) -> List[AocContributorMini]:
        # I do not think that we would get much of a performance benefit from this but leaving it here all the same
        if self._allow_cache_use("contributors_mini"):
            return self._cache["contributors_mini"]["data"]

        url = f'https://api.github.com/orgs/{ORGANIZATION}/repos'
        result = await self._make_request(url)

        async def get_repo_contri(repo):
            url = f"https://api.github.com/repos/{ORGANIZATION}/{repo}/contributors"
            res = await self._make_request(url)
            lst = set()
            for val in res:
                lst.add(val['login'])
            return lst

        lst = set()
        for repo in result:
            temp = await get_repo_contri(repo['name'])
            lst = lst.union(temp)

        contributors = [
            AocContributorMini(
                github=contributor,
            )
            for contributor in lst
        ]

        self._cache["contributors_mini"] = {
            "cached_at": datetime.now(),
            "data": contributors,
            "allowed_time": timedelta(hours=12),
        }
        return contributors
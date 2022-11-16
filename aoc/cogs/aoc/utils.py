from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict

import aiohttp
from discord import Color

from aoc.utils.objects import Singleton

from .config import ORGANIZATION, headers

AOC_COLOR = Color.from_rgb(255, 0, 149)


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

class PartialContributor(TypedDict):
    name: str
    score: int
    place: int


class AocContributorMini(TypedDict):
    github: str


class RequesterCachedAttribute(TypedDict):
    cached_at: datetime
    data: Any
    allowed_time: Optional[timedelta]


class Requester(Singleton):
    _cache: Dict[str, RequesterCachedAttribute] = {}
    _cache_team: Dict[str, RequesterCachedAttribute] = {}

    
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

    async def fetch_leaderboard(self) -> List[PartialContributor]:
        if self._allow_cache_use("leaderboard"):
            return self._cache["leaderboard"]["data"]

        contributors = await self.fetch_contributors_mini()
        result = list()
        for contrib in contributors:
            github = contrib['github']
            url = f"https://api.github.com/search/issues?q=is:pull-request +author:{github} +org:{ORGANIZATION}"
            prs = await self._make_request(url)
            count = prs['total_count']
            if count > 0:
                result.append({"github": github, "score": count})
        final_result = [
            PartialContributor(
                place=None,
                name=info["github"],
                score=info["score"],
            )
            for info in result
        ]
        self._cache["leaderboard"] = {
            "cached_at": datetime.now(),
            "data": final_result,
            "allowed_time": None,
        }
        return final_result

   
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
from github import Github
import os
from dotenv import load_dotenv
load_dotenv()

ORGANIZATION = os.getenv('ORGANIZATION')

g = Github(os.getenv('ACCESS_TOKEN'))
headers = {"Accept": "application/vnd.github+json",
           "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"
           }

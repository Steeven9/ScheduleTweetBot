from os import getenv

from requests import get

from data import bot_name

api_url = getenv("API_URL")
if api_url == None:
    raise ValueError(f"[{bot_name}] API URL not found!")


# Get new tweets (more recent than newest_id)
def fetch_tweets(newest_id: str) -> list:
    response = get(f"{api_url}?newestId={newest_id}")
    data = response.json()

    new_tweets = len(data)
    if new_tweets != 0:
        newest_id = data[-1]["id"]
    return [data, new_tweets, newest_id]


# Get new spaces
def fetch_spaces() -> list:
    #TODO find a way to implement
    response = []
    new_spaces = 0
    return [response, new_spaces]

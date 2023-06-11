from requests import get

from data import api_url


# Get new tweets (more recent than newest_id)
def fetch_tweets(newest_id: str) -> list:
    response = get(f"{api_url}?newestId={newest_id}")
    data = response.json()
    new_tweets = len(data)
    if new_tweets != 0:
        newest_id = data[-1]["id"]
    return [data, new_tweets, newest_id]


# Matches spaces that:
# - are from the talents array
def fetch_spaces(talents: list) -> list:
    user_ids = [user.id for user in talents]
    #TODO fix
    response = [
    ]  #client.get_spaces(user_ids=user_ids, expansions=["creator_id"])
    new_spaces = 0  #response.meta["result_count"]
    return [response, new_spaces]

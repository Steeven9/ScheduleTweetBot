from os import getenv

from tweepy import Client

from data import guerrilla_keywords, schedule_keywords

# Twitter bearer token
bearer_token = getenv("TWITTER_BEARER_TOKEN")

if bearer_token == None:
    raise ValueError("Twitter bearer token not found!")
client = Client(bearer_token)


# Matches tweets that:
# - have a keyword from schedule_keywords in them and have an image attached
#   OR have a keyword from guerrilla_keywords in them
# - are not retweets
# - are from someone in the talents array
# - are more recent than newest_id
def fetch_tweets(newest_id: str, talents: list) -> list:
    user_names = [user.username for user in talents]
    query = "-is:retweet ((" + " OR ".join(
        guerrilla_keywords) + ") OR ((" + " OR ".join(
            schedule_keywords) + ") has:media)) (from:"
    query += " OR from:".join(user_names)
    query += ")"
    response = client.search_recent_tweets(query,
                                           since_id=newest_id,
                                           expansions=["author_id"])

    new_tweets = response.meta["result_count"]
    if new_tweets != 0:
        newest_id = response.meta["newest_id"]
    return [response, new_tweets, newest_id]


# Fetches tweets from a given List
def fetch_tweets_from_list(list_id: str) -> list:
    response = client.get_list_tweets(
        list_id,
        max_results=10,
        expansions=["author_id", "attachments.media_keys"])

    new_tweets = response.meta["result_count"]
    return [response, new_tweets]


# Matches spaces that:
# - are from the talents array
def fetch_spaces(talents: list) -> list:
    user_ids = []
    for user in talents:
        user_ids.append(user.id)
    response = client.get_spaces(user_ids=user_ids, expansions=["creator_id"])
    new_spaces = response.meta["result_count"]
    return [response, new_spaces]


# Gets data about a list of given username strings
def fetch_user_ids(talents: list[str]) -> list:
    usernames = ",".join(talents)
    response = client.get_users(usernames=usernames).data
    return [response, len(response)]


# Gets members of a List
def fetch_user_ids_from_list(list_id: str) -> list:
    response = client.get_list_members(id=list_id).data
    return [response, len(response)]

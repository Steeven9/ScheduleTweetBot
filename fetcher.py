from os import getenv

from tweepy import Client

from data import guerrilla_keywords, schedule_keywords

# Twitter bearer token
bearer_token = getenv("TWITTER_BEARER_TOKEN")
# Max Twitter query length
query_max_len = 512

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
    query = build_query(talents)

    if len(query) > query_max_len:
        [res1, new_tweets1,
         newest_id1] = fetch_tweets(newest_id, talents[:len(talents) // 2])
        [res2, new_tweets2,
         newest_id2] = fetch_tweets(newest_id, talents[len(talents) // 2:])

        response = {
            "data": (res1.data if res1.data else []) +
            (res2.data if res2.data else []),
            "includes": {
                "users": (res1.includes["users"] if res1.includes else []) +
                (res2.includes["users"] if res2.includes else [])
            }
        }
        newest_id = newest_id1 if newest_id1 > newest_id2 else newest_id2
        return [response, new_tweets1 + new_tweets2, newest_id]
    else:
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
    user_ids = [user.id for user in talents]
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


# Builds the query string for tweets given a talents array
def build_query(talents: list) -> str:
    query = "-is:retweet (("
    query += " OR ".join(guerrilla_keywords)
    query += ") OR (("
    query += " OR ".join(schedule_keywords)
    query += ") has:media)) (from:"
    query += " OR from:".join(talents)
    query += ")"

    return query

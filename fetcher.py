from os import getenv

from tweepy import Client

# Separator between tweets
separator = "---------------------------------"
# Twitter bearer token
bearer_token = getenv("TWITTER_BEARER_TOKEN")

if bearer_token == None:
    raise ValueError("Twitter bearer token not found!")
client = Client(bearer_token, wait_on_rate_limit=True)

# Matches tweets that
# - have the keyword "schedule" in it
# - are not retweets
# - have an image attached
# - are from the talents below

# Myth
talents = [
    "gawrgura", "moricalliope", "ninomaeinanis", "takanashikiara",
    "watsonameliaEN"
]
# Hope
talents += ["irys_en"]
# Council
talents += [
    "ceresfauna",
    "hakosbaelz",
    "nanashimumei_en",
    "ourokronii",
    "tsukumosana",
]
# ID gen 1
talents += [
    "ayunda_risu",
    "airaniiofifteen",
    "moonahoshinova",
]
# ID gen 2
talents += [
    "anyamelfissa",
    "kureijiollie",
    "pavoliareine",
]
# ID gen 3
talents += [
    "kaelakovalskia",
    "kobokanaeru",
    "vestiazeta",
]

query = "-is:retweet ((guerrilla OR guerilla) OR ((schedule OR weekly) has:media)) (from:"
query += " OR from:".join(talents)
query += ")"


def fetch_tweets(newest_id):
    response = client.search_recent_tweets(query,
                                           since_id=newest_id,
                                           max_results=len(talents),
                                           expansions=["author_id"])

    new_tweets = response.meta["result_count"]
    if new_tweets != 0:
        newest_id = response.meta["newest_id"]
    return [response, new_tweets, newest_id]


if __name__ == "__main__":
    [response, tweets_fetched, newest_id] = fetch_tweets(None)
    tweets = response.data
    users = {user["id"]: user for user in response.includes["users"]}
    print(tweets_fetched, "found\n")
    for tweet in tweets:
        print("Tweet from {0} - https://twitter.com/twitter/statuses/{1}\n{2}".
              format(users[tweet.author_id].username, tweet.id, separator))

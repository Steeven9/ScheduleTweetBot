import os
from tweepy import Client

bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
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

query = "schedule -is:retweet has:media ("
for talent in talents:
    if talent == talents[0]:
        query += "from:" + talent
    else:
        query += " OR from:" + talent
query += ")"


def fetch_tweets(newest_id):
    tweets = client.search_recent_tweets(query,
                                         since_id=newest_id,
                                         max_results=len(talents))

    new_tweets = tweets.meta["result_count"]
    if new_tweets != 0:
        newest_id = tweets.meta["newest_id"]
    return [tweets.data, new_tweets, newest_id]


if __name__ == "__main__":
    [tweets, tweets_fetched, newest_id] = fetch_tweets(None)
    print(tweets_fetched, "found\n")
    for tweet in tweets:
        print(tweet, "\n---------------------------------\n")

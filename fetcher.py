import tweepy as tw
import os

bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
client = tw.Client(bearer_token, wait_on_rate_limit=True)

query = "schedule from:gawrgura -is:retweet OR schedule from:ninomaeinanis -is:retweet"


def fetch_tweets(newest_id):
    tweets = client.search_recent_tweets(query,
                                         since_id=newest_id,
                                         max_results=11)

    new_tweets = tweets.meta["result_count"]
    if new_tweets != 0:
        newest_id = tweets.meta["newest_id"]
    return [tweets.data, new_tweets, newest_id]

if __name__ == "__main__":
    print(fetch_tweets(None))

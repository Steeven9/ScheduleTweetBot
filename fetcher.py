import tweepy as tw
import os

bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
client = tw.Client(bearer_token, wait_on_rate_limit=True)
newest_id = None
new_tweets = 0

query = "schedule from:gawrgura -is:retweet OR schedule from:ninomaeinanis -is:retweet"


def fetch_tweets():
    global newest_id, new_tweets
    tweets = client.search_recent_tweets(query,
                                         since_id=newest_id,
                                         max_results=11)

    if tweets.data is None:
        new_tweets = 0
        print("Nothing new found")
        print("---------------------------------\n")
    else:
        newest_id = tweets.meta["newest_id"]
        new_tweets = tweets.meta["result_count"]
        print("Found " + str(new_tweets) + " new tweets")
        print("---------------------------------")

        for tweet in tweets.data:
            print(tweet)
            print("---------------------------------")
        print("\n")


if __name__ == "__main__":
    fetch_tweets()

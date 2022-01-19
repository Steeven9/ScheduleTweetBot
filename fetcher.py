import tweepy as tw
import os

bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
client = tw.Client(bearer_token, wait_on_rate_limit=True)

# Mathces tweets that
# - have the keyword "schedule" in it
# - are not retweets
# - have an image attached
# - are from one of the 11 EN talents
query = "schedule -is:retweet has:media (from:gawrgura OR from:ninomaeinanis \
    OR from:watsonameliaEN OR from:takanashikiara OR from:moricalliope \
    OR from:irys_en OR from:ourokronii OR from:hakosbaelz OR from:ceresfauna \
    OR from:tsukumosana OR from:nanashimumei_en)"


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

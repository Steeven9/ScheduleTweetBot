from os import getenv

from tweepy import Client

from data import guerrilla_keywords, schedule_keywords, talents

# Separator between tweets
separator = "---------------------------------"
# Twitter bearer token
bearer_token = getenv("TWITTER_BEARER_TOKEN")

if bearer_token == None:
    raise ValueError("Twitter bearer token not found!")
client = Client(bearer_token, wait_on_rate_limit=True)

# Matches tweets that:
# - have a keyword from schedule_keywords in them and have an image attached
#   OR have a keyword from guerrilla_keywords in them
# - are not retweets
# - are from someone in the talents array

query = "-is:retweet ((" + " OR ".join(
    guerrilla_keywords) + ") OR ((" + " OR ".join(
        schedule_keywords) + ") has:media)) (from:"
query += " OR from:".join(talents)
query += ")"

# Matches spaces that:
# - are from the talents array

spaces_query = "from:" + " OR from:".join(talents)


def fetch_tweets(newest_id):
    response = client.search_recent_tweets(query,
                                           since_id=newest_id,
                                           max_results=len(talents),
                                           expansions=["author_id"])

    new_tweets = response.meta["result_count"]
    if new_tweets != 0:
        newest_id = response.meta["newest_id"]
    return [response, new_tweets, newest_id]


def fetch_spaces():
    response_spaces = client.search_spaces(spaces_query,
                                           max_results=len(talents),
                                           expansions=["creator_id"])
    new_tweets = response_spaces.meta["result_count"]
    return [response_spaces, new_tweets]


if __name__ == "__main__":
    [response, tweets_fetched, newest_id] = fetch_tweets(None)
    tweets = response.data
    users = {user["id"]: user for user in response.includes["users"]}
    print(tweets_fetched, "found\n")
    for tweet in tweets:
        print("Tweet from {0} - https://twitter.com/twitter/statuses/{1}\n{2}".
              format(users[tweet.author_id].username, tweet.id, separator))

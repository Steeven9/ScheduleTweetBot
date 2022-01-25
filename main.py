import os
from discord import Activity, ActivityType, errors
from datetime import datetime
from discord.ext import tasks, commands
from discord_slash import SlashCommand
from fetcher import fetch_tweets

# Prefix is ignored
client = commands.Bot(".holotweetbot")
slash = SlashCommand(client, sync_commands=True)
newest_id = None

# -- Options --
# Interval between each tweet (in seconds)
timeout = 60
# ID of the channel where to send the notification
channel_id = os.getenv("HOLOTWEETBOT_CHANNEL")


async def get_tweets(channel):
    global newest_id
    [response, tweets_fetched, newest_id] = fetch_tweets(newest_id)
    if tweets_fetched == 0:
        return tweets_fetched
    else:
        result = ""
        ct = datetime.now()
        tweets = response.data
        users = {user["id"]: user for user in response.includes["users"]}
        for tweet in tweets:
            result += "Tweet from {0} - https://twitter.com/twitter/statuses/{1}\n".format(
                users[tweet.author_id].username, tweet.id)
            result += "{0}\n---------------------------------\n".format(
                tweet.text[:-24])
        try:
            print(ct, "-", tweets_fetched, "found")
            await channel.send(result)
        except errors.HTTPException:
            print(ct, "-", tweets_fetched, "skipped due to length")
            await channel.send(
                "Too much characters, skipping {0} tweets".format(
                    tweets_fetched))


@client.event
async def on_ready():
    await client.change_presence(
        activity=Activity(type=ActivityType.watching, name="tweets for you"))
    print("Logged in as {0}".format(client.user))
    check_tweets.start()


@slash.slash(
    name="holotweets",
    description="Get new tweets",
)
async def holotweets(ctx):
    global newest_id
    tweets_fetched = await get_tweets(ctx)
    ct = datetime.now()
    print(ct, "-", tweets_fetched, "found (via command)")
    if tweets_fetched == 0:
        await ctx.send("Nothing new found")


@tasks.loop(seconds=timeout)
async def check_tweets():
    global channel_id
    channel = client.get_channel(int(channel_id))
    await get_tweets(channel)


client.run(os.getenv("HOLOTWEETBOT_TOKEN"))

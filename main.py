import os
import discord
from discord_slash import SlashCommand
from fetcher import fetch_tweets

client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
newest_id = None


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="tweets for you"))
    print("Logged in as {0.user}".format(client))


@slash.slash(
    name="holotweets",
    description="Get new tweets",
)
async def holotweets(ctx):
    global newest_id
    [tweets, tweets_fetched, newest_id] = fetch_tweets(newest_id)
    if tweets_fetched == 0:
        await ctx.send(f"Nothing new found")
    else:
        result = str(tweets_fetched) + " new tweets found\n"
        for tweet in tweets:
            result += (str(tweet) + "---------------------------------\n")
        await ctx.send(result)


client.run(os.getenv("HOLOTWEETBOT_TOKEN"))

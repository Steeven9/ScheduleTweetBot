import os
import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from fetcher import fetch_tweets

client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)


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
    await ctx.send(f"{fetch_tweets()}")


client.run(os.getenv("HOLOTWEETBOT_TOKEN"))

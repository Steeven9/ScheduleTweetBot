import os
from discord import Activity, ActivityType, errors, utils
from datetime import datetime
from discord.ext import tasks, commands
from discord_slash import SlashCommand
from fetcher import fetch_tweets

# -- Options --
# Interval between each fetch (in seconds)
timeout = 60
# ID of the channel where to send the notification
channel_id = os.getenv("HOLOTWEETBOT_CHANNEL")
# Filename to store latest tweet ID
filename = "config/holotweetbot.ini"
# Separator between tweets
separator = "---------------------------------"
# Bot prefix (ignored, we use slash commands)
prefix = ".holotweetbot"
# Set this to True to register slash commands on boot
sync_commands = True
# Discord bot token
discord_token = os.getenv("HOLOTWEETBOT_TOKEN")
# -- End of options --

# Try to read latest ID from file
try:
    f = open(filename, "r")
    newest_id = f.read().strip()
    print("Loaded config from file")
except FileNotFoundError:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    newest_id = None
# Initialize stuff
client = commands.Bot(prefix)
slash = SlashCommand(client, sync_commands)
if channel_id == None:
    raise ValueError("Channel ID not found!")
if discord_token == None:
    raise ValueError("Discord bot token not found!")


async def get_and_send_tweets(channel):
    global newest_id
    [response, tweets_fetched, newest_id] = fetch_tweets(newest_id)
    if tweets_fetched == 0:
        return tweets_fetched
    else:
        # Log event
        ct = datetime.now()
        print(ct, "-", tweets_fetched, "found")

        # Save latest ID to file
        f = open(filename, "w")
        f.write(newest_id)
        f.close()

        # Construct message
        if channel_id == "882283424457568257":
            # Specific ping for KFP | The Office
            schedule_ping = utils.get(channel.guild.roles,
                                      id=801317291072946177)
            result = f"{schedule_ping.mention} "
        else:
            result = ""
        tweets = response.data
        users = {user["id"]: user for user in response.includes["users"]}
        i = 1
        for tweet in tweets:
            result += "Tweet from {0} - https://twitter.com/twitter/statuses/{1}\n".format(
                users[tweet.author_id].username, tweet.id)
            if i < tweets_fetched:
                result += separator + "\n"
            i += 1

        # Send Discord message
        try:
            await channel.send(result)
        except errors.HTTPException:
            print(ct, "-", tweets_fetched, "skipped due to length")
            await channel.send(
                "Too many characters to send in one message, skipping {0} tweets"
                .format(tweets_fetched))


@client.event
async def on_ready():
    await client.change_presence(
        activity=Activity(type=ActivityType.watching, name="tweets for you"))
    print("Logged in as {0}".format(client.user))
    # Start cron
    check_tweets.start()


# Slash command to get tweets manually
@slash.slash(
    name="holotweets",
    description="Get new tweets",
)
async def holotweets(ctx):
    global newest_id
    tweets_fetched = await get_and_send_tweets(ctx)
    ct = datetime.now()
    print(ct, "-", tweets_fetched, "found (via command)")
    if tweets_fetched == 0:
        await ctx.send("Nothing new found")


# Main loop that gets the tweets
@tasks.loop(seconds=timeout)
async def check_tweets():
    global channel_id
    channel = client.get_channel(int(channel_id))
    await get_and_send_tweets(channel)


client.run(discord_token)

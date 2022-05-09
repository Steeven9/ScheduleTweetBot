from datetime import datetime
from os import getenv, makedirs, path

from discord import Activity, ActivityType, errors, utils
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from tweepy.errors import BadRequest, TwitterServerError

from fetcher import fetch_spaces, fetch_tweets

# -- Options --
# Interval between each fetch (in seconds)
timeout = 60
# ID of the channel where to send the notification
channel_id = getenv("HOLOTWEETBOT_CHANNEL")
# Filename to store latest tweet ID
filename = "config/holotweetbot.ini"
# Separator between tweets
separator = "---------------------------------"
# Bot prefix (ignored, we use slash commands)
prefix = ".holotweetbot"
# Set this to True to register slash commands on boot
sync_commands = True
# Discord bot token
discord_token = getenv("HOLOTWEETBOT_TOKEN")
# Debug channel to send errors to (private)
debug_channel_id = 935532391550820372
# -- End of options --

# Try to read latest ID from file
try:
    f = open(filename, "r")
    newest_id = f.read().strip()
    print("Loaded config from file")
except FileNotFoundError:
    makedirs(path.dirname(filename), exist_ok=True)
    newest_id = None
# Initialize stuff
client = commands.Bot(prefix)
slash = SlashCommand(client, sync_commands)
if channel_id == None:
    raise ValueError("Channel ID not found!")
if discord_token == None:
    raise ValueError("Discord bot token not found!")


async def get_and_send_tweets(channel, debug_channel):
    global newest_id
    ct = datetime.now()
    try:
        [tweets, tweets_fetched, newest_id] = fetch_tweets(newest_id)
        [spaces, spaces_fetched] = fetch_spaces()
    except TwitterServerError as err:
        err_string = "Twitter died: {0}".format(err)
        print(ct, err_string)
        await debug_channel.send(err_string)
        return
    except BadRequest as err:
        err_string = "API error: {0}".format(err)
        print(ct, err_string)
        await debug_channel.send(err_string)
        return

    if tweets_fetched != 0:
        await send_message(tweets, channel, tweets_fetched)
    if spaces_fetched != 0:
        # TODO examine the data and see what it returns
        print(spaces)
        await send_message(spaces, debug_channel, spaces_fetched)

    # Save latest ID to file
    f = open(filename, "w")
    f.write(newest_id)
    f.close()

    return tweets_fetched + spaces_fetched


async def send_message(data, channel, tweets_fetched):
    ct = datetime.now()
    # Construct message
    if channel_id == "882283424457568257":
        # Specific ping for KFP | The Office
        schedule_ping = utils.get(channel.guild.roles, id=801317291072946177)
        result = f"{schedule_ping.mention} "
    else:
        result = ""
    tweets = data.data
    users = {user["id"]: user for user in data.includes["users"]}
    i = 1
    users_string = ""
    for tweet in tweets:
        if "RT @" in tweet.text[:4]:
            result += "[{0}] ".format(get_rt_text(tweet))

        if "schedule" in tweet.text.lower() or "weekly" in tweet.text.lower():
            result += "Schedule tweet"
        elif "guerilla" in tweet.text.lower(
        ) or "guerrilla" in tweet.text.lower():
            result += "Guerilla tweet"
        else:
            result += "Tweet"

        result += " from {0} - https://twitter.com/{0}/status/{1}\n".format(
            users[tweet.author_id].username, tweet.id)
        users_string += users[tweet.author_id].username
        if i < tweets_fetched:
            result += separator + "\n"
            users_string += ", "
        i += 1

    # Log event
    print(ct, "-", tweets_fetched, "found from", users_string)

    # Send Discord message
    try:
        await channel.send(result)
    except errors.HTTPException:
        print(ct, "-", tweets_fetched, "from", users_string,
              "skipped due to length")
        await channel.send(
            "Too many characters to send in one message, skipping {0} tweets from {1}"
            .format(tweets_fetched, users_string))


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
    global debug_channel_id
    debug_channel = client.get_channel(int(debug_channel_id))
    tweets_fetched = await get_and_send_tweets(ctx, debug_channel)
    if tweets_fetched == 0:
        await ctx.send("Nothing new found")


# Main loop that gets the tweets
@tasks.loop(seconds=timeout)
async def check_tweets():
    global channel_id, debug_channel_id
    channel = client.get_channel(int(channel_id))
    debug_channel = client.get_channel(int(debug_channel_id))
    await get_and_send_tweets(channel, debug_channel)


# Helper to get the "RT @username" string
def get_rt_text(tweet):
    result = ""
    pos = 1
    while str(tweet)[:pos][pos - 1] != ":":
        result += str(tweet)[:pos][pos - 1]
        pos += 1
    return result


client.run(discord_token)

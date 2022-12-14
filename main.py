from datetime import datetime
from os import getenv, makedirs, path

from discord import Activity, ActivityType, errors, utils
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from requests import get
from tweepy.errors import BadRequest, TooManyRequests, TwitterServerError

from data import (bot_name, channel_id, enable_retweets, guerrilla_keywords,
                  list_id, role_id, schedule_keywords)
from fetcher import (fetch_spaces, fetch_tweets_from_list,
                     fetch_user_ids_from_list)

# -- Options --
# Interval between each fetch (in seconds)
timeout = 60
# Filenames to store already fetched tweets and spaces
tweets_file = f"config/{bot_name}_tweets.ini"
spaces_file = f"config/{bot_name}_spaces.ini"
# Set this to True to register slash commands on boot
sync_commands = True
# Discord bot token
discord_token = getenv(f"{bot_name.upper()}BOT_TOKEN")
# Debug channel to send errors to (private)
debug_channel_id = 935532391550820372
# Heartbeat URL
heartbeat_url = getenv(f"{bot_name.upper()}BOT_HEARTBEAT_URL")
# -- End of options --

# Try to read existing tweets and spaces from files
try:
    f = open(tweets_file, "a+")
except FileNotFoundError:
    makedirs(path.dirname(tweets_file), exist_ok=True)
    f = open(tweets_file, "a+")
f.seek(0)
existing_tweets = f.read()[:-1].split("\n")

try:
    f2 = open(spaces_file, "a+")
except FileNotFoundError:
    makedirs(path.dirname(spaces_file), exist_ok=True)
    f2 = open(spaces_file, "a+")
f2.seek(0)
existing_spaces = f2.read()[:-1].split("\n")

# Initialize stuff
client = commands.Bot(".sch")
slash = SlashCommand(client, sync_commands)
if channel_id == None:
    raise ValueError(f"[{bot_name}] Channel ID not found!")
if discord_token == None:
    raise ValueError(f"[{bot_name}] Discord bot token not found!")
talents_data = []


async def get_and_send_tweets(channel, debug_channel):
    try:
        [tweets, tweets_fetched] = fetch_tweets_from_list(list_id)
        [spaces, spaces_fetched] = fetch_spaces(talents_data)
    except TwitterServerError as err:
        err_string = f"Twitter died: {err}"
        log(err_string)
        return
    except TooManyRequests as err:
        err_string = "Too many requests: {err}"
        log(err_string)
        await debug_channel.send(err_string)
        return
    except BadRequest as err:
        err_string = "API error: {err}"
        log(err_string)
        await debug_channel.send(err_string)
        return

    if tweets_fetched != 0:
        await send_tweets_message(tweets, channel, tweets_fetched)

    if spaces_fetched != 0:
        await send_spaces_message(spaces, channel, spaces_fetched)

    return tweets_fetched + spaces_fetched


async def send_spaces_message(spaces, channel, spaces_fetched):
    global existing_spaces
    schedule_ping = utils.get(channel.guild.roles, id=role_id)
    result = f"{schedule_ping.mention} "
    i = 0

    for space in spaces.data:
        if str(space.id) not in existing_spaces:
            user = spaces.includes["users"][i].username
            result += f":bird: {user} has a {space.state} space! https://twitter.com/i/spaces/{space.id}\n"
            # Save current space ID to file
            f2.write(str(space.id) + "\n")
            existing_spaces.append(str(space.id))
            i += 1
    if (i > 0):
        try:
            await channel.send(result)
        except errors.HTTPException:
            log(f"{spaces_fetched} spaces skipped due to length")
            await channel.send(
                f"Too many characters to send in one message, skipping {spaces_fetched} spaces"
            )


async def send_tweets_message(data, channel, tweets_fetched):
    schedule_ping = utils.get(channel.guild.roles, id=role_id)
    result = f"{schedule_ping.mention} " if schedule_ping else " "
    tweets = data.data
    users = {user["id"]: user for user in data.includes["users"]}
    i = 0
    users_string = ""
    tweet_type = "Tweet"
    ids = []

    for tweet in tweets:
        if str(tweet.id) not in existing_tweets:
            found = False

            for w in schedule_keywords:
                if w in tweet.text.lower(
                ) and "https://t.co/" in tweet.text.lower():
                    tweet_type = ":calendar: Schedule tweet"
                    found = True
                    break
            for w in guerrilla_keywords:
                if w in tweet.text.lower():
                    tweet_type = ":gorilla: Guerilla tweet"
                    found = True
                    break

            if found:
                if "RT @" in tweet.text[:4]:
                    if not enable_retweets:
                        continue
                    result += f"[{get_rt_text(tweet)}] "
                user = users[tweet.author_id].username
                result += f"{tweet_type} from {1} - https://twitter.com/{user}/status/{tweet.id}\n\n"
                users_string += users[tweet.author_id].username + ", "
                i += 1

            ids.append(tweet.id)

    # Save new IDs to file
    for id in ids:
        f.write(str(id) + "\n")
        existing_tweets.append(str(id))

    # Send Discord message
    if (i > 0):
        # Log event
        log(f"{i} found from {users_string[:-2]}")
        try:
            await channel.send(result)
        except errors.HTTPException:
            log(f"{tweets_fetched} skipped due to length from {users_string}")
            await channel.send(
                f"Too many characters to send in one message, skipping {i} tweets from {users_string}"
            )


# -- Event handling --


@client.event
async def on_ready():
    global talents_data
    talents_data, talents_amount = fetch_user_ids_from_list(list_id)
    log(f"Loaded {talents_amount} talents")

    await client.change_presence(
        activity=Activity(type=ActivityType.watching, name="tweets for you"))
    log(f"Logged in as {client.user}")
    # Start cron
    if not check_tweets.is_running():
        check_tweets.start()


# Slash command to get tweets manually
@slash.slash(
    name="getTweets",
    description=f"Get new tweets for {bot_name.upper()}",
)
async def holotweets(ctx):
    log(f"Command called from server {ctx.guild_id} by {ctx.author}")
    debug_channel = client.get_channel(int(debug_channel_id))
    tweets_fetched = await get_and_send_tweets(ctx, debug_channel)
    if tweets_fetched == 0:
        await ctx.send("Nothing new found")


# Main loop that gets the tweets
@tasks.loop(seconds=timeout)
async def check_tweets():
    # Send heartbeat
    if (heartbeat_url is not None):
        get(heartbeat_url)
    channel = client.get_channel(int(channel_id))
    debug_channel = client.get_channel(int(debug_channel_id))
    await get_and_send_tweets(channel, debug_channel)


# -- Helper functions --


# Helper to get the "RT @username" string
def get_rt_text(tweet):
    result = ""
    pos = 1
    while str(tweet)[:pos][pos - 1] != ":":
        result += str(tweet)[:pos][pos - 1]
        pos += 1
    return result


# Helper to log messages in stdout
def log(msg):
    print(f"{str(datetime.now())[:-7]} [{bot_name}] {msg}")


client.run(discord_token)

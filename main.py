from datetime import datetime
from os import getenv, makedirs, path

from discord import Activity, ActivityType, errors, utils
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext
from requests import get

from data import (bot_name, channel_id, enable_retweets, guerrilla_keywords,
                  list_id, role_id, schedule_keywords, talents)
from fetcher import fetch_spaces, fetch_tweets, fetch_user_ids_from_list

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

# -- Try to read existing tweets and spaces from files --
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

# -- Initialize stuff --
if channel_id == None:
    raise ValueError(f"[{bot_name}] Channel ID not found!")
if discord_token == None:
    raise ValueError(f"[{bot_name}] Discord bot token not found!")
client = commands.Bot(".sch")
slash = SlashCommand(client, sync_commands)
channel = None
schedule_ping = None
debug_channel = None
talents_data = []
newest_id = ""  #TODO read from file


# TODO save spaces in file (low prio since they are not so common)
async def send_spaces_message(data, channel, spaces_fetched: int) -> None:
    global existing_spaces
    result = f"{schedule_ping.mention} " if schedule_ping else " "
    i = 0

    for space in data.data:
        if str(space.id) not in existing_spaces:
            user = data.includes["users"][i].username
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


async def send_tweets_message(data, channel, tweets_fetched: int) -> None:
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
                result += f"{tweet_type} from {user} - https://twitter.com/{user}/status/{tweet.id}\n\n"
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
async def on_ready() -> None:
    global talents_data, channel, schedule_ping, debug_channel
    talents_data, talents_amount = fetch_user_ids_from_list(list_id)
    # TODO get rid of the List dependency
    if len(talents) != talents_amount:
        raise RuntimeError(
            f"Found {len(talents)} talents but {talents_amount} in List")
    log(f"Loaded {talents_amount} talents")

    await client.change_presence(
        activity=Activity(type=ActivityType.watching, name="tweets for you"))
    log(f"Logged in as {client.user}")
    channel = client.get_channel(int(channel_id))
    schedule_ping = utils.get(channel.guild.roles, id=role_id)
    debug_channel = client.get_channel(int(debug_channel_id))
    # Start cron
    if not check_tweets.is_running():
        check_tweets.start()


# Main loop that gets the tweets
@tasks.loop(seconds=timeout)
async def check_tweets() -> None:
    global newest_id
    # Send heartbeat
    if (heartbeat_url is not None):
        get(heartbeat_url)

    try:
        # [tweets, tweets_fetched] = fetch_tweets_from_list(list_id)
        [tweets, tweets_fetched, newest_id] = fetch_tweets(newest_id, talents)
        [spaces, spaces_fetched] = fetch_spaces(talents_data)
    except Exception as err:
        err_string = f"Error: {err}"
        log(err_string)
        await debug_channel.send(err_string)
        return

    if tweets_fetched != 0:
        await send_tweets_message(data=tweets,
                                  channel=channel,
                                  tweets_fetched=tweets_fetched)

    if spaces_fetched != 0:
        await send_spaces_message(data=spaces,
                                  channel=channel,
                                  spaces_fetched=spaces_fetched)


# -- Slash commands --


@slash.slash(name="ping", description="Show server latency")
async def ping(ctx: SlashContext) -> None:
    log(f"Command ping called from server {ctx.guild_id} by {ctx.author}")
    await ctx.send(f"Pong! ({round(client.latency*1000, 2)}ms)")


# -- Helper functions --


# Helper to get the "RT @username" string
def get_rt_text(tweet: str) -> str:
    result = ""
    pos = 1
    while str(tweet)[:pos][pos - 1] != ":":
        result += str(tweet)[:pos][pos - 1]
        pos += 1
    return result


# Helper to log messages in stdout
def log(msg: str) -> None:
    print(f"{str(datetime.now())[:-7]} [{bot_name}] {msg}")


client.run(discord_token)

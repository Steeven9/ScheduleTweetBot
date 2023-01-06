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
    f.seek(0)
    newest_id = f.read().split("\n")[0].strip()
except FileNotFoundError:
    makedirs(path.dirname(tweets_file), exist_ok=True)
    f = open(tweets_file, "a+")
    newest_id = None

try:
    f2 = open(spaces_file, "a+")
    f2.seek(0)
    existing_spaces = f2.read()[:-1].split("\n")
except FileNotFoundError:
    makedirs(path.dirname(spaces_file), exist_ok=True)
    f2 = open(spaces_file, "a+")
    existing_spaces = []

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


async def check_tweets() -> list:
    global newest_id
    try:
        [tweets, tweets_fetched, newest_id] = fetch_tweets(newest_id, talents)
        [spaces, spaces_fetched] = fetch_spaces(talents_data)
    except Exception as err:
        err_string = f"Error: {err}"
        log(err_string)
        await debug_channel.send(err_string)
        return [0, 0]

    if tweets_fetched != 0:
        await send_tweets_message(data=tweets,
                                  channel=channel,
                                  tweets_fetched=tweets_fetched)

    if spaces_fetched != 0:
        await send_spaces_message(data=spaces,
                                  channel=channel,
                                  spaces_fetched=spaces_fetched)

    return [tweets_fetched, spaces_fetched]


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

    for tweet in tweets:
        found = False

        for w in schedule_keywords:
            if w in tweet.text.lower():
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

    # Save new ID to file
    f.write(str(newest_id) + "\n")

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
    if not check_tweets_loop.is_running():
        check_tweets_loop.start()


# Main loop that gets the tweets
@tasks.loop(seconds=timeout)
async def check_tweets_loop() -> list:
    # Send heartbeat
    if (heartbeat_url is not None):
        get(heartbeat_url)
    await check_tweets()


# -- Slash commands --


@slash.slash(name="ping", description="Show server latency")
async def ping(ctx: SlashContext) -> None:
    log(f"Command `ping` called from server {ctx.guild_id} by {ctx.author}")
    await ctx.send(f"Pong! ({round(client.latency*1000, 2)}ms)")


@slash.slash(name="fetch", description="Manually fetch data")
async def fetch(ctx: SlashContext) -> None:
    log(f"Command `fetch` called from server {ctx.guild_id} by {ctx.author}")
    [tweets_fetched, spaces_fetched] = await check_tweets()
    await ctx.send(f"Found {tweets_fetched} tweets and {spaces_fetched} spaces"
                   )


@slash.slash(name="list", description="List watched talents")
async def list(ctx: SlashContext) -> None:
    log(f"Command `list` called from server {ctx.guild_id} by {ctx.author}")
    await ctx.send(f"Watching {len(talents)} talents: {', '.join(talents)}")


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

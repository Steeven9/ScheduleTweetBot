from datetime import datetime
from os import getenv, makedirs, path
from traceback import print_exc

from discord import Activity, ActivityType, errors, utils
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext
from requests import get

from data import bot_name, channel_id, enable_retweets, extra_pings, role_id
from fetcher import fetch_spaces, fetch_tweets

# -- Options --
# Interval between each fetch (in seconds)
timeout = 60
# Filenames to store already fetched tweets and spaces
tweets_file_path = f"config/{bot_name}_tweets.ini"
spaces_file_path = f"config/{bot_name}_spaces.ini"
# Set this to True to register slash commands on boot
sync_commands = True
# Discord bot token
discord_token = getenv("BOT_TOKEN")
# Debug channel to send errors to (private)
debug_channel_id = 935532391550820372
# Heartbeat URL
heartbeat_url = getenv("HEARTBEAT_URL")
# blooop API URL (where to get the tweets from)
api_url = getenv("API_URL")

# -- Try to read existing tweets and spaces from files --
try:
    tweets_file = open(tweets_file_path, "r")
    newest_id = tweets_file.read().strip()
    tweets_file.close()
except FileNotFoundError:
    makedirs(path.dirname(tweets_file_path), exist_ok=True)
    newest_id = 0

try:
    spaces_file = open(spaces_file_path, "a+")
    spaces_file.seek(0)
    existing_spaces = spaces_file.read()[:-1].split("\n")
except FileNotFoundError:
    makedirs(path.dirname(spaces_file_path), exist_ok=True)
    spaces_file = open(spaces_file_path, "a+")
    existing_spaces = []

# -- Initialize stuff --
if channel_id == None:
    raise ValueError(f"[{bot_name}] Channel ID not found!")
if discord_token == None:
    raise ValueError(f"[{bot_name}] Discord bot token not found!")
if api_url == None:
    raise ValueError(f"[{bot_name}] API URL not found!")
client = commands.Bot(".sch")
slash = SlashCommand(client, sync_commands)
channel = None
schedule_ping = None
debug_channel = None


async def check_tweets() -> list:
    global newest_id
    try:
        [tweets, tweets_fetched, newest_id] = fetch_tweets(newest_id)
        [spaces, spaces_fetched] = fetch_spaces()
    except Exception as err:
        print_exc()
        err_string = f"Error: {err}"
        log(err_string)
        await debug_channel.send(err_string)
        return [0, 0]

    if tweets_fetched != 0:
        await send_tweets_message(data=tweets, channel=channel)

    if spaces_fetched != 0:
        await send_spaces_message(data=spaces, channel=channel)

    return [tweets_fetched, spaces_fetched]


async def send_spaces_message(data, channel) -> None:
    global existing_spaces
    result = f"{schedule_ping.mention} " if schedule_ping else " "
    new_spaces = 0

    for space in data.data:
        if str(space.id) not in existing_spaces:
            user = data.includes["users"][new_spaces].username
            result += f":bird: {user} has a {space.state} space! https://twitter.com/i/spaces/{space.id}\n"
            # Save current space ID to file
            spaces_file.write(str(space.id) + "\n")
            existing_spaces.append(str(space.id))
            new_spaces += 1
    if (new_spaces > 0):
        try:
            await channel.send(result)
        except errors.HTTPException:
            print_exc()
            log(f"{new_spaces} spaces skipped due to length")
            await channel.send(
                f"Too many characters to send in one message, skipping {new_spaces} spaces"
            )


async def send_tweets_message(data, channel) -> None:
    ping = f"{schedule_ping.mention} " if schedule_ping else ""
    result = ""
    new_tweets = 0
    users_string = ""

    for tweet in data:
        if "RT @" in tweet["content"][:4]:
            if not enable_retweets:
                continue
            ping += f"[{get_rt_text(tweet)}] "
        user = tweet["talent"]
        if tweet["keyword"] == "schedule":
            tweet_type = ":calendar: Schedule tweet"
        elif tweet["keyword"] == "guerilla":
            tweet_type = ":gorilla: Guerilla tweet"
        else:
            tweet_type = "Tweet"
        tweet_string = f"{tweet_type} from {user} - https://vxtwitter.com/{user}/status/{tweet['id']}\n\n"
        result += tweet_string
        users_string += user + ", "
        new_tweets += 1

        # TEMPORARILY DISABLED 28.10.2023

        # for extra_ping in extra_pings:
        #     if user == extra_ping["talent"].lower():
        #         log(f"Sending extra ping for {user}")
        #         ch = client.get_channel(
        #             extra_ping["channel"]
        #         ) if extra_ping["role"] else await client.fetch_user(
        #             extra_ping["channel"])
        #         sch_ping = utils.get(ch.guild.roles, id=extra_ping["role"]
        #                              ).mention if extra_ping["role"] else ""
        #         try:
        #             await ch.send(sch_ping + tweet_string)
        #         except Exception as err:
        #             print_exc()
        #             err_string = f"Error: {err} sending ping to {extra_ping['channel']} for {user}"
        #             log(err_string)
        #             await debug_channel.send(err_string)

    # Save new ID to file
    tweets_file = open(tweets_file_path, "w")
    tweets_file.write(newest_id)
    tweets_file.close()

    # Send Discord message
    if (new_tweets > 0):
        # Log event
        log(f"{new_tweets} found from {users_string[:-2]}")
        try:
            await channel.send(ping + result)
        except errors.HTTPException:
            print_exc()
            log(f"{new_tweets} skipped due to length from {users_string[:-2]}")
            await channel.send(
                f"Too many characters to send in one message, skipping {new_tweets} tweets"
            )


# -- Event handling --


@client.event
async def on_ready() -> None:
    global channel, schedule_ping, debug_channel

    log(f"Loaded {len(extra_pings)} extra pings")

    await client.change_presence(activity=Activity(type=ActivityType.watching,
                                                   name="tweets for you 🏳️‍🌈"))
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


@slash.slash(name="list", description="List watched talents")
async def list(ctx: SlashContext) -> None:
    log(f"Command `list` called from server {ctx.guild_id} by {ctx.author}")
    response = get(f"{api_url}/talents/{bot_name}")
    data = response.json()
    names = [talent["name"] for talent in data]
    await ctx.send(f"Watching {len(names)} talents: {', '.join(names)}")


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

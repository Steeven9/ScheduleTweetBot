from datetime import datetime
from os import getenv, makedirs, path

from discord import Activity, ActivityType, errors, utils
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from tweepy.errors import BadRequest, TooManyRequests, TwitterServerError

from data import (bot_name, channel_id, guerrilla_keywords, list_id, role_id,
                  schedule_keywords)
from fetcher import (fetch_spaces, fetch_tweets_from_list,
                     fetch_user_ids_from_list)

# -- Options --
# Interval between each fetch (in seconds)
timeout = 60
# Filenames to store already fetched tweets and spaces
tweets_file = "config/{0}_tweets.ini".format(bot_name)
spaces_file = "config/{0}_spaces.ini".format(bot_name)
# Bot prefix (ignored, we use slash commands)
prefix = ".holotweetbot"
# Set this to True to register slash commands on boot
sync_commands = True
# Discord bot token
discord_token = getenv("{0}BOT_TOKEN".format(bot_name.upper()))
# Debug channel to send errors to (private)
debug_channel_id = 935532391550820372
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
client = commands.Bot(prefix)
slash = SlashCommand(client, sync_commands)
if channel_id == None:
    raise ValueError("[{0}] Channel ID not found!".format(bot_name))
if discord_token == None:
    raise ValueError("[{0}] Discord bot token not found!".format(bot_name))
talents_data = []


async def get_and_send_tweets(channel, debug_channel):
    global existing_spaces
    try:
        [tweets, tweets_fetched] = fetch_tweets_from_list(list_id)
        [spaces, spaces_fetched] = fetch_spaces(talents_data)
    except TwitterServerError as err:
        err_string = "Twitter died: {0}".format(err)
        log(err_string)
        return
    except TooManyRequests as err:
        err_string = "Too many requests: {0}".format(err)
        log(err_string)
        await debug_channel.send(err_string)
        return
    except BadRequest as err:
        err_string = "API error: {0}".format(err)
        log(err_string)
        await debug_channel.send(err_string)
        return

    if tweets_fetched != 0:
        await send_message(tweets, channel, tweets_fetched)

    if spaces_fetched != 0:
        schedule_ping = utils.get(channel.guild.roles, id=role_id)
        result = "{0} ".format(schedule_ping.mention)
        i = 0

        for space in spaces.data:
            if str(space.id) not in existing_spaces:
                result += ":bird: {0} has a {1} space! https://twitter.com/i/spaces/{2}\n".format(
                    spaces.includes["users"][i].username, space.state,
                    space.id)
                # Save current space ID to file
                f2.write(str(space.id) + "\n")
                existing_spaces.append(str(space.id))
                i += 1
        if (i > 0):
            try:
                await channel.send(result)
            except errors.HTTPException:
                log("{0} spaces skipped due to length".format(tweets_fetched))
                await channel.send(
                    "Too many characters to send in one message, skipping {0} spaces"
                    .format(tweets_fetched))

    return tweets_fetched + spaces_fetched


async def send_message(data, channel, tweets_fetched):
    # Construct message
    schedule_ping = utils.get(channel.guild.roles, id=role_id)
    result = "{0} ".format(schedule_ping.mention)
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
                if w in tweet.text.lower():
                    tweet_type = ":calendar: Schedule tweet"
                    found = True
                    break
            for w in guerrilla_keywords:
                if w in tweet.text.lower():
                    tweet_type = ":gorilla: Guerilla tweet"
                    found = True
                    break

            if found and "https://t.co/" in tweet.text.lower():
                if "RT @" in tweet.text[:4]:
                    result += "[{0}] ".format(get_rt_text(tweet))
                result += "{0} from {1} - https://twitter.com/{1}/status/{2}\n\n".format(
                    tweet_type, users[tweet.author_id].username, tweet.id)
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
        log("{0} found from {1}".format(i, users_string[:-2]))
        try:
            await channel.send(result)
        except errors.HTTPException:
            log("{0} skipped due to length from {1}".format(
                tweets_fetched, users_string))
            await channel.send(
                "Too many characters to send in one message, skipping {0} tweets from {1}"
                .format(i, users_string))


@client.event
async def on_ready():
    global talents_data
    talents_data, talents_amount = fetch_user_ids_from_list(list_id)
    log("Loaded {0} talents".format(talents_amount))

    await client.change_presence(
        activity=Activity(type=ActivityType.watching, name="tweets for you"))
    log("Logged in as {0}".format(client.user))
    # Start cron
    check_tweets.start()


# Slash command to get tweets manually
@slash.slash(
    name="holotweets",
    description="Get new tweets",
)
async def holotweets(ctx):
    log("Command called from server {0} by {1}".format(ctx.guild_id,
                                                       ctx.author))
    debug_channel = client.get_channel(int(debug_channel_id))
    tweets_fetched = await get_and_send_tweets(ctx, debug_channel)
    if tweets_fetched == 0:
        await ctx.send("Nothing new found")


# Main loop that gets the tweets
@tasks.loop(seconds=timeout)
async def check_tweets():
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


# Helper to log messages in stdout
def log(msg):
    print("{0} [{1}] {2}".format(str(datetime.now())[:-7], bot_name, msg))


client.run(discord_token)

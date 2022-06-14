from datetime import datetime
from os import getenv, makedirs, path

from discord import Activity, ActivityType, errors, utils
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from tweepy.errors import BadRequest, TwitterServerError

from data import (bot_name, channel_id, guerrilla_keywords, role_id,
                  schedule_keywords, talents)
from fetcher import fetch_spaces, fetch_tweets, fetch_user_ids

# -- Options --
# Interval between each fetch (in seconds)
timeout = 60
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


def get_timestamp():
    return str(datetime.now())[:-7]


# Try to read latest ID from file
try:
    f = open(filename, "r")
    newest_id = f.read().strip()
    print("{0} [{1}] Loaded config from file".format(get_timestamp(),
                                                     bot_name))
except FileNotFoundError:
    makedirs(path.dirname(filename), exist_ok=True)
    newest_id = None
# Initialize stuff
client = commands.Bot(prefix)
slash = SlashCommand(client, sync_commands)
if channel_id == None:
    raise ValueError("[{0}] Channel ID not found!".format(bot_name))
if discord_token == None:
    raise ValueError("[{0}] Discord bot token not found!".format(bot_name))
talents_data = []


async def get_and_send_tweets(channel, debug_channel):
    global newest_id
    try:
        [tweets, tweets_fetched,
         newest_id] = fetch_tweets(newest_id, talents_data)
        [spaces, spaces_fetched] = fetch_spaces(talents_data)
    except TwitterServerError as err:
        err_string = "[{0}] Twitter died: {1}".format(bot_name, err)
        print(get_timestamp(), err_string)
        return
    except BadRequest as err:
        err_string = "[{0}] API error: {1}".format(bot_name, err)
        print(get_timestamp(), err_string)
        await debug_channel.send(err_string)
        return

    if tweets_fetched != 0:
        await send_message(tweets, channel, tweets_fetched)
    if spaces_fetched != 0:
        # TODO examine the data and see what it returns
        print(spaces)
        #await send_message(spaces, debug_channel, spaces_fetched)

    # Save latest ID to file
    f = open(filename, "w")
    f.write(newest_id)
    f.close()

    return tweets_fetched + spaces_fetched


async def send_message(data, channel, tweets_fetched):
    # Construct message
    schedule_ping = utils.get(channel.guild.roles, id=role_id)
    result = "{0} ".format(schedule_ping.mention)
    tweets = data.data
    users = {user["id"]: user for user in data.includes["users"]}
    i = 1
    users_string = ""
    for tweet in tweets:
        if "RT @" in tweet.text[:4]:
            result += "[{0}] ".format(get_rt_text(tweet))

        tweet_type = "Tweet"
        for w in schedule_keywords:
            if w in tweet.text.lower():
                tweet_type = "Schedule tweet"
                break
        for w in guerrilla_keywords:
            if w in tweet.text.lower():
                tweet_type = "Guerilla tweet"
                break

        result += "{0} from {1} - https://twitter.com/{1}/status/{2}\n".format(
            tweet_type, users[tweet.author_id].username, tweet.id)
        users_string += users[tweet.author_id].username
        if i < tweets_fetched:
            result += separator + "\n"
            users_string += ", "
        i += 1

    # Log event
    print("{0} [{1}] {2} found from {3}".format(get_timestamp(), bot_name,
                                                tweets_fetched, users_string))

    # Send Discord message
    if (i > 1):
        try:
            await channel.send(result)
        except errors.HTTPException:
            print("{0} [{1}] {2} skipped due to length from {3}".format(
                get_timestamp(), bot_name, tweets_fetched, users_string))
            await channel.send(
                "Too many characters to send in one message, skipping {0} tweets from {1}"
                .format(tweets_fetched, users_string))


@client.event
async def on_ready():
    global talents_data
    talents_data, talents_amount = fetch_user_ids()
    print("{0} [{1}] Loaded {2} talents".format(get_timestamp(), bot_name,
                                                talents_amount))
    if talents_amount != len(talents):
        print(
            "{0} [{1}] Error fetching talents data! Found {2} but should be {3}"
            .format(get_timestamp(), bot_name, talents_amount, len(talents)))
        exit(-1)

    await client.change_presence(
        activity=Activity(type=ActivityType.watching, name="tweets for you"))
    print("{0} [{1}] Logged in as {2}".format(get_timestamp(), bot_name,
                                              client.user))
    # Start cron
    check_tweets.start()


# Slash command to get tweets manually
@slash.slash(
    name="holotweets",
    description="Get new tweets",
)
async def holotweets(ctx):
    print("{0} [{1}] Command called from server {2} by {3}".format(
        get_timestamp(), bot_name, ctx.guild_id, ctx.author))
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


client.run(discord_token)

# <img src="logo.png" width="100"> ScheduleTweetBot

[![License](https://img.shields.io/github/license/Steeven9/ScheduleTweetBot)](/LICENSE)
[![C/C++ CI](https://github.com/Steeven9/ScheduleTweetBot/actions/workflows/docker-image.yml/badge.svg)](https://github.com/Steeven9/ScheduleTweetBot/actions/workflows/docker-image.yml)
![Lines](https://img.shields.io/tokei/lines/github/Steeven9/ScheduleTweetBot)

A simple Discord bot to fetch schedule-related tweets to
feed our [Hololive](https://holocal.moe) and [Nijisanji](https://nijien.vercel.app/) calendars.

## Setup

1. Obtain a [Twitter API Bearer token](https://developer.twitter.com/en/docs/twitter-api) and
a [Discord bot token](https://www.writebots.com/discord-bot-token).

2. Create a Twitter List with all the talents you want to monitor and save its id.

3. Clone the repo and install the requirements:

    `pip install --no-cache-dir -r requirements.txt`

4. Set the following environment variables with the two respective values:

    ```bash
    TWITTER_BEARER_TOKEN
    NAMEBOT_TOKEN
    ```

    Note: `NAME` is the alias you want to set for the bot (must match `bot_name` in `data.py`).

5. Customize ehe configuration for scraping and notifying: edit the `data.py` file and fill in all the values.

6. Finally, run `python main.py`.

## Usage

The bot automatically sends new tweets in the specified channel every 60 seconds
(the timeout is configurable in `main.py`), pinging the specified role if any keyword matches.
The watched List and keywords can be set in the `data.py` file.

Optionally you can also use `/getTweets` to fetch and display new tweets manually.
If you don't see the slash command in your server, wait around one hour to allow it
to sync, or check that you invited the bot with the `applications.commands` scope.

The already scraped tweets and spaces are saved each time so you won't see the same one twice;
by default the IDs are written in the `config/[NAME]_tweets.ini` and `config/[NAME]_spaces.ini`
files (configurable in `main.py` as well).

## Run in Docker

Create a `.env` file with the environment variables mentioned in step 4,
then build or pull the image and run it:

`docker build . -t scheduletweetbot`

`docker run --name scheduletweetbot --env-file .env scheduletweetbot`

## Credits

Profile picture by the one and only [DuDuL](https://twitter.com/DuDuLtv)!

Huge thanks to the team at KFP | The Office for helping with debugging
and feature suggestions.

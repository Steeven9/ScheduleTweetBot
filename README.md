# <img src="logo.png" width="100"> ScheduleTweetBot

[![](https://img.shields.io/github/license/Steeven9/ScheduleTweetBot)](/LICENSE)
[![C/C++ CI](https://github.com/Steeven9/ScheduleTweetBot/actions/workflows/docker-image.yml/badge.svg)](https://github.com/Steeven9/ScheduleTweetBot/actions/workflows/docker-image.yml)
![](https://img.shields.io/tokei/lines/github/Steeven9/ScheduleTweetBot)

A simple Discord bot to fetch schedule-related tweets to
feed our [schedule](https://holocal.moe).

Profile picture by the one and only [DuDuL](https://twitter.com/DuDuLtv)!

## Setup

To install the requirements, run `pip install --no-cache-dir -r requirements.txt`.

You will need a Twitter API Bearer token and the Discord bot token.

Set the following environment variables with the two respective values:

```bash
TWITTER_BEARER_TOKEN
[NAME]BOT_TOKEN
```

The configuration used for scraping and notifying is stored in the `data.py` file.

Finally, run `python main.py`.

## Usage

The bot automatically sends new tweets in the specified channel every 120 seconds
(the timeout is configurable in `main.py`). The query is configurable in the
`fetcher.py` file, while the watched users and keywords can be set in the `data.py` file.

Optionally you can also use `/holotweets` to fetch and display new tweets manually.
If you don't see the slash command in your server, wait around one hour to allow it
to sync, or check that you invited the bot with the `applications.commands` scope.

The already scraped tweets and spaces are saved each time so you won't see the same one twice;
by default the IDs are written in the `config/[NAME]_tweets.ini` and `config/[NAME]_spaces.ini`
files (configurable in `main.py` as well).

## Docker? Docker

Create a `.env` file with the environment variables above, then build or pull the image and run it:

`docker build . -t scheduletweetbot` or `docker pull steeven9/scheduletweetbot:[NAME]`

`docker run --name scheduletweetbot --env-file .env scheduletweetbot`

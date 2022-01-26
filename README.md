# <img src="logo.png" width="100"> HoloTweetBot

[![](https://img.shields.io/github/license/Steeven9/HoloTweetBot)](/LICENSE)
[![C/C++ CI](https://github.com/Steeven9/HoloTweetBot/actions/workflows/docker-image.yml/badge.svg)](https://github.com/Steeven9/HoloTweetBot/actions/workflows/docker-image.yml)
![](https://img.shields.io/tokei/lines/github/Steeven9/HoloTweetBot)

A simple Discord bot to fetch schedule-related Hololive tweets to
feed our [schedule](https://holocal.moe).

Profile picture by the one and only [DuDuL](https://twitter.com/DuDuLtv)!

## Setup

To install the requirements, run `pip install --no-cache-dir -r requirements.txt`.

You will need a Twitter API Bearer token and the Discord bot token.

Set the following environment variables with the two respective values:

```
TWITTER_BEARER_TOKEN
HOLOTWEETBOT_TOKEN
```

You will also need to set the `HOLOTWEETBOT_CHANNEL` variable with the
Discord channel ID where you want the messages to be sent to.

Finally, run `python main.py`.


## Usage

The bot automatically sends new tweets in the specified channel every 60 seconds
(the timeout is configurable in `main.py`). The query is configurable in the
`fetcher.py` file.

Optionally you can also use `/holotweets` to fetch and display new tweets manually.
If you don't see the slash command in your server, wait around one hour to allow it
to sync, or check that you invited the bot with the `applications.commands` scope.

The most recent tweet is saved each time so you won't see the same one twice;
by default the ID is written in the `config/holotweetbot.ini` file
(configurable in `main.py` as well).


## Docker? Docker!

Create a `.env` file with the environment variables above, then build or pull the image and run it:

`docker build . -t holotweetbot` or `docker pull steeven9/holotweetbot`

`docker run --name holotweetbot --env-file .env holotweetbot`

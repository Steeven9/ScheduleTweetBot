# <img src="logo.png" width="100"> ScheduleTweetBot

[![License](https://img.shields.io/github/license/Steeven9/ScheduleTweetBot)](/LICENSE)
[![C/C++ CI](https://github.com/Steeven9/ScheduleTweetBot/actions/workflows/docker-image.yml/badge.svg)](https://github.com/Steeven9/ScheduleTweetBot/actions/workflows/docker-image.yml)
![Lines](https://img.shields.io/tokei/lines/github/Steeven9/ScheduleTweetBot)

A simple Discord bot to fetch schedule-related tweets and spaces to
feed our [Hololive](https://holocal.moe) and [Nijisanji](https://nijien.vercel.app) calendars.

## Setup

1. Obtain a [Discord bot token](https://www.writebots.com/discord-bot-token).

2. Clone the repo and install the requirements:

    ```bash
    pip install --no-cache-dir -r requirements.txt
    ```

3. Set the NAMEBOT_TOKEN environment variables with the token from step 1.
   Note: `NAME` is the alias you want to set for the bot (must match `bot_name` in `data.py`).

4. Customize the configuration for scraping and notifying: edit the `data.py` file and fill in all the values.

5. Finally, run `python main.py`. If everything went well, you should see an output similar to this:

    ```bash
    2023-02-18 00:26:56 [NAME] Loaded <n> extra pings
    2023-02-18 00:26:56 [NAME] Logged in as <your bot name and ID>
    ```

## Usage

The bot automatically sends new tweets in the specified channel every 60 seconds
(the timeout is configurable in `main.py`), pinging the specified role if any keyword matches.
The watched talents and keywords can be set in the `data.py` file.

Optionally you can also use `/fetch` to fetch and display new tweets and spaces manually.
If you don't see the slash command in your server, wait around one hour to allow it
to sync, or check that you invited the bot with the `applications.commands` scope.

The already scraped tweets and spaces are saved each time so you won't see the same one twice;
by default the IDs are written in the `config/[NAME]_tweets.ini` and `config/[NAME]_spaces.ini`
files (configurable in `main.py` as well).

## Run in Docker

Create a `.env` file with the environment variables mentioned in step 3,
then build or pull the image from [Dockerhub](https://hub.docker.com/repository/docker/steeven9/scheduletweetbot) and run it:

```bash
    docker build . -t scheduletweetbot
    docker run --name scheduletweetbot --env-file .env scheduletweetbot
```

## Credits

Logo by the one and only [DuDuL](https://twitter.com/DuDuLtv)!

Twitter data is provided by [blooop](https://github.com/Steeven9/blooop).

Huge thanks to the teams of `KFP | The Office` and `Nijisanji EN Schedule Team`
for helping with debugging and feature suggestions.

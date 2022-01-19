# HoloTweetBot
Discord bot to fetch specific tweets

## Setup

To install the requirements, run `pip install --no-cache-dir -r requirements.txt`.

You will need a Twitter API Bearer token and the Discord bot token.

Set the following environment variables with the two respective values:

```
TWITTER_BEARER_TOKEN
HOLOTWEETBOT_TOKEN
```

You will also need to set the `HOLOTWEETBOT_CHANNEL` variable with the
channel ID where you want the messages to be sent to.

Finally, run `python main.py`.


## Usage

The bot automatically sends new tweets in the specified channel, every 60 seconds
(the timeout is configurable in `main.py`). The query is configurable in the
`fetcher.py` file.

Optionally you can use `/holotweets` to fetch and display new tweets manually.


## Docker? Docker!

Create a `.env` file with the environment variables above, then build or pull the image and run it:

`docker build . -t holotweetbot` or `docker pull steeven9/holotweetbot`

`docker run --name holotweetbot --env-file .env holotweetbot`

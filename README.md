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

Finally, run `python main.py`.


## Usage

Currently: use `/holotweets` to fetch and display new tweets.

Ideally: the bot automatically sends new tweets in a specified channel.


## Docker? Docker!

Create a `.env` file with the environment variables above, then build or pull the image and run it:

`docker build . -t holotweetbot` or `docker pull steeven9/holotweetbot`

`docker run --name holotweetbot --env-file .env holotweetbot`

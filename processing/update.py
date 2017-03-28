"""
Store tweets more recent than SHORT_TERM in .json file
Older tweets that are passed to process_new_tweets are discarded.
Newer tweets are taken into account.
"""
import json
import logging

from processing import get_short_term_start, get_long_intervals_between, get_short_intervals, Tweet
from processing.status import StatusAggregate, write_disk_status, load_disk_status
from main import app
SHORT_TWEETS_FILE = "output/short_term_tweets.json"


def load_disk_tweets():
    try:
        with open(SHORT_TWEETS_FILE, 'r') as f:
            data = f.read()
            if len(data) == 0:
                return []
            tweets = json.load(f)
            return [Tweet(tweet) for tweet in tweets]
    except:
        return []


def write_disk_tweets(tweets):
    with open(SHORT_TWEETS_FILE, 'w') as f:
        json.dump([tweet.get_dict() for tweet in tweets], f)


ALL_STRIPPED_TWEETS_FILE = "output/all_stripped_tweets.json"


def get_stored_tweets():
    try:
        with open(ALL_STRIPPED_TWEETS_FILE, "r") as f:
            tweets = json.load(f)
            return [Tweet.load_stripped_tweet(tweet) for tweet in tweets]
    except IOError as err:
        logging.error("{} not found: no stripped tweets loaded!".format(ALL_STRIPPED_TWEETS_FILE))
        return []


def store_new_tweets(new_tweets_original):
    logging.info("Storing new tweets")
    all_tweets = get_stored_tweets()
    all_tweet_ids = {tweet.tweet_id for tweet in all_tweets}
    for tweet_obj in new_tweets_original:
        t = Tweet.load_raw_tweet(tweet_obj)
        if t.tweet_id in all_tweet_ids:
            continue
        all_tweets.append(t)
        all_tweet_ids.add(t.tweet_id)
    with open(ALL_STRIPPED_TWEETS_FILE, "w") as f:
        json.dump([tweet.get_full_dict() for tweet in all_tweets], f)
    logging.info("Storing new tweets DONE")


def update_statistics():
    logging.info("Updating statistics")
    new_status = StatusAggregate({})

    all_tweets = get_stored_tweets()

    earliest_date = min(map(lambda tweet: tweet.get_datetime(), all_tweets))
    all_intervals = get_short_intervals() + get_long_intervals_between(earliest_date, get_short_term_start())
    for interval in all_intervals:
        new_status.add_interval(interval, all_tweets)

    write_disk_status(new_status)
    app.status_structure = load_disk_status()
    logging.info("Updating statistics DONE")


def process_new_tweets(new_tweets_original):
    logging.info("Processing new tweets!")
    store_new_tweets(new_tweets_original)
    update_statistics()
    logging.info("Processing new tweets DONE")

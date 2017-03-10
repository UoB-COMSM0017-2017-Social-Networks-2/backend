"""
Store tweets more recent than SHORT_TERM in .json file
Older tweets that are passed to process_new_tweets are discarded.
Newer tweets are taken into account.
"""
import json

from processing import get_short_term_start, get_long_intervals_between, get_short_intervals, Tweet
from processing.status import load_disk_status, StatusAggregate, write_disk_status, get_tweets_after

SHORT_TWEETS_FILE = "output/short_term_tweets.json"


def load_disk_tweets():
    with open(SHORT_TWEETS_FILE, 'r') as f:
        data = f.read()
        if len(data) == 0:
            return []
        tweets = json.load(f)
        return [Tweet(tweet) for tweet in tweets]


def write_disk_tweets(tweets):
    with open(SHORT_TWEETS_FILE, 'w') as f:
        json.dump([tweet.get_dict() for tweet in tweets], f)


def process_new_tweets(new_tweets):
    # Convert new_tweets to Tweet objects
    new_tweets = [Tweet.load_raw_tweet(tweet) for tweet in new_tweets]
    # Load tweets from disk
    disk_tweets = load_disk_tweets()
    # Add tweets to set
    all_tweets = disk_tweets + new_tweets

    short_term_start = get_short_term_start()

    disk_status = load_disk_status()
    new_status = StatusAggregate(disk_status.get_long_intervals_data())

    short_intervals = get_short_intervals()
    for interval in short_intervals:
        new_status.add_interval(interval, all_tweets)

    if disk_status.short_term_start < short_term_start:
        # Process tweets from disk that are more than SHORT_TERM old and merge into 1 day block
        long_intervals = get_long_intervals_between(disk_status.short_term_start,
                                                    short_term_start)
        for interval in long_intervals:
            new_status.add_interval(interval, all_tweets)

    # Write tweets more recent than SHORT_TERM to disk
    recent_tweets = get_tweets_after(all_tweets, short_term_start)
    write_disk_tweets(recent_tweets)
    # Write categories to disk
    write_disk_status(new_status)
    pass

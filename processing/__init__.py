"""
==FIRST==
interval -> topics
topic -> (interval -> data)
(topic, location) -> (interval -> data)
(topic, interval) -> data
(topic, interval, location) -> data

==SECOND==
topics
topic -> (data)
(topic, location) -> (data)
(topic) -> data
(topic, location) -> data
topics

==THIRD==
(data)
(location) -> (data)
() -> data
(location) -> data

==STORAGE==
interval -> topic -> location -> data
interval -> topic -> data

Store tweets more recent than SHORT_TERM in .json file
Older tweets that are passed to process_new_tweets are discarded.
Newer tweets are taken into account.
"""
import calendar
import datetime
import json

SHORT_TWEETS_FILE = "output/short_term_tweets.json"
STATUS_FILE = "output/status.json"
SHORT_PERIOD = datetime.timedelta(days=7)
SHORT_INTERVAL_LENGTH = datetime.timedelta(hours=1)
LONG_INTERVAL_LENGTH = datetime.timedelta(days=1)


def get_tweet_time(tweet):
    if 'timestamp_ms' not in tweet:
        return None
    timestamp = tweet['timestamp_ms'] / 1000
    return datetime.datetime.fromtimestamp(timestamp=timestamp, tz=datetime.timezone.utc)


def get_tweets_after(tweets, start):
    return [tweet for tweet in tweets if get_tweet_time(tweet) >= start]


def get_tweets_between(tweets, start, end):
    return [tweet for tweet in tweets if start <= get_tweet_time(tweet) < end]


def get_short_term_start():
    # TODO: check daylight saving time issues
    now = datetime.datetime.utcnow()
    period_start = (now - SHORT_PERIOD).date()
    period_timestamp = calendar.timegm(period_start.timetuple())
    return datetime.datetime.fromtimestamp(period_timestamp)


def get_long_intervals_between(start, end):
    assert (datetime.timedelta(days=1).seconds % LONG_INTERVAL_LENGTH.seconds == 0), \
        "LONG_INTERVAL_LENGTH must fit an integer number of times into a day"
    intervals = []
    start_day = start.date()
    current_start = start_day
    while current_start + LONG_INTERVAL_LENGTH <= end:
        intervals.append((current_start, current_start + LONG_INTERVAL_LENGTH))
        current_start += LONG_INTERVAL_LENGTH
    return intervals


def get_short_intervals():
    start = get_short_term_start()
    intervals = []
    current_start = start
    while current_start < datetime.datetime.now():
        intervals.append((current_start, current_start + SHORT_INTERVAL_LENGTH))
        current_start += SHORT_INTERVAL_LENGTH
    return intervals


def load_disk_tweets():
    with open(SHORT_TWEETS_FILE, 'r') as f:
        data = f.read()
        if len(data) == 0:
            return []
        return json.load(f)


def write_disk_tweets(tweets):
    with open(SHORT_TWEETS_FILE, 'w') as f:
        json.dump(tweets, f)


class StatusAggregate:
    def __init__(self, long_intervals):
        pass

    def add_interval(self, interval, tweets):
        tweets = get_tweets_between(tweets, interval[0], interval[1])
        # TODO: process

    def get_long_intervals(self):
        pass


def load_disk_status():
    pass


def write_disk_status(status):
    pass


def process_new_tweets(tweets):
    # Load tweets from disk
    disk_tweets = load_disk_tweets()
    # Add tweets to set
    all_tweets = disk_tweets + tweets

    short_term_start = get_short_term_start()

    disk_status = load_disk_status()
    new_status = StatusAggregate(disk_status.get_long_intervals())

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

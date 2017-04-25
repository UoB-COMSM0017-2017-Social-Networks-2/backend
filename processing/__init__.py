import calendar
import datetime
import logging

from helpers.tweet import Tweet
from processing import regions
from processing import sentiment

SHORT_PERIOD = datetime.timedelta(days=-1)
SHORT_INTERVAL_LENGTH = datetime.timedelta(hours=1)
LONG_INTERVAL_LENGTH = datetime.timedelta(days=1)

from pymongo import MongoClient, ASCENDING, errors

from main import app

mongo = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
db = mongo.database

db.tweets.create_index("tweet_id")
try:
    db.tweets.create_index([("tweet_id", ASCENDING), ("topic", ASCENDING)], unique=True)
except errors.DuplicateKeyError as err:
    logging.error("Failed to create a unique index: {}".format(err))


def get_short_term_start():
    # TODO: check daylight saving time issues
    now = datetime.datetime.utcnow()
    period_start = (now - SHORT_PERIOD).date()
    period_timestamp = calendar.timegm(period_start.timetuple())
    return datetime.datetime.fromtimestamp(period_timestamp)


def get_long_intervals_between(start, end):
    assert (datetime.timedelta(days=1).total_seconds() % LONG_INTERVAL_LENGTH.total_seconds() == 0), \
        "LONG_INTERVAL_LENGTH must fit an integer number of times into a day"
    intervals = []
    start_day = start.date()
    current_start = datetime.datetime.combine(start_day, datetime.time())
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


def get_earliest_time():
    tweet = Tweet.load_stripped_tweet(db.tweets.find_one(sort=[("timestamp", 1)]))
    return tweet.get_datetime()


def get_intervals():
    start_date = get_earliest_time()
    long_intervals = get_long_intervals_between(start_date, get_short_term_start())
    short_intervals = get_short_intervals()
    return long_intervals + short_intervals


def get_last_interval():
    return get_intervals()[-1]

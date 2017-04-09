import calendar
import datetime

from processing import regions
from processing import sentiment

SHORT_PERIOD = datetime.timedelta(days=7)
SHORT_INTERVAL_LENGTH = datetime.timedelta(hours=1)
LONG_INTERVAL_LENGTH = datetime.timedelta(days=1)

MINING_TOPIC_KEY = "TrendingTopic"
MINING_TEXT_KEY = "text"
MINING_ID_KEY = "id"
MINING_TIMESTAMP_KEY = "timestamp_ms"
MINING_COORDINATES_KEY = "coordinates"
MINING_PLACE_KEY = "place"
MINING_USER_KEY = "user"
MINING_USER_LOCATION_KEY = "location"

from pymongo import MongoClient

from main import app

mongo = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
db = mongo.database


def get_attribute_if_exists(d, key):
    return d[key] if key in d else None


def get_tweet_region_id(tweet_obj):
    coordinates = tweet_obj['coordinates']
    if coordinates is None:
        return regions.get_global_region().region_id
    else:
        coordinates = coordinates["coordinates"]
        region = regions.get_smallest_region_by_coordinates(coordinates[0], coordinates[1])
        if region is None:
            return None
        return region.region_id


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


def get_last_interval():
    return get_short_intervals()[-1]


class Tweet:
    def __init__(self, tweet_obj, use_parsed=False):
        self.text = tweet_obj["text"]
        self.tweet_id = tweet_obj["tweet_id"]
        self.timestamp = tweet_obj["timestamp"]
        self.topic = tweet_obj["topic"]
        self.coordinates = tweet_obj["coordinates"]
        self.place = tweet_obj["place"]
        self.user_location = tweet_obj["user_location"]

        self.sentiment = tweet_obj["sentiment"] if use_parsed and "sentiment" in tweet_obj \
            else sentiment.get_tweet_sentiment(tweet_obj)
        self.region_id = tweet_obj["region_id"] if use_parsed and "region_id" in tweet_obj \
            else get_tweet_region_id(tweet_obj)

    def get_datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp)

    def get_compound_sentiment(self):
        return self.sentiment["compound"]

    def negative_sentiment(self):
        return self.sentiment['neg'] > max(self.sentiment['neu'], self.sentiment['pos'])

    def neutral_sentiment(self):
        return self.sentiment['neu'] > max(self.sentiment['pos'], self.sentiment['neg'])

    def positive_sentiment(self):
        return self.sentiment['pos'] > max(self.sentiment['neg'], self.sentiment['neu'])

    @classmethod
    def load_raw_tweet(cls, tweet_obj):
        arr = dict()
        arr["coordinates"] = tweet_obj[MINING_COORDINATES_KEY]
        arr["place"] = tweet_obj[MINING_PLACE_KEY]
        arr["user_location"] = tweet_obj[MINING_USER_KEY][MINING_USER_LOCATION_KEY]
        arr["text"] = tweet_obj[MINING_TEXT_KEY]
        arr["tweet_id"] = tweet_obj[MINING_ID_KEY]
        arr["timestamp"] = int(tweet_obj[MINING_TIMESTAMP_KEY]) // 1000
        arr["topic"] = get_attribute_if_exists(tweet_obj, MINING_TOPIC_KEY)
        return Tweet(arr, use_parsed=False)

    @classmethod
    def load_stripped_tweet(cls, tweet_obj):
        return Tweet(tweet_obj, True)

    def get_parsed_dict(self):
        return {
            "text": self.text,
            "tweet_id": self.tweet_id,
            "sentiment": self.sentiment,
            "region_id": self.region_id,
            "timestamp": self.timestamp,
            "topic": self.topic,
        }

    def get_original_dict(self):
        return {
            "tweet_id": self.tweet_id,
            "text": self.text,
            "timestamp": self.timestamp,
            "topic": self.topic,
            "coordinates": self.coordinates,
            "place": self.place,
            "user_location": self.user_location
        }

    def get_full_dict(self):
        data = self.get_original_dict()
        data.update(self.get_parsed_dict())
        return data

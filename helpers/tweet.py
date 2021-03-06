import datetime

from helpers.topics import transform_topic_name
from processing import regions, sentiment

MINING_TOPIC_KEY = "TrendingTopic"
MINING_TEXT_KEY = "text"
MINING_ID_KEY = "id"
MINING_TIMESTAMP_KEY = "timestamp_ms"
MINING_COORDINATES_KEY = "coordinates"
MINING_PLACE_KEY = "place"
MINING_USER_KEY = "user"
MINING_USER_LOCATION_KEY = "location"


def get_attribute_if_exists(d, key, default=None):
    return d[key] if key in d else default


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


class Tweet:
    def __init__(self, tweet_obj, use_parsed=False):
        self.id = get_attribute_if_exists(tweet_obj, "_id")
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

    def process(self):
        self.sentiment = sentiment.get_tweet_sentiment(self.get_original_dict())
        self.region_id = get_tweet_region_id(self.get_original_dict())

    def get_datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp)

    def get_compound_sentiment(self):
        return self.sentiment["compound"]

    def negative_sentiment(self):
        return self.sentiment['neg'] > self.sentiment['pos']

    def neutral_sentiment(self):
        return self.sentiment['pos'] == self.sentiment['neg']

    def positive_sentiment(self):
        # return self.sentiment['pos'] > max(self.sentiment['neg'], self.sentiment['neu'])
        return self.sentiment['pos'] > self.sentiment['neg']

    @classmethod
    def load_raw_tweet(cls, tweet_obj):
        arr = dict()
        arr["coordinates"] = tweet_obj[MINING_COORDINATES_KEY]
        arr["place"] = tweet_obj[MINING_PLACE_KEY]
        arr["user_location"] = tweet_obj[MINING_USER_KEY][MINING_USER_LOCATION_KEY]
        arr["text"] = tweet_obj[MINING_TEXT_KEY]
        arr["tweet_id"] = tweet_obj[MINING_ID_KEY]
        arr["timestamp"] = int(tweet_obj[MINING_TIMESTAMP_KEY]) // 1000
        arr["topic"] = transform_topic_name(get_attribute_if_exists(tweet_obj, MINING_TOPIC_KEY, ""))
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

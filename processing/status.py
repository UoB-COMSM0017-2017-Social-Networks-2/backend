import datetime
import json

from processing import regions, get_short_term_start

STATUS_FILE = "output/status.json"


def get_tweet_time(tweet):
    timestamp = tweet.timestamp
    return datetime.datetime.fromtimestamp(timestamp=timestamp, tz=datetime.timezone.utc)


def get_tweet_region(tweet):
    return regions.get_region_by_woeid(tweet.woeid)


def get_tweets_after(tweets, start):
    return [tweet for tweet in tweets if get_tweet_time(tweet) >= start]


def get_tweets_between(tweets, start, end):
    return [tweet for tweet in tweets if start <= get_tweet_time(tweet) < end]


def get_tweets_in_region(tweets, region):
    return [tweet for tweet in tweets if regions.is_in_region(get_tweet_region(tweet), region)]


class StatusInterval:
    def __init__(self, topic_data):
        # topic_data: topic -> StatusIntervalTopic
        self.topic_data = topic_data

    @classmethod
    def from_dict(cls, data):
        topic_data = dict()
        for topic in data['topics']:
            topic_data[topic] = StatusIntervalTopic.from_dict(data['topics'][topic])
        return StatusInterval(topic_data)

    @classmethod
    def from_tweets(cls, tweets):
        topic_data = dict()
        topics = {tweet.topic for tweet in tweets}
        for topic in topics:
            topic_tweets = [tweet for tweet in tweets if tweet.topic == topic]
            topic_data[topic] = StatusIntervalTopic(topic_tweets)
        return StatusInterval(topic_data)

    def get_dict(self):
        result = dict()
        for topic in self.topic_data:
            result[topic] = self.topic_data[topic].get_dict()
        return {"topics": result}

    def get_global_topic_details(self):
        result = []
        for topic in self.topic_data:
            data = self.topic_data[topic].get_global_data()
            result.append({
                "topic": topic,
                "nb_tweets": data.get_popularity(),
                "overall_sentiment": data.get_overall_sentiment(),
                "positive_ratio": data.get_positive_ratio()
            })
        return result

    def discusses_topic(self, topic_id):
        return topic_id in self.topic_data

    def get_global_topic_data(self, topic_id):
        return self.topic_data[topic_id].get_global_data()

    def get_location_data_for_topic(self, topic_id, location_id):
        return self.topic_data[topic_id].get_location_data(location_id)


class StatusIntervalTopic:
    def __init__(self, location_data):
        # location_data: region id -> StatusIntervalTopicRegion
        self.location_data = location_data

    @classmethod
    def from_tweets(cls, tweets):
        location_data = dict()
        all_regions = regions.get_all_regions()
        for region in all_regions:
            region_tweets = get_tweets_in_region(tweets, region)
            location_data[region.woeid] = StatusIntervalTopicRegion(region_tweets)
        return StatusIntervalTopic(location_data)

    @classmethod
    def from_dict(cls, data):
        location_data = dict()
        for location in data:
            location_data[location] = StatusIntervalTopicRegion.from_dict(data[location])
        return StatusIntervalTopic(location_data)

    def get_dict(self):
        result = dict()
        for location in self.location_data:
            result[location] = self.location_data[location].get_dict()
        return result

    def get_global_data(self):
        global_region = regions.get_global_region()
        return self.get_location_data(global_region.woeid)

    def get_location_data(self, location_id):
        return self.location_data[location_id]


class StatusIntervalTopicRegion:
    def __init__(self, popularity, nb_positive, nb_negative, nb_neutral):
        self.popularity = popularity
        self.nb_positive = nb_positive
        self.nb_negative = nb_negative
        self.nb_neutral = nb_neutral

    @classmethod
    def from_tweets(cls, tweets):
        popularity = len(tweets)
        nb_positive = sum([1 for tweet in tweets if tweet.positive_sentiment()])
        nb_negative = sum([1 for tweet in tweets if tweet.negative_sentiment()])
        nb_neutral = sum([1 for tweet in tweets if tweet.neutral_sentiment()])
        return StatusIntervalTopicRegion(popularity, nb_positive, nb_negative, nb_neutral)

    @classmethod
    def from_dict(cls, data):
        popularity = data['popularity']
        nb_positive = data['nb_positive']
        nb_negative = data['nb_negative']
        nb_neutral = data['nb_neutral']
        return StatusIntervalTopicRegion(popularity, nb_positive, nb_negative, nb_neutral)

    def get_dict(self):
        return {
            "popularity": self.popularity,
            "nb_positive": self.nb_positive,
            "nb_negative": self.nb_negative,
            "nb_neutral": self.nb_neutral
        }

    def get_popularity(self):
        return self.popularity

    def get_overall_sentiment(self):
        if self.nb_positive > max(self.nb_neutral, self.nb_negative):
            return 1
        if self.nb_negative > max(self.nb_neutral, self.nb_positive):
            return -1
        return 0

    def get_positive_ratio(self):
        return self.nb_positive / (self.nb_positive + self.nb_negative)


class StatusAggregate:
    def __init__(self, intervals):
        # intervals: interval -> StatusInterval
        self.intervals = dict()
        for interval in intervals:
            self.intervals[interval] = StatusInterval(interval)

    @classmethod
    def from_dict(cls, data):
        intervals = dict()
        for interval_data in data:
            intervals[(interval_data["start"], interval_data["end"])] = StatusInterval.from_dict(interval_data)
        return StatusAggregate(intervals)

    def to_dict(self):
        result = []
        for interval in self.intervals:
            interval_data = interval.get_dict()
            interval_data["start"] = interval[0]
            interval_data["end"] = interval[1]
            result.append(interval_data)
        return result

    def add_interval(self, interval, tweets):
        self.validate_interval(interval)
        if interval in self.intervals:
            raise Exception("Interval {} already present in StatusAggregate".format(interval))
        tweets = get_tweets_between(tweets, interval[0], interval[1])
        self.intervals[interval] = StatusInterval(tweets)

    def get_long_intervals_data(self):
        short_start = get_short_term_start()
        return [self.intervals[interval] for interval in self.intervals if interval[0] < short_start]

    def get_topics(self, interval):
        self.validate_interval(interval)
        return None

    def get_last_interval(self):
        last = None
        for interval in self.intervals:
            if last is None or interval > last:
                last = interval
        return last

    def get_topic_details_for_interval(self, interval):
        self.validate_interval(interval)
        return self.intervals[interval].get_global_topic_details()

    def get_global_topic_evolution(self, topic_id):
        self.validate_topic(topic_id)
        global_region = regions.get_global_region()
        return self.get_topic_location_evolution(topic_id, global_region.woeid)

    def get_topic_location_evolution(self, topic_id, location_id):
        self.validate_topic(topic_id)
        self.validate_location(location_id)
        result = []
        for interval in self.intervals:
            if not interval.discusses_topic(topic_id):
                result.append(None)
            global_data = interval.get_location_data_for_topic(topic_id, location_id)
            result.append({
                "interval_start": interval[0],
                "interval_end": interval[1],
                "sentiment_distribution": {
                    "nb_positive": global_data.nb_positive,
                    "nb_negative": global_data.nb_negative,
                    "nb_neutral": global_data.nb_neutral
                }
            })
        left = 0
        while result[left] is None:
            left += 1
        right = -1
        while result[right] is None:
            right -= 1
        return result[left:right + 1]

    def get_topic_interval_data_per_region(self, topic_id, interval):
        self.validate_topic(topic_id)
        self.validate_interval(interval)
        # TODO: implement
        return None

    def get_topic_interval_location_data(self, topic_id, interval, location_id):
        self.validate_topic(topic_id)
        self.validate_interval(interval)
        self.validate_location(location_id)
        # TODO: implement
        return None

    def validate_topic(self, topic_id):
        discussed = False
        for interval in self.intervals.items():
            if interval.discusses_topic(topic_id):
                discussed = True
        if not discussed:
            raise Exception("Topic not discussed in any interval")

    def validate_interval(self, interval):
        if interval not in self.intervals:
            raise Exception("Invalid interval: not present")

    def validate_location(self, location_id):
        # TODO: implement
        return None


def load_disk_status():
    with open(STATUS_FILE, 'r') as f:
        data = json.loads(f.read())
        return StatusAggregate(data)


def write_disk_status(status):
    with open(STATUS_FILE, 'w') as f:
        json.dump(status.to_dict(), f)

import datetime
import json

from processing import regions

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
    def __init__(self, tweets):
        # topic_data: topic -> StatusIntervalTopic
        self.topic_data = dict()
        topics = {tweet.topic for tweet in tweets}
        for topic in topics:
            topic_tweets = [tweet for tweet in tweets if tweet.topic == topic]
            self.topic_data[topic] = StatusIntervalTopic(topic_tweets)

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
    def __init__(self, tweets):
        # location_data: region id -> StatusIntervalTopicRegion
        self.location_data = dict()
        all_regions = regions.get_all_regions()
        for region in all_regions:
            region_tweets = get_tweets_in_region(tweets, region)
            self.location_data[region.woeid] = StatusIntervalTopicRegion(region_tweets)

    def get_global_data(self):
        global_region = regions.get_global_region()
        return self.get_location_data(global_region.woeid)

    def get_location_data(self, location_id):
        return self.location_data[location_id]


class StatusIntervalTopicRegion:
    def __init__(self, tweets):
        self.popularity = len(tweets)
        self.nb_positive = sum([1 for tweet in tweets if tweet.positive_sentiment()])
        self.nb_negative = sum([1 for tweet in tweets if tweet.negative_sentiment()])
        self.nb_neutral = sum([1 for tweet in tweets if tweet.neutral_sentiment()])

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
        self.intervals = intervals

    def add_interval(self, interval, tweets):
        self.validate_interval(interval)
        if interval in self.intervals:
            raise Exception("Interval {} already present in StatusAggregate".format(interval))
        tweets = get_tweets_between(tweets, interval[0], interval[1])
        self.intervals[interval] = StatusInterval(tweets)
        # TODO: process

    def get_interval_data(self):
        return None

    def get_long_intervals(self):
        pass

    def get_topics(self, interval):
        self.validate_interval(interval)
        return None

    def get_last_interval(self):
        return None

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
        return None

    def get_topic_interval_location_data(self, topic_id, interval, location_id):
        self.validate_topic(topic_id)
        self.validate_interval(interval)
        self.validate_location(location_id)
        return None

    def validate_topic(self, topic_id):
        return None

    def validate_interval(self, interval):
        return None

    def validate_location(self, location_id):
        return None


def load_disk_status():
    with open(STATUS_FILE, 'r') as f:
        data = json.loads(f.read())
        return StatusAggregate(data)


def write_disk_status(status):
    with open(STATUS_FILE, 'w') as f:
        json.dump(status.get_interval_data(), f)

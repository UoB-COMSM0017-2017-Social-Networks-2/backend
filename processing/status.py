import datetime
import json
import logging

from processing import regions, get_short_term_start

STATUS_FILE = "output/status.json"


def get_tweet_time(tweet):
    timestamp = tweet.timestamp
    return datetime.datetime.fromtimestamp(timestamp=timestamp)


def get_tweet_region(tweet):
    return regions.get_region_by_id(tweet.region_id)


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
            topic_data[topic] = StatusIntervalTopic.from_tweets(topic_tweets)
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
                "positive_ratio": data.get_positive_ratio(),
                "average_sentiment": data.get_average_sentiment()
            })
        return result

    def validate_topic(self, topic_id):
        if topic_id not in self.topic_data:
            raise Exception("Invalid topic in this interval!")

    def get_topics(self):
        return list(self.topic_data.keys())

    def get_topic_data_per_region(self, topic_id):
        self.validate_topic(topic_id)
        return self.topic_data[topic_id].get_data_per_region()

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
            location_data[region.region_id] = StatusIntervalTopicRegion.from_tweets(region_tweets)
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
        return self.get_location_data(global_region.region_id)

    def get_location_data(self, location_id):
        return self.location_data[location_id]

    def get_data_per_region(self):
        result = []
        for region in self.location_data:
            data = self.location_data[region]
            result.append({
                "region_id": region,
                "popularity": data.get_popularity(),
                "overall_sentiment": data.get_overall_sentiment(),
                "average_sentiment": data.get_average_sentiment()
            })
        return result


class StatusIntervalTopicRegion:
    def __init__(self, popularity, nb_positive, nb_negative, nb_neutral, average_sentiment):
        self.popularity = popularity
        self.nb_positive = nb_positive
        self.nb_negative = nb_negative
        self.nb_neutral = nb_neutral
        self.average_sentiment = average_sentiment

    @classmethod
    def from_tweets(cls, tweets):
        popularity = len(tweets)
        nb_positive = sum([1 for tweet in tweets if tweet.positive_sentiment()])
        nb_negative = sum([1 for tweet in tweets if tweet.negative_sentiment()])
        nb_neutral = sum([1 for tweet in tweets if tweet.neutral_sentiment()])
        sentiments = [tweet.get_compound_sentiment() for tweet in tweets]
        average_sentiment = 0
        if len(tweets) > 0:
            average_sentiment = sum(sentiments) / len(sentiments)
        return StatusIntervalTopicRegion(popularity, nb_positive, nb_negative, nb_neutral, average_sentiment)

    @classmethod
    def from_dict(cls, data):
        popularity = data['popularity']
        nb_positive = data['nb_positive']
        nb_negative = data['nb_negative']
        nb_neutral = data['nb_neutral']
        average_sentiment = data['average_sentiment']
        return StatusIntervalTopicRegion(popularity, nb_positive, nb_negative, nb_neutral, average_sentiment)

    def get_dict(self):
        return {
            "popularity": self.popularity,
            "nb_positive": self.nb_positive,
            "nb_negative": self.nb_negative,
            "nb_neutral": self.nb_neutral,
            "average_sentiment": self.average_sentiment
        }

    def get_average_sentiment(self):
        return self.average_sentiment

    def get_popularity(self):
        return self.popularity

    def get_overall_sentiment(self):
        if self.nb_positive > max(self.nb_neutral, self.nb_negative):
            return 1
        if self.nb_negative > max(self.nb_neutral, self.nb_positive):
            return -1
        return 0

    def get_positive_ratio(self):
        if self.nb_positive == self.nb_negative == 0:
            return 0
        return self.nb_positive / (self.nb_positive + self.nb_negative)


class StatusAggregate:
    def __init__(self, intervals, short_term_start=None):
        # intervals: interval -> StatusInterval
        self.intervals = dict()
        for interval in intervals:
            self.intervals[interval] = intervals[interval]
        self.short_term_start = short_term_start
        if short_term_start is None:
            self.short_term_start = get_short_term_start()

    @classmethod
    def from_dict(cls, data):
        intervals = dict()
        for interval_data in data['intervals']:
            start_time = datetime.datetime.fromtimestamp(interval_data["start"])
            end_time = datetime.datetime.fromtimestamp(interval_data["end"])
            intervals[(start_time, end_time)] = StatusInterval.from_dict(interval_data)
        short_term_start = None
        if 'short_term_start' in data:
            short_term_start = datetime.datetime.fromtimestamp(data['short_term_start'])
        return StatusAggregate(intervals, short_term_start)

    def get_intervals(self):
        return self.intervals.keys()

    def to_dict(self):
        result = []
        for interval in self.intervals:
            interval_data = self.intervals[interval].get_dict()
            interval_data["start"] = interval[0].timestamp()
            interval_data["end"] = interval[1].timestamp()
            result.append(interval_data)

        return {
            "intervals": result,
            "short_term_start": self.short_term_start.timestamp()
        }

    def add_interval(self, interval, tweets):
        if interval in self.intervals:
            raise Exception("Interval {} already present in StatusAggregate".format(interval))
        tweets = get_tweets_between(tweets, interval[0], interval[1])
        self.intervals[interval] = StatusInterval.from_tweets(tweets)

    def get_long_intervals_data(self):
        short_start = get_short_term_start()
        return {interval: self.intervals[interval] for interval in self.intervals if interval[0] < short_start}

    def get_topics(self, interval):
        self.validate_interval(interval)
        return self.intervals[interval].get_topics()

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
        return self.get_topic_location_evolution(topic_id, global_region.get_id())

    def get_topic_location_evolution(self, topic_id, location_id):
        self.validate_topic(topic_id)
        self.validate_location(location_id)
        result = []
        for interval in self.intervals:
            interval_data = self.intervals[interval]
            data = {
                "interval_start": interval[0],
                "interval_end": interval[1]
            }
            if not interval_data.discusses_topic(topic_id):
                data["sentiment_distribution"] = {
                    "nb_positive": 0,
                    "nb_negative": 0,
                    "nb_neutral": 0
                }
                data["present"] = False
            else:
                global_data = interval_data.get_location_data_for_topic(topic_id, location_id)
                data["sentiment_distribution"] = {
                    "nb_positive": global_data.nb_positive,
                    "nb_negative": global_data.nb_negative,
                    "nb_neutral": global_data.nb_neutral
                }
                data["present"] = True
            result.append(data)
        left = 0
        while not result[left]["present"]:
            left += 1
        right = -1
        while not result[right]["present"]:
            right -= 1
        return result[left:right + 1]

    def get_topic_interval_data_per_region(self, topic_id, interval):
        self.validate_topic(topic_id)
        self.validate_interval(interval)
        return self.intervals[interval].get_topic_data_per_region(topic_id)

    def get_topic_interval_location_data(self, topic_id, interval, location_id):
        self.validate_topic(topic_id)
        self.validate_interval(interval)
        self.validate_location(location_id)
        # TODO: implement
        return None

    def validate_topic(self, topic_id):
        discussed = False
        for interval in self.intervals.values():
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
    try:
        with open(STATUS_FILE, 'r') as f:
            data = json.load(f)
            return StatusAggregate.from_dict(data)
    except Exception as ex:
        logging.error("Couldn't load status from disk: {}".format(ex))
        return StatusAggregate([])


def write_disk_status(status):
    with open(STATUS_FILE, 'w') as f:
        json.dump(status.to_dict(), f)

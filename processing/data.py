"""
Initial version loads data from files.
Better version loads file content to memory and updates on changes.
"""

from processing import db, get_last_interval, get_short_intervals, get_long_intervals_between, get_short_term_start, \
    Tweet
from processing import regions


def get_interval_filter(interval):
    return {"timestamp": {"$gt": interval[0].timestamp(), "$lt": interval[1].timestamp()}}


def get_topic_filter(topic):
    return {"topic": topic}


def get_children_locations_filter(location_id):
    all_region_ids = list(regions.get_all_sub_region_ids(location_id))
    return {"region_id": {"$in": all_region_ids}}


def get_tweets_in_interval(interval):
    return get_tweets(get_interval_filter(interval))


def get_tweets_in_interval_region_topic(interval, location_id, topic):
    query = dict()
    query.update(get_children_locations_filter(location_id))
    query.update(get_interval_filter(interval))
    query.update(get_topic_filter(topic))
    return get_tweets(query)


def get_tweets(query):
    tweets = db.tweets.find(query)
    return [Tweet.load_stripped_tweet(tweet) for tweet in tweets]


def count_tweets(query):
    return db.tweets.count(query)


def get_tweets_in_interval_for_topic(interval, topic):
    query = dict()
    query.update(get_interval_filter(interval))
    query.update(get_topic_filter(topic))
    return get_tweets(query)


def get_current_topics():
    interval = get_last_interval()
    return get_interval_topics(interval)


def get_earliest_time():
    tweet = Tweet.load_stripped_tweet(db.tweets.find_one(sort=[("timestamp", 1)]))
    return tweet.get_datetime()
    # TODO: use MongoDB min query
    # all_tweets = get_tweets({})
    # return min(tweet.get_datetime() for tweet in all_tweets)


def get_intervals():
    start_date = get_earliest_time()
    long_intervals = get_long_intervals_between(start_date, get_short_term_start())
    short_intervals = get_short_intervals()
    return long_intervals + short_intervals


def get_interval_topics(interval):
    return list({tweet.topic for tweet in get_tweets_in_interval(interval)})


class TweetsSummary:
    def __init__(self, popularity=0, nb_positive=0, nb_negative=0, nb_neutral=0, average_sentiment=0):
        self.popularity = popularity
        self.nb_positive = nb_positive
        self.nb_negative = nb_negative
        self.nb_neutral = nb_neutral
        self.average_sentiment = average_sentiment

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

    def get_dict(self):
        return {
            "popularity": self.popularity,
            "nb_positive": self.nb_positive,
            "nb_negative": self.nb_negative,
            "nb_neutral": self.nb_neutral,
            "average_sentiment": self.average_sentiment,
            "overall_sentiment": self.get_overall_sentiment(),
            "positive_ratio": self.get_positive_ratio()
        }


def get_tweets_summary(tweets):
    popularity = len(tweets)
    nb_positive = sum([1 for tweet in tweets if tweet.positive_sentiment()])
    nb_negative = sum([1 for tweet in tweets if tweet.negative_sentiment()])
    nb_neutral = sum([1 for tweet in tweets if tweet.neutral_sentiment()])
    sentiments = [tweet.get_compound_sentiment() for tweet in tweets]
    average_sentiment = 0
    if len(tweets) > 0:
        average_sentiment = sum(sentiments) / len(sentiments)

    return TweetsSummary(
        popularity=popularity,
        nb_positive=nb_positive,
        nb_negative=nb_negative,
        nb_neutral=nb_neutral,
        average_sentiment=average_sentiment
    )


def get_interval_topics_details(interval):
    topics = get_interval_topics(interval)
    topic_data = dict()
    for topic in topics:
        tweets = get_tweets_in_interval_for_topic(interval, topic)
        topic_data[topic] = get_tweets_summary(tweets)
    return topic_data


def get_global_topic_evolution(topic_id):
    interval_data = dict()
    for interval in get_intervals():
        tweets = get_tweets_in_interval_for_topic(interval, topic_id)
        interval_data[interval] = get_tweets_summary(tweets)
    return interval_data


def get_topic_location_evolution(topic_id, location_id):
    interval_data = dict()
    for interval in get_intervals():
        tweets = get_tweets_in_interval_region_topic(interval, location_id, topic_id)
        interval_data[interval] = get_tweets_summary(tweets)
    return interval_data


def get_topic_interval_data_per_region(topic_id, interval):
    region_data = dict()
    for region in regions.get_all_regions():
        tweets = get_tweets_in_interval_region_topic(interval, topic=topic_id, location_id=region.region_id)
        region_data[region.region_id] = get_tweets_summary(tweets)
    return region_data


def get_topic_interval_location_data(topic_id, interval, location_id):
    tweets = get_tweets_in_interval_region_topic(topic=topic_id, interval=interval, location_id=location_id)
    return get_tweets_summary(tweets)

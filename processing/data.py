"""
Initial version loads data from files.
Better version loads file content to memory and updates on changes.
"""

import datetime
import logging
import time

from processing import db, get_last_interval, Tweet, get_intervals
from processing import regions


def get_interval_filter(interval):
    return {"timestamp": {"$gt": interval[0].timestamp(), "$lt": interval[1].timestamp()}}


def get_topic_filter(topic):
    return {"topic": topic}


def get_children_locations_filter(location_id):
    all_region_ids = regions.get_region_by_id(location_id).get_all_sub_region_ids()
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
    logging.info("Getting tweets for query: {}".format(query))
    logging.info("Nb results: {}".format(count_tweets(query)))
    start_time = time.time()
    tweets = db.tweets.find(query)
    end_time = time.time()
    logging.info("Took {} seconds".format(end_time - start_time))
    return [Tweet.load_stripped_tweet(tweet) for tweet in tweets]


def count_tweets(query):
    return db.tweets.count(query)


def get_tweets_in_interval_for_topic(interval, topic):
    query = dict()
    query.update(get_interval_filter(interval))
    query.update(get_topic_filter(topic))
    return get_tweets(query)


def get_all_topics():
    logging.info("Getting all topics")
    res = db.tweets.distinct('topic', {})
    logging.info("Result size: {}".format(len(res)))
    res = [x for x in res if x is not None]
    return res


def get_current_topics():
    interval = get_last_interval()
    return get_interval_topics(interval)


def get_interval_string(interval):
    return "{}-{}".format(int(interval[0].timestamp()), int(interval[1].timestamp()))


def parse_interval_string(interval_string):
    part1, part2 = interval_string.split("-")
    return datetime.datetime.utcfromtimestamp(int(part1)), datetime.datetime.utcfromtimestamp(int(part2))


def get_interval_topics(interval):
    return list({tweet.topic for tweet in get_tweets_in_interval(interval)})


class TweetsSummary:
    def __init__(self, popularity=0, nb_positive=0, nb_negative=0, nb_neutral=0, average_sentiment=0):
        # assert (popularity == nb_positive + nb_negative + nb_neutral)
        self.popularity = popularity
        self.nb_positive = nb_positive
        self.nb_negative = nb_negative
        self.nb_neutral = nb_neutral
        self.average_sentiment = average_sentiment

    def get_relative_positive(self):
        return float(self.nb_positive) / self.popularity if self.popularity > 0 else 0

    def get_relative_neutral(self):
        return float(self.nb_neutral) / self.popularity if self.popularity > 0 else 0

    def get_relative_negative(self):
        return float(self.nb_negative) / self.popularity if self.popularity > 0 else 0

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

    def add_contributions(self, parent_summaries):
        total_sentiment = self.average_sentiment
        total_weight = 1
        for summary_descendants in parent_summaries:
            summary = summary_descendants[0]
            nb_descendants = summary_descendants[1]
            total_weight += summary.popularity / nb_descendants
            self.nb_positive += summary.nb_positive / nb_descendants
            self.nb_neutral += summary.nb_neutral / nb_descendants
            self.nb_negative += summary.nb_negative / nb_descendants
            self.popularity += summary.popularity / nb_descendants
            total_sentiment += summary.average_sentiment / nb_descendants * summary.popularity
        self.average_sentiment = total_sentiment / total_weight


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
    # logging.info("get_interval_topics_details!")
    topics = get_interval_topics(interval)
    all_tweets = get_tweets_in_interval(interval)
    topic_data = dict()
    for topic in topics:
        # tweets = get_tweets_in_interval_for_topic(interval, topic)
        tweets = [tweet for tweet in all_tweets if tweet.topic == topic]
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
    all_regions = regions.get_all_regions()
    leaf_regions = [region for region in all_regions if region.is_leaf()]
    non_leaf_regions = [region for region in all_regions if not region.is_leaf()]

    all_tweets = get_tweets_in_interval_for_topic(interval, topic_id)

    non_leaf_start = time.time()
    parent_data = dict()
    for region in non_leaf_regions:
        tweets = [t for t in all_tweets if t.region_id == region.region_id]
        parent_data[region.region_id] = get_tweets_summary(tweets)
    non_leaf_end = time.time()

    region_data = dict()
    for region in leaf_regions:
        tweets = [t for t in all_tweets if t.region_id == region.region_id]
        total_summary = get_tweets_summary(tweets)
        parent_contributions = [
            (parent_data[ancestor_region.region_id], ancestor_region.get_number_of_leaf_descendants()) for
            ancestor_region in region.get_ancestors()]
        total_summary.add_contributions(parent_contributions)
        region_data[region.region_id] = total_summary

    leaf_end = time.time()
    logging.info("Non-leaf regions: {} seconds".format(non_leaf_end - non_leaf_start))
    logging.info("Leaf regions: {} seconds".format(leaf_end - non_leaf_end))
    return region_data


def get_topic_interval_location_data(topic_id, interval, location_id):
    tweets = get_tweets_in_interval_region_topic(topic=topic_id, interval=interval, location_id=location_id)
    return get_tweets_summary(tweets)

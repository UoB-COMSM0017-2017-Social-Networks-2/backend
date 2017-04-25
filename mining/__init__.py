# Import the necessary methods from tweepy library
import _thread
import glob
import html
import json
import logging
import os
import time

from tweepy import API
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

import mining.authentication
from helpers.topics import Topic, get_static_topics
from main import app
from processing import scripts

MINING_TWEET_JSON_FILE = 'output/tweetlocation.json'
STORING_INTERVAL = app.config['STORING_INTERVAL'] if 'STORING_INTERVAL' in app.config else 60 * 10  # 10 minutes

COUNTRY_ID = '23424975'  # UK
streaming_regions = [{
    "name": "South West England",
    "bounding_box": [-5.71, 49.71, -0.62, 53.03]
}, {
    "name": "South East England",
    "bounding_box": [-0.56, 50.77, 1.83, 53.07]
}, {
    "name": "Central UK",
    "bounding_box": [-5.38, 53.09, 0.53, 55.15]
}, {
    "name": "Northern UK",
    "bounding_box": [-7.48, 55.21, -0.35, 61.05]
}, {
    "name": "Northern Ireland",
    "bounding_box": [-10.5359, 53.2586, -5.2823, 55.2102]
}, {
    "name": "Southern Ireland",
    "bounding_box": [-10.83, 51.22, -5.57, 53.27]
}]

TrendingTopics = []
StaticTopics = []
startTime = time.time()

# timeLimit = 60  # 1/2 hour limit

MINUTES_PER_QUERY = 1
QUERIES_PER_BATCH = 2


class StdOutListener(StreamListener):
    topics = []

    # On every tweet arrival
    def on_data(self, data):
        data = json.loads(html.unescape(data))
        # Gives the content of the tweet.
        tweet = str(data['text']) if 'text' in data else None
        if tweet is None:
            logging.error("Found empty tweet: {}".format(json.dumps(data)))
            return True

        # If tweet content contains any of the trending topic.
        for topic in StdOutListener.topics:
            if topic.tweet_is_about_topic(tweet):
                logging.info("Received relevant tweet ({}): {}".format(topic.topic_name, tweet))
                data['TrendingTopic'] = topic.topic_name
                with open(MINING_TWEET_JSON_FILE, 'a') as tf:
                    tf.write(json.dumps(data) + '\n')
        return True

    def on_error(self, status):
        logging.error("Received streaming error: {}".format(status))


import processing.update


def send_tweets(tweets_file=MINING_TWEET_JSON_FILE, move_old=False):
    logging.info("SENDING TWEETS!")
    try:
        with open(tweets_file, 'r') as f:
            for line in f.readlines():
                if len(line.strip()) == 0:
                    continue
                try:
                    tweet = json.loads(line.strip())
                    processing.update.process_new_tweets([tweet])
                except Exception as ex:
                    logging.error(ex)
                    logging.error("error for tweet: {}".format(line))
        if move_old:
            os.rename(tweets_file, "{}_{}".format(tweets_file, time.time()))
    except Exception as ex:
        logging.warning("Processing tweets failed, continuing!")
        logging.warning(ex)


def stream_tweets_for_region(name, bounding_box, consumer_keys, user_keys):
    logging.info("Streaming tweets for {}".format(name))
    consumer_key = consumer_keys['CONSUMER_KEY']
    consumer_secret = consumer_keys['CONSUMER_SECRET']
    access_token = user_keys['ACCESS_TOKEN']
    access_secret = user_keys['ACCESS_SECRET']
    # This handles Twitter authentication and the connection to Twitter Streaming API
    while True:
        try:
            l = StdOutListener()
            auth = OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_secret)
            stream = Stream(auth, l)
            stream.filter(locations=bounding_box)
        except:
            logging.error("Need to restart for {}".format(name))


def send_all_old_tweets_thread():
    logging.info("Start storing old tweets")
    tweet_files = glob.glob(MINING_TWEET_JSON_FILE + "_*")
    for tweet_filename in tweet_files:
        send_tweets(tweet_filename, move_old=False)
    logging.info("Done storing old tweets")
    logging.info("MongoDB population DONE")
    logging.info("Starting to run cleanup functions")
    logging.info("Remove irrelevant tweets:")
    scripts.remove_irrelevant_tweets()
    logging.info("Done")
    logging.info("Update sentiment and region classification")
    scripts.update_sentiment_and_region_classification()
    logging.info("Done")


def send_all_old_tweets():
    _thread.start_new_thread(send_all_old_tweets_thread, ())


def start_mining():
    _thread.start_new_thread(master_mining_thread, ())


def start_region_threads(consumer_keys, mining_keys):
    min_length = min(len(streaming_regions), len(mining_keys))
    logging.debug("Found {} regions and key tuples".format(min_length))
    for region, user_keys in zip(streaming_regions[:min_length], mining_keys[:min_length]):
        _thread.start_new_thread(stream_tweets_for_region, (region['name'], region['bounding_box'], consumer_keys, {
            "ACCESS_TOKEN": user_keys[0],
            "ACCESS_SECRET": user_keys[1]
        }))
        time.sleep(10)


def get_trending_topics(consumer_key, consumer_secret, access_token, access_secret):
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    api = API(auth)
    api_trend_data = api.trends_place(COUNTRY_ID)
    data = api_trend_data[0]
    trends = data['trends']
    return [Topic(trend['name']) for trend in trends[:10]]


def update_all_topics(static_topics, consumer_keys, mining_keys):
    trending_topics = get_trending_topics(consumer_keys['CONSUMER_KEY'], consumer_keys['CONSUMER_SECRET'],
                                          mining_keys[0][0], mining_keys[0][1])
    StdOutListener.topics = trending_topics + static_topics
    logging.info("All topics are now: {}".format([x.topic_name for x in StdOutListener.topics]))


def master_mining_thread():
    consumer_keys = {
        "CONSUMER_KEY": app.config['TWITTER_CONSUMER_KEY'],
        "CONSUMER_SECRET": app.config['TWITTER_CONSUMER_SECRET']
    }
    static_topics = get_static_topics()
    mining_keys = mining.authentication.get_authentication_keys()
    logging.debug("Mining keys: {}".format(mining_keys))
    update_all_topics(static_topics, consumer_keys, mining_keys)
    start_region_threads(consumer_keys, mining_keys)
    while True:
        send_tweets(move_old=True)
        update_all_topics(static_topics, consumer_keys, mining_keys)
        time.sleep(STORING_INTERVAL)


if __name__ == '__main__':
    start_mining()

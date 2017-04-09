"""
Store tweets more recent than SHORT_TERM in .json file
Older tweets that are passed to process_new_tweets are discarded.
Newer tweets are taken into account.
"""

from processing import Tweet
from processing import db


def get_tweet_by_twitter_id(tweet_id):
    return db.tweets.find_one({"tweet_id": tweet_id})


def insert_tweet(tweet):
    db.tweets.insert_one(tweet.get_full_dict())


def store_new_tweets(new_tweets_original):
    for tweet_obj in new_tweets_original:
        tweet = Tweet.load_raw_tweet(tweet_obj)
        if get_tweet_by_twitter_id(tweet.tweet_id) is not None:
            # logging.warning("Tweet {} already present".format(tweet.tweet_id))
            continue
        insert_tweet(tweet)
        # logging.info("Storing new tweets DONE")


def process_new_tweets(new_tweets_original):
    # logging.info("Processing new tweets!")
    store_new_tweets(new_tweets_original)
    # logging.info("Processing new tweets DONE")

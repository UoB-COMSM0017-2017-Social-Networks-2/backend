import logging

import click

from helpers.topics import get_static_topics, transform_topic_name
from main import app
from helpers.tweet import Tweet
from processing.database import db


@app.cli.command()
def cli_update_sentiment_and_region_classification():
    click.echo("Running update_region_and_topic_classification")
    update_sentiment_and_region_classification()
    click.echo("Done")


def update_sentiment_and_region_classification():
    cursor = db.tweets.find({})
    for t in cursor:
        tweet = Tweet.load_stripped_tweet(t)
        tweet.process()
        db.tweets.update_one({"_id": tweet.id}, {"$set": tweet.get_full_dict()})


@app.cli.command()
def cli_remove_irrelevant_tweets():
    click.echo("Running remove_irrelevant_tweets")
    nb_invalid_classification, nb_no_topics, nb_transformed_topic_names = remove_irrelevant_tweets()
    click.echo("Removed {} because they were assigned to an invalid topic".format(nb_invalid_classification))
    click.echo("Removed {} because they had no topic assigned".format(nb_no_topics))
    click.echo("Removed {} because they had an invalid topic name".format(nb_transformed_topic_names))
    click.echo("Done")


def remove_irrelevant_tweets():
    cursor = db.tweets.find({})
    static_topics = get_static_topics()
    static_topics = {topic.topic_name: topic for topic in static_topics}
    nb_invalid_classification = 0
    nb_no_topics = 0
    nb_transformed_topic_names = 0
    for t in cursor:
        tweet = Tweet.load_stripped_tweet(t)
        if tweet.topic in static_topics:
            if static_topics[tweet.topic].tweet_is_about_topic(tweet.text):
                continue
            logging.info("Invalid topic classification ({}) for tweet {}".format(tweet.topic, tweet.text))
            for topic_name, topic in static_topics.items():
                if topic.tweet_is_about_topic(tweet.text):
                    logging.info("Instead classifying as {}".format(topic_name))
                    current = db.tweets.find_one({"tweet_id": tweet.tweet_id, "topic": topic_name})
                    if current is not None:
                        logging.info("Already present")
                        continue
                    logging.info("Newly added")
                    updated_dict = tweet.get_full_dict()
                    updated_dict["topic"] = topic_name
                    db.tweets.insert_one(updated_dict)
            nb_invalid_classification += 1
            db.tweets.delete_one({"_id": tweet.id})
        elif tweet.topic is None:
            nb_no_topics += 1
            db.tweets.delete_one({"_id": tweet.id})
        else:
            transformed_topic = transform_topic_name(tweet.topic)
            if transformed_topic == tweet.topic:
                continue
            db.tweets.delete_one({"_id": tweet.id})
            nb_transformed_topic_names += 1
            if db.tweets.find_one({"tweet_id": tweet.tweet_id, "topic": transformed_topic}) is not None:
                continue
            updated_dict = tweet.get_full_dict()
            updated_dict["topic"] = transformed_topic
            if db.tweets.find_one({"tweet_id": tweet.tweet_id, "topic": transformed_topic}) is not None:
                continue
            db.tweets.insert_one(updated_dict)

    return nb_invalid_classification, nb_no_topics, nb_transformed_topic_names

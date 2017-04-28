from pymongo import MongoClient

from main import app

mongo = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
db = mongo.database

import logging

from pymongo import ASCENDING, errors

db.tweets.create_index("tweet_id")
try:
    db.tweets.create_index([("tweet_id", ASCENDING), ("topic", ASCENDING)], unique=True)
except errors.DuplicateKeyError as err:
    logging.error("Failed to create a unique index: {}".format(err))

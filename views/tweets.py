from flask import jsonify

from main import app
from processing import data


@app.route('/tweets/<string:interval>/download.json')
def download_tweets_for_interval(interval):
    tweets = data.get_tweets_in_interval(data.parse_interval_string(interval))
    return jsonify([
        tweet.get_full_dict() for tweet in tweets
    ])

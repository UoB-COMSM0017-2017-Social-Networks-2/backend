# Import the necessary methods from tweepy library
import _thread
import html
import json
import subprocess
import time

from tweepy import API
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

import mining.authentication
from main import app
from processing.update import process_new_tweets

MINING_TWEET_JSON_FILE = 'output/tweetlocation.json'

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
# count = 0;
startTime = time.time()


# timeLimit = 60  # 1/2 hour limit

# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    # On every tweet arrival
    def on_data(self, data):
        global startTime, TrendingTopics
        original_data = data
        if ((time.time() - startTime) < (60 * 15)):
            # Convert the string data to pyhton json object.
            data = json.loads(html.unescape(data))
            # Gives the content of the tweet.
            tweet = data['text']
            # print(json.dumps(tweet))
            # If tweet content contains any of the trending topic.
            for topic in TrendingTopics:
                if (topic in json.dumps(tweet)):
                    print("Received relevant tweet: {}".format(str(tweet)))
                    data['TrendingTopic'] = topic
                    with open(MINING_TWEET_JSON_FILE, 'a') as tf:
                        tf.write(original_data)
            return True
        else:
            startTime = time.time()
            return False

    def on_error(self, status):
        print(status)


def send_tweets():
    print("SENDING TWEETS!")
    tweets = []
    with open(MINING_TWEET_JSON_FILE, 'r') as f:
        for line in f.readlines():
            if len(line.strip()) == 0:
                continue
            tweets.append(json.loads(line))
    process_new_tweets(tweets)

    # This runs the system command of transfering file to s3 bucket
    proc = subprocess.Popen(["aws", "s3", "cp", MINING_TWEET_JSON_FILE, "s3://sentiment-bristol"],
                            stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print("program output:", out)
    # Remove file
    proc = subprocess.Popen(["rm", MINING_TWEET_JSON_FILE], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print("Removed JSON: {}".format(out))


def stream_tweets_for_region(name, bounding_box, consumer_keys, user_keys):
    global TrendingTopics
    print("Streaming tweets for {}".format(name))
    consumer_key = consumer_keys['CONSUMER_KEY']
    consumer_secret = consumer_keys['CONSUMER_SECRET']
    access_token = user_keys['ACCESS_TOKEN']
    access_secret = user_keys['ACCESS_SECRET']
    # print("\n ########################################## Data mining for location : ", location, "started ########################################## \n")
    # print(startTime)
    count = 0
    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    api = API(auth)
    stream = Stream(auth, l)

    while True:

        # # send data to s3 every 5th hour
        # # only one thread is required to write data to s3 bucket
        if count % 5 == 0 and name == streaming_regions[0]['name']:
            try:
                send_tweets()
            except:
                print("An error occurred sending tweets, keeping all data for now!")

        count += 1
        # This runs every an hour
        print('\n************************* Tweet Collection for next {0} hours started *************************\n'
              .format(count / 2))

        trends1 = api.trends_place(COUNTRY_ID)
        data = trends1[0]
        # grab the trends
        trends = data['trends']
        # grab the name from each trend
        TrendingTopics = [trend['name'] for trend in trends[:10]]
        # put all the names together with a ' ' separating them
        print("Trending Topics: {}".format(TrendingTopics))
        # Stream the tweets for given location coordinates
        stream.filter(locations=bounding_box)


def start_mining():
    _thread.start_new_thread(start_threads, ())


def start_threads():
    try:
        consumer_keys = {
            "CONSUMER_KEY": app.config['TWITTER_CONSUMER_KEY'],
            "CONSUMER_SECRET": app.config['TWITTER_CONSUMER_SECRET']
        }
        mining_keys = mining.authentication.get_authentication_keys()
        # min_length = min(len(streaming_regions), len(app.config['MINING_KEYS']))
        min_length = min(len(streaming_regions), len(mining_keys))
        print("Found {} regions and key tuples".format(min_length))
        # for region, user_keys in zip(streaming_regions[:min_length], app.config['MINING_KEYS'][:min_length]):
        for region, user_keys in zip(streaming_regions[:min_length], mining_keys[:min_length]):
            _thread.start_new_thread(stream_tweets_for_region, (region['name'], region['bounding_box'], consumer_keys, {
                "ACCESS_TOKEN": user_keys[0],
                "ACCESS_SECRET": user_keys[1]
            }))
            time.sleep(60)
    except Exception as ex:
        print("Error: unable to start the thread: {}".format(ex))

    while 1:
        pass


if __name__ == '__main__':
    start_mining()

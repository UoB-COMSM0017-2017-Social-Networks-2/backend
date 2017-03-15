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

from main import app

# sample woeid code for countries USA, UK, Brazil, Canada, India
# woeidList = ['23424977','23424975','23424768', '23424775', '23424848']
woeidList = ['23424975']  # Used to fetch trending topics
# sample location bounding box coordinates of south west england
location = [-5.71, 49.71, -0.62, 53.03]  # Used to fetch all tweets for this location
# south east england
location1 = [-0.56, 50.77, 1.83, 53.07]
# central uk
location2 = [-5.38, 53.09, 0.53, 55.15]
# north uk
location3 = [-7.48, 55.21, -0.35, 61.05]
# north Ireland
location4 = [-10.5359, 53.2586, -5.2823, 55.2102]
# south Ireland
location5 = [-10.83, 51.22, -5.57, 53.27]
# location1 = [-87.122124,33.38376,-86.57815,33.678715]

TrendingTopics = []
# count = 0;
startTime = time.time()


# timeLimit = 60  # 1/2 hour limit

# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    # On every tweet arrival
    def on_data(self, data):
        global startTime, TrendingTopics
        if ((time.time() - startTime) < (60 * 15)):
            # Convert the string data to pyhton json object.
            data = json.loads(html.unescape(data))
            # Gives the content of the tweet.
            tweet = data['text']
            # print(json.dumps(tweet))
            # If tweet content contains any of the trending topic.
            if any(topic in json.dumps(tweet) for topic in TrendingTopics):
                # Add trending topic and original bounding box as attribute
                # data['TrendingTopic'] = topic
                print(json.dumps(tweet))
                # data['QueriedBoundingBox'] = location[0]
                # Convert the json object again to string
                dataObj = json.dumps(data)
                # Appending the data in tweetlondon.json file
                with open('tweetlocation.json', 'a') as tf:
                    tf.write(dataObj)
                    # prints on console
            return True
        else:
            startTime = time.time();
            return False

    def on_error(self, status):
        print(status)


def StreamTheTweets(consumerKey, consumerSecret, accessToken, accessSecret, location):
    global TrendingTopics
    # print("\n ########################################## Data mining for location : ", location, "started ########################################## \n")
    # print(startTime)
    count = 0
    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumerKey, consumerSecret)
    auth.set_access_token(accessToken, accessSecret)

    api = API(auth)
    stream = Stream(auth, l)

    while True:
        count = count + 1
        # This runs every an hour
        print(
            '\n ****************************************** Tweet Collection for next {0} hours started ************************************************************** \n'.format(
                count / 2))
        print(count)

        # for country in location:
        for country in woeidList:
            trends1 = api.trends_place(country)
            data = trends1[0]
            # grab the trends
            trends = data['trends']
            # grab the name from each trend
            TrendingTopics = [trend['name'] for trend in trends[:10]]
            # put all the names together with a ' ' separating them
            # trendsName = ' '.join(names)
            # print("\n &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& Trending topic for this time are &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
            print(TrendingTopics, "\n")
            # Stream the tweets for given location coordinates
            stream.filter(locations=[location[0], location[1], location[2], location[3]])

    # # send data to s3 every 5th hour
    # # only one thread is required to write data to s3 bucket
    if (count % 5 == 0 and count != 0 and location[1] == 49.71):
        # This runs the system command of transfering file to s3 bucket
        proc = subprocess.Popen(["aws", "s3", "cp", "tweetlocation.json", "s3://sentiment-bristol"],
                                stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print("program output:", out)


# multithreading function
def multiThreading(threadName):
    if threadName == "SouthWestEngland":
        StreamTheTweets(app.config['BEN_CONSUMER_KEY'], app.config['BEN_CONSUMER_SECRET'],
                        app.config['BEN_ACCESS_TOKEN'], app.config['BEN_ACCESS_TOKEN_SECRET'], location)

    elif threadName == "SouthEastEngland":
        StreamTheTweets(app.config['JULIAN_CONSUMER_KEY'], app.config['JULIAN_CONSUMER_SECRET'],
                        app.config['JULIAN_ACCESS_TOKEN'], app.config['JULIAN_ACCESS_TOKEN_SECRET'], location1)

    elif threadName == "CentralUk":
        StreamTheTweets(app.config['HOLI_CONSUMER_KEY'], app.config['HOLI_CONSUMER_SECRET'],
                        app.config['HOLI_ACCESS_TOKEN'], app.config['HOLI_ACCESS_TOKEN_SECRET'], location2)

    elif threadName == "NorthUK":
        StreamTheTweets(app.config['KANU_CONSUMER_KEY'], app.config['KANU_CONSUMER_SECRET'],
                        app.config['KANU_ACCESS_TOKEN'], app.config['KANU_ACCESS_TOKEN_SECRET'], location3)

    elif threadName == "NorthIreland":
        StreamTheTweets(app.config['FLORIS_CONSUMER_KEY'], app.config['FLORIS_CONSUMER_SECRET'],
                        app.config['FLORIS_ACCESS_TOKEN'], app.config['FLORIS_ACCESS_TOKEN_SECRET'], location4)

    elif threadName == "SouthIreland":
        StreamTheTweets(app.config['VISHAL_CONSUMER_KEY'], app.config['VISHAL_CONSUMER_SECRET'],
                        app.config['VISHAL_ACCESS_TOKEN'], app.config['VISHAL_ACCESS_TOKEN_SECRET'], location5)


if __name__ == '__main__':

    try:
        _thread.start_new_thread(multiThreading, ("SouthWestEngland",))
        time.sleep(10)
        _thread.start_new_thread(multiThreading, ("SouthEastEngland",))
        time.sleep(10)
        _thread.start_new_thread(multiThreading, ("CentralUk",))
        time.sleep(10)
        _thread.start_new_thread(multiThreading, ("NorthUK",))
        time.sleep(10)
        _thread.start_new_thread(multiThreading, ("NorthIreland",))
        time.sleep(10)
        _thread.start_new_thread(multiThreading, ("SouthIreland",))
    except:
        print("Error: unable to start the thread")

    while 1:
        pass

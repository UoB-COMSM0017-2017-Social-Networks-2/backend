import logging

from nltk.sentiment.vader import SentimentIntensityAnalyzer

sid = SentimentIntensityAnalyzer()


def get_tweet_sentiment(tweet):
    polarity_scores = sid.polarity_scores(tweet['text'])
    return {
        "pos": polarity_scores['pos'],
        "neg": polarity_scores['neg'],
        "neu": polarity_scores['neu'],
        "compound": polarity_scores['compound']
    }

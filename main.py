import logging

from flask import Flask

import mining

app = Flask("SN2", template_folder='templates')
app.config.from_pyfile('config.cfg')
logging.basicConfig(level=app.config['LOGGING_LEVEL'])

from flask_oauthlib.client import OAuth

oauth = OAuth()
twitter = oauth.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=app.config['TWITTER_CONSUMER_KEY'],
    consumer_secret=app.config['TWITTER_CONSUMER_SECRET'],
)


@twitter.tokengetter
def get_twitter_token():
    return session.get('twitter_token')


from views import *


def main():
    logging.info("Starting mining")
    mining.start_mining()
    logging.info("Starting Flask Application.")
    app.run(host=app.config['HOSTNAME'], port=int(app.config['PORT']))
    logging.info("Flask application stopped running.")


if __name__ == "__main__":
    main()

import json

from flask import url_for, request, redirect, flash, session

from main import app, twitter


@app.route('/twitter_authentication')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
                                              next=request.args.get('next') or request.referrer or None))


def store_credentials(user, token, secret):
    session['twitter_token'] = (token, secret)
    session['twitter_user'] = user
    with open('output/keys.json', 'w+') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = dict()
        data[user] = (token, secret)
        json.dump(data, f)


@app.route('/oauth_authorized')
def oauth_authorized():
    next_url = request.args.get('next') or url_for('index')
    resp = twitter.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
    store_credentials(user=resp['screen_name'], token=resp['oauth_token'], secret=resp['oauth_token_secret'])
    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)

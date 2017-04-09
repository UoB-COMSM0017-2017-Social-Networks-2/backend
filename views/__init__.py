from flask import render_template

from main import app
from processing.data import get_tweets
from views.authentication import *
from views.data import *


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/application')
def application():
    return render_template('application.html')


@app.route('/stats')
def stats():
    all_tweets = get_tweets({})
    return jsonify({
        "nb_tweets": len(all_tweets)
    })

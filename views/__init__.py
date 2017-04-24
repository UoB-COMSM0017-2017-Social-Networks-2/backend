from main import app
from processing.data import count_tweets
from views.authentication import *
from views.data import *
from views.sitemap import *


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/application')
def application():
    return render_template('application.html')


@app.route('/stats')
def stats():
    return jsonify({
        "nb_tweets": count_tweets({})
    })

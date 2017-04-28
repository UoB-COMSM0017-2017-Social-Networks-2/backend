import time

import processing
import processing.intervals
from main import app
from processing.data import count_tweets
from views.authentication import *
from views.data import *
from views.sitemap import *
from views.tweets import *


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/application')
def application():
    step = int(processing.intervals.LONG_INTERVAL_LENGTH.total_seconds())
    intervals = sorted(processing.intervals.get_intervals())
    logging.info(intervals)
    start = int(intervals[0][0].timestamp())
    end = int(intervals[-1][0].timestamp())
    logging.info("start, end, step: {} {} {}".format(start, end, step))
    return render_template('application.html', step=step, start=start, end=end, timestamp=time.time())


@app.route('/stats')
def stats():
    return jsonify({
        "nb_tweets": count_tweets({})
    })

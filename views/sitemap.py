import logging

from flask import render_template

from main import app
from processing import data, regions


@app.route('/sitemap')
def show_sitemap():
    return render_template('sitemap/sitemap.html')


@app.route('/sitemap/topics/all')
def show_sitemap_all_topics():
    all_topics = data.get_all_topics()
    logging.debug("All topics: {}".format(all_topics))
    return render_template('sitemap/all_topics.html', all_topics=all_topics)


def get_all_intervals_as_strings():
    return [data.get_interval_string(interval) for interval in data.get_intervals()]


@app.route('/sitemap/topic/<string:topic_id>/details')
def show_sitemap_topic_details(topic_id):
    all_locations = regions.get_all_regions()
    return render_template('sitemap/topic_details.html',
                           topic_id=topic_id,
                           all_locations=all_locations,
                           all_intervals=get_all_intervals_as_strings())


@app.route('/sitemap/intervals/all')
def show_sitemap_all_intervals():
    all_intervals = [
        (interval[0].isoformat(), interval[1].isoformat(), data.get_interval_string(interval))
        for interval in data.get_intervals()
    ]
    return render_template('sitemap/all_intervals.html', all_intervals=all_intervals)


@app.route('/sitemap/regions/all')
def show_sitemap_all_regions():
    all_regions = regions.get_all_regions()
    return render_template('sitemap/all_regions.html', all_regions=all_regions)

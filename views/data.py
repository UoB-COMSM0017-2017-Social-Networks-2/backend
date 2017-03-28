import csv
import datetime
import io

from flask import make_response, jsonify

from main import app
from processing import data, regions


def parse_interval_string(interval_string):
    part1, part2 = interval_string.split("-")
    return datetime.datetime.utcfromtimestamp(int(part1)), datetime.datetime.utcfromtimestamp(int(part2))


def interval_to_string(interval):
    return "{}-{}".format(int(interval[0].timestamp()), int(interval[1].timestamp()))


def output_csv_file(filename, data):
    sio = io.StringIO()
    cw = csv.writer(sio)
    for r in data:
        cw.writerow(r)
    output = make_response(sio.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/topics.json')
def get_current_topics():
    """
    :return: List of topics that are currently being monitored as JSON response.
    """
    topics = data.get_current_topics()
    return jsonify({
        "topics": topics
    })


@app.route('/intervals.json')
def get_intervals():
    """
    :return: List of available intervals
    """
    intervals = data.get_intervals()
    return jsonify({
        "intervals": sorted([interval_to_string(interval) for interval in intervals])
    })


@app.route('/interval/<string:interval>/topics.json')
def get_interval_topics(interval):
    """
    :param interval:
    :return: List of topics that were monitored during interval as JSON response.
    """
    topics = data.get_interval_topics(parse_interval_string(interval))
    return jsonify({
        "topics": topics
    })


@app.route('/topic/<string:topic_id>/evolution.csv')
@app.route('/stream_chart/<string:topic_id>/evolution.csv')
def get_topic_evolution(topic_id):
    """
    :param topic_id:
    :return: Evolution of global topic popularity and sentiment over time as CSV response.
    """
    return get_topic_location_evolution(topic_id, regions.get_global_region().region_id)


@app.route('/topic/<string:topic_id>/location/<string:location_id>/evolution.csv')
@app.route('/stream_chart/<string:topic_id>/location/<string:location_id>/evolution.csv')
def get_topic_location_evolution(topic_id, location_id):
    """
    :param topic_id:
    :param location_id:
    :return: Evolution of local topic popularity and sentiment over time as CSV response.
    """
    topic_evolution = data.get_topic_location_evolution(topic_id, location_id)
    pos_lines = []
    neg_lines = []
    neut_lines = []
    for interval in topic_evolution:
        timestamp = (interval["interval_start"] +
                     (interval["interval_end"] - interval["interval_start"]) / 2)
        pos_lines.append(
            ["POS", interval["sentiment_distribution"]["nb_positive"], timestamp])
        neut_lines.append(
            ["NEUT", interval["sentiment_distribution"]["nb_neutral"], timestamp])
        neg_lines.append(
            ["NEG", interval["sentiment_distribution"]["nb_negative"], timestamp])
    data_array = pos_lines + neut_lines + neg_lines
    return output_csv_file("evolution.csv", data_array)


@app.route('/topics/interval/<string:interval>/data.csv')
@app.route('/bubble_chart/<string:interval>/data.csv')
def get_interval_topics_details(interval):
    """
    :param interval:
    :return: Popularity and overall sentiment of all topics in interval as a CSV response.
    """
    topics_details = data.get_interval_topics_details(parse_interval_string(interval))
    data_array = [("TOPIC", "TOPIC", "Popularity", "Overall sentiment", "Positive ratio", "Average sentiment")] + \
                 [(topic["topic"], topic["topic"], topic["nb_tweets"], topic["overall_sentiment"],
                   topic["positive_ratio"], topic["average_sentiment"])
                  for topic in topics_details]
    return output_csv_file("data.csv", data_array)


@app.route('/topic/<string:topic_id>/interval/<string:interval>.csv')
def get_topic_interval_data(topic_id, interval):
    """
    :param topic_id:
    :param interval:
    :return: Local sentiment and popularity of topic in interval for each region as a CSV response.
    """
    topic_interval_data = data.get_topic_interval_data_per_region(topic_id, parse_interval_string(interval))
    data_array = [["Region ID", "Popularity", "Average sentiment", "Overall sentiment"]]
    for record in topic_interval_data:
        data_array.append([
            record["region_id"], record["popularity"], record["average_sentiment"], record["overall_sentiment"]
        ])
    return output_csv_file("{}.csv".format(interval), data_array)


@app.route('/topic/<string:topic_id>/interval/<string:interval>/location/<string:location_id>/data.json')
def get_topic_interval_location_data(topic_id, interval, location_id):
    """
    :param topic_id:
    :param interval:
    :param location_id:
    :return: Local sentiment and popularity of topic in interval for specific region as CSV response.
    """
    topic_interval_location_data = data.get_topic_interval_location_data(topic_id, parse_interval_string(interval),
                                                                         location_id)
    return jsonify({
        "data": topic_interval_location_data
    })

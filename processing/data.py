"""
Initial version loads data from files.
Better version loads file content to memory and updates on changes.
"""
import logging

import processing.status
from main import app


def load_status():
    if not hasattr(app, 'status_structure'):
        app.status_structure = processing.status.load_disk_status()
    return app.status_structure


def get_current_topics():
    status = load_status()
    interval = status.get_last_interval()
    logging.info("Last interval: {}".format(interval))
    return status.get_topics(interval)


def get_intervals():
    status = load_status()
    return status.get_intervals()


def get_interval_topics(interval):
    status = load_status()
    return status.get_topics(interval)


def get_interval_topics_details(interval):
    status = load_status()
    return status.get_topic_details_for_interval(interval)


def get_global_topic_evolution(topic_id):
    status = load_status()
    return status.get_global_topic_evolution(topic_id)


def get_topic_location_evolution(topic_id, location_id):
    status = load_status()
    return status.get_topic_location_evolution(topic_id, location_id)


def get_topic_interval_data_per_region(topic_id, interval):
    status = load_status()
    return status.get_topic_interval_data_per_region(topic_id, interval)


def get_topic_interval_location_data(topic_id, interval, location_id):
    status = load_status()
    return status.get_topic_interval_location_data(topic_id, interval, location_id)

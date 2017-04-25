import json


class Topic:
    def __init__(self, topic_name, tags=None):
        self.topic_name = transform_topic_name(topic_name)
        self.tags = tags
        if tags is None:
            self.tags = [topic_name]

    def tweet_is_about_topic(self, text):
        for tag in self.tags:
            if tag in text.lower().split():
                return True
        return False


def get_static_topics():
    with open('data/ads_topics.json', 'r') as staticTopicData:
        d = json.load(staticTopicData)
    return [Topic(x['name'], x['queries']) for x in d]


def transform_topic_name(t):
    if t[:1] == "#":
        t = t[1:]
    t = "".join(t.split())
    return t.lower()

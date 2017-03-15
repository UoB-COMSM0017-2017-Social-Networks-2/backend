import json


def get_authentication_keys():
    try:
        with open('output/keys.json', 'r') as f:
            data = json.load(f)
            return list(data.values())
    except:
        return []

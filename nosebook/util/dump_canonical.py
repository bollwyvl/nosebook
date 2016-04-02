import json


def dump_canonical(obj):
    return json.dumps(obj, indent=2, sort_keys=True)

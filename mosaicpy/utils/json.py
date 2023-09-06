import json


def load_jsonl(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]


def dump_jsonl(file_path, data):
    with open(file_path, 'w') as f:
        for line in data:
            f.write(json.dumps(line) + '\n')

import json


def load_jsonl(file_path, cb_func=None, skip_none=False):
    with open(file_path, 'r') as f:
        data = []
        for line in f:
            line = json.loads(line)

            if cb_func is not None:
                line = cb_func(line)

            if skip_none and line is None:
                continue

            data.append(line)
        return data


def dump_jsonl(file_path, data):
    with open(file_path, 'w') as f:
        for line in data:
            f.write(json.dumps(line) + '\n')

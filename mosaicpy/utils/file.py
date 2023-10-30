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


def dump_jsonl(data, file_path):
    with open(file_path, 'w') as f:
        for line in data:
            f.write(json.dumps(line) + '\n')


def load_pickle(file_path, default=None):
    import pickle
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return default


def dump_pickle(data, file_path):
    import pickle
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

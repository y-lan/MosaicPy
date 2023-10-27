from collections.abc import Iterable
import itertools


def sample(collection, n, seed=None):
    import random
    if seed is not None:
        random.seed(seed)

    total_items = len(collection)
    if n >= total_items:
        return collection

    if isinstance(collection, dict):
        keys = iter(collection.keys())

        sampled_dict = {}
        sampled_indices = sorted(random.sample(range(len(collection)), n))
        cur_i = 0
        for i in sampled_indices:
            next_key = next(itertools.islice(
                keys, i - cur_i, i - cur_i + 1))
            sampled_dict[next_key] = collection[next_key]
            cur_i = i + 1

        return sampled_dict
    elif isinstance(collection, set):
        indices = random.sample(range(len(collection)), n)
        return set([x for i, x in enumerate(collection) if i in indices])

    elif isinstance(collection, Iterable):
        return random.sample(collection, n)
    else:
        raise TypeError("Input collection must be a list, set, or dictionary.")


def pmap(collection, map_func,
         workers=-1, use_process=False,
         show_progress=False):
    if show_progress:
        from tqdm import tqdm

    if use_process:
        import multiprocessing

        if workers == -1:
            workers = multiprocessing.cpu_count()

        with multiprocessing.Pool(workers) as pool:

            if show_progress:
                result = list(
                    tqdm(pool.imap(map_func, collection), total=len(collection)))
            else:
                result = pool.map(map_func, collection)
            return result
    else:
        from concurrent.futures import ThreadPoolExecutor

        if workers == -1:
            import multiprocessing
            workers = multiprocessing.cpu_count()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            if show_progress:
                result = list(tqdm(executor.map(map_func, collection),
                                   total=len(collection)))
            else:
                result = list(executor.map(map_func, collection))
        return result

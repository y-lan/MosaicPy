def sample(collection, n, seed=None):
    import random
    if seed is not None:
        random.seed(seed)
    return random.sample(collection, n)


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

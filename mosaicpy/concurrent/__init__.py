

def parallel_map_lite(collection, map_func, workers=-1):
    from concurrent.futures import ThreadPoolExecutor

    if workers == -1:
        import multiprocessing
        workers = multiprocessing.cpu_count()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(map_func, collection))


def parallel_map(collection, map_func, workers=-1):
    import multiprocessing

    if workers == -1:
        workers = multiprocessing.cpu_count()

    with multiprocessing.Pool(workers) as pool:
        return pool.map(map_func, collection)

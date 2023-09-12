import math


def dcg_at_k(r, k):
    """Calculate DCG@k for a ranking list r.
    Args:
        r (list): A list of relevancy scores.
        k (int): The position up to which to consider.
    Returns:
        float: DCG@k value.
    """
    r = r[:k]
    return sum([rel / math.log2(i + 2) for i, rel in enumerate(r)])


def ndcg_at_k(r, k):
    """Calculate NDCG@k for a ranking list r.
    Args:
        r (list): A list of relevancy scores.
        k (int): The position up to which to consider.
    Returns:
        float: NDCG@k value.
    """
    dcg_max = dcg_at_k(sorted(r, reverse=True), k)
    if dcg_max == 0:
        return 0
    return dcg_at_k(r, k) / dcg_max

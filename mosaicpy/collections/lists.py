from typing import List


def sort_by_value(items):
    return sorted(items, key=lambda x: x[1], reverse=True)


def values_to_rank(values, reverse=False, start_rank=0) -> List[int]:
    """
    This function converts a list of scores into a list of ranks.

    Args:
        values (list): The original list of scores.
        reverse (bool, optional): If True, the scores are ranked in descending order. Defaults to False.
        start_rank (int, optional): The starting rank for the ranking. Defaults to 0.

    Returns:
        list: A new list where each item is the rank of the corresponding original value in the sorted ranking.
    """
    sorted_values = sorted([(v, i)
                           for i, v in enumerate(values)], reverse=reverse)
    ranks = [0] * len(values)
    for rank, (_, i) in enumerate(sorted_values):
        ranks[i] = rank + start_rank
    return ranks


def sort_by_scores(items: List, scores: List, reverse: bool = False) -> List:
    """
    This function sorts a given list by the value in the corresponding position in another given list (scores).

    Args:
        items (List): The original list of items.
        scores (List): The list of scores corresponding to each item.
        reverse (bool, optional): If True, the items are sorted in descending order. Defaults to False.

    Returns:
        List: A new list where each item is sorted according to the corresponding score.
    """
    return [item for _, item in sorted(zip(scores, items), reverse=reverse)]

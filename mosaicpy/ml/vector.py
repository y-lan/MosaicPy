import numpy as np


def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)


def min_max_norm(lst):
    min_val = np.min(lst)
    max_val = np.max(lst)
    norm_lst = (lst - min_val) / (max_val - min_val)
    return norm_lst

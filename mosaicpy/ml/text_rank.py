import numpy as np

from mosaicpy.ml.vector import cosine_similarity


def _norm_similarity_matrix(similarity_matrix):
    for i in range(similarity_matrix.shape[0]):
        similarity_matrix[i] /= similarity_matrix[i].sum()


class TextRanker:

    def __init__(self, damping_factor=0.85, max_iter=100, tol=1e-6):
        self.damping_factor = damping_factor
        self.max_iter = max_iter
        self.tol = tol

    def _rank(self, similarity_matrix):
        ranks = np.ones(similarity_matrix.shape[0])

        for iter in range(self.max_iter):
            new_ranks = (1 - self.damping_factor) + self.damping_factor * \
                np.dot(similarity_matrix.T, ranks)

            if np.linalg.norm(new_ranks - ranks, 2) < self.tol:
                break

            ranks = new_ranks

        return ranks

    def rank_sentences(self, sentences):
        pass

    def rank_embeddings(self, embeddings):
        size = len(embeddings)
        similarity_matrix = np.zeros((size, size))

        for i in range(size):
            for j in range(size):
                similarity_matrix[i][j] = cosine_similarity(
                    embeddings[i], embeddings[j])

        _norm_similarity_matrix(similarity_matrix)

        return self._rank(similarity_matrix)

import numpy as np
from numpy.linalg import norm


def cosine_similarity(emb1,emb2):
    emb1=np.array(emb1)
    emb2=np.array(emb2)
    return np.dot(emb1, emb2) / (norm(emb1)* norm(emb2))


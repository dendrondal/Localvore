import pickle
from random import randint
from typing import List, Dict

from sklearn.neighbors import NearestNeighbors

from src.models import backend_query


def create_samples(collection: str, state: str) -> Dict:
    """Creates dict of recipe names, along with their associated vectors.
    Goal is to feed this forward into NearestNeighbors algorithm"""
    result = dict()
    cursor = backend_query(collection, state)
    cursor.rewind()
    for recipe in cursor:
        name = recipe['title']
        result[name] = pickle.loads(recipe['vector'])
    assert len(result) > 0, 'No matching recipes'
    return result


def clustering(state, collections=['BB'], n_neighbors=5) -> List[Dict]:
    names, X = list(), list()
    for collection in collections:
        collection_dict = create_samples(collection, state)
        key, val = collection_dict.keys(), collection_dict.values()
        names.append(list(key))
        X.append(list(val))
    names = names[0]
    X = X[0]
    neigh = NearestNeighbors(n_neighbors=n_neighbors, n_jobs=-1)
    neigh.fit(X)
    indices = neigh.kneighbors([X[randint(0, len(X))]], return_distance=False)
    return [names[index] for index in indices[0]]


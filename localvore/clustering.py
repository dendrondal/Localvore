import pickle
from random import randint
from typing import List, Dict

from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN, OPTICS
import numpy as np
import pandas as pd

from models import backend_query


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


def clustering(state: str, collections: List[str], n_recipes=5) -> List[Dict]:
    """Simplest clustering algorithm for recipe vectors. Requires State name, 
    recipe collections used, and the number of recipes to be output. Valid
    collection names are currently BB for BudgetBytes, Recipe1M, and 
    Epi for Epicurious.
    
    Returns a list of length n_recipes containing recipe names satisfying
    the criteria of create_samples"""
    nested_names, nested_X = [], []
    for collection in collections:
        collection_dict = create_samples(collection, state)
        key, val = collection_dict.keys(), collection_dict.values()
        nested_names.append(list(key))
        nested_X.append(list(val))

    names, X = [], []
    for name_sublist, x_sublist in zip(nested_names, nested_X):
        for item in name_sublist:
            names.append(item)
        for item in x_sublist:
            X.append(item)

    neigh = NearestNeighbors(n_neighbors=n_recipes, n_jobs=-1)
    neigh.fit(X)
    indices = neigh.kneighbors([X[randint(0, len(X))]], return_distance=False)
    return [names[index] for index in indices[0]]


def dbscan(state, collection='BB', epsilon=0.2) -> List[Dict]:
    names, X = [], []
    collection_dict = create_samples(collection, state)
    names.append(list(collection_dict.keys()))
    X.append(list(collection_dict.values()))
    names = names[0]
    X = X[0]
    print(f'Finished query. {len(names)} Items returned.')
    neigh = OPTICS(cluster_method='dbscan', n_jobs=-1)
    neigh.fit(X)
    df = pd.DataFrame({'X': X, 'cluster_label': neigh.labels_, 'name': names})
    inliers = df[df['cluster_label'] != -1]
    print(inliers.head())
    inliers.groupby('cluster_label').first()
    return list(df.loc[df['name', :5]])

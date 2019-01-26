import spacy
import os, json, pickle
from src.models import recipe_collection, backend_query, mock_query
from tqdm import tqdm
from bson.binary import Binary
from sklearn.neighbors import NearestNeighbors


def keyword_vectorization():
    """Large write operation to mongodb. Adds average word vector to each
    document"""
    nlp = spacy.load('en_core_web_lg')
    collection = recipe_collection()
    for recipe in tqdm(collection.find()):
        ingredients = " ".join([item.lower() for item in recipe['categories']])
        tokens = nlp(ingredients)
        recipe['vector'] = Binary(pickle.dumps(tokens.vector))
        collection.save(recipe)


def create_samples(state):
    """Creates dict of recipe names, along with their associated vectors.
    Goal is to feed this forward into NearestNeighbors algorithm"""
    result = dict()
    cursor = backend_query(state)
    cursor.rewind()
    for recipe in cursor:
        name = recipe['title']
        result[name] = pickle.loads(recipe['vector'])
    return result


def clustering(state, n_neighbors=5):
    sample = create_samples(state)
    X = list(sample.values())
    neigh = NearestNeighbors(n_neighbors=n_neighbors, n_jobs=-1)
    neigh.fit(X)
    indices = neigh.kneighbors([X[4443]], return_distance=False)
    names = list(sample.keys())
    return [names[index] for index in indices[0]]


def load_json():
    """Tests directory for  test json dump, creates one if there is none.
    Likely a memory-intensive operation, so this function should not be called
    in production, only in testing."""
    if "test_query.json" not in os.listdir():
        mock_query()
    return json.load("test_query.json")

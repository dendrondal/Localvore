import pickle

import spacy
from bson.binary import Binary
from pymongo import MongoClient
from tqdm import tqdm

from src.scraper import get_seasonal_veggies

#Global variable here until google location services added.
STATE = 'tennessee'


def backend_query(collection, state=STATE):
    """Pings API from seasonalfoodguide, scrapes html, and finds set union
    of veggies and recipe collection by keyword."""
    client = MongoClient()
    recipes = client.RECIPES[collection]
    assert recipes.count_documents({}) > 0, "Invalid collection name entered"
    veggies = get_seasonal_veggies(state)
    result = recipes.find({'ingredients': {"$in": veggies}})
    return result


def keyword_vectorization(collection: str):
    """Large write operation to mongodb. Adds average word vector to each
    document"""
    nlp = spacy.load('en_core_web_lg')
    collection = backend_query(collection)
    for recipe in tqdm(collection.find()):
        ingredients = " ".join([item.lower() for item in recipe['ingredients']])
        tokens = nlp(ingredients)
        recipe['vector'] = Binary(pickle.dumps(tokens.vector))
        collection.save(recipe)













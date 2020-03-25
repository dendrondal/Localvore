import pickle
import re
import sys
from typing import List
from threading import Thread

import spacy
from bson.binary import Binary
from loguru import logger
from pymongo import MongoClient
from tqdm import tqdm

MONGOPATH = 'mongodb://localhost:27017/'
STATE = 'tennessee'
from scraper import get_seasonal_veggies

logger.add(sys.stderr)


def backend_query(collection: str, state=STATE, mongo_path=MONGOPATH):
    """Pings API from seasonalfoodguide, scrapes html, and finds set union
    of veggies and recipe collection by keyword."""
    client = MongoClient(mongo_path)
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


def strip_details(ingredients: List[str]):
    """Removes everything in parentheses and after a comma in every string"""
    no_parentheses = [re.sub(r'\([^()]*\)', '', string)
                      for string in ingredients]
    precomma = [re.findall(r'[^,]+', string)[0] for string in no_parentheses]
    return precomma


def trim_ingredients(mongo_path=MONGOPATH):
    """Removes everything after comma and in parentheses for
    existing documents"""
    client = MongoClient(mongo_path)
    db = client.RECIPES
    col = db.BB
    num_failures = 0
    for recipe in tqdm(col.find()):
        try:
            recipe['ingredients'] = strip_details(recipe['ingredients'])
        except Exception as e:
            print(e)
            num_failures += 1
            print(num_failures)
            pass
        col.save(recipe)


@logger.catch()
def make_post(r):
    """"Uses currently open Response object to test for existence of various CSS
    tags. Returns dictionary for insertion into MongoDB, or None if the
    ingredients field is blank."""
    tags = {'title': 'h1.title',
            'cost': 'span.wprm-recipe-recipe_cost',
            'rating': 'div.wprm-recipe-rating-details',
            'keywords': 'span.wprm-recipe-keyword'
            }
    post = dict()
    for key, val in zip(list(tags.keys()), list(tags.values())):
        try:
            post[key] = r.html.find(val)[0].text
        except IndexError:
            pass
    raw_ingredients = [item.text for item in
                       r.html.find('span.wprm-recipe-ingredient-name')]
    if len(raw_ingredients) == 0:
        return None
    else:
        post['ingredients'] = strip_details(raw_ingredients)
        try:
            post['keywords'] = post['keywords'].split(',')
        except KeyError:
            pass
        return post

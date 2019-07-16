import itertools
import pickle
import sys

import click
import ijson
import numpy as np
import pandas as pd
import spacy
from bson.binary import Binary
from loguru import logger
from pymongo import MongoClient
from tqdm import tqdm

#Global variables for default filepaths/urls, can be altered via click
MONGOPATH = 'mongodb://localhost:27017/'
PATH_TO_LAYER1 = '/media/dal/Localvore Volume/layer1.json'
PREDICTION_DATA = 'http://data.csail.mit.edu/im2recipe/det_ingrs.json'

logger.add(sys.stderr, format="{level} {message}", level='INFO')


def mongo_init(mongopath):
    """Instantiates MongoDB instance, creating recipe1M collection if it does
    not exist"""
    client = MongoClient(mongopath)
    database = client.RECIPES
    col = database['recipe1M']
    return col


@logger.catch()
def insert_recipes(layer1_path, collection):
    """Chunks through json text of recipe dataset, writes id, name, and url
    to MongoDB. Due to large size of json (1.8gb on disk), data is instead
    streamed using ijson, with checks for matchingETL_pipeline import filter_predictions, garbage_collection json keys at each point."""
    entry = dict()
    for prefix, _, value in tqdm(ijson.parse(open(layer1_path))):
        if len(entry) == 3:
            collection.insert_one(entry)
            entry = dict()
        if prefix == 'item.id':
            entry['_id'] = value
        elif prefix == 'item.title':
            entry['title'] = value
        elif prefix == 'item.url':
            entry['url'] = value


def _compression(ingrs, truths):
    """Helper function for filter_predictions"""
    if not any(truths):
        return np.NaN
    else:
        return list(itertools.compress(ingrs, truths))


def _textract(row):
    """Helper function for filter_predictions"""
    return [item['text'] for item in row]


def load_predictions(data_url):
    """I/O function for filter_predictions"""
    df = pd.read_json(data_url)
    df.rename(columns={'id': '_id',
                       'ingredients': 'raw_ingrs',
                       'valid': 'valid'},
              inplace=True)
    return df


def filter_predictions(df):
    """
    Uses predictions from bidirectional LSTM + Logistic Regression
    to extract actual ingredients from full ingredient listing

    Examples:
    1 cup flour -> flour
    1 tbsp butter, softened -> butter
    4 slices Kraft American Cheese -> American Cheese

    The layout of each json item is as follows:

    id: unique 10-digit identifier for recipe
    ingredients: Array of dicts, all with "text" as key
    valid: Array of boolean values to be mapped over "ingredients"

    These are mapped by a "valid" array with boolean values, then written to
    mongo.
    """
    logger.info('Starting compression operation...')
    df['cleaned'] = df[['raw_ingrs', 'valid']].apply(lambda x:
                                                     _compression(*x),
                                                     axis=1)
    df.dropna(inplace=True)
    logger.info('Doing list comprehensions on cleaned df...')
    df['ingredients'] = df['cleaned'].apply(_textract)
    df.drop(['raw_ingrs', 'valid', 'cleaned'], axis=1, inplace=True)
    logger.info('Cleaning done!')
    return df


def insert_ingredients(df, collection):
    """Bulk write of filtered ingredient lists to MongoDB"""
    logger.info('Starting bulk write to Mongo')
    for row in tqdm(df.iterrows(index=False)):
        collection.update_one({'_id': row[0]},
                              {'$set': {'ingredients': row[1]}})


def ingredient_vectorization(collection):
    """Performs word2vec on all ingredients in each recipe, pickles average
    vector of each recipe"""
    nlp = spacy.load('en_core_web_lg')
    logger.info('Starting word2vec')
    for recipe in tqdm(collection.find({})):
        ingredients = " ".join([item.lower() for item in recipe['ingredients']])
        tokens = nlp(ingredients)
        recipe['vector'] = Binary(pickle.dumps(tokens.vector))
        collection.update_one(recipe)
    logger.info('Mongo collection is up to date!')


@click.command()
@click.option('--layer1', default=False, help='Layer1 json filepath')
@click.option('--mongopath', default=MONGOPATH, help='MongoDB url')
@click.option('--prediction_url', default=PREDICTION_DATA,
              help='URL to LSTM predictions')
@click.option('--vectorization', default=True,
              help='Whether to calculate recipe vectors (time intensive!)')
def main(layer1, mongopath, prediction_url, vectorization):
    col = mongo_init(mongopath)
    if layer1:
        insert_recipes(layer1, col)
    predictions = load_predictions(prediction_url)
    insert_ingredients(filter_predictions(predictions), col)
    if vectorization:
        ingredient_vectorization(col)


if __name__ == '__main__':
    main()

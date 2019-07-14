import pandas as pd
import pickle
from bson.binary import Binary
from pymongo import MongoClient
import click
import itertools
import ijson
from tqdm import tqdm
import spacy
from loguru import logger
import sys
import dask.dataframe as dd


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
    streamed using ijson, with checks for matching json keys at each point."""
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


def _compression(row):
    return list(itertools.compress(row['raw_ingrs'], row['valid']))


def _textract(row):
    return [item['text'] for item in row]


def load_layer1(data_url):
    df = pd.read_json(data_url)
    df.columns = ['_id', 'raw_ingrs', 'valid']
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
    tqdm.pandas(desc='Map/Reduce')
    df['cleaned'] = df.progress_apply(lambda row: _compression(row), axis=1)
    df['ingredients'] = df['cleaned'].progress_apply(_textract)
    return df


def garbage_collection(df):
    df.drop(['raw_ingrs', 'valid', 'cleaned'], axis=1)
    return df.to_dict()


def insert_ingredients(ingr_dict, collection):
    collection.update_many(ingr_dict)


def ingredient_vectorization(collection):
    """Performs word2vec on all ingredients in each recipe, pickles average
    vector of each recipe"""
    nlp = spacy.load('en_core_web_lg')
    for recipe in tqdm(collection.find({})):
        ingredients = " ".join([item.lower() for item in recipe['ingredients']])
        tokens = nlp(ingredients)
        recipe['vector'] = Binary(pickle.dumps(tokens.vector))
        collection.update_one(recipe)


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
    insert_results(prediction_url, col)
    if vectorization:
        ingredient_vectorization(col)


if __name__ == '__main__':
    main()

from pymongo import MongoClient
from src.scraper import get_seasonal_veggies
from pathlib import Path
from sqlite3 import Error
import json, sqlite3
import pandas as pd


#Global variable here until google location services added.
STATE = 'tennessee'


def recipe_collection(collection):
    client = MongoClient()
    if collection == 'BB':
        db = client.BB
        recipes = db.full_format_recipes
        return recipes
    elif collection == 'RECIPES':
        db = client.RECIPES
        recipes = db.full_format_recipes
        return recipes
    else:
        print('Invalid collection name entered')
        return None


def backend_query(state=STATE):
    """Pings API from seasonalfoodguide, scrapes html, and finds set union
    of veggies and recipe collection by keyword."""
    recipes = recipe_collection()
    veggies = get_seasonal_veggies(state)
    result = recipes.find({'categories': {"$in": veggies}})
    return result


def mock_query(state=STATE):
    """Helper function to allow mock data to be obtained without running
    entire module."""
    file = open('test_query.json', 'w')
    file.write('[')
    for recipe in backend_query():
        file.write(json.dumps(recipe))
        file.write(',')
    file.write(']')


def rdbms_constructor(db_file):
    """Instantiates SQLite 3 database of ingredient metadata"""
    try:
        conn = sqlite3.connect(str(db_file))
    except Error as e:
        print(e)
    df = pd.read_csv('epi_r.csv')
    df.to_sql('recipes', conn, if_exists='replace', index=False)
    print("Successfully created recipes table!")


if __name__ == '__main__':
    client = MongoClient()
    #below code instantiates sqlite database if it doesn't exist.
    sqldb = Path('./recipe_metadata.sqlite')
    if sqldb.is_file():
        pass
    else:
        rdbms_constructor(sqldb)












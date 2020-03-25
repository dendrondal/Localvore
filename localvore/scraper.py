from datetime import date
from typing import List

from pymongo import MongoClient
from requests_html import HTMLSession
from tqdm import tqdm

import models
MONGOPATH = 'mongodb://localhost:27017/'


def get_date() -> str:
    """Gets date in format compatible with seasonalfoodguide urls,
    i.e. early-january, late-may, etc."""
    month = date.today().strftime('%B').lower()
    period = 'early' if date.today().day <= 15 else 'late'
    return f'{period}-{month}'


def get_seasonal_veggies(state: str) -> List[str]:
    """TODO: State should be extracted from Google location services
    """
    today = get_date()
    session = HTMLSession()
    r = session.get(f'http://www.seasonalfoodguide.org/{state}/{today}')
    r.html.render(wait=1, sleep=1)
    veggies = [card.text.lower().split('\n')[0]
               for card in r.html.find('#col-veg-detail-card')]
    #The CSS selector above returns the individual cards, and the first item
    #is the card title, aka vegetable.
    assert r.status_code == 200, 'Unsuccessful request. Check wait and sleep.'
    assert len(veggies) > 0, 'No vegetables returned. Check state spelling.'
    return veggies


def get_all_bb_recipes() -> List[str]:
    """Scraper that finds all recipe titles on BudgetBytes. More precise than
    doing 'find all links', as unique recipe URLs are of format url/recipe-title
    """
    recipe_list = list()
    i = 1
    while True:
        sess = HTMLSession()
        r = sess.get(f'http://www.budgetbytes.com/category/recipes/page/{i}')
        if r.status_code == 404:
            break
        r.html.render(wait=1, sleep=1)
        for recipe in r.html.find('h4.title'):
            recipe_list.append(recipe.text)
        print(f'Processed page {i}')
        sess.close()
        i += 1
    return recipe_list

def bulk_write(mongo_path=MONGOPATH):
    """Scrapes all recipes extracted from budget bytes, writes ingredients
    to new MongoDB collection"""
    client = MongoClient(mongo_path)
    db = client.RECIPES
    col = db.BB
    recipe_list = get_all_bb_recipes()
    for recipe in tqdm(recipe_list):
        with HTMLSession() as sess:
            fmtd_recipe = recipe.lower().replace(" ", "-")
            r = sess.get(f'https://www.budgetbytes.com/{fmtd_recipe}')
            post = models.make_post(r)
            if post is not None:
                col.insert_one(post)

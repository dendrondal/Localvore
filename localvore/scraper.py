import asyncio
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from loguru import logger
from pymongo import MongoClient
from requests_html import AsyncHTMLSession, HTMLSession
from tqdm import tqdm

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
    # The CSS selector above returns the individual cards, and the first item
    # is the card title, aka vegetable.
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


class RecipeScraper:
    """
    Takes in a list of HTML tags for an arbitrary website, and either
    scrapes them to save to a MongoDB collection or dump into a text
    file.
    
    Required Tags:
        - root_url: base url of the view all recipes function of the website
        - pagination: Extension for pagination, i.e. /page/1 or ?_paged=1
        - nav_title: HTML element for title within pagination
        - title: HTML element for title within recipe webpage
        - ingredients: HTML element for ingredients
    Optional tags:
        - cost, rating, keywords, category, cuisine. 
        Should all be self-explanatory
    """
    def __init__(self, tags: Dict[str, str], collection_name: str, save=True, mongo_path=MONGOPATH):
        self.tags = tags
        self.col_name = collection_name
        self.save = save
        self.mongo_path = mongo_path
        logger.add(sys.stderr)

    async def get_page_content(self, url):
        recipe_list = []
        async with ClientSession() as sess:
            async with sess.get(url) as r:
                html = await r.read()
                print(f"Got recipes from {url.split('/')[-1]}")
                soup = BeautifulSoup(html)
                for recipe in soup.find_all('a', 'entry-title-link'):
                    recipe_list.append(recipe.get('href'))
        return recipe_list

    async def get_recipes(self, page_url):
        async with ClientSession() as sess:
            async with sess.get(page_url) as r:
                html = await r.read()
                post = self.make_post(html)
                if post is not None:
                    print(f"Got recipe for {post['title']}")
                    if self.save:
                        self.save_to_disk(post['title'], post)

    async def bulk_write(self, base_url):
        """Scrapes all recipes extracted from budget bytes, writes ingredients
        to new MongoDB collection"""
        content = await self.get_page_content(base_url) 
        task_list = [asyncio.create_task(self.get_recipes(recipe)) for recipe in content]
        sem = asyncio.Semaphore(10)
        async with sem:
            await asyncio.gather(*task_list)

    async def _main(self):
        urls = [f"{self.tags['root_url']}/recipes/page/{i}" for i in
                     range(1, self.tags['pagination']+1)]
        sem = asyncio.Semaphore(10)
        task_list = [asyncio.create_task(self.bulk_write(url)) for url in urls]
        async with sem:
            await asyncio.gather(*task_list)

    @staticmethod
    def strip_details(ingredients: List[str]):
        """Removes everything in parentheses and after a comma in every string"""
        no_parentheses = [re.sub(r'\([^()]*\)', '', string)
                          for string in ingredients]
        precomma = [re.findall(r'[^,]+', string)[0] for string in no_parentheses]
        return precomma
    
    def make_post(self, r):
        """"Uses currently open Response object to test for existence of various CSS
        tags. Returns dictionary for insertion into MongoDB, or None if the
        ingredients field is blank."""
        post = dict()
        soup = BeautifulSoup(r)
        for key, val in zip(list(self.tags.keys())[3:],
                            list(self.tags.values())[3:]):
            try:
                post[key] = soup.find(val.split('.')).string
            except AttributeError:
                pass
        raw_ingredients = soup.find(self.tags['full_recipe'].split('.'))
        if len(raw_ingredients) == 0:
            return None
        else:
            post['ingredients'] = raw_ingredients
            try:
                post['keywords'] = post['keywords'].split(',')
            except Exception as e:
                logger.catch(e)
                pass
            return post

    def save_to_disk(self, recipe_title, post):
        Path(Path.cwd() / self.col_name).mkdir(parents=True,
                                                      exist_ok=True)
        path = Path(Path.cwd() / self.col_name)
        output = path / f"{recipe_title.lower().replace(' ', '-')}.html"
        output.write_text(post['ingredients'].decode())

    def scrape(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._main())
        loop.close()


ella_tags = {
    'root_url': 'https://naturallyella.com',
    'pagination': 46,
    'nav_title': 'h2.entry-title',
    'title': 'h1.entry-title',
    'category': 'span.tasty-recipes-category',
    'full_recipe': 'div.tasty-recipes-entry-content',
    'ingredients': 'div.tasty-recipes-ingredients',
    'instructions': 'div.tasty-recipes-instructions',
    'notes':  'div.tasty-recipes-notes',
    'keywords': 'em'
}

RecipeScraper(ella_tags, 'ella').scrape()

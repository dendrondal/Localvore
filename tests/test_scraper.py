import asyncio
from pathlib import Path

import pytest
from requests_html import AsyncHTMLSession

from localvore.scraper import RecipeScraper

mock_tags = {
    'root_url': 'http://naturallyella.com',
    'pagination': 2,
    'nav_title': 'h2.entry-title',
    'title': 'h1.entry-title',
    'category': 'span.tasty-recipes-category',
    'full_recipe': 'div.tasty-recipes-entry-content',
    'ingredients': 'div.tasty-recipes-ingredients',
    'instructions': 'div.tasty-recipes-instructions',
    'notes':  'div.tasty-recipes-notes',
    'keywords': 'em'
}
mock_object = RecipeScraper(mock_tags, 'test')
abbv_list = [
    'https://naturallyella.com/crispy-scallion-asparagus-pizza',
    'https://naturallyella.com/roasted-brussels-sprouts'
]
mock_url = 'https://naturallyella.com/crispy-scallion-asparagus-pizza'
             

@pytest.mark.asyncio
async def test_get_recipes():
    results = await mock_object.get_recipes(mock_url)
    test_file = Path(__file__).parents[1].resolve() / 'test' / 'crispy-scallion-asparagus-pizza.html'
    assert test_file.exists() 
    test_file.unlink()


@pytest.mark.asyncio
async def test_post():
    sess = AsyncHTMLSession()
    r = await sess.get(mock_url)
    await r.html.arender(timeout=60, wait=1, sleep=1, keep_page=True)
    post = mock_object.make_post(r)
    assert type(post) == dict
    assert post['ingredients'] is not None

def test_scrape():
    mock_object.scrape()
    test_file = Path(__file__).parents[1].resolve() / 'test' / 'crispy-scallion-asparagus-pizza.html'
    assert test_file.exists() 
    test_file.unlink()

import asyncio
from pathlib import Path

import pytest
from aiohttp import ClientSession

from localvore.scraper import RecipeScraper

mock_tags = {
    'root_url': 'https://naturallyella.com',
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
    async with ClientSession() as sess:
        async with sess.get(mock_url) as r:
            html = await r.read()
            post = mock_object.make_post(html)
            assert type(post) == dict
            assert post['ingredients'] is not None


@pytest.mark.asyncio
async def test_get_page_content():
    url = mock_tags['root_url'] + '/recipes/page/1/'
    result = await mock_object.get_page_content(url)
    assert len(result) == 18
    assert mock_tags['root_url'] in result[0]

def test_scrape():
    mock_object.scrape()
    test_file = Path(__file__).parents[1].resolve() / 'test' / 'crispy-scallion-asparagus-pizza.html'
    assert test_file.exists() 
    test_file.unlink()

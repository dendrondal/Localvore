from requests_html import HTMLSession
from datetime import date


def get_date():
    month = date.today().strftime('%B').lower()
    period = 'early' if date.today().day <= 15 else 'late'
    return f'{period}-{month}'


def get_seasonal_veggies(state):
    """TODO: State should be extracted from Google location services
    """
    today = get_date()
    session = HTMLSession()
    r = session.get(f'http://www.seasonalfoodguide.org/{state}/{today}')
    r.html.render(wait=1, sleep=1)
    veggies = [card.text.split('\n')[0]
               for card in r.html.find('#col-veg-detail-card')]
    #The CSS selector above returns the individual cards, and the first item
    #is the card title, aka vegetable.
    assert r.status_code == 200, 'Unsuccessful request. Check wait and sleep.'
    assert len(veggies) > 0, 'No vegetables returned. Check state spelling.'
    return veggies


def get_all_bb_recipes():
    """"Scraper that finds all recipe titles on BudgetBytes. More precise than
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
            recipe_list.append(recipe)
        print(f'Processed page {i}')
        sess.close()
        i += 1
    return recipe_list



# Localvore

Localvore is a menu planner that reccomends recipes based on what's in season in your area. This relies on [seasonalfoodguide](http://www.seasonalfoodguide.org) to get locally seasonal veggies. Next, recipes are clustered based on total ingredient similarity. The full background and technical details of the implementation are available via the [blog post](https://dalwilliams.info/localvore-menu-planner.html) on this project.

## Installation

This project is still in the experimental stage. The eventual intent is deployment as a REST API. Dependency management is done with [Poetry](https://python-poetry.org/) It can be run locally as follows:

1. [Clone](https://github.com/dendrondal/Localvore.git) the repository
2. `cd` into it locally, then install the dependencies with `poetry install`
3. Inside the localvore folder, you can then run the app using `poetry run flask run`
4. By default, this will run the app at `localhost:8001`. You can generate a JSON of a weekly menu for your state by navigating to `localhost:8001/api/menu/{YOUR_STATE}` 

Contributions are welcome! The roadmap for this project is as follows:

- [ ] Improve clustering algorithm to include entrees only
- [ ] Add the ability to add/remove ingredients based on dietary preferences/restrictions
- [ ] Add a simple Bootstrap interface
- [ ] Deploy the MongoDB and API to an AWS instance

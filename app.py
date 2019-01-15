from flask import Flask, jsonify
from clustering import clustering


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/menu/<string:state>', methods=['GET'])
def get_menu(state):
    return jsonify({'menu': clustering(state)})


def create_app(config=None):
    """Theoretically, this function should instantiate the app.
    See Armin Ronicher's video on Flask for fun and profit"""
    app = Flask(__name__)
    app.config.update(config or {})
    return app


if __name__ == '__main__':
    app.run(debug=True)

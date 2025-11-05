from flask import Flask, render_template

from entities.city import get_all

app = Flask(__name__)


@app.route('/cities')
def hello_world():  # put application's code here
    print('get from /cities')
    for c in get_all():
        print(c.name)
    return 'get from /cities'


if __name__ == '__main__':
    app.run()

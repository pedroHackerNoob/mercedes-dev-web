from flask import Flask, render_template, request, jsonify

from entities.city import get_all, City

app = Flask(__name__)


@app.route('/cities')
def get_cities():  # put application's code here
    cities = get_all()
    print('get from /cities')
    for c in cities:
        print(c.name)
    return 'get from /cities'

@app.post('/cities')
def post_cities():
    data = request.get_json()
    c = City(name=data['name'])
    id = c.save()
    print(id)
    succes = id is not None
    return jsonify(succes), 201

if __name__ == '__main__':
    app.run()

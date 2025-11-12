from flask import Flask, render_template, request, jsonify

from entities.city import get_all, City

app = Flask(__name__)


@app.route('/cities')
def get_cities():  # put application's code here
    cities = get_all()
    print('get from /cities')
    for c in cities:
        print(c.name)
    return jsonify([c.name for c in cities]),200
@app.post('/cities')
def post_city():
    data = request.get_json()
    c = City(name=data['name'])
    id = c.save()
    print(id)
    succes = id is not None
    return jsonify(succes), 201
@app.put('/cities/<int:id>')
def put_city(id):
    print('put from /cities')
    data = request.get_json()
    c = City(id_city=id, name=data['name'])
    c.poster_city()
    return jsonify(True), 201
@app.delete('/cities/<int:id>')
def delete_city(id):
    c = City(id_city=id)
    c.delete_city()
    return jsonify(True), 200

if __name__ == '__main__':
    app.run()

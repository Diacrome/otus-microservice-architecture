from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/warehouse/<id>', methods=['GET'])
def get_warehouse_status(id):
    warehouse_available = True if int(id) < 10 else False
    return jsonify({'warehouse_available': warehouse_available})


@app.route('/delivery/<hour>', methods=['GET'])
def get_courier_status(hour):
    delivery_available = True if int(hour) < 18 else False
    return jsonify({'delivery_available': delivery_available})


@app.route("/")
def hello_world():
    return "<p>logic resource is alive!</p>"

import requests
from kubernetes import client, config

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import base64

db = SQLAlchemy()

config.load_incluster_config()
v1 = client.CoreV1Api()

secret = v1.read_namespaced_secret("hw10-secret", "hw10").data
db_user = base64.b64decode(secret['postgres-root-username']).decode('utf-8')
db_password = base64.b64decode(secret['postgres-root-password']).decode('utf-8')
config_map = v1.read_namespaced_config_map("hw10-config", "hw10").data
db_host = config_map['databaseUrl']


def create_app(db_user, db_password, db_host):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/hw10'
    db.init_app(app)
    return app


app = create_app(db_user, db_password, db_host)
app.app_context().push()

ma = Marshmallow(app)


# User Class/Model


class User(db.Model):
    __tablename__ = 'user_data'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    balance = db.Column(db.Integer)

    def __init__(self, name, balance):
        self.name = name
        self.balance = balance


# User Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'balance')


# Init schema
user_schema = UserSchema()


class Transaction(db.Model):
    __tablename__ = 'transaction_data'
    id = db.Column(db.Integer, primary_key=True)
    user_data_id = db.Column(db.Integer)
    product_name = db.Column(db.String(100))
    balance_change = db.Column(db.Integer)
    payment = db.Column(db.Boolean)
    store = db.Column(db.Boolean)
    delivery = db.Column(db.Boolean)

    def __init__(self, user_data_id, product_name, balance_change, payment, store, delivery):
        self.user_data_id = user_data_id
        self.product_name = product_name
        self.balance_change = balance_change
        self.payment = payment
        self.store = store
        self.delivery = delivery


# Transaction Schema
class TransactionSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_data_id', 'product_name', 'balance_change', 'payment', 'store', 'delivery')


# Init schema
TransactionSchema_schema = TransactionSchema()


# buy a product

@app.route('/buy', methods=['POST'])
def add_user():
    user_data_id = request.json['user_data_id']
    product_name = request.json['product_name']
    balance_change = request.json['balance_change']
    warehouse_id = request.json['warehouse_id']
    delivery_hour = request.json['delivery_hour']

    user = User.query.get(user_data_id)
    new_balance = calculate_balance(user_data_id, user) + balance_change
    if new_balance < 0:
        transaction = Transaction(user_data_id, product_name, balance_change, False, None, None)
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'failed': 'Not enough balance'})

    warehouse_request = requests.get("http://logic:8001/warehouse/" + str(warehouse_id))
    warehouse_available = warehouse_request.json().get('warehouse_available')
    if not warehouse_available:
        transaction = Transaction(user_data_id, product_name, balance_change, True, False, None)
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'failed': 'Warehouse is empty'})

    delivery_request = requests.get("http://logic:8001/delivery/" + str(delivery_hour))
    delivery_available = delivery_request.json().get('delivery_available')
    if not delivery_available:
        transaction = Transaction(user_data_id, product_name, balance_change, True, True, False)
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'failed': 'No courier is available'})

    transaction = Transaction(user_data_id, product_name, balance_change, True, True, True)
    db.session.add(transaction)
    db.session.commit()

    return jsonify({'success': 'Transaction created'})


# Get user balance


@app.route('/user/balance/<id>', methods=['GET'])
def get_user(id):
    balance = calculate_balance(id)
    return jsonify({'balance': balance})


def calculate_balance(user_id, user=None):
    if user is None:
        user = User.query.get(user_id)
    transactions = Transaction.query.filter_by(user_data_id=user_id).all()
    success_transactions = \
        filter(lambda t: (t.payment is True and t.store is True and t.delivery is True), transactions)
    sum_success_transactions = sum([t.balance_change for t in success_transactions])
    calculated_balance = user.balance + sum_success_transactions
    return calculated_balance


@app.route("/")
def hello_world():
    return "<p>transactions resource is alive!</p>"

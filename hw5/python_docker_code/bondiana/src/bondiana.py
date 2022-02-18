from kubernetes import client, config

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import base64

db = SQLAlchemy()

config.load_incluster_config()
v1 = client.CoreV1Api()

secret = v1.read_namespaced_secret("bondiana-secret", "bondiana").data
db_user = base64.b64decode(secret['postgres-root-username']).decode('utf-8')
db_password = base64.b64decode(secret['postgres-root-password']).decode('utf-8')
config_map = v1.read_namespaced_config_map("bondiana-config", "bondiana").data
db_host = config_map['databaseUrl']


def create_app(db_user, db_password, db_host):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/bondiana'
    db.init_app(app)
    return app


app = create_app(db_user, db_password, db_host)
app.app_context().push()

ma = Marshmallow(app)


# Product Class/Model


class Bond(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sec_id = db.Column(db.String(100))
    short_name = db.Column(db.String(100))
    prev_wap_price = db.Column(db.Numeric(8, 2))  # ??
    yield_at_prev_wap_price = db.Column(db.Numeric(8, 2))
    prev_price = db.Column(db.Numeric(8, 2))  # проверить этот или prev_wap_price нужен
    face_value = db.Column(db.Numeric(8, 2))
    mat_date = db.Column(db.Date)
    sec_name = db.Column(db.String(100))
    currency_id = db.Column(db.String(10))
    list_level = db.Column(db.Integer)
    offer_date = db.Column(db.Date)

    def __init__(self, sec_id, short_name, prev_wap_price, yield_at_prev_wap_price, prev_price, face_value, mat_date,
                 sec_name, currency_id, list_level, offer_date):
        self.sec_id = sec_id
        self.short_name = short_name
        self.prev_wap_price = prev_wap_price
        self.yield_at_prev_wap_price = yield_at_prev_wap_price
        self.prev_price = prev_price
        self.face_value = face_value
        self.mat_date = mat_date
        self.sec_name = sec_name
        self.currency_id = currency_id
        self.list_level = list_level
        self.offer_date = offer_date

    # Product Schema


class BondSchema(ma.Schema):
    class Meta:
        fields = ('id', 'sec_id', 'short_name', 'prev_wap_price', 'yield_at_prev_wap_price', 'prev_price', 'face_value',
                  'mat_date', 'sec_name', 'currency_id', 'list_level', 'offer_date')


# Init schema
bond_schema = BondSchema()


# Create a Product


@app.route('/product', methods=['POST'])
def add_product():
    name = request.json['name']
    description = request.json['description']

    new_product = Bond(name, description, None, None, None, None, None, None, None, None, None)

    db.session.add(new_product)
    db.session.commit()

    return bond_schema.jsonify(new_product)


# Get Single Products


@app.route('/product/<id>', methods=['GET'])
def get_product(id):
    product = Bond.query.get(id)
    return bond_schema.jsonify(product)


# Update a Product


@app.route('/product/<id>', methods=['PUT'])
def update_product(id):
    product = Bond.query.get(id)

    name = request.json['name']
    description = request.json['description']

    product.name = name
    product.description = description

    db.session.commit()

    return bond_schema.jsonify(product)


# Delete Product


@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
    product = Bond.query.get(id)
    db.session.delete(product)
    db.session.commit()

    return bond_schema.jsonify(product)


@app.route("/")
def hello_world():
    return "<p>It is alive!</p>"

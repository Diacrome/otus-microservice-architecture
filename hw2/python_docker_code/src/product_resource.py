from logging import info
from kubernetes import client, config

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import base64
import os

db = SQLAlchemy()

config.load_incluster_config()
v1 = client.CoreV1Api()

secret = v1.read_namespaced_secret("hw2-secret", "hw2").data
db_user = base64.b64decode(secret['postgres-root-username']).decode('utf-8')
db_password = base64.b64decode(secret['postgres-root-password']).decode('utf-8')
config_map = v1.read_namespaced_config_map("hw2-config", "hw2").data
db_host = config_map['databaseUrl']

def create_app(db_user, db_password, db_host):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/hw2'
    db.init_app(app)
    return app

app=create_app(db_user, db_password, db_host)
app.app_context().push()


ma = Marshmallow(app)

# Product Class/Model


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(200))

    def __init__(self, name, description):
        self.name = name
        self.description = description

# Product Schema


class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'description')


# Init schema
product_schema = ProductSchema()

# Create a Product


@app.route('/product', methods=['POST'])
def add_product():
    name = request.json['name']
    description = request.json['description']

    new_product = Product(name, description)

    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product)

# Get Single Products


@app.route('/product/<id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    return product_schema.jsonify(product)

# Update a Product


@app.route('/product/<id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)

    name = request.json['name']
    description = request.json['description']

    product.name = name
    product.description = description

    db.session.commit()

    return product_schema.jsonify(product)

# Delete Product


@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()

    return product_schema.jsonify(product)


@app.route("/")
def hello_world():
    return "<p>It is alive!</p>"

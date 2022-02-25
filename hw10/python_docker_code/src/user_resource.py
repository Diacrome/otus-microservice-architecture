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

app=create_app(db_user, db_password, db_host)
app.app_context().push()


ma = Marshmallow(app)

# User Class/Model


class User(db.Model):
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

# Create a User


@app.route('/user', methods=['POST'])
def add_user():
    name = request.json['name']
    balance = request.json['balance']

    new_user = User(name, balance)

    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user)

# Get Single User


@app.route('/user/<id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    return user_schema.jsonify(user)


@app.route("/")
def hello_world():
    return "<p>It is alive!</p>"

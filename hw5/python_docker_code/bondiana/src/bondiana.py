import datetime

from kubernetes import client, config
from operator import attrgetter

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import base64
import jwt

db = SQLAlchemy()

config.load_incluster_config()
v1 = client.CoreV1Api()

secret = v1.read_namespaced_secret("bondiana-secret", "bondiana").data
db_user = base64.b64decode(secret['postgres-root-username']).decode('utf-8')
db_password = base64.b64decode(secret['postgres-root-password']).decode('utf-8')
config_map = v1.read_namespaced_config_map("bondiana-config", "bondiana").data
db_host = config_map['databaseUrl']
jwt_secret = str(base64.b64decode(secret['jwt']).decode('utf-8'))


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
    face_value = db.Column(db.Numeric(12, 2))
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

    # bond Schema


class BondSchema(ma.Schema):
    class Meta:
        fields = ('id', 'sec_id', 'short_name', 'prev_wap_price', 'yield_at_prev_wap_price', 'prev_price', 'face_value',
                  'mat_date', 'sec_name', 'currency_id', 'list_level', 'offer_date')


# Init schema
bond_schema = BondSchema()


# Get Single bond


@app.route('/bond/<id>', methods=['GET'])
def get_bond(id):
    bond = Bond.query.get(id)
    return bond_schema.jsonify(bond)


@app.route("/")
def hello_world():
    return "<p>It is alive!</p>"

# Token class


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500))
    risk = db.Column(db.Integer)
    offer = db.Column(db.Boolean)

    def __init__(self, token, risk, offer):
        self.token = token
        self.risk = risk
        self.offer = offer


@app.route('/token', methods=['POST'])
def add_user():
    risk = request.json['risk']
    offer = request.json['offer']
    int_risk = 0
    try:
        int_risk = int(risk)
    except ValueError:
        int_risk = 0
    if int_risk > 3 or int_risk < 1:
        return jsonify({'message': 'Wrong risk level. Accept 1,2,3'}), 401
    int_offer = 0
    try:
        if offer is not None:
            int_offer = int(offer)
    except ValueError:
        int_offer = -1
    if int_offer < 0:
        return jsonify({'message': 'Wrong offer condition. Accept 0,1'}), 401

    token = jwt.encode({str(int_risk): str(datetime.datetime.now())},
                       jwt_secret,
                       algorithm="HS256")

    new_token = Token(token, int_risk, int_offer > 0)

    db.session.add(new_token)
    db.session.commit()

    return jsonify({'token': token}), 201


@app.route('/bond', methods=['GET'])
def get_best_bond():
    token = None
    # jwt is passed in the request header
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    # return 401 if token is not passed
    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    db_token = Token.query.filter_by(token=token).first()
    if not db_token:
        return jsonify({'message': 'Token not found'}), 401

    bonds = Bond.query.filter_by(list_level=db_token.risk).all()
    if not bonds:
        return jsonify({'error': 'Bond db is empty'}), 404
    if db_token.offer:
        filtered_bond = [bond for bond in bonds if bond.offer_date is not None]
    else:
        filtered_bond = [bond for bond in bonds if bond.offer_date is None]

    best_bond = max(filtered_bond, key=attrgetter('yield_at_prev_wap_price'))

    return bond_schema.jsonify(best_bond)

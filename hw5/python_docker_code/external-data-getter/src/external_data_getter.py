import base64
import logging
import time
import requests

from kubernetes import client, config
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

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


# Bond Class/Model


class Bond(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sec_id = db.Column(db.String(100))
    short_name = db.Column(db.String(100))
    prev_wap_price = db.Column(db.Numeric(8, 2))
    yield_at_prev_wap_price = db.Column(db.Numeric(8, 2))
    prev_price = db.Column(db.Numeric(8, 2))
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

    def __eq__(self, other):
        if not isinstance(other, Bond):
            return False
        return self.sec_id == other.sec_id and \
            self.short_name == other.short_name and \
            self.prev_wap_price == other.prev_wap_price and \
            self.yield_at_prev_wap_price == other.yield_at_prev_wap_price and \
            self.prev_price == other.prev_price and \
            self.face_value == other.face_value and \
            self.mat_date == other.mat_date and \
            self.sec_name == other.sec_name and \
            self.currency_id == other.currency_id and \
            self.list_level == other.list_level and \
            self.offer_date == other.offer_date

    def __hash__(self):
        return hash((self.sec_id, self.short_name, self.prev_wap_price, self.yield_at_prev_wap_price, self.prev_price,
                     self.face_value, self.mat_date, self.sec_name, self.currency_id, self.list_level, self.offer_date))


# Bond Schema
class BondSchema(ma.Schema):
    class Meta:
        fields = ('id', 'sec_id', 'short_name', 'prev_wap_price', 'yield_at_prev_wap_price', 'prev_price', 'face_value',
                  'mat_date', 'sec_name', 'currency_id', 'list_level', 'offer_date')


# Init schema
bond_schema = BondSchema()


# Update bond data
def get_moex_bond_data():
    url = "https://iss.moex.com/iss/engines/stock/markets/bonds/boardgroups/58/securities.json"
    response_fields = 'SECID,SHORTNAME,PREVWAPRICE,YIELDATPREVWAPRICE,PREVPRICE,FACEVALUE,MATDATE,SECNAME,CURRENCYID,' \
                      'LISTLEVEL,OFFERDATE'
    params = {'iss.meta': 'off', 'iss.only': 'securities',
              'securities.columns': response_fields}
    try:
        r = requests.get(url=url, params=params)
    except ConnectionError:
        app.logger.log('Failed to connect to MOEX')
        return

    data = r.json()
    securities = data.get('securities')
    bonds_plane_data = None
    if securities:
        bonds_plane_data = securities.get('data')
    if bonds_plane_data:
        for bond_plane in bonds_plane_data:
            bond = Bond(bond_plane[0], bond_plane[1], bond_plane[2], bond_plane[3], bond_plane[4], bond_plane[5],
                        None if bond_plane[6] == "0000-00-00" else bond_plane[6],
                        bond_plane[7], bond_plane[8], bond_plane[9], bond_plane[10])
            try:
                update_bond(bond)
            except Exception as e:
                logging.exception(e, exc_info=True)
    else:
        app.logger.error('No bond data received')


def update_bond(new_bond):
    bond_exists = db.session.query(Bond.id).filter_by(sec_id=new_bond.sec_id).first()
    if bond_exists is None:
        db.session.add(new_bond)
        db.session.commit()
        return
    db_bond = Bond.query.filter_by(sec_id=new_bond.sec_id)
    if new_bond == db_bond:
        return
    db_bond.sec_id = new_bond.sec_id
    db_bond.short_name = new_bond.short_name
    db_bond.prev_wap_price = new_bond.prev_wap_price
    db_bond.yield_at_prev_wap_price = new_bond.yield_at_prev_wap_price
    db_bond.prev_price = new_bond.prev_price
    db_bond.face_value = new_bond.face_value
    db_bond.mat_date = new_bond.mat_date
    db_bond.sec_name = new_bond.sec_name
    db_bond.currency_id = new_bond.currency_id
    db_bond.list_level = new_bond.list_level
    db_bond.offer_date = new_bond.offer_date
    db.session.commit()


while True:
    get_moex_bond_data()
    time.sleep(100)

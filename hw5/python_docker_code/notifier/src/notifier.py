import base64
import time
import requests
from operator import attrgetter

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
bot_token = base64.b64decode(secret['telegram']).decode('utf-8')


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
def send_telegram_message():

    bonds = Bond.query.all()
    if not bonds:
        message = "Something wrong, no available bonds"
    else:
        filtered_bonds = [bond for bond in bonds if bond.offer_date is not None]
        listing1 = [bond for bond in filtered_bonds if bond.list_level == 1 and
                    bond.yield_at_prev_wap_price is not None and bond.yield_at_prev_wap_price < 50]
        listing2 = [bond for bond in filtered_bonds if bond.list_level == 2 and
                    bond.yield_at_prev_wap_price is not None and bond.yield_at_prev_wap_price < 50]
        listing3 = [bond for bond in filtered_bonds if bond.list_level == 3 and
                    bond.yield_at_prev_wap_price is not None and bond.yield_at_prev_wap_price < 50]

        best_bond1 = max(listing1, key=attrgetter('yield_at_prev_wap_price'))
        best_bond2 = max(listing2, key=attrgetter('yield_at_prev_wap_price'))
        best_bond3 = max(listing3, key=attrgetter('yield_at_prev_wap_price'))

        message = f'Лучший безопасный бонд это {best_bond1.short_name} ' \
                  f'c доходностью {best_bond1.yield_at_prev_wap_price}\n' \
                  f'Лучший сред. риск бонд это {best_bond2.short_name} ' \
                  f'c доходностью {best_bond2.yield_at_prev_wap_price}\n' \
                  f'Лучший опасный бонд это {best_bond3.short_name} ' \
                  f'c доходностью {best_bond3.yield_at_prev_wap_price}'

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {'chat_id': '@bondiana_bonds',
              'text': message}
    try:
        requests.post(url=url, params=params)
    except Exception:
        app.logger.log('Failed to send telegram')
        return


while True:
    send_telegram_message()
    time.sleep(2000)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
import xmltodict
import json
from geopy.geocoders import Nominatim
from functools import wraps

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'AIzaSyCOD3KvY2DDzEfel-NZ_LKIWXr86EF_EUw'
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Address Class/Model


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(500))
    output_format = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    def __init__(self, address, output_format, lat, lng):
        self.address = address
        self.output_format = output_format
        self.lat = lat
        self.lng = lng

# Address Schema


class AddressSchema(ma.Schema):
    class Meta:
        fields = ('id', 'address', 'output_format', 'lat', 'lng')


# Init schema
address_schema = AddressSchema()
addresses_schema = AddressSchema(many=True)


def token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': 'You are not Authorized Person.'}), 403

        if token == (app.config['SECRET_KEY']):
            return f(*args, *kwargs)
        else:
            return jsonify({'message': 'Token is Invalid!'}), 403

    return decorated

# Add an Address


@app.route('/address', methods=['POST'])
@token
def add_address():
    address = request.json['address']
    output_format = request.json['output_format']
    try:
        geolocator = Nominatim(user_agent="mrd")
        location = geolocator.geocode(address)
    except:
        return jsonify({'message':'Please provide simple address.'})
    lat = location.latitude
    lng = location.longitude
    new_address = Address(address, output_format, lat, lng)

    db.session.add(new_address)
    db.session.commit()
    if output_format == 'json':
        return address_schema.jsonify(new_address)
    elif output_format == 'xml':
        sample_json = {"root": {"address": address,
                                "output_format": output_format, "coordinates": {"lat": lat, "lng": lng}}}
        json_to_xml = xmltodict.unparse(sample_json)
        return(json_to_xml)
    else:
        return jsonify({'message': 'Please provide either "JSON" or "XML" Output Format.'})

# Get All Addresses


@app.route('/addresses', methods=['GET'])
def get_addresses():
    all_addresses = Address.query.all()
    result = addresses_schema.dump(all_addresses)
    return jsonify(result)

# Get Single Address


@app.route('/address/<id>', methods=['GET'])
def get_address(id):
    address = Address.query.get(id)
    return address_schema.jsonify(address)

# Delete an Address


@app.route('/address/<id>', methods=['DELETE'])
def delete_address(id):
    address = Address.query.get(id)
    db.session.delete(address)
    db.session.commit()

    return address_schema.jsonify(address)


# Run Server
if __name__ == '__main__':
    app.run(debug=True)

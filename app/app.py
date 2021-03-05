from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import base64
import random
import json
import enum
import string
import os
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{os.environ.get("DB_USER")}:{os.environ.get("DB_PASS")}@postgres_db_container/vinehealthdb'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
class Gender(enum.Enum):
    MALE = 'M'
    FEMALE = 'F'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)
    
class Licence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80))
    middle_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    date_of_birth = db.Column(db.DateTime)
    gender = db.Column(db.Enum(Gender))
    driving_licence = db.Column(db.String(13)) 
 
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=True)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message':'New User Created!'}), 201

@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {"WWW-Authenticate":'Basic realm="Login Required!"'})
    
    user = User.query.filter_by(name=auth.username).first()
    if not user:
        return make_response('Could not verify', 401, {"WWW-Authenticate":'Basic realm="Login Required!"'})
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id':user.public_id, 'exp':datetime.utcnow() + timedelta(minutes=60)}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})
    
    return make_response('Could not verify', 401, {"WWW-Authenticate":'Basic realm="Login Required!"'})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message':'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message':'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def generate_licence_number(first_name, middle_name, last_name, date_of_birth, gender):
    digits_1_5 = last_name[0:5]
    if len(digits_1_5)<5:
        new_additon = '9' * (5 - len(digits_1_5))
        digits_1_5 += new_additon
        
    # convert date
    digit_6 = str(date_of_birth.year)[2]
    if gender == 'F':
        digits_7_8 = str(date_of_birth.month + 5)
    else:
        digits_7_8 = str(date_of_birth.month)
    digits_9_10 = str(date_of_birth.day)
    digit_11 = str(date_of_birth)[-1]
    
    # initials 
    digits_12_13 = first_name[0:2]
    
    # artibrary
    digit_14 = str(random.randint(1,9))
    
    rand_string1 = random.choice(string.ascii_letters)
    rand_string2 = random.choice(string.ascii_letters)
    digit_15_16 = rand_string1+rand_string2
    
    driving_licence = digits_1_5+digit_6+digits_7_8+digits_9_10+digit_11+digits_12_13+digit_14+digit_15_16
    return driving_licence.upper()
    
        
    
    

@app.route('/licence', methods=['POST'])
@token_required
def licence_number(current_user):
    data = request.data
    decoded_data = data.decode("utf-8")
    cleaned_data = json.loads(data)
    first_name=cleaned_data['first_name']
    middle_name=cleaned_data['middle_name']
    last_name=cleaned_data['last_name']
    gender=cleaned_data['gender']
    try:
        date_of_birth= datetime.strptime(cleaned_data['date_of_birth'],"%Y-%m-%d")
    except ValueError:
        return jsonify({'error': 'Please send dates in the format (YYYY-mm-dd)'})
    
    driving_licence = generate_licence_number(first_name, middle_name, last_name, date_of_birth, gender)
    
    new_licence = Licence(first_name=first_name, middle_name=middle_name,last_name=last_name,
                        date_of_birth=date_of_birth, gender=gender,driving_licence=driving_licence)
    db.session.add(new_licence)
    db.session.commit()

    return jsonify({'message':driving_licence}), 201

@app.route('/licences', methods=['GET'])
@token_required
def get_all_licences(current_user):
    objects = Licence.query.with_entities(Licence.name).all()
    return jsonify({'message':objects}), 200


    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
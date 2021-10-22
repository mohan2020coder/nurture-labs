import jwt
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from faker import Faker

app = Flask(__name__)

app.config['SECRET_KEY'] = 'SomeRandomSecretKey'
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///advisor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# creates SQLALCHEMY object
db = SQLAlchemy(app)


# Database ORMs
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))


class Advisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(140))
    photo_url = db.Column(db.String(150))


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    advisor_id = db.Column(db.Integer, db.ForeignKey('advisor.id'))
    date = db.Column(db.String(150))


# db.create_all()
#
#
# def dummy_data():
#     fake = Faker()
#     for i in range(10):
#         name = fake.name()
#         url = fake.url()
#         advisor = Advisor(name=name, photo_url=url)
#         db.session.add(advisor)
#         db.session.commit()

@app.route("/")
def home():
    return render_template('index.html')


@app.route('/admin/advisor', methods=['POST'])
def add_advisor():
    new_advisor_data = request.get_json()

    name = new_advisor_data['name']
    photo_url = new_advisor_data['photo_url']

    if name == "" and photo_url == "":
        return make_response('BAD_REQUEST', 400)
    else:
        advisor = Advisor.query.filter_by(name=name).first()
        if not advisor:
            # database ORM object
            advisor = Advisor(
                name=name,
                photo_url=photo_url,
            )
            # insert user
            db.session.add(advisor)
            db.session.commit()

        return make_response('OK', 200)


@app.route('/user/register', methods=['POST'])
def user_register():
    new_user = {}
    new_user_data = request.get_json()

    name = new_user_data['name']
    email = new_user_data['email']
    password = new_user_data['password']

    if name == "" and email == "" and password == "":
        return make_response('BAD_REQUEST', 400)
    else:
        user = User.query.filter_by(email=email).first()
        if not user:
            # database ORM object
            user = User(
                public_id=str(uuid.uuid4()),
                name=name,
                email=email,
                password=generate_password_hash(password)
            )
            # insert user
            db.session.add(user)
            db.session.commit()

            token = jwt.encode({
                'public_id': user.public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, app.config['SECRET_KEY'])
            new_user['id'] = user.id
            new_user['token'] = token

            return make_response(jsonify({'id': new_user['id'],
                                          'token': new_user['token']}), 200)
        else:
            # returns 202 if user already exists
            return make_response('User already exists. Please Log in.', 202)


# route for logging user in
@app.route('/user/login', methods=['POST'])
def user_login():
    # creates dictionary of form data
    auth = request.get_json()

    if not auth or not auth['email'] or not auth['password']:
        # returns 401 if any email or / and password is missing
        return make_response('BAD_REQUEST', 400)

    user = User.query.filter_by(email=auth['email']).first()

    if not user:
        # returns 401 if user does not exist
        return make_response(
            'AUTHENTICATION_ERROR',
            401)

    if check_password_hash(user.password, auth['password']):
        # generates the JWT Token
        token = jwt.encode({
            'public_id': user.public_id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'])
        user_id = user.id
        return make_response(jsonify({'token': token}, {'id': user_id}), 200)
    # returns 403 if password is wrong
    return make_response('AUTHENTICATION_ERROR', 401)


@app.route('/user/<int:user_id>/advisor/<int:advisor_id>', methods=['POST'])
def book_appointment(user_id, advisor_id):
    booking_date = request.get_json()
    if user_id and advisor_id:
        appointment = Appointment(user_id=user_id, advisor_id=advisor_id, date=booking_date['date_time'])
        # insert user
        db.session.add(appointment)
        db.session.commit()
        return make_response("OK", 200)


@app.route('/user/<int:user_id>/advisor', methods=['GET'])
def get_advisors(user_id):
    if user_id:
        return_values = []
        # advisors = Advisor.query.filter_by(user_id=user_id)
        advisors = Advisor.query.all()
        for advisor in advisors:
            advisor_dict = {'name': advisor.name,
                            'profile_pic': advisor.photo_url,
                            'id': advisor.id}

            return_values.append(advisor_dict)

        return make_response(jsonify({'advisors': return_values}), 200)


@app.route('/user/<int:user_id>/advisor/booking', methods=['GET'])
def appointments(user_id):
    if user_id:
        return_values = []
        appointments = Appointment.query.filter_by(user_id=user_id).all()
        for appointment in appointments:
            advisor = Advisor.query.filter_by(id=appointment.advisor_id).first()
            advisor_dict = {'name': advisor.name,
                            'profile_pic': advisor.photo_url,
                            'advisor_id': advisor.id,
                            'booking_time': appointment.date,
                            'booking_id': appointment.id}

            return_values.append(advisor_dict)

        return make_response(jsonify({'bookings': return_values}), 200)


if __name__ == '__main__':
    # dummy_data()
    app.run(debug=True)

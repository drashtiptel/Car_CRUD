
import secrets
from flask_cors import CORS
from flask import Flask, request, jsonify, make_response, session
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import bcrypt
import jwt 
import datetime
from functools import wraps
import logging
from sqlalchemy import or_
from config import Config
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message
import random
import string

app = Flask(__name__)
app.config.from_object(Config)


# bcrypt.init_app(app)

car_inventory = []
CORS(app) 
cors = CORS(app, resources={r"/add-car": {"origins": "*"}})
CORS(app, resources={r"/get-cars": {"origins": "http://127.0.0.1:5500"}})
cors = CORS(app, resources={r"/get-cars": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}})
cors = CORS(app, resources={r"/get-cars": {"origins": "*"}})
app.secret_key = 'super-secret-key'

blacklist = set()

# connection = mysql.connector.connect(host='localhost', port='3306', database='javascriptusing', user='root', password='drashti2908')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:drashti2908@localhost/javascriptusing'

db = SQLAlchemy(app)

bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    contactno = db.Column(db.VARCHAR(155), nullable=False)
    email = db.Column(db.VARCHAR(155), unique=True, nullable=False)



class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carName = db.Column(db.String(80), nullable=False)
    carModel = db.Column(db.String(80), nullable=False)
    carPrice = db.Column(db.Float, nullable=False)
    carBrand = db.Column(db.String(80), nullable=False)


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com' # Your SMTP server address
app.config['MAIL_PORT'] = 465  # Your SMTP port
app.config['MAIL_USE_SSL'] = True  # Enable ssl
app.config['MAIL_USERNAME'] = 'drashtivadaliya123@gmail.com'  # Your email username
app.config['MAIL_PASSWORD'] = 'zres wlyr odvo wnhy'  # Your email password

mail = Mail(app)



payload = {
    'user': 'your_user_identifier',  # This should be the unique identifier for the user (e.g., user ID)
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token valid for 1 hour
}

# Encode the token
token = jwt.encode(payload, app.secret_key, algorithm="HS256")
print(token)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check if the token is passed in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        if token in blacklist:
            return jsonify({'message': 'Token has been revoked!'}), 403

        try:
            # Decode the token using the app's secret key
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 403

        return f(current_user, *args, **kwargs)
    return decorated  

# Mock user database (replace this with your actual database)
users = {
    "drashtivadaliya123@gmail.com": {
        "password": "12345"  # Initially set to the old password
    }
}
# Function to generate a random password
def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# Forgot password endpoint
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    if email:
        # Generate a new password
        new_password = generate_password()
        otp = random.randint(1000,9999)
        otp_storage[email] = otp
            # Update password in the database
        if email in users:
                try:
                    users[email]['password'] = new_password
                    print(f"Password updated for user {email}")
                except Exception as e:
                    print(f"Error updating password for user {email}: {e}")
        else:
                print(f"User {email} not found in database")
                return jsonify({'message': 'Email Id not found.'}), 404

        # Send email with the new password
        msg = Message('Password Reset', sender='drashtivadaliya123@gmail.com', recipients=[email])
        msg.body = f'Your OTP for Forget Password is: {otp}'
        
        mail.send(msg)

        # Return success response
        return jsonify({'message': 'Password reset link sent to your email.'}), 200
    else:
        return jsonify({'error': 'Email address not provided.'}), 400

# Store OTPs temporarily
otp_storage = {}
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.json.get('email')
    otp = request.json.get('otp')
    if email and otp:
        stored_otp = otp_storage.get(email)
      
        if stored_otp and str(otp).strip() == str(stored_otp).strip():
            return jsonify({'message': 'OTP verification successful.'}), 200
        else:
            return jsonify({'error': 'Invalid OTP.'}), 400
    else:
        return jsonify({'error': 'Email address or OTP not provided.'}), 400

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.json.get('email')
    new_password = request.json.get('password')
    cnew_password = request.json.get('cnpassword')
    if email and new_password:
        if cnew_password == new_password:
            user = User.query.filter_by(email=email).first()
            user.password = new_password
            # Commit the changes to the database
            db.session.commit()
            return jsonify({'message': 'Password reset successful.'}), 200
        else:
            return jsonify({'error': 'New Password and cnew password not match.'}), 400
    else:
        return jsonify({'error': 'Email address or new password not provided.'}), 400


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    fname = data.get('fname')
    lname = data.get('lname')
    password = data.get('password')
    contactno = data.get('contactno')
    email = data.get('email')
    # created_at = data.get('created_at')

    if not fname or not lname or not password or not contactno or not email:
        return jsonify({"message": "All fields are required"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": "Email already exists"}), 400

    new_user = User(fname=fname, lname=lname, password=password, contactno=contactno, email=email, )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Registration successful"}), 200


    # You can add more fields as needed
    
    # Here you can do whatever you want with the registration data,
    # like storing it in a database
    
    # return "Registration successful for {} with email {}".format(username, email)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        # return jsonify({"message": "Email and password are required"}), 400
        response = {
            'status' : False,
            'message' : "Email and password are required",
            'token' : ""
        }
        return make_response(response, 400)

    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        # return jsonify({"message": "Invalid credentials"}), 401
        response = {
            'status' : False,
            'message' : "Invalid credentials",
            'token' : ""
        }
        return make_response(response, 401)


    token = jwt.encode({'user': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=5)}, app.config['SECRET_KEY'])

    response = {
        'status' : True,
        'message' : "Login Successfully",
        'token' : token
        }
    return make_response(response, 200)


@app.route('/add-car', methods=['POST'])
@token_required
def insert_item(current_user):
    data = request.get_json()
    newCar = Car(carName=data['carName'], carModel=data['carModel'], carPrice=data['carPrice'], carBrand=data['carBrand'])
    db.session.add(newCar)
    db.session.commit()
    return jsonify({'message': 'car Added successfully'})

@app.route('/get-car', methods=['POST'])
@token_required
def get_car(current_user):
    data = request.get_json()
    page_size = data.get('pageSize', 5)  # Default page size is 5
    page_number = data.get('pageNumber', 1)  # Default page number is 1
    search_query = data.get('searchQuery', '')  # Get the search query

    app.logger.info(f'Received data: {data}')
    # Calculate the offset based on the page number and page size

    offset = (page_number - 1) * page_size
    
    # Query to get the total count of cars
    if search_query:
        total_cars = Car.query.filter(Car.carName.ilike(f"%{search_query}%")).count()
        
    else:
        total_cars = Car.query.count()
    
    # Query to get the cars for the current page
    if search_query:
        cars = Car.query.filter(Car.carName.ilike(f"%{search_query}%")).offset(offset).limit(page_size).all()
    else:
        cars = Car.query.offset(offset).limit(page_size).all()
    
    # Calculate the total number of pages
    total_pages = (total_cars + page_size - 1) // page_size
    
    # Prepare the list of cars
    car_list = [{
        "carID": car.id,
        "carName": car.carName,
        "carModel": car.carModel,
        "carPrice": car.carPrice,
        "carBrand": car.carBrand
    } for car in cars]
    
    # Return the response with car list and total pages
    return jsonify({"cars": car_list, "totalPages": total_pages})


@app.route('/delete-car/<int:id>', methods=['DELETE'])  # Change 'PUT' to 'DELETE'
@token_required
def delete_car(current_user, id):
    car = Car.query.get_or_404(id)
    db.session.delete(car)
    db.session.commit()
    return jsonify({'message': 'Car deleted successfully'})


@app.route('/update-car/<int:id>', methods=['PUT'])
@token_required
def update_car(current_user, id):
    car = Car.query.get_or_404(id)
    data = request.get_json()
    print("!!!",data)
    car.carName = data.get('CarName', car.carName)
    car.carModel = data.get('CarModel', car.carModel)
    car.carPrice = data.get('CarPrice', car.carPrice)
    car.carBrand = data.get('CarBrand', car.carBrand)
    db.session.commit()
    return jsonify({'message': 'Car updated successfully'})



@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    # Check if user is logged in
    if 'user_id' in session:
        session.pop('user_id', None)  # Clear session data
    resp = make_response(jsonify({'message': 'Logout successful'}))
    # Explicitly set the cookie to expire
    resp.set_cookie('session', '', expires=0)  # Adjust the cookie name if different
    return resp


@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({'message': f'Welcome {current_user.username}!'})



if __name__ == '__main__':
 app.run(debug=True)

from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import Users
from werkzeug.utils import secure_filename
import os

users_bp = Blueprint('users', __name__)
bcrypt = Bcrypt()

UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@users_bp.route('/register', methods=['POST'])
def register_user():
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        if 'user_name' not in request.form or 'email' not in request.form or 'password' not in request.form:
            return jsonify({
                'status': 'error',
                'message': 'user_name, email, and password are required'
            }), 400

        user_name = request.form['user_name']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form.get('phone_number')
        country = request.form.get('country')

        if Users.query.filter_by(email=email).first():
            return jsonify({
                'status': 'error',
                'message': 'email already exists'
            }), 400

        avatar_url = None
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = str(int(os.times().elapsed * 1000))
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{email}_{timestamp}.{file_ext}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                avatar_url = f"/{file_path}"

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = Users(
            user_name=user_name,
            email=email,
            phone_number=phone_number,
            country=country,
            point=0,
            password=password_hash,
            avatar_url=avatar_url
        )
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=new_user.email)

        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'id': new_user.id,
                'user_name': new_user.user_name,
                'email': new_user.email,
                'phone_number': new_user.phone_number,
                'country': new_user.country,
                'point': new_user.point,
                'avatar_url': new_user.avatar_url,
                'access_token': access_token
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error registering user: {str(e)}'
        }), 500

@users_bp.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No input data provided'
            }), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'email and password are required'
            }), 400

        user = Users.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401

        access_token = create_access_token(identity=user.email)

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'id': user.id,
                'user_name': user.user_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'country': user.country,
                'avatar_url': user.avatar_url,
                'point': user.point,
                'access_token': access_token
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error logging in: {str(e)}'
        }), 500

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Profile retrieved successfully',
            'data': {
                'id': user.id,
                'user_name': user.user_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'country': user.country,
                'point': user.point,
                'avatar_url': user.avatar_url
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving profile: {str(e)}'
        }), 500
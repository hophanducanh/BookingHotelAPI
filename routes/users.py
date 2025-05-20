from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import Users
from werkzeug.utils import secure_filename
import os
from datetime import datetime

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
                'access_token': access_token,
                'date_of_birth': user.date_of_birth
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

@users_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No input data provided'
            }), 400

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({
                'status': 'error',
                'message': 'Current password and new password are required'
            }), 400

        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        if not bcrypt.check_password_hash(user.password, current_password):
            return jsonify({
                'status': 'error',
                'message': 'Current password is incorrect'
            }), 401

        new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = new_password_hash
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error changing password: {str(e)}'
        }), 500

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        user_name = request.form.get('user_name', user.user_name)
        new_email = request.form.get('email', user.email)
        phone_number = request.form.get('phone_number', user.phone_number)
        country = request.form.get('country', user.country)
        date_of_birth = request.form.get('date_of_birth')

        if new_email != user.email and Users.query.filter_by(email=new_email).first():
            return jsonify({
                'status': 'error',
                'message': 'Email already exists'
            }), 400

        if date_of_birth:
            try:
                date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid date_of_birth format. Use YYYY-MM-DD'
                }), 400

        avatar_url = user.avatar_url
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = str(int(os.times().elapsed * 1000))
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{new_email}_{timestamp}.{file_ext}"  # Use new_email for filename
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                avatar_url = f"/{file_path}"

                if user.avatar_url and os.path.exists(user.avatar_url[1:]):
                    os.remove(user.avatar_url[1:])

        user.user_name = user_name
        user.email = new_email
        user.phone_number = phone_number
        user.country = country
        user.date_of_birth = date_of_birth if date_of_birth else user.date_of_birth
        user.avatar_url = avatar_url
        db.session.commit()

        access_token = create_access_token(identity=user.email) if new_email != email else None

        response_data = {
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': {
                'id': user.id,
                'user_name': user.user_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'country': user.country,
                'point': user.point,
                'avatar_url': user.avatar_url,
                'date_of_birth': user.date_of_birth
            }
        }
        if access_token:
            response_data['data']['access_token'] = access_token

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error updating profile: {str(e)}'
        }), 500
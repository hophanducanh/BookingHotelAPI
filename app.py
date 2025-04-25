from datetime import timedelta

from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from extensions import db
from routes.locations import locations_bp
from routes.hotels import hotels_bp
from routes.users import users_bp
from routes.exec_sql import exec_sql_bp
from import_data import import_data

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jasoidopisdhjqwbmclkqmwlckpqisocuioqp[ojweiouifeojlmelcklecjejcopcjlwcj'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
db.init_app(app)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)


@jwt.unauthorized_loader
def custom_unauthorized_response(callback):
    return jsonify({
        'status': 'error',
        'message': 'Missing or invalid JWT. Please log in again.'
    }), 401

@jwt.invalid_token_loader
def custom_invalid_token_response(callback):
    return jsonify({
        'status': 'error',
        'message': 'Invalid JWT token.'
    }), 422

@jwt.expired_token_loader
def custom_expired_token_response(jwt_header, jwt_payload):
    return jsonify({
        'status': 'error',
        'message': 'JWT token has expired.'
    }), 401

@jwt.revoked_token_loader
def custom_revoked_token_response(jwt_header, jwt_payload):
    return jsonify({
        'status': 'error',
        'message': 'Token has been revoked.'
    }), 401

app.register_blueprint(locations_bp, url_prefix='/')
app.register_blueprint(hotels_bp, url_prefix='/')
app.register_blueprint(users_bp, url_prefix='/')
app.register_blueprint(exec_sql_bp,url_prefix='/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import_data(db)
    app.run(host='0.0.0.0',port=5000,debug=True)
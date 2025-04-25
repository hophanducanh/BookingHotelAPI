from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import Locations
from extensions import db

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/locations', methods=['GET'])
@jwt_required()
def get_locations():
    try:
        locations = Locations.query.all()
        result = [
            {
                'id_location': loc.id_location,
                'name': loc.name,
                'city': loc.city,
                'country': loc.country
            } for loc in locations
        ]
        response = {
            'status': 'success',
            'message': 'Locations retrieved successfully',
            'data': result
        }
        return jsonify(response), 200

    except Exception as e:
        response = {
            'status': 'error',
            'message': f'Error retrieving locations: {str(e)}',
            'data': []
        }
        return jsonify(response), 500
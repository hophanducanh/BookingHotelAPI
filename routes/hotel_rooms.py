from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import Hotel_Room, Hotel
from extensions import db
from sqlalchemy.orm import joinedload

hotel_rooms_bp = Blueprint('hotel_rooms', __name__)

@hotel_rooms_bp.route('/hotels/<int:hotel_id>/rooms', methods=['GET'])
@jwt_required()
def getRoomByHotelId(hotel_id):
    try:
        # Check if hotel exists
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            response = {
                'status': 'error',
                'message': f'Hotel with id {hotel_id} not found',
                'data': [],
                'pagination': {}
            }
            return jsonify(response), 404

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if page < 1 or per_page < 1:
            response = {
                'status': 'error',
                'message': 'Page and per_page must be positive integers',
                'data': [],
                'pagination': {}
            }
            return jsonify(response), 400

        # Query rooms for the hotel
        query = Hotel_Room.query.filter_by(hotel_id=hotel_id).options(
            joinedload(Hotel_Room.hotel)
        )

        # Paginate the query
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        rooms = pagination.items

        # Prepare response data
        result = []
        for room in rooms:
            result.append({
                'id_hotel_room': room.id_hotel_room,
                'hotel_id': room.hotel_id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'hotel_name': room.hotel.hotel_name if room.hotel else None
            })

        # Pagination info
        pagination_info = {
            'current_page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_rooms': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_page': pagination.prev_num,
            'next_page': pagination.next_num
        }

        response = {
            'status': 'success',
            'message': f'Rooms for hotel id {hotel_id} retrieved successfully',
            'data': result,
            'pagination': pagination_info
        }
        return jsonify(response), 200

    except Exception as e:
        response = {
            'status': 'error',
            'message': f'Error retrieving rooms: {str(e)}',
            'data': [],
            'pagination': {}
        }
        return jsonify(response), 500
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import Hotel, Locations, HotelFacilities, Facilities
from extensions import db
import json
from sqlalchemy import asc, desc, or_

hotels_bp = Blueprint('hotels', __name__)

VALID_SORT_FIELDS = ['hotel_name', 'new_price', 'old_price', 'hotel_star', 'hotel_rating']
VALID_SEARCH_FIELDS = ['hotel_name', 'address', 'facilities']

@hotels_bp.route('/hotels/location/<int:id>', methods=['GET'])
@jwt_required()
def get_hotels_by_location(id):
    try:
        location = Locations.query.get(id)
        if not location:
            response = {
                'status': 'error',
                'message': f'Location with id {id} not found',
                'data': [],
                'pagination': {}
            }
            return jsonify(response), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', default=None)
        sort_order = request.args.get('sort_order', default='asc')
        search_field = request.args.get('search_field', default=None)
        search_value = request.args.get('search_value', default=None)

        if page < 1 or per_page < 1:
            response = {
                'status': 'error',
                'message': 'Page and per_page must be positive integers',
                'data': [],
                'pagination': {}
            }
            return jsonify(response), 400

        query = Hotel.query.filter_by(id_location=id)

        if search_field and search_value:
            search_fields = search_field.split(',')
            invalid_fields = [field for field in search_fields if field not in VALID_SEARCH_FIELDS]
            if invalid_fields:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid search_field(s): {invalid_fields}. Must be one of {VALID_SEARCH_FIELDS}',
                    'data': [],
                    'pagination': {}
                }), 400

            search_pattern = f'%{search_value}%'
            search_conditions = []

            # Tạo điều kiện tìm kiếm cho từng trường được chỉ định
            for field in search_fields:
                if field == 'hotel_name':
                    search_conditions.append(Hotel.hotel_name.ilike(search_pattern))
                elif field == 'address':
                    search_conditions.append(Hotel.address.ilike(search_pattern))
                elif field == 'facilities':
                    query = query.outerjoin(HotelFacilities).outerjoin(Facilities)
                    search_conditions.append(Facilities.name.ilike(search_pattern))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        if sort_by:
            if sort_by not in VALID_SORT_FIELDS:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid sort_by. Must be one of {VALID_SORT_FIELDS}',
                    'data': [],
                    'pagination': {}
                }), 400
            sort_column = getattr(Hotel, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        hotels = pagination.items
        result = []

        for hotel in hotels:
            facilities = [facility.name for facility in hotel.facilities]
            policies = hotel.policies
            images = [image.image_url for image in hotel.images]
            hotel_data = {
                'id': hotel.id,
                'hotel_name': hotel.hotel_name,
                'new_price': hotel.new_price,
                'old_price': hotel.old_price,
                'hotel_star': hotel.hotel_star,
                'hotel_rating': hotel.hotel_rating,
                'address': hotel.address,
                'image': images,
                'policies': policies,
                'descriptions':hotel.description,
                'location': {
                    'id_location': hotel.location.id_location,
                    'name': hotel.location.name,
                    'city': hotel.location.city,
                    'country': hotel.location.country
                },
                'facilities': facilities
            }
            result.append(hotel_data)

        pagination_info = {
            'current_page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_hotels': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_page': pagination.prev_num,
            'next_page': pagination.next_num
        }

        response = {
            'status': 'success',
            'message': f'Hotels for location id {id} retrieved successfully',
            'data': result,
            'pagination': pagination_info
        }
        return jsonify(response), 200

    except Exception as e:
        response = {
            'status': 'error',
            'message': f'Error retrieving hotels: {str(e)}',
            'data': [],
            'pagination': {}
        }
        return jsonify(response), 500
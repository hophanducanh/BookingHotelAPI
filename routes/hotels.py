from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import Hotel, Locations, HotelFacilities, Facilities, Comment
from extensions import db
from sqlalchemy import asc, desc, and_, func
from sqlalchemy.orm import joinedload

hotels_bp = Blueprint('hotels', __name__)

VALID_SORT_FIELDS = ['hotel_name', 'new_price', 'old_price', 'hotel_star', 'hotel_rating']
VALID_SEARCH_FIELDS = ['hotel_name', 'address', 'facilities', 'hotel_star']

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

        if page < 1 or per_page < 1:
            response = {
                'status': 'error',
                'message': 'Page and per_page must be positive integers',
                'data': [],
                'pagination': {}
            }
            return jsonify(response), 400

        # Base query
        query = Hotel.query.filter_by(id_location=id).outerjoin(
            Comment, Hotel.id == Comment.hotel_id
        ).group_by(Hotel.id).add_columns(
            func.avg(Comment.rating_point).label('user_rating')
        ).options(
            joinedload(Hotel.facilities),
            joinedload(Hotel.images),
            joinedload(Hotel.location)
        )

        search_conditions = []
        having_conditions = []

        # Filter by fields (original logic)
        for param, value in request.args.items():
            if param in ['page', 'per_page', 'sort_by', 'sort_order',
                         'hotel_star_min', 'hotel_star_max',
                         'user_rating_min', 'user_rating_max',
                         'new_price_min', 'new_price_max']:
                continue
            if param not in VALID_SEARCH_FIELDS:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid search parameter: {param}. Must be one of {VALID_SEARCH_FIELDS}',
                    'data': [],
                    'pagination': {}
                }), 400

            if param == 'hotel_star':
                try:
                    star_value = float(value)
                    search_conditions.append(Hotel.hotel_star == star_value)
                except ValueError:
                    return jsonify({
                        'status': 'error',
                        'message': f'Invalid value for hotel_star: {value}. Must be a valid number',
                        'data': [],
                        'pagination': {}
                    }), 400
            else:
                search_pattern = f'%{value}%'
                if param == 'hotel_name':
                    search_conditions.append(Hotel.hotel_name.ilike(search_pattern))
                elif param == 'address':
                    search_conditions.append(Hotel.address.ilike(search_pattern))
                elif param == 'facilities':
                    query = query.outerjoin(HotelFacilities).outerjoin(Facilities)
                    search_conditions.append(Facilities.name.ilike(search_pattern))

        # --- New range filter logic ---
        hotel_star_min = request.args.get('hotel_star_min', type=float)
        hotel_star_max = request.args.get('hotel_star_max', type=float)
        user_rating_min = request.args.get('user_rating_min', type=float)
        user_rating_max = request.args.get('user_rating_max', type=float)
        new_price_min = request.args.get('new_price_min', type=int)
        new_price_max = request.args.get('new_price_max', type=int)

        if hotel_star_min is not None:
            search_conditions.append(Hotel.hotel_star >= hotel_star_min)
        if hotel_star_max is not None:
            search_conditions.append(Hotel.hotel_star <= hotel_star_max)
        if new_price_min is not None:
            search_conditions.append(Hotel.new_price >= new_price_min)
        if new_price_max is not None:
            search_conditions.append(Hotel.new_price <= new_price_max)

        if user_rating_min is not None:
            having_conditions.append(func.avg(Comment.rating_point) >= user_rating_min)
        if user_rating_max is not None:
            having_conditions.append(func.avg(Comment.rating_point) <= user_rating_max)

        if search_conditions:
            query = query.filter(and_(*search_conditions))

        if having_conditions:
            query = query.having(and_(*having_conditions))

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
        for hotel, user_rating in hotels:
            # Filter by user_rating after query
            if user_rating_min is not None and (user_rating is None or user_rating < user_rating_min):
                continue
            if user_rating_max is not None and (user_rating is None or user_rating > user_rating_max):
                continue

            result.append({
                'id': hotel.id,
                'hotel_name': hotel.hotel_name,
                'new_price': hotel.new_price,
                'old_price': hotel.old_price,
                'hotel_star': hotel.hotel_star,
                'hotel_rating': hotel.hotel_rating,
                'user_rating': float(user_rating) if user_rating is not None else None,
                'address': hotel.address,
                'image': [image.image_url for image in hotel.images],
                'policies': hotel.policies,
                'descriptions': hotel.description,
                'distance':hotel.distance,
                'location': {
                    'id_location': hotel.location.id_location,
                    'name': hotel.location.name,
                    'city': hotel.location.city,
                    'country': hotel.location.country
                },
                'facilities': [facility.name for facility in hotel.facilities]
            })

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

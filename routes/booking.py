from flask import Blueprint, request, jsonify
from extensions import db
from models import Hotel_Room, Booking, Users, Hotel, UserDiscount
from datetime import datetime
from sqlalchemy import and_, not_
from flask_jwt_extended import jwt_required, get_jwt_identity

booking = Blueprint('booking', __name__, url_prefix='/')

@booking.route('/available-rooms', methods=['GET'])
@jwt_required()
def get_available_rooms():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        hotel_id = request.args.get('hotel_id', type=int)
        check_in_str = request.args.get('check_in')
        check_out_str = request.args.get('check_out')
        room_type = request.args.get('room_type')

        if not all([hotel_id, check_in_str, check_out_str]):
            return jsonify({'status': 'error', 'message': 'Missing required parameters'}), 400

        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

        if check_in >= check_out:
            return jsonify({'status': 'error', 'message': 'Check-in must be before check-out'}), 400

        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            return jsonify({'status': 'error', 'message': 'Hotel not found'}), 404

        booked_rooms = db.session.query(Booking.room_id).filter(
            Booking.room_id.in_(
                db.session.query(Hotel_Room.id_hotel_room).filter(Hotel_Room.hotel_id == hotel_id)
            ),
            Booking.check_out > check_in,
            Booking.check_in < check_out
        ).distinct()

        query = Hotel_Room.query.filter(
            Hotel_Room.hotel_id == hotel_id,
            ~Hotel_Room.id_hotel_room.in_(booked_rooms)
        )
        if room_type:
            query = query.filter(Hotel_Room.room_type == room_type)

        rooms = [{
            'id_hotel_room': room.id_hotel_room,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'hotel_id': room.hotel_id
        } for room in query.all()]

        return jsonify({'status': 'success', 'message': 'Rooms retrieved', 'data': rooms}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@booking.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        data = request.get_json()
        required = ['room_id', 'check_in', 'check_out', 'number_of_people', 'number_of_rooms', 'number_of_children']
        if not data or not all(k in data for k in required):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        room_id = data['room_id']
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        print(check_in, check_out)
        if check_in >= check_out:
            return jsonify({'status': 'error', 'message': 'Invalid dates'}), 400

        room = Hotel_Room.query.get(room_id)
        if not room:
            return jsonify({'status': 'error', 'message': 'Room not found'}), 404

        hotel = room.hotel
        num_days = (check_out - check_in).days
        daily_price = hotel.new_price
        base_price = num_days * daily_price

        discount_value = 0
        discount_info = {}
        final_price = base_price
        user_discount_id = data.get('user_discount_id')

        if user_discount_id:
            user_discount = UserDiscount.query.get(user_discount_id)
            if (
                    not user_discount or
                    user_discount.user_id != user.id or
                    user_discount.amount <= 0
            ):
                return jsonify({'status': 'error', 'message': 'Invalid or expired discount'}), 400

            discount = user_discount.discount
            discount_value = discount.discount_value
            final_price = max(0, base_price * (1 - discount_value / 100))

            user_discount.amount -= 1

            discount_info = {
                'discount_id': discount.id,
                'discount_name': discount.discount_name,
                'description': discount.description,
                'discount_value_percent': discount.discount_value,
                'point_required': discount.point_required
            }

        # Check room availability
        conflicts = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.check_out > check_in,
            Booking.check_in < check_out
        ).count()
        print(conflicts)
        if conflicts > 0:
            return jsonify({'status': 'error', 'message': 'Room not available'}), 409

        booking = Booking(
            room_id=room_id,
            users_id=user.id,
            check_in=check_in,
            check_out=check_out,
            number_of_people=data['number_of_people'],
            number_of_rooms=data['number_of_rooms'],
            number_of_children=data['number_of_children'],
            price=final_price,
            user_discount_id=user_discount_id
        )

        user.point += 10
        db.session.add(booking)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Booking created', 'data': {
            'booking_id': booking.id,
            'user_points': user.point,
            'hotel_info': {
                'hotel_id': hotel.id,
                'hotel_name': hotel.hotel_name,
                'address': hotel.address,
                'star': hotel.hotel_star,
                'description': hotel.description
            },
            'room_info': {
                'room_id': room_id,
                'room_type': room.room_type,
                'room_price': daily_price
            },
            'booking_info': {
                'check_in': data['check_in'],
                'check_out': data['check_out'],
                'num_days': num_days,
                'number_of_people': data['number_of_people'],
                'number_of_rooms': data['number_of_rooms'],
                'number_of_children': data['number_of_children'],
                'base_price': base_price,
                'discount_applied': bool(user_discount_id),
                'discount_info': discount_info,
                'total_price': final_price
            }
        }}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500




@booking.route('/calculate-price', methods=['POST'])
@jwt_required()
def calculate_price():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        data = request.get_json()
        required = ['room_id', 'check_in', 'check_out']
        if not data or not all(k in data for k in required):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        room_id = data['room_id']
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        if check_in >= check_out:
            return jsonify({'status': 'error', 'message': 'Invalid dates'}), 400

        room = Hotel_Room.query.get(room_id)
        if not room:
            return jsonify({'status': 'error', 'message': 'Room not found'}), 404

        num_days = (check_out - check_in).days
        price = num_days * room.hotel.new_price

        discount_value = 0
        user_discount_id = data.get('user_discount_id')
        if user_discount_id:
            discount = UserDiscount.query.get(user_discount_id)
            if not discount or discount.user_id != user.id:
                return jsonify({'status': 'error', 'message': 'Invalid discount'}), 400
            discount_value = discount.discount.discount_value
            price = max(0, price * (1 - discount_value / 100))

        return jsonify({'status': 'success', 'message': 'Price calculated', 'data': {
            'room_id': room_id,
            'hotel_id': room.hotel_id,
            'room_type': room.room_type,
            'check_in': data['check_in'],
            'check_out': data['check_out'],
            'num_days': num_days,
            'daily_price': room.hotel.new_price,
            'discount_value': discount_value,
            'total_price': price
        }}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@booking.route('/booking-history', methods=['GET'])
@jwt_required()
def booking_history():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        bookings = Booking.query.filter_by(users_id=user.id).order_by(Booking.check_in.desc()).all()

        history = []
        for b in bookings:
            room = Hotel_Room.query.get(b.room_id)
            hotel = room.hotel

            history.append({
                'booking_id': b.id,
                'check_in': b.check_in.strftime('%Y-%m-%d'),
                'check_out': b.check_out.strftime('%Y-%m-%d'),
                'number_of_people': b.number_of_people,
                'number_of_children': b.number_of_children,
                'number_of_rooms': b.number_of_rooms,
                'price': b.price,
                'room_info': {
                    'room_id': room.id_hotel_room,
                    'room_number': room.room_number,
                    'room_type': room.room_type
                },
                'hotel_info': {
                    'hotel_id': hotel.id,
                    'hotel_name': hotel.hotel_name,
                    'address': hotel.address,
                    'star': hotel.hotel_star,
                    'description': hotel.description
                }
            })

        return jsonify({'status': 'success', 'message': 'Booking history retrieved', 'data': history}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

from flask import Blueprint, request, jsonify
from extensions import db
from models import Hotel_Room, Booking, Users, Hotel, UserDiscount, Discount
from datetime import datetime
from sqlalchemy import and_, not_
from flask_jwt_extended import jwt_required, get_jwt_identity


discount = Blueprint('discount', __name__, url_prefix='/')


@discount.route('/change-discount', methods=['POST'])
@jwt_required()
def change_discount():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        data = request.get_json()
        if not data or 'discount_id' not in data:
            return jsonify({'status': 'error', 'message': 'Missing discount_id'}), 400

        discount_id = data['discount_id']

        discount = Discount.query.filter_by(id=discount_id).first()
        if not discount:
            return jsonify({'status': 'error', 'message': 'Discount not found'}), 404

        if user.point < discount.point_required:
            return jsonify({'status': 'error', 'message': 'Not enough points for this discount'}), 400

        user_discount = UserDiscount.query.filter_by(user_id=user.id, discount_id=discount.id).first()

        if user_discount:
            user_discount.amount = user_discount.amount + 1 if user_discount.amount else 1
        else:
            user_discount = UserDiscount(
                user_id=user.id,
                discount_id=discount.id,
                is_used=False,
                amount=1
            )
            db.session.add(user_discount)

        user.point -= discount.point_required

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Discount claimed successfully',
            'data': {
                'discount_id': discount.id,
                'discount_value': discount.discount_value,
                'amount': user_discount.amount,
                'remaining_points': user.point
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500



@discount.route('/get-discount', methods=['GET'])
@jwt_required()
def get_user_discounts():
    try:
        email = get_jwt_identity()
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        user_discounts = UserDiscount.query.filter_by(user_id=user.id).all()

        data = []
        for ud in user_discounts:
            discount = Discount.query.get(ud.discount_id)
            if discount:
                data.append({
                    'discount_id': discount.id,
                    'discount_name': discount.discount_name,
                    'discount_value': discount.discount_value,
                    'point_required': discount.point_required,
                    'is_used': ud.is_used,
                    'amount': ud.amount
                })

        return jsonify({
            'status': 'success',
            'message': 'User discounts retrieved successfully',
            'data': data
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@discount.route('/all-discounts', methods=['GET'])
def get_all_discounts():
    try:
        discounts = Discount.query.all()
        data = [
            {
                'id': d.id,
                'discount_name': d.discount_name,
                'discount_value': d.discount_value,
                'point_required': d.point_required,
                'description': d.description if hasattr(d, 'description') else None
            }
            for d in discounts
        ]

        return jsonify({
            'status': 'success',
            'message': 'All discounts retrieved successfully',
            'data': data
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

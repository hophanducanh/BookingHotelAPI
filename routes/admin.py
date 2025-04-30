from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Discount, Hotel, Locations, Users, Comment, Hotel_Room
from sqlalchemy.sql import func

admin_bp = Blueprint('admin', __name__, template_folder='templates')


def paginate_query(query, page, per_page=10):
    return query.paginate(page=page, per_page=per_page, error_out=False)


@admin_bp.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@admin_bp.route('/admin/discounts', methods=['GET', 'POST'])
def manage_discounts():
    page = request.args.get('page', 1, type=int)
    message = None
    message_type = None

    if request.method == 'POST':
        try:
            discount = Discount(
                discount_name=request.form['discount_name'],
                description=request.form['description'],
                point_required=int(request.form['point_required'])
            )
            db.session.add(discount)
            db.session.commit()
            message = 'Discount added successfully!'
            message_type = 'success'
        except Exception as e:
            db.session.rollback()
            message = f'Error adding discount: {str(e)}'
            message_type = 'error'

    discounts = paginate_query(Discount.query, page)
    return render_template('admin_discounts.html', discounts=discounts, message=message, message_type=message_type)


@admin_bp.route('/admin/discounts/delete/<int:id>')
def delete_discount(id):
    discount = Discount.query.get_or_404(id)
    message = None
    message_type = None

    try:
        db.session.delete(discount)
        db.session.commit()
        message = 'Discount deleted successfully!'
        message_type = 'success'
    except Exception as e:
        db.session.rollback()
        message = f'Error deleting discount: {str(e)}'
        message_type = 'error'

    discounts = paginate_query(Discount.query, page=1)
    return render_template('admin_discounts.html', discounts=discounts, message=message, message_type=message_type)


@admin_bp.route('/admin/hotels', methods=['GET', 'POST'])
def manage_hotels():
    page = request.args.get('page', 1, type=int)
    message = None
    message_type = None

    if request.method == 'POST':
        try:
            hotel = Hotel(
                hotel_name=request.form['hotel_name'],
                new_price=int(request.form['new_price']),
                old_price=int(request.form['old_price']),
                hotel_star=float(request.form['hotel_star']),
                hotel_rating=float(request.form['hotel_rating']),
                address=request.form['address'],
                policies=request.form['policies'],
                description=request.form['description'],
                distance=request.form['distance'],
                id_location=int(request.form['id_location'])
            )
            db.session.add(hotel)
            db.session.commit()
            message = 'Hotel added successfully!'
            message_type = 'success'
        except Exception as e:
            db.session.rollback()
            message = f'Error adding hotel: {str(e)}'
            message_type = 'error'

    hotels = paginate_query(Hotel.query, page)
    for hotel in hotels.items:
        avg_rating = db.session.query(func.avg(Comment.rating_point)).filter(Comment.hotel_id == hotel.id).scalar()
        hotel.user_rating = float(avg_rating) if avg_rating else None

    locations = Locations.query.all()
    return render_template('admin_hotels.html', hotels=hotels, locations=locations, message=message,
                           message_type=message_type)


@admin_bp.route('/admin/hotels/<int:id>')
def hotel_detail(id):
    hotel = Hotel.query.get_or_404(id)
    avg_rating = db.session.query(func.avg(Comment.rating_point)).filter(Comment.hotel_id == hotel.id).scalar()
    hotel.user_rating = float(avg_rating) if avg_rating else None
    return render_template('admin_hotel_detail.html', hotel=hotel)


@admin_bp.route('/admin/hotels/edit/<int:id>', methods=['GET', 'POST'])
def edit_hotel(id):
    hotel = Hotel.query.get_or_404(id)
    locations = Locations.query.all()
    message = None
    message_type = None

    if request.method == 'POST':
        try:
            hotel.hotel_name = request.form['hotel_name']
            hotel.new_price = int(request.form['new_price'])
            hotel.old_price = int(request.form['old_price'])
            hotel.hotel_star = float(request.form['hotel_star'])
            hotel.hotel_rating = float(request.form['hotel_rating'])
            hotel.address = request.form['address']
            hotel.policies = request.form['policies']
            hotel.description = request.form['description']
            hotel.distance = request.form['distance']
            hotel.id_location = int(request.form['id_location'])
            db.session.commit()
            message = 'Hotel updated successfully!'
            message_type = 'success'
            return render_template('admin_hotel_detail.html', hotel=hotel, message=message, message_type=message_type)
        except Exception as e:
            db.session.rollback()
            message = f'Error updating hotel: {str(e)}'
            message_type = 'error'

    return render_template('admin_edit_hotel.html', hotel=hotel, locations=locations, message=message,
                           message_type=message_type)


@admin_bp.route('/admin/hotels/delete/<int:id>')
def delete_hotel(id):
    hotel = Hotel.query.get_or_404(id)
    message = None
    message_type = None

    try:
        db.session.delete(hotel)
        db.session.commit()
        message = 'Hotel deleted successfully!'
        message_type = 'success'
    except Exception as e:
        db.session.rollback()
        message = f'Error deleting hotel: {str(e)}'
        message_type = 'error'

    hotels = paginate_query(Hotel.query, page=1)
    locations = Locations.query.all()
    return render_template('admin_hotels.html', hotels=hotels, locations=locations, message=message,
                           message_type=message_type)


@admin_bp.route('/admin/hotels/<int:hotel_id>/rooms', methods=['GET', 'POST'])
def manage_hotel_rooms(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Hotel_Room.query.filter_by(hotel_id=hotel_id).all()
    message = None
    message_type = None

    if request.method == 'POST':
        try:
            room = Hotel_Room(
                room_number=request.form['room_number'],
                room_type=request.form['room_type'],
                hotel_id=hotel_id
            )
            db.session.add(room)
            db.session.commit()
            message = 'Room added successfully!'
            message_type = 'success'
        except Exception as e:
            db.session.rollback()
            message = f'Error adding room: {str(e)}'
            message_type = 'error'

    return render_template('admin_hotel_rooms.html', hotel=hotel, rooms=rooms, message=message,
                           message_type=message_type)


@admin_bp.route('/admin/rooms/delete/<int:id>')
def delete_hotel_room(id):
    room = Hotel_Room.query.get_or_404(id)
    hotel_id = room.hotel_id
    message = None
    message_type = None

    try:
        db.session.delete(room)
        db.session.commit()
        message = 'Room deleted successfully!'
        message_type = 'success'
    except Exception as e:
        db.session.rollback()
        message = f'Error deleting room: {str(e)}'
        message_type = 'error'

    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Hotel_Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('admin_hotel_rooms.html', hotel=hotel, rooms=rooms, message=message,
                           message_type=message_type)


@admin_bp.route('/admin/locations', methods=['GET', 'POST'])
def manage_locations():
    page = request.args.get('page', 1, type=int)
    message = None
    message_type = None

    if request.method == 'POST':
        try:
            location = Locations(
                name=request.form['name'],
                country=request.form['country'],
                city=request.form['city']
            )
            db.session.add(location)
            db.session.commit()
            message = 'Location added successfully!'
            message_type = 'success'
        except Exception as e:
            db.session.rollback()
            message = f'Error adding location: {str(e)}'
            message_type = 'error'

    locations = paginate_query(Locations.query, page)
    return render_template('admin_locations.html', locations=locations, message=message, message_type=message_type)


@admin_bp.route('/admin/locations/delete/<int:id>')
def delete_location(id):
    location = Locations.query.get_or_404(id)
    message = None
    message_type = None

    try:
        db.session.delete(location)
        db.session.commit()
        message = 'Location deleted successfully!'
        message_type = 'success'
    except Exception as e:
        db.session.rollback()
        message = f'Error deleting location: {str(e)}'
        message_type = 'error'

    locations = paginate_query(Locations.query, page=1)
    return render_template('admin_locations.html', locations=locations, message=message, message_type=message_type)


@admin_bp.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    page = request.args.get('page', 1, type=int)
    message = None
    message_type = None

    if request.method == 'POST':
        try:
            user = Users(
                user_name=request.form['user_name'],
                email=request.form['email'],
                phone_number=request.form['phone_number'],
                country=request.form['country'],
                password=request.form['password'],
                avatar_url=request.form['avatar_url'],
                point=int(request.form['point'])
            )
            db.session.add(user)
            db.session.commit()
            message = 'User added successfully!'
            message_type = 'success'
        except Exception as e:
            db.session.rollback()
            message = f'Error adding user: {str(e)}'
            message_type = 'error'

    users = paginate_query(Users.query, page)
    return render_template('admin_users.html', users=users, message=message, message_type=message_type)


@admin_bp.route('/admin/users/delete/<int:id>')
def delete_user(id):
    user = Users.query.get_or_404(id)
    message = None
    message_type = None

    try:
        db.session.delete(user)
        db.session.commit()
        message = 'User deleted successfully!'
        message_type = 'success'
    except Exception as e:
        db.session.rollback()
        message = f'Error deleting user: {str(e)}'
        message_type = 'error'

    users = paginate_query(Users.query, page=1)
    return render_template('admin_users.html', users=users, message=message, message_type=message_type)
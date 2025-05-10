from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Discount, Hotel, Locations, Users, Comment, Hotel_Room, Booking
from sqlalchemy.sql import func
from datetime import datetime
from urllib.parse import urlencode

admin = Blueprint('admin', __name__, template_folder='templates')


# Helper function for pagination
def paginate_query(query, page, per_page=10):
    return query.paginate(page=page, per_page=per_page, error_out=False)


@admin.route('/')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@admin.route('/message')
def show_message():
    message = request.args.get('message', 'No message provided')
    status = request.args.get('status', 'error')
    back_url = request.args.get('back_url', url_for('admin.admin_dashboard'))
    return render_template('message.html', message=message, status=status, back_url=back_url)


@admin.route('/hotels', methods=['GET', 'POST'])
def manage_hotels():
    page = request.args.get('page', 1, type=int)
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
            return redirect(url_for('admin.show_message',
                                    message='Hotel added successfully!',
                                    status='success',
                                    back_url=url_for('admin.manage_hotels')))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('admin.show_message',
                                    message=f'Error adding hotel: {str(e)}',
                                    status='error',
                                    back_url=url_for('admin.manage_hotels')))

    # Query hotels with their average user rating
    hotels = paginate_query(Hotel.query, page)

    # Calculate user_rating for each hotel
    for hotel in hotels.items:
        avg_rating = db.session.query(func.avg(Comment.rating_point)).filter(Comment.hotel_id == hotel.id).scalar()
        hotel.user_rating = float(avg_rating) if avg_rating else None

    locations = Locations.query.all()
    return render_template('admin_hotels.html', hotels=hotels, locations=locations)


@admin.route('/hotels/<int:id>')
def hotel_detail(id):
    hotel = Hotel.query.get_or_404(id)
    # Calculate user_rating
    avg_rating = db.session.query(func.avg(Comment.rating_point)).filter(Comment.hotel_id == hotel.id).scalar()
    hotel.user_rating = float(avg_rating) if avg_rating else None
    # Fetch bookings for this hotel
    hotel_bookings = Booking.query.join(Hotel_Room).filter(Hotel_Room.hotel_id == hotel.id).all()
    return render_template('admin_hotel_detail.html', hotel=hotel, hotel_bookings=hotel_bookings)


@admin.route('/hotels/<int:id>/add_room', methods=['POST'])
def add_hotel_room(id):
    hotel = Hotel.query.get_or_404(id)
    try:
        room = Hotel_Room(
            room_number=request.form['room_number'],
            room_type=request.form['room_type'],
            hotel_id=hotel.id
        )
        db.session.add(room)
        db.session.commit()
        return redirect(url_for('admin.show_message',
                                message='Room added successfully!',
                                status='success',
                                back_url=url_for('admin.hotel_detail', id=hotel.id)))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('admin.show_message',
                                message=f'Error adding room: {str(e)}',
                                status='error',
                                back_url=url_for('admin.hotel_detail', id=hotel.id)))


@admin.route('/hotels/delete/<int:id>')
def delete_hotel(id):
    hotel = Hotel.query.get_or_404(id)
    try:
        db.session.delete(hotel)
        db.session.commit()
        return redirect(url_for('admin.show_message',
                                message='Hotel deleted successfully!',
                                status='success',
                                back_url=url_for('admin.manage_hotels')))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('admin.show_message',
                                message=f'Error deleting hotel: {str(e)}',
                                status='error',
                                back_url=url_for('admin.manage_hotels')))


@admin.route('/discounts', methods=['GET', 'POST'])
def manage_discounts():
    page = request.args.get('page', 1, type=int)
    if request.method == 'POST':
        try:
            discount = Discount(
                discount_name=request.form['discount_name'],
                description=request.form['description'],
                point_required=int(request.form['point_required']),
                discount_value=float(request.form['discount_value'])
            )
            db.session.add(discount)
            db.session.commit()
            return redirect(url_for('admin.show_message',
                                    message='Discount added successfully!',
                                    status='success',
                                    back_url=url_for('admin.manage_discounts')))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('admin.show_message',
                                    message=f'Error adding discount: {str(e)}',
                                    status='error',
                                    back_url=url_for('admin.manage_discounts')))

    discounts = paginate_query(Discount.query, page)
    return render_template('admin_discounts.html', discounts=discounts)


@admin.route('/discounts/delete/<int:id>')
def delete_discount(id):
    discount = Discount.query.get_or_404(id)
    try:
        db.session.delete(discount)
        db.session.commit()
        return redirect(url_for('admin.show_message',
                                message='Discount deleted successfully!',
                                status='success',
                                back_url=url_for('admin.manage_discounts')))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('admin.show_message',
                                message=f'Error deleting discount: {str(e)}',
                                status='error',
                                back_url=url_for('admin.manage_discounts')))


@admin.route('/locations', methods=['GET', 'POST'])
def manage_locations():
    page = request.args.get('page', 1, type=int)
    if request.method == 'POST':
        try:
            location = Locations(
                name=request.form['name'],
                country=request.form['country'],
                city=request.form['city']
            )
            db.session.add(location)
            db.session.commit()
            return redirect(url_for('admin.show_message',
                                    message='Location added successfully!',
                                    status='success',
                                    back_url=url_for('admin.manage_locations')))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('admin.show_message',
                                    message=f'Error adding location: {str(e)}',
                                    status='error',
                                    back_url=url_for('admin.manage_locations')))

    locations = paginate_query(Locations.query, page)
    return render_template('admin_locations.html', locations=locations)


@admin.route('/locations/delete/<int:id>')
def delete_location(id):
    location = Locations.query.get_or_404(id)
    try:
        db.session.delete(location)
        db.session.commit()
        return redirect(url_for('admin.show_message',
                                message='Location deleted successfully!',
                                status='success',
                                back_url=url_for('admin.manage_locations')))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('admin.show_message',
                                message=f'Error deleting location: {str(e)}',
                                status='error',
                                back_url=url_for('admin.manage_locations')))


@admin.route('/users', methods=['GET', 'POST'])
def manage_users():
    page = request.args.get('page', 1, type=int)
    if request.method == 'POST':
        try:
            date_of_birth_str = request.form['date_of_birth']
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date() if date_of_birth_str else None
            user = Users(
                user_name=request.form['user_name'],
                email=request.form['email'],
                phone_number=request.form['phone_number'],
                country=request.form['country'],
                password=request.form['password'],
                avatar_url=request.form['avatar_url'],
                point=int(request.form['point']),
                date_of_birth=date_of_birth
            )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('admin.show_message',
                                    message='User added successfully!',
                                    status='success',
                                    back_url=url_for('admin.manage_users')))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('admin.show_message',
                                    message=f'Error adding user: {str(e)}',
                                    status='error',
                                    back_url=url_for('admin.manage_users')))

    users = paginate_query(Users.query, page)
    return render_template('admin_users.html', users=users)


@admin.route('/users/delete/<int:id>')
def delete_user(id):
    user = Users.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('admin.show_message',
                                message='User deleted successfully!',
                                status='success',
                                back_url=url_for('admin.manage_users')))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('admin.show_message',
                                message=f'Error deleting user: {str(e)}',
                                status='error',
                                back_url=url_for('admin.manage_users')))

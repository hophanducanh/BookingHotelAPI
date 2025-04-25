from extensions import db
from datetime import datetime

class Discount(db.Model):
    __tablename__ = 'discount'
    id = db.Column(db.Integer, primary_key=True)
    discount_name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    point_required = db.Column(db.Integer, nullable=False)

class Hotel(db.Model):
    __tablename__ = 'hotel'
    id = db.Column(db.Integer, primary_key=True)
    hotel_name = db.Column(db.String, nullable=False)
    new_price = db.Column(db.Integer, nullable=False)
    old_price = db.Column(db.Integer, nullable=False)
    hotel_star = db.Column(db.Float, nullable=False)
    hotel_rating = db.Column(db.Float, nullable=False)
    address = db.Column(db.String, nullable=False)
    policies = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    id_location = db.Column(db.Integer, db.ForeignKey('locations.id_location'), nullable=False)
    location = db.relationship('Locations', backref='hotels')
    facilities = db.relationship('Facilities', secondary='hotel_facilities', backref='hotels')
    images = db.relationship('HotelImages', backref='hotel', cascade='all, delete-orphan')
    rooms = db.relationship('HotelRoom', backref='hotel', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='hotel', cascade='all, delete-orphan')

class HotelImages(db.Model):
    __tablename__ = 'hotel_images'
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    image_url = db.Column(db.String, nullable=False)

class HotelFacilities(db.Model):
    __tablename__ = 'hotel_facilities'
    id_hotel = db.Column(db.Integer, db.ForeignKey('hotel.id'), primary_key=True)
    id_facilities = db.Column(db.Integer, db.ForeignKey('facilities.id_fac'), primary_key=True)

class Facilities(db.Model):
    __tablename__ = 'facilities'
    id_fac = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

class Locations(db.Model):
    __tablename__ = 'locations'
    id_location = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    phone_number = db.Column(db.String)
    country = db.Column(db.String)
    point = db.Column(db.Float, nullable=False, default=0.0)
    password = db.Column(db.String, nullable=False)
    avatar_url = db.Column(db.String)
    comments = db.relationship('Comment', backref='user', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', cascade='all, delete-orphan')

# Comment Table
class Comment(db.Model):
    __tablename__ = 'comment'
    id_comment = db.Column(db.Integer, primary_key=True)
    room_rating_point = db.Column(db.Float, nullable=False)
    service_rating_point = db.Column(db.Float, nullable=False)
    staff_rating_point = db.Column(db.Float, nullable=False)
    price_rating_point = db.Column(db.Float, nullable=False)
    bad_comment = db.Column(db.String)
    good_comment = db.Column(db.String)
    image_url = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hotel_room_id = db.Column(db.Integer, db.ForeignKey('hotel_room.id_hotel_room'), nullable=False)

# Booking Table
class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    hotels_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False)
    number_of_rooms = db.Column(db.Integer, nullable=False)
    number_of_children = db.Column(db.Integer, nullable=False)

class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    hotels_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    bookings = db.relationship('Booking', backref='schedule', cascade='all, delete-orphan')

class HotelRoom(db.Model):
    __tablename__ = 'hotel_room'
    id_hotel_room = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String, nullable=False)
    room_type = db.Column(db.String, nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    comments = db.relationship('Comment', backref='hotel_room', cascade='all, delete-orphan')
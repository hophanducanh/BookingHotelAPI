from extensions import db
from datetime import datetime

class Discount(db.Model):
    __tablename__ = 'Discount'
    id = db.Column(db.Integer, primary_key=True)
    discount_name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    point_required = db.Column(db.Integer, nullable=False)
    discount_value = db.Column(db.Float, nullable=False)
    user_discounts = db.relationship('UserDiscount', backref='discount', cascade='all, delete-orphan')

class Hotel(db.Model):
    __tablename__ = 'Hotel'
    id = db.Column(db.Integer, primary_key=True)
    hotel_name = db.Column(db.String, nullable=False)
    new_price = db.Column(db.Integer, nullable=False)
    old_price = db.Column(db.Integer, nullable=False)
    hotel_star = db.Column(db.Float, nullable=False)
    hotel_rating = db.Column(db.Float, nullable=False)
    address = db.Column(db.String, nullable=False)
    policies = db.Column(db.String)
    description = db.Column(db.String)
    distance = db.Column(db.String)
    id_location = db.Column(db.Integer, db.ForeignKey('Locations.id_location'), nullable=False)
    location = db.relationship('Locations', backref='hotels')
    facilities = db.relationship('Facilities', secondary='Hotel_Facilities', backref='hotels')
    images = db.relationship('HotelImages', backref='hotel', cascade='all, delete-orphan')
    rooms = db.relationship('Hotel_Room', backref='hotel', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='hotel', cascade='all, delete-orphan')

class HotelImages(db.Model):
    __tablename__ = 'Hotel_Images'
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('Hotel.id'), nullable=False)
    image_url = db.Column(db.String, nullable=False)

class HotelFacilities(db.Model):
    __tablename__ = 'Hotel_Facilities'
    id_hotel = db.Column(db.Integer, db.ForeignKey('Hotel.id'), primary_key=True)
    id_facilities = db.Column(db.Integer, db.ForeignKey('Facilities.id_fac'), primary_key=True)

class Facilities(db.Model):
    __tablename__ = 'Facilities'
    id_fac = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

class Locations(db.Model):
    __tablename__ = 'Locations'
    id_location = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)

class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    phone_number = db.Column(db.String)
    country = db.Column(db.String)
    password = db.Column(db.String, nullable=False)
    avatar_url = db.Column(db.String)
    point = db.Column(db.Integer, default=0)
    date_of_birth = db.Column(db.Date, nullable=True)
    comments = db.relationship('Comment', backref='user', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', cascade='all, delete-orphan')
    user_discounts = db.relationship('UserDiscount', backref='user', cascade='all, delete-orphan')

class Comment(db.Model):
    __tablename__ = 'Comment'
    id_comment = db.Column(db.Integer, primary_key=True)
    rating_point = db.Column(db.Float, nullable=False)
    comment = db.Column(db.String)
    image_url = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('Hotel.id'), nullable=False)
    images = db.relationship('CommentImages', backref='Comment', cascade='all, delete-orphan')

class Booking(db.Model):
    __tablename__ = 'Booking'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('Hotel_Room.id_hotel_room'), nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False)
    number_of_rooms = db.Column(db.Integer, nullable=False)
    number_of_children = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    user_discount_id = db.Column(db.Integer, db.ForeignKey('user_discount.id'), nullable=True)
    room = db.relationship('Hotel_Room', backref='bookings')

class Hotel_Room(db.Model):
    __tablename__ = 'Hotel_Room'
    id_hotel_room = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String, nullable=False)
    room_type = db.Column(db.String, nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('Hotel.id'), nullable=False)

class UserDiscount(db.Model):
    __tablename__ = 'user_discount'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('Discount.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user_discount', cascade='all, delete-orphan')

class CommentImages(db.Model):
    __tablename__ = 'Comment_Images'
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('Comment.id_comment'), nullable=False)
    image_url = db.Column(db.String, nullable=False)
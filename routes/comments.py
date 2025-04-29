from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Comment, Hotel, Users, CommentImages
from extensions import db
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

comments_bp = Blueprint('comments', __name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGES = 3

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created upload folder: {UPLOAD_FOLDER}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@comments_bp.route('/comments', methods=['POST'])
@jwt_required()
def create_comment():
    try:
        # Log incoming request
        logger.debug(f"Form data: {request.form}")
        logger.debug(f"Files: {request.files}")

        # Get the authenticated user's email from JWT
        email = get_jwt_identity()
        logger.debug(f"JWT identity: {email}")
        user = Users.query.filter_by(email=email).first()
        if not user:
            logger.error("User not found")
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        # Check if form data is present
        if not request.form:
            logger.error("No form data received")
            return jsonify({
                'status': 'error',
                'message': 'Request must contain form data'
            }), 400

        # Validate required fields
        required_fields = ['rating_point', 'hotel_id']
        missing_fields = [field for field in required_fields if field not in request.form]
        if missing_fields:
            logger.error(f"Missing fields: {missing_fields}")
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {missing_fields}'
            }), 400

        # Extract form data
        rating_point = request.form.get('rating_point')
        hotel_id = request.form.get('hotel_id')
        comment_text = request.form.get('comment')
        image_files = request.files.getlist('image')  # Get list of uploaded images
        logger.debug(f"Received {len(image_files)} image files")

        # Validate number of images
        if len(image_files) > MAX_IMAGES:
            logger.error(f"Too many images: {len(image_files)}")
            return jsonify({
                'status': 'error',
                'message': f'Maximum {MAX_IMAGES} images allowed'
            }), 400

        # Validate rating_point
        try:
            rating_point = float(rating_point)
            if not (0 <= rating_point <= 10):
                logger.error(f"Invalid rating_point: {rating_point}")
                return jsonify({
                    'status': 'error',
                    'message': 'rating_point must be between 0 and 10'
                }), 400
        except (TypeError, ValueError):
            logger.error(f"Invalid rating_point format: {rating_point}")
            return jsonify({
                'status': 'error',
                'message': 'rating_point must be a valid number'
            }), 400

        # Validate hotel_id
        try:
            hotel_id = int(hotel_id)
            hotel = Hotel.query.get(hotel_id)
            if not hotel:
                logger.error(f"Hotel not found: {hotel_id}")
                return jsonify({
                    'status': 'error',
                    'message': f'Hotel with id {hotel_id} not found'
                }), 404
        except (TypeError, ValueError):
            logger.error(f"Invalid hotel_id: {hotel_id}")
            return jsonify({
                'status': 'error',
                'message': 'hotel_id must be a valid integer'
            })

        # Validate comment (if provided)
        if comment_text is not None and not isinstance(comment_text, str):
            logger.error(f"Invalid comment type: {type(comment_text)}")
            return jsonify({
                'status': 'error',
                'message': 'comment must be a string'
            }), 400

        # Handle image uploads
        image_urls = []
        for image_file in image_files:
            # Validate file presence
            if not image_file or not image_file.filename:
                logger.error("Empty or missing image file")
                return jsonify({
                    'status': 'error',
                    'message': 'All image files must have valid filenames'
                }), 400

            # Validate file size
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            if file_size > MAX_FILE_SIZE:
                logger.error(f"File too large: {file_size} bytes")
                return jsonify({
                    'status': 'error',
                    'message': f'Image file size exceeds {MAX_FILE_SIZE / (1024 * 1024)}MB'
                }), 400
            image_file.seek(0)  # Reset file pointer

            # Validate file type
            if not allowed_file(image_file.filename):
                logger.error(f"Invalid file type: {image_file.filename}")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid file type. Allowed extensions: {ALLOWED_EXTENSIONS}'
                }), 400

            # Generate a unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
            filename = secure_filename(image_file.filename)
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Save the file
            logger.debug(f"Saving file to: {file_path}")
            image_file.save(file_path)
            image_urls.append(f"/{UPLOAD_FOLDER}/{unique_filename}")

        # Store image URLs as a comma-separated string
        image_url = ','.join(image_urls) if image_urls else None

        # Create new comment
        new_comment = Comment(
            rating_point=rating_point,
            comment=comment_text,
            user_id=user.id,
            hotel_id=hotel_id
        )

        # Save to database
        db.session.add(new_comment)
        db.session.commit()

        for image_url in image_urls:
            comment_image = CommentImages(
                comment_id=new_comment.id_comment,
                image_url=image_url
            )
            db.session.add(comment_image)

        db.session.commit()

        # Prepare response
        response = {
            'status': 'success',
            'message': 'Comment created successfully',
            'data': {
                'id_comment': new_comment.id_comment,
                'rating_point': new_comment.rating_point,
                'comment': new_comment.comment,
                'user_id': new_comment.user_id,
                'hotel_id': new_comment.hotel_id,
                'images': image_urls  # Trả về danh sách ảnh đã lưu
            }
        }
        logger.info(f"Comment created: {new_comment.id_comment}")
        return jsonify(response), 201

    except IntegrityError as e:
        db.session.rollback()
        # Clean up uploaded files on error
        for image_url in image_urls:
            file_path = image_url.lstrip('/')
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
        logger.error(f"Database error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        # Clean up uploaded files on error
        for image_url in image_urls:
            file_path = image_url.lstrip('/')
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
        logger.error(f"Error creating comment: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error creating comment: {str(e)}'
        }), 500
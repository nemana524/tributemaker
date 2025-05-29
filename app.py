from flask import Flask, request, jsonify, send_file, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime, timedelta
import secrets
import subprocess
import threading
from PIL import Image
import io
import base64
import time
import queue
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional
import re

# Import configuration
from config import config

# Import the new email service
from email_service import email_service

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("ℹ️  python-dotenv not installed. Using system environment variables only.")
    print("   To use .env file, install with: pip install python-dotenv")

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

print(f"🚀 Running in {config_name} mode")
print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, origins=["*"])

# Initialize email service with app context
email_service.app = app

# Create upload directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'music'), exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(20), default='local')  # local, facebook, google
    provider_id = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    tributes = db.relationship('Tribute', backref='user', lazy=True, cascade='all, delete-orphan')

class Tribute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    music_choice = db.Column(db.String(50), nullable=False)
    custom_music_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, processing, completed, failed
    video_url = db.Column(db.String(255), nullable=True)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    images = db.relationship('TributeImage', backref='tribute', lazy=True, cascade='all, delete-orphan')

class TributeImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tribute_id = db.Column(db.Integer, db.ForeignKey('tribute.id'), nullable=False)

class VideoGeneration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tribute_id = db.Column(db.Integer, db.ForeignKey('tribute.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    video_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

# Global task manager for video generation
class VideoGenerationTaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)  # Limit concurrent video generations
        self.active_tasks: Dict[int, Future] = {}
        self.task_queue = queue.Queue()
        
    def submit_task(self, generation_id: int, task_func, *args, **kwargs):
        """Submit a video generation task"""
        if generation_id in self.active_tasks:
            return False  # Task already running
            
        future = self.executor.submit(task_func, *args, **kwargs)
        self.active_tasks[generation_id] = future
        
        # Add cleanup callback
        future.add_done_callback(lambda f: self.cleanup_task(generation_id))
        return True
    
    def cancel_task(self, generation_id: int) -> bool:
        """Cancel a running task"""
        if generation_id in self.active_tasks:
            future = self.active_tasks[generation_id]
            cancelled = future.cancel()
            if cancelled:
                self.cleanup_task(generation_id)
            return cancelled
        return False
    
    def cleanup_task(self, generation_id: int):
        """Clean up completed/cancelled task"""
        if generation_id in self.active_tasks:
            del self.active_tasks[generation_id]
    
    def get_task_status(self, generation_id: int) -> Optional[str]:
        """Get status of a task"""
        if generation_id in self.active_tasks:
            future = self.active_tasks[generation_id]
            if future.running():
                return 'running'
            elif future.cancelled():
                return 'cancelled'
            elif future.done():
                return 'completed' if future.exception() is None else 'failed'
        return None

# Global task manager instance
task_manager = VideoGenerationTaskManager()

# Utility Functions
def get_current_user_id():
    """Get current user ID from JWT token and convert to integer"""
    user_id_str = get_jwt_identity()
    return int(user_id_str) if user_id_str else None

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def send_verification_email(user_email, verification_token):
    """Send email verification using the new email service"""
    try:
        # Use the new email service
        success, message = email_service.send_verification_email(
            user_email, 
            verification_token, 
            request.host_url
        )
        
        if success:
            print(f"✅ Verification email sent successfully to {user_email}")
        else:
            print(f"❌ Failed to send verification email: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

def optimize_image(image_path, max_size=(1920, 1080), quality=85):
    """Optimize uploaded images"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized version
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
        return True
    except Exception as e:
        print(f"Image optimization failed: {e}")
        return False

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        # Validate email format
        email = data['email'].strip().lower()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'error': 'Please enter a valid email address'}), 400
        
        # Validate password strength
        password = data['password']
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Validate name
        name = data['name'].strip()
        if len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters long'}), 400
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.is_verified:
                return jsonify({'error': 'Email already registered. Please sign in instead.'}), 400
            else:
                # User exists but not verified, update their info and resend verification
                existing_user.name = name
                existing_user.password_hash = generate_password_hash(password)
                verification_token = secrets.token_urlsafe(32)
                existing_user.verification_token = verification_token
                db.session.commit()
                
                # Send verification email using new service
                email_sent = send_verification_email(existing_user.email, verification_token)
                
                # Handle email verification based on service configuration
                if email_service.is_enabled():
                    return jsonify({
                        'message': 'Account updated. Please check your email for verification instructions.' if email_sent else 'Account updated. Email verification temporarily unavailable.',
                        'email_sent': email_sent,
                        'user_id': existing_user.id,
                        'requires_verification': email_sent
                    }), 200
                else:
                    # Development mode or email disabled - auto-verify
                    existing_user.is_verified = True
                    existing_user.verification_token = None
                    db.session.commit()
                    return jsonify({
                        'message': 'Account updated and verified automatically (development mode).',
                        'email_sent': False,
                        'user_id': existing_user.id,
                        'requires_verification': False,
                        'auto_verified': True
                    }), 200
        
        # Create new user
        verification_token = secrets.token_urlsafe(32)
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            verification_token=verification_token
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Handle email verification based on service configuration
        if email_service.is_enabled():
            # Email verification is enabled - send email
            email_sent = send_verification_email(user.email, verification_token)
            
            if email_sent:
                return jsonify({
                    'message': 'Registration successful! Please check your email to verify your account.',
                    'email_sent': True,
                    'user_id': user.id,
                    'requires_verification': True,
                    'auto_verified': False
                }), 201
            else:
                # Email sending failed - auto-verify for better UX
                user.is_verified = True
                user.verification_token = None
                db.session.commit()
                return jsonify({
                    'message': 'Registration successful! Email verification temporarily unavailable - account verified automatically.',
                    'email_sent': False,
                    'user_id': user.id,
                    'requires_verification': False,
                    'auto_verified': True,
                    'warning': 'Email verification temporarily unavailable'
                }), 201
        else:
            # Development mode or email disabled - auto-verify
            user.is_verified = True
            user.verification_token = None
            db.session.commit()
            return jsonify({
                'message': 'Registration successful! Account verified automatically (development mode).',
                'email_sent': False,
                'user_id': user.id,
                'requires_verification': False,
                'auto_verified': True
            }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Auto-verify users if email verification is disabled
        if not email_service.is_enabled() and not user.is_verified:
            user.is_verified = True
            user.verification_token = None
            db.session.commit()
            print(f"Auto-verified user {user.email} (email verification disabled)")
        
        if not user.is_verified:
            return jsonify({
                'error': 'Please verify your email before logging in',
                'requires_verification': True,
                'email': user.email
            }), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/api/auth/verify/<token>', methods=['GET'])
def verify_email(token):
    try:
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            # Redirect to an error page or login with error message
            return redirect('/first-index.html?error=invalid_token')
        
        if user.is_verified:
            # Already verified, redirect to login
            return redirect('/first-index.html?message=already_verified')
        
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        # Redirect to success page
        return redirect('/email-verified.html')
        
    except Exception as e:
        print(f"Email verification error: {e}")
        return redirect('/first-index.html?error=verification_failed')

@app.route('/api/auth/resend-verification', methods=['POST'])
def resend_verification():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_verified:
            return jsonify({'error': 'Email is already verified'}), 400
        
        # Handle email verification based on service configuration
        if email_service.is_enabled():
            # Generate new verification token
            verification_token = secrets.token_urlsafe(32)
            user.verification_token = verification_token
            db.session.commit()
            
            # Send verification email
            email_sent = send_verification_email(user.email, verification_token)
            
            if email_sent:
                return jsonify({
                    'message': 'Verification email sent successfully',
                    'email_sent': True,
                    'auto_verified': False
                }), 200
            else:
                # Email sending failed - auto-verify user for better UX
                user.is_verified = True
                user.verification_token = None
                db.session.commit()
                return jsonify({
                    'message': 'Email verification temporarily unavailable. Account verified automatically.',
                    'email_sent': False,
                    'auto_verified': True,
                    'warning': 'Email verification temporarily unavailable'
                }), 200
        else:
            # Development mode or email disabled - auto-verify user
            user.is_verified = True
            user.verification_token = None
            db.session.commit()
            return jsonify({
                'message': 'Email verification is disabled. Account verified automatically.',
                'auto_verified': True,
                'email_sent': False
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/social-login', methods=['POST'])
def social_login():
    try:
        data = request.get_json()
        provider = data.get('provider')  # 'facebook' or 'google'
        provider_id = data.get('provider_id')
        email = data.get('email')
        name = data.get('name')
        avatar_url = data.get('avatar_url')
        
        if not all([provider, provider_id, email, name]):
            return jsonify({'error': 'Missing required social login data'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                name=name,
                provider=provider,
                provider_id=provider_id,
                avatar_url=avatar_url,
                is_verified=True  # Social logins are pre-verified
            )
            db.session.add(user)
            db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# File Upload Routes
@app.route('/api/upload/images', methods=['POST'])
@jwt_required()
def upload_images():
    try:
        user_id = get_current_user_id()
        
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 images allowed'}), 400
        
        uploaded_files = []
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        
        for file in files:
            if file and allowed_file(file.filename, allowed_extensions):
                # Generate unique filename
                filename = generate_unique_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename)
                
                # Save file
                file.save(file_path)
                
                # Optimize image
                optimize_image(file_path)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                uploaded_files.append({
                    'filename': filename,
                    'original_filename': file.filename,
                    'file_path': file_path,
                    'file_size': file_size,
                    'url': f'/api/files/images/{filename}'
                })
        
        return jsonify({
            'message': f'{len(uploaded_files)} images uploaded successfully',
            'images': uploaded_files
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/music', methods=['POST'])
@jwt_required()
def upload_music():
    try:
        user_id = get_current_user_id()
        print(f"DEBUG: Music upload request from user {user_id}")
        
        if 'music' not in request.files:
            print("DEBUG: No 'music' key in request.files")
            print(f"DEBUG: Available keys: {list(request.files.keys())}")
            return jsonify({'error': 'No music file provided'}), 400
        
        file = request.files['music']
        print(f"DEBUG: Received file: {file.filename}, content_type: {file.content_type}")
        
        if not file or file.filename == '':
            print("DEBUG: File is empty or no filename")
            return jsonify({'error': 'No music file selected'}), 400
        
        # Validate file type and size
        allowed_extensions = {'mp3', 'wav', 'ogg', 'm4a', 'aac'}
        max_size = 10 * 1024 * 1024  # 10MB
        
        if not allowed_file(file.filename, allowed_extensions):
            print(f"DEBUG: File type not allowed: {file.filename}")
            return jsonify({'error': 'Invalid file type. Allowed: MP3, WAV, OGG, M4A, AAC'}), 400
        
        # Check file size (this is approximate, actual size checked after save)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        print(f"DEBUG: File size: {file_size} bytes")
        
        if file_size > max_size:
            print(f"DEBUG: File too large: {file_size} > {max_size}")
            return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'music', filename)
        print(f"DEBUG: Saving to: {file_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        print(f"DEBUG: File saved successfully")
        
        # Verify actual file size
        actual_size = os.path.getsize(file_path)
        print(f"DEBUG: Actual file size after save: {actual_size} bytes")
        
        if actual_size > max_size:
            os.remove(file_path)  # Clean up
            print(f"DEBUG: File too large after save, removed")
            return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400
        
        music_url = f'/api/files/music/{filename}'
        print(f"DEBUG: Music upload successful, URL: {music_url}")
        
        return jsonify({
            'message': 'Music uploaded successfully',
            'music_url': music_url,
            'filename': filename,
            'original_filename': file.filename,
            'file_size': actual_size
        }), 200
        
    except Exception as e:
        print(f"DEBUG: Exception in upload_music: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/images/<filename>')
def serve_image(filename):
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename),
            as_attachment=False
        )
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/music/<filename>')
def serve_music(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'music', filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Frontend static file serving for email verification
@app.route('/first-index.html')
def serve_login_page():
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'first-index.html')
        if os.path.exists(frontend_path):
            return send_file(frontend_path)
        else:
            return jsonify({'error': 'Login page not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/email-verified.html')
def serve_verification_success_page():
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'email-verified.html')
        if os.path.exists(frontend_path):
            return send_file(frontend_path)
        else:
            return jsonify({'error': 'Verification page not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/signup.html')
def serve_signup_page():
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'signup.html')
        if os.path.exists(frontend_path):
            return send_file(frontend_path)
        else:
            return jsonify({'error': 'Signup page not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/style.css')
def serve_css():
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'style.css')
        if os.path.exists(frontend_path):
            return send_file(frontend_path, mimetype='text/css')
        else:
            return jsonify({'error': 'CSS file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/script.js')
def serve_js():
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'script.js')
        if os.path.exists(frontend_path):
            return send_file(frontend_path, mimetype='application/javascript')
        else:
            return jsonify({'error': 'JS file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api.js')
def serve_api_js():
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'api.js')
        if os.path.exists(frontend_path):
            return send_file(frontend_path, mimetype='application/javascript')
        else:
            return jsonify({'error': 'API JS file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tribute Management Routes
@app.route('/api/tributes', methods=['POST'])
@jwt_required()
def create_tribute():
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Debug logging
        print(f"DEBUG: Received tribute data: {data}")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Music choice: {data.get('music_choice')}")
        print(f"DEBUG: Custom music URL: {data.get('custom_music_url')}")
        
        # Validation
        required_fields = ['title', 'message', 'music_choice']
        for field in required_fields:
            if not data.get(field):
                print(f"DEBUG: Missing field: {field}")
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if custom music is being used
        music_choice = data.get('music_choice')
        is_custom_music = music_choice in ['custom', 'custom_uploaded']
        
        # Images validation - required unless custom music is used
        images_data = data.get('images', [])
        if not is_custom_music:
            # Images are required for non-custom music
            if not images_data:
                print("DEBUG: Images are required for non-custom music")
                return jsonify({'error': 'Images are required'}), 400
            
            if not isinstance(images_data, list):
                print(f"DEBUG: Images is not a list: {type(images_data)}")
                return jsonify({'error': 'Images must be a list'}), 400
            
            if len(images_data) == 0:
                print("DEBUG: Images list is empty")
                return jsonify({'error': 'At least one image is required'}), 400
        else:
            # For custom music, images are optional
            print("DEBUG: Custom music detected - images are optional")
            if images_data and not isinstance(images_data, list):
                print(f"DEBUG: Images is not a list: {type(images_data)}")
                return jsonify({'error': 'Images must be a list'}), 400
        
        # Validate image data structure if images are provided
        if images_data:
            for i, image_data in enumerate(images_data):
                print(f"DEBUG: Image {i} data: {image_data}")
                required_image_fields = ['filename', 'original_filename', 'file_path', 'file_size']
                for field in required_image_fields:
                    if field not in image_data:
                        print(f"DEBUG: Missing image field {field} in image {i}")
                        return jsonify({'error': f'Image {field} is required'}), 400
        
        # Create tribute
        tribute = Tribute(
            title=data['title'],
            message=data['message'],
            music_choice=data['music_choice'],
            custom_music_url=data.get('custom_music_url'),
            user_id=user_id
        )
        
        db.session.add(tribute)
        db.session.flush()  # Get the tribute ID
        
        # Add images if provided
        if images_data:
            for index, image_data in enumerate(images_data):
                tribute_image = TributeImage(
                    filename=image_data['filename'],
                    original_filename=image_data['original_filename'],
                    file_path=image_data['file_path'],
                    file_size=image_data['file_size'],
                    order_index=index,
                    tribute_id=tribute.id
                )
                db.session.add(tribute_image)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tribute created successfully',
            'tribute_id': tribute.id,
            'tribute': {
                'id': tribute.id,
                'title': tribute.title,
                'message': tribute.message,
                'music_choice': tribute.music_choice,
                'status': tribute.status,
                'created_at': tribute.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Exception in create_tribute: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tributes/<int:tribute_id>', methods=['GET'])
@jwt_required()
def get_tribute(tribute_id):
    try:
        user_id = get_jwt_identity()
        
        tribute = Tribute.query.filter_by(id=tribute_id, user_id=user_id).first()
        
        if not tribute:
            return jsonify({'error': 'Tribute not found'}), 404
        
        # Get images
        images = []
        for img in tribute.images:
            images.append({
                'id': img.id,
                'filename': img.filename,
                'original_filename': img.original_filename,
                'url': f'/api/files/images/{img.filename}',
                'order_index': img.order_index
            })
        
        return jsonify({
            'tribute': {
                'id': tribute.id,
                'title': tribute.title,
                'message': tribute.message,
                'music_choice': tribute.music_choice,
                'status': tribute.status,
                'video_url': tribute.video_url,
                'thumbnail_url': tribute.thumbnail_url,
                'created_at': tribute.created_at.isoformat(),
                'images': images
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tributes', methods=['GET'])
@jwt_required()
def get_user_tributes():
    try:
        user_id = get_current_user_id()
        
        tributes = Tribute.query.filter_by(user_id=user_id).order_by(Tribute.created_at.desc()).all()
        
        tribute_list = []
        for tribute in tributes:
            tribute_list.append({
                'id': tribute.id,
                'title': tribute.title,
                'status': tribute.status,
                'created_at': tribute.created_at.isoformat(),
                'thumbnail_url': tribute.thumbnail_url,
                'image_count': len(tribute.images)
            })
        
        return jsonify({'tributes': tribute_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Video Generation Routes
@app.route('/api/video/generate', methods=['POST'])
@jwt_required()
def generate_video():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        tribute_id = data.get('tribute_id')
        if not tribute_id:
            return jsonify({'error': 'tribute_id is required'}), 400
        
        # Verify tribute ownership
        tribute = Tribute.query.filter_by(id=tribute_id, user_id=user_id).first()
        if not tribute:
            return jsonify({'error': 'Tribute not found'}), 404
        
        # Check if video generation is already in progress
        existing_generation = VideoGeneration.query.filter_by(
            tribute_id=tribute_id
        ).filter(
            VideoGeneration.status.in_(['pending', 'processing'])
        ).first()
        
        if existing_generation:
            return jsonify({
                'error': 'Video generation already in progress',
                'generation_id': existing_generation.id
            }), 400
        
        # Create video generation record
        video_gen = VideoGeneration(tribute_id=tribute_id, status='pending', progress=0)
        db.session.add(video_gen)
        db.session.commit()
        
        # Submit task to task manager
        task_submitted = task_manager.submit_task(
            video_gen.id,
            process_video_generation_async,
            video_gen.id,
            tribute_id
        )
        
        if not task_submitted:
            video_gen.status = 'failed'
            video_gen.error_message = 'Failed to start video generation task'
            db.session.commit()
            return jsonify({'error': 'Failed to start video generation'}), 500
        
        return jsonify({
            'message': 'Video generation started',
            'generation_id': video_gen.id,
            'status': 'pending'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/status/<int:generation_id>', methods=['GET'])
@jwt_required()
def get_video_status(generation_id):
    try:
        user_id = get_jwt_identity()
        
        video_gen = VideoGeneration.query.join(Tribute).filter(
            VideoGeneration.id == generation_id,
            Tribute.user_id == user_id
        ).first()
        
        if not video_gen:
            return jsonify({'error': 'Video generation not found'}), 404
        
        return jsonify({
            'status': video_gen.status,
            'progress': video_gen.progress,
            'error_message': video_gen.error_message,
            'tribute_id': video_gen.tribute_id,
            'video_url': f'/api/video/download/{video_gen.tribute_id}' if video_gen.status == 'completed' else None,
            'created_at': video_gen.created_at.isoformat(),
            'completed_at': video_gen.completed_at.isoformat() if video_gen.completed_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/cancel/<int:generation_id>', methods=['POST'])
@jwt_required()
def cancel_video_generation(generation_id):
    try:
        user_id = get_jwt_identity()
        
        # Verify ownership
        video_gen = VideoGeneration.query.join(Tribute).filter(
            VideoGeneration.id == generation_id,
            Tribute.user_id == user_id
        ).first()
        
        if not video_gen:
            return jsonify({'error': 'Video generation not found'}), 404
        
        if video_gen.status not in ['pending', 'processing']:
            return jsonify({'error': 'Cannot cancel completed or failed generation'}), 400
        
        # Try to cancel the task
        cancelled = task_manager.cancel_task(generation_id)
        
        if cancelled:
            video_gen.status = 'cancelled'
            video_gen.error_message = 'Cancelled by user'
            db.session.commit()
            
            return jsonify({
                'message': 'Video generation cancelled successfully',
                'status': 'cancelled'
            }), 200
        else:
            # Task might be too far along to cancel
            return jsonify({
                'message': 'Video generation could not be cancelled (may be completing)',
                'status': video_gen.status
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_video_generation_async(generation_id, tribute_id):
    """Improved asynchronous video generation with progress tracking"""
    try:
        with app.app_context():
            video_gen = VideoGeneration.query.get(generation_id)
            tribute = Tribute.query.get(tribute_id)
            
            if not video_gen or not tribute:
                return False
            
            # Check if task was cancelled before starting
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return False
            
            # Update status to processing
            video_gen.status = 'processing'
            video_gen.progress = 5
            db.session.commit()
            
            # Simulate realistic progress updates
            progress_steps = [
                (10, "Initializing video generation..."),
                (20, "Loading tribute data..."),
                (30, "Processing images..."),
                (40, "Preparing audio track..."),
                (50, "Creating video frames..."),
                (65, "Rendering video..."),
                (80, "Adding effects and transitions..."),
                (90, "Finalizing video..."),
                (95, "Saving video file..."),
                (100, "Video generation complete!")
            ]
            
            for progress, message in progress_steps:
                # Check for cancellation at each step
                if task_manager.get_task_status(generation_id) == 'cancelled':
                    video_gen.status = 'cancelled'
                    video_gen.error_message = 'Cancelled by user'
                    db.session.commit()
                    return False
                
                # Update progress
                video_gen.progress = progress
                db.session.commit()
                
                # Simulate processing time (remove in production)
                time.sleep(2)  # 2 seconds per step for demo
                
                print(f"DEBUG: Generation {generation_id} - {progress}% - {message}")
            
            # Get tribute images
            images = TributeImage.query.filter_by(tribute_id=tribute_id).order_by(TributeImage.order_index).all()
            
            # Check if this is a custom music tribute (images optional)
            is_custom_music = tribute.music_choice in ['custom', 'custom_uploaded']
            
            if not images and not is_custom_music:
                video_gen.status = 'failed'
                video_gen.error_message = 'No images found for tribute'
                db.session.commit()
                return False
            
            # Create video using FFmpeg
            video_filename = f"tribute_{tribute_id}_{uuid.uuid4().hex}.mp4"
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', video_filename)
            
            # Ensure video directory exists
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            
            # Prepare tribute data
            tribute_data = {
                'title': tribute.title,
                'message': tribute.message,
                'music_choice': tribute.music_choice,
                'custom_music_url': tribute.custom_music_url
            }
            
            # Final check for cancellation before video creation
            if task_manager.get_task_status(generation_id) == 'cancelled':
                video_gen.status = 'cancelled'
                video_gen.error_message = 'Cancelled by user'
                db.session.commit()
                return False
            
            # Generate video using advanced processor
            success = create_tribute_video_async(images, tribute, video_path, tribute_data, generation_id)
            
            if success:
                video_gen.status = 'completed'
                video_gen.progress = 100
                video_gen.video_path = video_path
                video_gen.completed_at = datetime.utcnow()
                
                # Update tribute
                tribute.status = 'completed'
                tribute.video_url = f'/api/video/download/{tribute_id}'
                
                print(f"DEBUG: Video generation {generation_id} completed successfully")
            else:
                video_gen.status = 'failed'
                video_gen.error_message = 'Video generation failed'
                print(f"DEBUG: Video generation {generation_id} failed")
            
            db.session.commit()
            return success
            
    except Exception as e:
        print(f"ERROR: Video generation {generation_id} exception: {e}")
        import traceback
        traceback.print_exc()
        
        with app.app_context():
            video_gen = VideoGeneration.query.get(generation_id)
            if video_gen:
                video_gen.status = 'failed'
                video_gen.error_message = str(e)
                db.session.commit()
        return False

def create_tribute_video_async(images, tribute, output_path, tribute_data, generation_id):
    """Create tribute video with cancellation support"""
    try:
        print(f"DEBUG: Starting video creation for tribute: {tribute.title}")
        print(f"DEBUG: Output path: {output_path}")
        print(f"DEBUG: Number of images: {len(images)}")
        print(f"DEBUG: Music choice: {tribute_data.get('music_choice')}")
        
        # Check for cancellation
        if task_manager.get_task_status(generation_id) == 'cancelled':
            print(f"DEBUG: Video creation cancelled for generation {generation_id}")
            return False
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Check if this is a custom music tribute without images
        is_custom_music = tribute_data.get('music_choice') in ['custom', 'custom_uploaded']
        has_images = len(images) > 0
        
        # Create a simple placeholder video file to test the flow
        # In production, this would use FFmpeg or the VideoProcessor
        
        # Create a simple text file as placeholder (for testing)
        placeholder_content = f"""
TributeMaker Video Placeholder
==============================
Title: {tribute.title}
Message: {tribute.message}
Music: {tribute_data.get('music_choice')}
Custom Music URL: {tribute_data.get('custom_music_url', 'None')}
Images: {len(images)} files
Type: {'Music-only tribute' if is_custom_music and not has_images else 'Image slideshow'}
Created: {datetime.utcnow().isoformat()}
Generation ID: {generation_id}

"""
        
        if has_images:
            placeholder_content += "Image Files:\n"
            for i, img in enumerate(images):
                # Check for cancellation during processing
                if task_manager.get_task_status(generation_id) == 'cancelled':
                    print(f"DEBUG: Video creation cancelled during image processing")
                    return False
                    
                placeholder_content += f"{i+1}. {img.original_filename} ({img.file_size} bytes)\n"
        else:
            placeholder_content += "No images - Music-only tribute\n"
        
        # Write placeholder file (will be replaced with actual video generation)
        info_path = output_path.replace('.mp4', '_info.txt')
        with open(info_path, 'w') as f:
            f.write(placeholder_content)
        
        # Check for cancellation before video processor
        if task_manager.get_task_status(generation_id) == 'cancelled':
            print(f"DEBUG: Video creation cancelled before video processor")
            return False
        
        # Try to use the VideoProcessor if available
        try:
            from video_processor import VideoProcessor
            print("DEBUG: VideoProcessor found, attempting video creation...")
            
            processor = VideoProcessor()
            
            # Create video using advanced processor with cancellation support
            success = processor.create_tribute_video_with_cancellation(
                images, tribute_data, output_path, generation_id, task_manager
            )
            
            if success:
                print("DEBUG: Video created successfully with VideoProcessor")
                return True
            else:
                print("DEBUG: VideoProcessor failed, falling back to placeholder")
                
        except ImportError as e:
            print(f"DEBUG: VideoProcessor not available: {e}")
        except Exception as e:
            print(f"DEBUG: VideoProcessor error: {e}")
        
        # Check for cancellation before fallback
        if task_manager.get_task_status(generation_id) == 'cancelled':
            print(f"DEBUG: Video creation cancelled before fallback")
            return False
        
        # Fallback: Create appropriate content based on what's available
        if has_images:
            # Create a simple image slideshow using PIL
            try:
                print("DEBUG: Creating simple image slideshow...")
                return create_simple_slideshow_async(images, tribute, output_path, generation_id)
                
            except Exception as e:
                print(f"DEBUG: Slideshow creation failed: {e}")
        else:
            # For music-only tributes, create a simple audio visualization or text video
            try:
                print("DEBUG: Creating music-only tribute video...")
                return create_music_only_video_async(tribute, tribute_data, output_path, generation_id)
                
            except Exception as e:
                print(f"DEBUG: Music-only video creation failed: {e}")
        
        # Final check for cancellation
        if task_manager.get_task_status(generation_id) == 'cancelled':
            print(f"DEBUG: Video creation cancelled at final step")
            return False
        
        # Final fallback: Just create a placeholder file to indicate completion
        print("DEBUG: Creating placeholder file as final fallback")
        with open(output_path, 'w') as f:
            f.write(f"Tribute video placeholder - generation {generation_id} - video generation needs FFmpeg setup")
        
        return True
        
    except Exception as e:
        print(f"DEBUG: Video creation completely failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_music_only_video_async(tribute, tribute_data, output_path, generation_id):
    """Create a simple music-only video for music-only tributes"""
    try:
        print(f"DEBUG: Creating music-only tribute video for: {tribute.title}")
        
        # For now, create a simple placeholder video file to test the flow
        # In production, this would use FFmpeg to create a video with just the audio
        
        # Create a simple text file as placeholder (for testing)
        placeholder_content = f"""
TributeMaker Music-Only Video Placeholder
========================================
Title: {tribute.title}
Message: {tribute.message}
Music: {tribute_data.get('music_choice')}
Custom Music URL: {tribute_data.get('custom_music_url', 'None')}
Type: Music-only tribute
Created: {datetime.utcnow().isoformat()}
Generation ID: {generation_id}

This is a music-only tribute with no images.
The video would contain the custom music with a simple text overlay.
"""
        
        # Write placeholder file (will be replaced with actual video generation)
        with open(output_path.replace('.mp4', '_info.txt'), 'w') as f:
            f.write(placeholder_content)
        
        # Try to use the VideoProcessor if available
        try:
            from video_processor import VideoProcessor
            print("DEBUG: VideoProcessor found, attempting music-only video creation...")
            
            processor = VideoProcessor()
            
            # Create music-only video using advanced processor
            success = processor.create_music_only_video_with_cancellation(tribute_data, output_path, generation_id, task_manager)
            
            if success:
                print("DEBUG: Music-only video created successfully with VideoProcessor")
                return True
            else:
                print("DEBUG: VideoProcessor failed, falling back to placeholder")
                
        except ImportError as e:
            print(f"DEBUG: VideoProcessor not available: {e}")
        except Exception as e:
            print(f"DEBUG: VideoProcessor error: {e}")
        
        # Final fallback: Just create a placeholder file to indicate completion
        print("DEBUG: Creating placeholder file as final fallback")
        with open(output_path, 'w') as f:
            f.write("Music-only tribute video placeholder - video generation needs FFmpeg setup")
        
        return True
        
    except Exception as e:
        print(f"DEBUG: Music-only video creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_simple_slideshow_async(images, tribute, output_path, generation_id):
    """Create a simple image slideshow without FFmpeg with cancellation support"""
    try:
        from PIL import Image as PILImage, ImageDraw, ImageFont
        import io
        
        print("DEBUG: Creating simple slideshow with PIL")
        
        # Check for cancellation
        if task_manager.get_task_status(generation_id) == 'cancelled':
            print(f"DEBUG: Slideshow creation cancelled for generation {generation_id}")
            return False
        
        # Create a simple GIF slideshow as a fallback
        frames = []
        
        # Create title frame
        title_frame = PILImage.new('RGB', (800, 600), color='black')
        draw = ImageDraw.Draw(title_frame)
        
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 36)
            small_font = ImageFont.truetype("arial.ttf", 24)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw title
        draw.text((50, 200), tribute.title, fill='white', font=font)
        draw.text((50, 300), tribute.message[:100] + "..." if len(tribute.message) > 100 else tribute.message, 
                 fill='lightgray', font=small_font)
        
        frames.append(title_frame)
        
        # Add image frames
        for i, img in enumerate(images[:5]):  # Limit to first 5 images
            # Check for cancellation during processing
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"DEBUG: Slideshow creation cancelled during image {i+1}")
                return False
                
            try:
                with PILImage.open(img.file_path) as pil_img:
                    # Resize image to fit frame
                    pil_img = pil_img.convert('RGB')
                    pil_img.thumbnail((800, 600), PILImage.Resampling.LANCZOS)
                    
                    # Create frame with black background
                    frame = PILImage.new('RGB', (800, 600), color='black')
                    
                    # Center the image
                    x = (800 - pil_img.width) // 2
                    y = (600 - pil_img.height) // 2
                    frame.paste(pil_img, (x, y))
                    
                    frames.append(frame)
            except Exception as e:
                print(f"DEBUG: Error processing image {img.filename}: {e}")
        
        # Final check for cancellation before saving
        if task_manager.get_task_status(generation_id) == 'cancelled':
            print(f"DEBUG: Slideshow creation cancelled before saving")
            return False
        
        # Save as animated GIF (temporary solution)
        gif_path = output_path.replace('.mp4', '.gif')
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=2000,  # 2 seconds per frame
            loop=0
        )
        
        print(f"DEBUG: Created slideshow GIF: {gif_path}")
        
        # Create a placeholder MP4 file
        with open(output_path, 'w') as f:
            f.write(f"Tribute slideshow created as {gif_path} - Generation {generation_id}")
        
        return True
        
    except Exception as e:
        print(f"DEBUG: Simple slideshow creation failed: {e}")
        return False

@app.route('/api/video/download/<int:tribute_id>')
@jwt_required()
def download_video(tribute_id):
    try:
        user_id = get_jwt_identity()
        
        tribute = Tribute.query.filter_by(id=tribute_id, user_id=user_id).first()
        if not tribute:
            return jsonify({'error': 'Tribute not found'}), 404
        
        video_gen = VideoGeneration.query.filter_by(
            tribute_id=tribute_id,
            status='completed'
        ).first()
        
        if not video_gen or not video_gen.video_path:
            return jsonify({'error': 'Video not available'}), 404
        
        return send_file(
            video_gen.video_path,
            as_attachment=True,
            download_name=f"tribute_{tribute.title.replace(' ', '_')}.mp4"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Routes
@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        users = User.query.all()
        user_list = []
        
        for u in users:
            user_list.append({
                'id': u.id,
                'email': u.email,
                'name': u.name,
                'provider': u.provider,
                'is_verified': u.is_verified,
                'is_admin': u.is_admin,
                'created_at': u.created_at.isoformat(),
                'tribute_count': len(u.tributes)
            })
        
        return jsonify({'users': user_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/tributes', methods=['GET'])
@jwt_required()
def admin_get_tributes():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        tributes = Tribute.query.join(User).all()
        tribute_list = []
        
        for tribute in tributes:
            tribute_list.append({
                'id': tribute.id,
                'title': tribute.title,
                'status': tribute.status,
                'created_at': tribute.created_at.isoformat(),
                'user_email': tribute.user.email,
                'user_name': tribute.user.name,
                'image_count': len(tribute.images)
            })
        
        return jsonify({'tributes': tribute_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

# Test Helper Endpoint (for development only)
@app.route('/api/test/verify-user', methods=['POST'])
def test_verify_user():
    """Test endpoint to verify users - DEVELOPMENT ONLY"""
    if not app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_verified = True
        db.session.commit()
        
        return jsonify({'message': 'User verified successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Music API endpoints
@app.route('/api/music/available', methods=['GET'])
@jwt_required()
def get_available_music():
    """Get list of available music options"""
    try:
        from video_processor import VideoProcessor
        vp = VideoProcessor()
        
        music_options = []
        music_descriptions = {
            'sad_piano': {'name': 'Gentle Piano', 'description': 'Peaceful and reflective'},
            'soft_strings': {'name': 'Soft Strings', 'description': 'Warm and comforting'},
            'calm_guitar': {'name': 'Acoustic Guitar', 'description': 'Serene and hopeful'}
        }
        
        for music_id, info in music_descriptions.items():
            music_options.append({
                'id': music_id,
                'name': info['name'],
                'description': info['description'],
                'available': vp.has_music_file(music_id)
            })
        
        # Add custom music option
        music_options.append({
            'id': 'custom',
            'name': 'Upload Custom Music',
            'description': 'Upload your own music file',
            'available': True
        })
        
        return jsonify({
            'music': music_options,
            'total': len(music_options)
        }), 200
        
    except Exception as e:
        print(f"DEBUG: Exception in get_available_music: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/music/preview/<music_choice>', methods=['GET'])
@jwt_required()
def get_music_preview(music_choice):
    """Get music preview file"""
    try:
        from video_processor import VideoProcessor
        vp = VideoProcessor()
        
        if not vp.has_music_file(music_choice):
            return jsonify({'error': 'Music file not available'}), 404
        
        music_path = vp.get_music_path(music_choice)
        
        if not os.path.exists(music_path):
            return jsonify({'error': 'Music file not found'}), 404
        
        # Return the music file for preview
        return send_file(
            music_path,
            as_attachment=False,
            mimetype='audio/mpeg' if music_path.endswith('.mp3') else 'audio/wav'
        )
        
    except Exception as e:
        print(f"DEBUG: Exception in get_music_preview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/music/status', methods=['GET'])
@jwt_required()
def get_music_status():
    """Get music system status"""
    try:
        from video_processor import VideoProcessor
        vp = VideoProcessor()
        
        # Check FFmpeg availability
        ffmpeg_available = vp._has_ffmpeg()
        
        # Check music file availability
        music_files = {}
        for music_choice in ['sad_piano', 'soft_strings', 'calm_guitar']:
            music_files[music_choice] = vp.has_music_file(music_choice)
        
        # Count available files
        available_count = sum(1 for available in music_files.values() if available)
        
        return jsonify({
            'ffmpeg_available': ffmpeg_available,
            'music_files': music_files,
            'available_count': available_count,
            'total_count': len(music_files),
            'status': 'fully_functional' if ffmpeg_available and available_count > 0 else 'limited'
        }), 200
        
    except Exception as e:
        print(f"DEBUG: Exception in get_music_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Test Music Configuration Endpoint
@app.route('/api/test/music-config', methods=['GET'])
def test_music_config():
    """Test endpoint to check music upload configuration - DEVELOPMENT ONLY"""
    if not app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        music_folder = os.path.join(upload_folder, 'music')
        
        config_info = {
            'upload_folder': upload_folder,
            'music_folder': music_folder,
            'upload_folder_exists': os.path.exists(upload_folder),
            'music_folder_exists': os.path.exists(music_folder),
            'max_content_length': app.config.get('MAX_CONTENT_LENGTH'),
            'current_directory': os.getcwd(),
            'music_files_in_folder': []
        }
        
        # List files in music folder if it exists
        if os.path.exists(music_folder):
            try:
                files = os.listdir(music_folder)
                for file in files:
                    file_path = os.path.join(music_folder, file)
                    if os.path.isfile(file_path):
                        config_info['music_files_in_folder'].append({
                            'name': file,
                            'size': os.path.getsize(file_path),
                            'path': file_path
                        })
            except Exception as e:
                config_info['music_folder_error'] = str(e)
        
        return jsonify(config_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token required'}), 401

# Initialize database
def create_tables():
    """Initialize database tables and create admin user"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Create admin user if it doesn't exist
            admin = User.query.filter_by(email='admin@tributemaker.com').first()
            if not admin:
                admin = User(
                    email='admin@tributemaker.com',
                    password_hash=generate_password_hash('admin123'),
                    name='Admin User',
                    is_verified=True,
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")
            else:
                print("✅ Admin user already exists")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise

# Production startup initialization
def initialize_production():
    """Initialize application for production deployment"""
    try:
        # Create necessary directories
        directories = ['uploads', 'uploads/images', 'uploads/videos', 'uploads/music', 'assets', 'assets/music']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        print("✅ Upload directories created/verified")
        
        # Initialize database
        create_tables()
        
        print("🚀 TributeMaker backend initialized successfully!")
        return True
        
    except Exception as e:
        print(f"💥 Production initialization failed: {e}")
        return False

# Auto-initialize for production (when not running directly)
if __name__ != '__main__':
    # This runs when imported by gunicorn
    initialize_production()

if __name__ == '__main__':
    # Development mode
    print("🔧 Running in development mode...")
    create_tables()
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False) 
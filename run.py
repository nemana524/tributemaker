#!/usr/bin/env python3
"""
TributeMaker Backend Server
Main entry point for the Flask application
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from admin import admin_bp

# Register admin blueprint
app.register_blueprint(admin_bp)

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'uploads',
        'uploads/images',
        'uploads/videos',
        'uploads/music',
        'uploads/temp',
        'assets',
        'assets/music'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def initialize_database():
    """Initialize the database with tables and default data"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Import models after app context is established
            from app import User
            
            # Create admin user if it doesn't exist
            admin = User.query.filter_by(email='admin@tributemaker.com').first()
            if not admin:
                from werkzeug.security import generate_password_hash
                
                admin = User(
                    email='admin@tributemaker.com',
                    password_hash=generate_password_hash('admin123'),
                    name='Admin User',
                    is_verified=True,
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✓ Admin user created (admin@tributemaker.com / admin123)")
            else:
                print("✓ Admin user already exists")
                
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    dependencies = {
        'FFmpeg': 'ffmpeg',
        'FFprobe': 'ffprobe'
    }
    
    missing = []
    
    for name, command in dependencies.items():
        try:
            import subprocess
            result = subprocess.run([command, '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {name} is available")
            else:
                missing.append(name)
        except FileNotFoundError:
            missing.append(name)
    
    if missing:
        print(f"⚠ Warning: Missing dependencies: {', '.join(missing)}")
        print("Video generation may not work properly without FFmpeg")
        return False
    
    return True

def print_startup_info():
    """Print startup information"""
    print("\n" + "="*60)
    print("🎬 TributeMaker Backend Server")
    print("="*60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {app.debug}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Upload Folder: {app.config['UPLOAD_FOLDER']}")
    print("="*60)
    print("\n📋 Available Endpoints:")
    print("  Authentication:")
    print("    POST /api/auth/register")
    print("    POST /api/auth/login")
    print("    POST /api/auth/social-login")
    print("    GET  /api/auth/verify/<token>")
    print("\n  File Management:")
    print("    POST /api/upload/images")
    print("    GET  /api/files/images/<filename>")
    print("\n  Tribute Management:")
    print("    POST /api/tributes")
    print("    GET  /api/tributes")
    print("    GET  /api/tributes/<id>")
    print("\n  Video Generation:")
    print("    POST /api/video/generate")
    print("    GET  /api/video/status/<id>")
    print("    GET  /api/video/download/<id>")
    print("\n  Admin Panel:")
    print("    GET  /admin/dashboard")
    print("    GET  /admin/users")
    print("    GET  /admin/tributes")
    print("    GET  /admin/analytics")
    print("\n  Health Check:")
    print("    GET  /api/health")
    print("\n" + "="*60)

def main():
    """Main function to start the server"""
    print("🚀 Starting TributeMaker Backend...")
    
    # Create necessary directories
    print("\n📁 Setting up directories...")
    create_directories()
    
    # Check dependencies
    print("\n🔍 Checking dependencies...")
    check_dependencies()
    
    # Initialize database
    print("\n💾 Initializing database...")
    if not initialize_database():
        print("❌ Failed to initialize database. Exiting.")
        sys.exit(1)
    
    # Print startup information
    print_startup_info()
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '127.0.0.1')  # Use localhost instead of 0.0.0.0
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"\n🌐 Server starting on http://{host}:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Start the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable auto-reloader to prevent Windows socket issues
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
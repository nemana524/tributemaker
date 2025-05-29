#!/usr/bin/env python3
"""
TributeMaker Production Startup Script
Handles database initialization and environment validation for Railway deployment
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def setup_directories():
    """Create necessary directories for file uploads"""
    directories = [
        'uploads',
        'uploads/images',
        'uploads/videos', 
        'uploads/music',
        'assets',
        'assets/music'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✅ Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def initialize_database():
    """Initialize database tables and create admin user"""
    try:
        from app import app, db, User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("✅ Database tables created/verified")
            
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
                logger.info("✅ Admin user created")
            else:
                logger.info("✅ Admin user already exists")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ FFmpeg is available")
            return True
        else:
            logger.warning("⚠️ FFmpeg not available - video generation will be limited")
            return False
    except Exception as e:
        logger.warning(f"⚠️ FFmpeg check failed: {e}")
        return False

def startup_checks():
    """Run all startup checks"""
    logger.info("🚀 Starting TributeMaker production startup checks...")
    
    checks = [
        ("Environment Variables", validate_environment),
        ("Directories", setup_directories),
        ("Database", initialize_database),
        ("FFmpeg", check_ffmpeg)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        logger.info(f"Running {check_name} check...")
        try:
            result = check_func()
            if not result and check_name in ["Environment Variables", "Directories", "Database"]:
                all_passed = False
        except Exception as e:
            logger.error(f"❌ {check_name} check failed with exception: {e}")
            if check_name in ["Environment Variables", "Directories", "Database"]:
                all_passed = False
    
    if all_passed:
        logger.info("🎉 All critical startup checks passed!")
    else:
        logger.error("💥 Some critical startup checks failed!")
        sys.exit(1)
    
    return all_passed

if __name__ == "__main__":
    startup_checks() 
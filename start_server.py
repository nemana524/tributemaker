#!/usr/bin/env python3
"""
TributeMaker Backend Server Startup Script
This script initializes the database and starts the Flask server
"""

import os
import sys
from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create a default admin user for testing"""
    admin_email = "admin@tributemaker.com"
    admin_password = "admin123"
    
    # Check if admin already exists
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        print(f"Admin user already exists: {admin_email}")
        return existing_admin
    
    # Create admin user
    admin_user = User(
        email=admin_email,
        password_hash=generate_password_hash(admin_password),
        name="Admin User",
        is_verified=True,
        is_admin=True
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"Created admin user: {admin_email} / {admin_password}")
    return admin_user

def create_test_user():
    """Create a test user for frontend testing"""
    test_email = "test@example.com"
    test_password = "test123"
    
    # Check if test user already exists
    existing_user = User.query.filter_by(email=test_email).first()
    if existing_user:
        print(f"Test user already exists: {test_email}")
        return existing_user
    
    # Create test user
    test_user = User(
        email=test_email,
        password_hash=generate_password_hash(test_password),
        name="Test User",
        is_verified=True,
        is_admin=False
    )
    
    db.session.add(test_user)
    db.session.commit()
    
    print(f"Created test user: {test_email} / {test_password}")
    return test_user

def initialize_database():
    """Initialize the database with tables and default data"""
    print("Initializing database...")
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
        
        # Create default users
        create_admin_user()
        create_test_user()
        
        print("Database initialization complete")

def start_server():
    """Start the Flask development server"""
    print("\n" + "="*50)
    print("🚀 Starting TributeMaker Backend Server")
    print("="*50)
    print(f"Server URL: http://localhost:5000")
    print(f"API Base URL: http://localhost:5000/api")
    print(f"Health Check: http://localhost:5000/api/health")
    print("\nTest Credentials:")
    print("  Admin: admin@tributemaker.com / admin123")
    print("  User:  test@example.com / test123")
    print("\nPress Ctrl+C to stop the server")
    print("="*50)
    
    # Start the server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to prevent double initialization
    )

if __name__ == "__main__":
    try:
        # Initialize database first
        initialize_database()
        
        # Start the server
        start_server()
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1) 
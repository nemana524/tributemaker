#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL
Run this script to migrate your existing data when switching to PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sqlite3
import psycopg2
from datetime import datetime
import re

# Import your models
from app import User, Tribute, TributeImage, VideoGeneration, db

def validate_postgres_url(url):
    """Validate PostgreSQL URL format"""
    if not url:
        return False, "DATABASE_URL is empty"
    
    # Check for placeholder values
    placeholders = ['host', 'port', 'user', 'password', 'database', 'username']
    for placeholder in placeholders:
        if placeholder in url.lower() and not url.startswith('postgresql://'):
            return False, f"DATABASE_URL contains placeholder '{placeholder}'"
    
    # Basic URL format check
    if not (url.startswith('postgresql://') or url.startswith('postgres://')):
        return False, "DATABASE_URL must start with 'postgresql://' or 'postgres://'"
    
    # Check for required components
    pattern = r'postgresql?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, url)
    if not match:
        return False, "Invalid PostgreSQL URL format. Expected: postgresql://user:password@host:port/database"
    
    return True, "Valid PostgreSQL URL"

def test_postgres_connection(url):
    """Test PostgreSQL connection"""
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            return True, f"Connected successfully. PostgreSQL version: {version[:50]}..."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def backup_sqlite_data():
    """Create a backup of SQLite data"""
    print("📦 Creating SQLite backup...")
    
    # Check multiple possible SQLite locations
    possible_paths = [
        'instance/tributemaker.db',
        'tributemaker.db',
        '../instance/tributemaker.db'
    ]
    
    sqlite_path = None
    for path in possible_paths:
        if os.path.exists(path):
            sqlite_path = path
            break
    
    if not sqlite_path:
        print("❌ SQLite database not found!")
        print("   Searched in:")
        for path in possible_paths:
            print(f"   - {os.path.abspath(path)}")
        return None
    
    print(f"✅ Found SQLite database: {sqlite_path}")
    
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Get all table data
    data = {}
    
    try:
        # Users table
        cursor.execute("SELECT * FROM user")
        data['users'] = cursor.fetchall()
        cursor.execute("PRAGMA table_info(user)")
        data['user_columns'] = [col[1] for col in cursor.fetchall()]
        
        # Tributes table
        cursor.execute("SELECT * FROM tribute")
        data['tributes'] = cursor.fetchall()
        cursor.execute("PRAGMA table_info(tribute)")
        data['tribute_columns'] = [col[1] for col in cursor.fetchall()]
        
        # Tribute Images table
        cursor.execute("SELECT * FROM tribute_image")
        data['tribute_images'] = cursor.fetchall()
        cursor.execute("PRAGMA table_info(tribute_image)")
        data['tribute_image_columns'] = [col[1] for col in cursor.fetchall()]
        
        # Video Generation table
        cursor.execute("SELECT * FROM video_generation")
        data['video_generations'] = cursor.fetchall()
        cursor.execute("PRAGMA table_info(video_generation)")
        data['video_generation_columns'] = [col[1] for col in cursor.fetchall()]
        
    except sqlite3.Error as e:
        print(f"❌ Error reading SQLite database: {e}")
        conn.close()
        return None
    
    conn.close()
    
    print(f"✅ Backed up {len(data['users'])} users, {len(data['tributes'])} tributes, {len(data['tribute_images'])} images, {len(data['video_generations'])} video generations")
    return data

def migrate_to_postgres(postgres_url, sqlite_data):
    """Migrate data to PostgreSQL"""
    print("🐘 Migrating to PostgreSQL...")
    
    try:
        # Create PostgreSQL engine
        engine = create_engine(postgres_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL connection successful")
        
        # Create all tables
        from app import app
        with app.app_context():
            db.create_all()
            print("✅ Tables created in PostgreSQL")
            
            # Migrate Users
            print("👥 Migrating users...")
            migrated_users = 0
            for row in sqlite_data['users']:
                user_data = dict(zip(sqlite_data['user_columns'], row))
                
                # Check if user already exists
                existing_user = User.query.filter_by(email=user_data['email']).first()
                if not existing_user:
                    try:
                        user = User(
                            email=user_data['email'],
                            password_hash=user_data['password_hash'],
                            name=user_data['name'],
                            provider=user_data.get('provider', 'local'),
                            provider_id=user_data.get('provider_id'),
                            avatar_url=user_data.get('avatar_url'),
                            is_verified=bool(user_data.get('is_verified', False)),
                            verification_token=user_data.get('verification_token'),
                            reset_token=user_data.get('reset_token'),
                            reset_token_expires=datetime.fromisoformat(user_data['reset_token_expires']) if user_data.get('reset_token_expires') else None,
                            created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else datetime.utcnow(),
                            is_admin=bool(user_data.get('is_admin', False))
                        )
                        db.session.add(user)
                        migrated_users += 1
                    except Exception as e:
                        print(f"   ⚠️ Error migrating user {user_data.get('email', 'unknown')}: {e}")
            
            # Commit users first
            db.session.commit()
            print(f"   ✅ Migrated {migrated_users} users")
            
            # Migrate Tributes
            print("🎬 Migrating tributes...")
            migrated_tributes = 0
            for row in sqlite_data['tributes']:
                tribute_data = dict(zip(sqlite_data['tribute_columns'], row))
                
                existing_tribute = Tribute.query.filter_by(id=tribute_data['id']).first()
                if not existing_tribute:
                    try:
                        tribute = Tribute(
                            title=tribute_data['title'],
                            message=tribute_data['message'],
                            music_choice=tribute_data['music_choice'],
                            custom_music_url=tribute_data.get('custom_music_url'),
                            status=tribute_data.get('status', 'draft'),
                            video_url=tribute_data.get('video_url'),
                            thumbnail_url=tribute_data.get('thumbnail_url'),
                            created_at=datetime.fromisoformat(tribute_data['created_at']) if tribute_data.get('created_at') else datetime.utcnow(),
                            updated_at=datetime.fromisoformat(tribute_data['updated_at']) if tribute_data.get('updated_at') else datetime.utcnow(),
                            user_id=tribute_data['user_id']
                        )
                        db.session.add(tribute)
                        migrated_tributes += 1
                    except Exception as e:
                        print(f"   ⚠️ Error migrating tribute {tribute_data.get('title', 'unknown')}: {e}")
            
            # Commit tributes
            db.session.commit()
            print(f"   ✅ Migrated {migrated_tributes} tributes")
            
            # Migrate Tribute Images
            print("🖼️ Migrating tribute images...")
            migrated_images = 0
            for row in sqlite_data['tribute_images']:
                image_data = dict(zip(sqlite_data['tribute_image_columns'], row))
                
                existing_image = TributeImage.query.filter_by(id=image_data['id']).first()
                if not existing_image:
                    try:
                        image = TributeImage(
                            filename=image_data['filename'],
                            original_filename=image_data['original_filename'],
                            file_path=image_data['file_path'],
                            file_size=image_data['file_size'],
                            order_index=image_data.get('order_index', 0),
                            created_at=datetime.fromisoformat(image_data['created_at']) if image_data.get('created_at') else datetime.utcnow(),
                            tribute_id=image_data['tribute_id']
                        )
                        db.session.add(image)
                        migrated_images += 1
                    except Exception as e:
                        print(f"   ⚠️ Error migrating image {image_data.get('filename', 'unknown')}: {e}")
            
            # Commit images
            db.session.commit()
            print(f"   ✅ Migrated {migrated_images} images")
            
            # Migrate Video Generations
            print("🎥 Migrating video generations...")
            migrated_videos = 0
            for row in sqlite_data['video_generations']:
                video_data = dict(zip(sqlite_data['video_generation_columns'], row))
                
                existing_video = VideoGeneration.query.filter_by(id=video_data['id']).first()
                if not existing_video:
                    try:
                        video = VideoGeneration(
                            tribute_id=video_data['tribute_id'],
                            status=video_data.get('status', 'pending'),
                            progress=video_data.get('progress', 0),
                            error_message=video_data.get('error_message'),
                            video_path=video_data.get('video_path'),
                            created_at=datetime.fromisoformat(video_data['created_at']) if video_data.get('created_at') else datetime.utcnow(),
                            completed_at=datetime.fromisoformat(video_data['completed_at']) if video_data.get('completed_at') else None
                        )
                        db.session.add(video)
                        migrated_videos += 1
                    except Exception as e:
                        print(f"   ⚠️ Error migrating video generation {video_data.get('id', 'unknown')}: {e}")
            
            # Final commit
            db.session.commit()
            print(f"   ✅ Migrated {migrated_videos} video generations")
            print("✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main migration function"""
    print("🔄 Starting SQLite to PostgreSQL migration...")
    
    # Get PostgreSQL URL from environment
    postgres_url = os.environ.get('DATABASE_URL')
    if not postgres_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("   Set it like: export DATABASE_URL='postgresql://user:password@host:port/database'")
        print("   Or for Railway: get it from your Railway dashboard")
        return
    
    # Validate PostgreSQL URL
    is_valid, message = validate_postgres_url(postgres_url)
    if not is_valid:
        print(f"❌ Invalid DATABASE_URL: {message}")
        print("   Example: postgresql://user:password@localhost:5432/tributemaker")
        return
    
    # Fix Railway/Heroku postgres URL if needed
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
        print("🔧 Fixed postgres:// URL to postgresql://")
    
    print(f"🎯 Target PostgreSQL: {postgres_url[:50]}...")
    
    # Test PostgreSQL connection
    print("🔌 Testing PostgreSQL connection...")
    connected, conn_message = test_postgres_connection(postgres_url)
    if not connected:
        print(f"❌ {conn_message}")
        return
    
    print(f"✅ {conn_message}")
    
    # Backup SQLite data
    sqlite_data = backup_sqlite_data()
    if not sqlite_data:
        return
    
    # Migrate to PostgreSQL
    success = migrate_to_postgres(postgres_url, sqlite_data)
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("💡 You can now switch to PostgreSQL by setting FLASK_ENV=production")
        print("💡 Don't forget to update your environment variables for production")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main() 
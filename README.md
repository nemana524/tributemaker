# TributeMaker Backend

A comprehensive Flask-based backend for the TributeMaker application that handles user authentication, file uploads, tribute management, and video generation.

## 🚀 Features

- **User Authentication**: JWT-based authentication with email verification
- **Social Login**: Support for Facebook and Google OAuth
- **File Management**: Secure image upload with optimization
- **Video Generation**: Automated tribute video creation with FFmpeg
- **Admin Panel**: Complete administrative interface
- **Email Integration**: Automated email verification and notifications
- **Database Management**: SQLAlchemy with SQLite/PostgreSQL support
- **API Documentation**: RESTful API with comprehensive endpoints

## 📋 Requirements

### System Dependencies
- Python 3.8+
- FFmpeg (for video processing)
- SQLite (included) or PostgreSQL (production)

### Python Dependencies
All Python dependencies are listed in `requirements.txt`:
- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- Flask-JWT-Extended 4.5.3
- Flask-CORS 4.0.0
- Pillow 10.0.1
- And more...

## 🛠️ Installation

### 1. Clone and Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install FFmpeg
**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to system PATH

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. Environment Configuration
Create a `.env` file in the backend directory:
```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///tributemaker.db

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5500
```

### 4. Start the Server
```bash
# Using the startup script (recommended)
python run.py

# Or directly with Flask
python app.py
```

The server will start on `http://localhost:5000`

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Social Login
```http
POST /api/auth/social-login
Content-Type: application/json

{
  "provider": "google",
  "provider_id": "google_user_id",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

#### Verify Email
```http
GET /api/auth/verify/{token}
```

### File Upload Endpoints

#### Upload Images
```http
POST /api/upload/images
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data

Form data:
- images: [file1, file2, ...] (max 10 files, 5MB each)
```

#### Serve Image
```http
GET /api/files/images/{filename}
```

### Tribute Management Endpoints

#### Create Tribute
```http
POST /api/tributes
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "title": "In Memory of...",
  "message": "A beautiful tribute message...",
  "music_choice": "sad_piano",
  "images": [
    {
      "filename": "uuid.jpg",
      "original_filename": "photo1.jpg",
      "file_path": "uploads/images/uuid.jpg",
      "file_size": 1024000
    }
  ]
}
```

#### Get User Tributes
```http
GET /api/tributes
Authorization: Bearer {jwt_token}
```

#### Get Specific Tribute
```http
GET /api/tributes/{tribute_id}
Authorization: Bearer {jwt_token}
```

### Video Generation Endpoints

#### Generate Video
```http
POST /api/video/generate
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "tribute_id": 1
}
```

#### Check Video Status
```http
GET /api/video/status/{generation_id}
Authorization: Bearer {jwt_token}
```

#### Download Video
```http
GET /api/video/download/{tribute_id}
Authorization: Bearer {jwt_token}
```

### Admin Panel Endpoints

#### Admin Dashboard
```http
GET /admin/dashboard
Authorization: Bearer {admin_jwt_token}
```

#### Manage Users
```http
GET /admin/users?page=1&per_page=20&search=query
Authorization: Bearer {admin_jwt_token}
```

#### Update User
```http
PUT /admin/users/{user_id}
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "is_verified": true,
  "is_admin": false
}
```

#### Delete User
```http
DELETE /admin/users/{user_id}
Authorization: Bearer {admin_jwt_token}
```

#### Manage Tributes
```http
GET /admin/tributes?page=1&status=completed
Authorization: Bearer {admin_jwt_token}
```

#### System Analytics
```http
GET /admin/analytics
Authorization: Bearer {admin_jwt_token}
```

#### System Cleanup
```http
POST /admin/system/cleanup
Authorization: Bearer {admin_jwt_token}
```

### Health Check
```http
GET /api/health
```

## 🗄️ Database Schema

### User Model
- `id`: Primary key
- `email`: Unique email address
- `password_hash`: Hashed password
- `name`: User's full name
- `provider`: Authentication provider (local, facebook, google)
- `provider_id`: External provider ID
- `avatar_url`: Profile picture URL
- `is_verified`: Email verification status
- `verification_token`: Email verification token
- `reset_token`: Password reset token
- `reset_token_expires`: Reset token expiration
- `created_at`: Account creation timestamp
- `is_admin`: Admin privileges flag

### Tribute Model
- `id`: Primary key
- `title`: Tribute title
- `message`: Tribute message
- `music_choice`: Selected background music
- `status`: Processing status (draft, processing, completed, failed)
- `video_url`: Generated video URL
- `thumbnail_url`: Video thumbnail URL
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `user_id`: Foreign key to User

### TributeImage Model
- `id`: Primary key
- `filename`: Stored filename
- `original_filename`: Original upload filename
- `file_path`: Full file path
- `file_size`: File size in bytes
- `order_index`: Display order
- `created_at`: Upload timestamp
- `tribute_id`: Foreign key to Tribute

### VideoGeneration Model
- `id`: Primary key
- `tribute_id`: Foreign key to Tribute
- `status`: Generation status (pending, processing, completed, failed)
- `progress`: Progress percentage (0-100)
- `error_message`: Error details if failed
- `video_path`: Generated video file path
- `created_at`: Generation start timestamp
- `completed_at`: Generation completion timestamp

## 🎬 Video Processing

The backend uses FFmpeg for advanced video processing with the following features:

### Video Specifications
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 FPS
- **Duration per Image**: 4 seconds
- **Transition Duration**: 1 second
- **Codec**: H.264 (libx264)
- **Audio**: AAC 128kbps

### Processing Pipeline
1. **Image Preparation**: Resize and optimize images
2. **Title Slide Creation**: Generate title slide with tribute information
3. **Vignette Effects**: Add subtle vignette to images
4. **Video Assembly**: Combine images with transitions
5. **Audio Integration**: Add background music
6. **Optimization**: Compress for web delivery

### Music Options
- `sad_piano`: Melancholic piano melody
- `soft_strings`: Gentle string arrangement
- `calm_guitar`: Peaceful acoustic guitar

## 👨‍💼 Admin Panel Features

### Dashboard
- User registration statistics
- Tribute creation metrics
- Storage usage monitoring
- System health indicators

### User Management
- View all users with pagination
- Search users by name/email
- Update user verification status
- Grant/revoke admin privileges
- Delete users and associated data

### Tribute Management
- View all tributes with filtering
- Monitor video generation status
- Delete tributes and files
- Search by title or user

### Analytics
- Daily registration trends
- Tribute creation patterns
- Status distribution charts
- Provider usage statistics

### System Maintenance
- Automated cleanup of orphaned files
- Failed generation cleanup
- Storage optimization
- System settings management

## 🔧 Configuration

### Environment Variables
All configuration is handled through environment variables:

- `SECRET_KEY`: Flask secret key for sessions
- `JWT_SECRET_KEY`: JWT token signing key
- `DATABASE_URL`: Database connection string
- `MAIL_*`: Email server configuration
- `UPLOAD_FOLDER`: File upload directory
- `CORS_ORIGINS`: Allowed CORS origins
- `FFMPEG_PATH`: Path to FFmpeg executable

### Development vs Production
The application automatically detects the environment and adjusts:

**Development:**
- SQLite database
- Debug mode enabled
- Relaxed CORS policy
- Detailed error messages

**Production:**
- PostgreSQL database
- Debug mode disabled
- Strict CORS policy
- Error logging

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p uploads/images uploads/videos uploads/temp

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "run.py"]
```

### Production Checklist
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up email server credentials
- [ ] Install FFmpeg on server
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates
- [ ] Configure file storage (AWS S3, etc.)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Werkzeug secure password hashing
- **Email Verification**: Required email verification for new accounts
- **File Validation**: Strict file type and size validation
- **CORS Protection**: Configurable CORS policies
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Admin Access Control**: Role-based access control for admin features

## 🐛 Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
# Check if FFmpeg is installed
ffmpeg -version

# Install FFmpeg if missing
# Windows: Download from https://ffmpeg.org/
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

**Database connection errors:**
```bash
# Check database URL in .env file
# For SQLite, ensure directory is writable
# For PostgreSQL, verify connection string
```

**Email sending fails:**
```bash
# Verify email credentials in .env
# For Gmail, use app-specific password
# Check firewall/network restrictions
```

**File upload errors:**
```bash
# Check upload directory permissions
# Verify MAX_CONTENT_LENGTH setting
# Ensure sufficient disk space
```

### Logging
The application logs important events and errors. Check the console output for detailed information about:
- Database operations
- File uploads
- Video generation progress
- Authentication attempts
- Admin actions

## 📞 Support

For technical support or questions:
- Check the troubleshooting section above
- Review the API documentation
- Examine server logs for error details
- Verify environment configuration

## 🔄 Updates

To update the backend:
1. Pull latest changes
2. Update dependencies: `pip install -r requirements.txt`
3. Run database migrations if needed
4. Restart the server

## 📄 License

This project is part of the TributeMaker application suite. All rights reserved. 
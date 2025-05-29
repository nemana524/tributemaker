from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, User, Tribute, TributeImage, VideoGeneration
from datetime import datetime, timedelta
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        try:
            user_id_str = get_jwt_identity()
            if not user_id_str:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = int(user_id_str)
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Authentication required'}), 401
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@jwt_required()
@admin_required
def dashboard():
    """Admin dashboard with system statistics"""
    try:
        # Get system statistics
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_verified=True).count()
        total_tributes = Tribute.query.count()
        completed_tributes = Tribute.query.filter_by(status='completed').count()
        processing_tributes = Tribute.query.filter_by(status='processing').count()
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_tributes = Tribute.query.filter(Tribute.created_at >= thirty_days_ago).count()
        
        # Get storage usage
        upload_folder = 'uploads'
        total_storage = 0
        if os.path.exists(upload_folder):
            for root, dirs, files in os.walk(upload_folder):
                total_storage += sum(os.path.getsize(os.path.join(root, file)) for file in files)
        
        # Convert bytes to MB
        total_storage_mb = round(total_storage / (1024 * 1024), 2)
        
        # Get top users by tribute count
        top_users = db.session.query(
            User.id, User.name, User.email, 
            db.func.count(Tribute.id).label('tribute_count')
        ).outerjoin(Tribute).group_by(User.id).order_by(
            db.func.count(Tribute.id).desc()
        ).limit(10).all()
        
        # Get recent tributes
        recent_tributes_data = Tribute.query.join(User).order_by(
            Tribute.created_at.desc()
        ).limit(10).all()
        
        stats = {
            'total_users': total_users,
            'verified_users': verified_users,
            'total_tributes': total_tributes,
            'completed_tributes': completed_tributes,
            'processing_tributes': processing_tributes,
            'recent_users': recent_users,
            'recent_tributes': recent_tributes,
            'total_storage_mb': total_storage_mb,
            'verification_rate': round((verified_users / total_users * 100) if total_users > 0 else 0, 1),
            'completion_rate': round((completed_tributes / total_tributes * 100) if total_tributes > 0 else 0, 1)
        }
        
        # Format top users
        top_users_data = []
        for user in top_users:
            top_users_data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'tribute_count': user.tribute_count
            })
        
        # Format recent tributes
        recent_tributes_list = []
        for tribute in recent_tributes_data:
            recent_tributes_list.append({
                'id': tribute.id,
                'title': tribute.title,
                'status': tribute.status,
                'created_at': tribute.created_at.isoformat(),
                'user_name': tribute.user.name,
                'user_email': tribute.user.email
            })
        
        return jsonify({
            'stats': stats,
            'top_users': top_users_data,
            'recent_tributes': recent_tributes_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users')
@jwt_required()
@admin_required
def get_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.name.contains(search),
                    User.email.contains(search)
                )
            )
        
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = []
        for user in users.items:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'provider': user.provider,
                'is_verified': user.is_verified,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat(),
                'tribute_count': len(user.tributes),
                'last_tribute': user.tributes[-1].created_at.isoformat() if user.tributes else None
            })
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user details"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'is_verified' in data:
            user.is_verified = data['is_verified']
        
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_verified': user.is_verified,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete user and all associated data"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deleting the last admin
        if user.is_admin:
            admin_count = User.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                return jsonify({'error': 'Cannot delete the last admin user'}), 400
        
        # Delete user (cascades to tributes and images)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tributes')
@jwt_required()
@admin_required
def get_tributes():
    """Get all tributes with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        query = Tribute.query.join(User)
        
        if status:
            query = query.filter(Tribute.status == status)
        
        if search:
            query = query.filter(
                db.or_(
                    Tribute.title.contains(search),
                    User.name.contains(search),
                    User.email.contains(search)
                )
            )
        
        tributes = query.order_by(Tribute.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        tributes_data = []
        for tribute in tributes.items:
            tributes_data.append({
                'id': tribute.id,
                'title': tribute.title,
                'status': tribute.status,
                'music_choice': tribute.music_choice,
                'created_at': tribute.created_at.isoformat(),
                'updated_at': tribute.updated_at.isoformat(),
                'user': {
                    'id': tribute.user.id,
                    'name': tribute.user.name,
                    'email': tribute.user.email
                },
                'image_count': len(tribute.images),
                'video_url': tribute.video_url
            })
        
        return jsonify({
            'tributes': tributes_data,
            'pagination': {
                'page': tributes.page,
                'pages': tributes.pages,
                'per_page': tributes.per_page,
                'total': tributes.total,
                'has_next': tributes.has_next,
                'has_prev': tributes.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tributes/<int:tribute_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_tribute(tribute_id):
    """Delete tribute and associated files"""
    try:
        tribute = Tribute.query.get_or_404(tribute_id)
        
        # Delete associated files
        for image in tribute.images:
            try:
                if os.path.exists(image.file_path):
                    os.remove(image.file_path)
            except:
                pass
        
        # Delete video file if exists
        video_gen = VideoGeneration.query.filter_by(tribute_id=tribute_id).first()
        if video_gen and video_gen.video_path and os.path.exists(video_gen.video_path):
            try:
                os.remove(video_gen.video_path)
            except:
                pass
        
        # Delete tribute (cascades to images and video generation records)
        db.session.delete(tribute)
        db.session.commit()
        
        return jsonify({'message': 'Tribute deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics')
@jwt_required()
@admin_required
def get_analytics():
    """Get detailed analytics data"""
    try:
        # User registration analytics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        daily_registrations = []
        daily_tributes = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            reg_count = User.query.filter(
                User.created_at >= date,
                User.created_at < next_date
            ).count()
            
            tribute_count = Tribute.query.filter(
                Tribute.created_at >= date,
                Tribute.created_at < next_date
            ).count()
            
            daily_registrations.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': reg_count
            })
            
            daily_tributes.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': tribute_count
            })
        
        # Status distribution
        status_counts = db.session.query(
            Tribute.status,
            db.func.count(Tribute.id).label('count')
        ).group_by(Tribute.status).all()
        
        status_distribution = [
            {'status': status, 'count': count}
            for status, count in status_counts
        ]
        
        # Provider distribution
        provider_counts = db.session.query(
            User.provider,
            db.func.count(User.id).label('count')
        ).group_by(User.provider).all()
        
        provider_distribution = [
            {'provider': provider, 'count': count}
            for provider, count in provider_counts
        ]
        
        return jsonify({
            'daily_registrations': daily_registrations,
            'daily_tributes': daily_tributes,
            'status_distribution': status_distribution,
            'provider_distribution': provider_distribution
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system/cleanup', methods=['POST'])
@jwt_required()
@admin_required
def system_cleanup():
    """Clean up orphaned files and failed video generations"""
    try:
        cleanup_stats = {
            'orphaned_files': 0,
            'failed_generations': 0,
            'freed_space_mb': 0
        }
        
        # Clean up failed video generations older than 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        failed_generations = VideoGeneration.query.filter(
            VideoGeneration.status == 'failed',
            VideoGeneration.created_at < twenty_four_hours_ago
        ).all()
        
        for gen in failed_generations:
            if gen.video_path and os.path.exists(gen.video_path):
                try:
                    file_size = os.path.getsize(gen.video_path)
                    os.remove(gen.video_path)
                    cleanup_stats['freed_space_mb'] += file_size / (1024 * 1024)
                except:
                    pass
            
            db.session.delete(gen)
            cleanup_stats['failed_generations'] += 1
        
        # Find orphaned image files
        upload_dir = os.path.join('uploads', 'images')
        if os.path.exists(upload_dir):
            db_filenames = set(img.filename for img in TributeImage.query.all())
            
            for filename in os.listdir(upload_dir):
                if filename not in db_filenames:
                    file_path = os.path.join(upload_dir, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleanup_stats['orphaned_files'] += 1
                        cleanup_stats['freed_space_mb'] += file_size / (1024 * 1024)
                    except:
                        pass
        
        db.session.commit()
        cleanup_stats['freed_space_mb'] = round(cleanup_stats['freed_space_mb'], 2)
        
        return jsonify({
            'message': 'System cleanup completed',
            'stats': cleanup_stats
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings', methods=['GET', 'POST'])
@jwt_required()
@admin_required
def system_settings():
    """Get or update system settings"""
    try:
        if request.method == 'GET':
            # Return current system settings
            settings = {
                'max_file_size_mb': 5,
                'max_images_per_tribute': 10,
                'video_quality': 'high',
                'email_verification_required': True,
                'auto_cleanup_enabled': True,
                'maintenance_mode': False
            }
            
            return jsonify({'settings': settings}), 200
        
        elif request.method == 'POST':
            # Update system settings
            data = request.get_json()
            
            # In a real application, you would save these to a settings table
            # For now, we'll just return success
            
            return jsonify({
                'message': 'Settings updated successfully',
                'settings': data
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
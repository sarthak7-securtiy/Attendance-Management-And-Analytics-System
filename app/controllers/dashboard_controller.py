import os
import glob
from flask import Blueprint, render_template, flash, redirect, url_for
from app.models.models import Student, Attendance, db
from app.controllers.auth_controller import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard showing system overview"""
    total_students = Student.query.count()
    total_attendance_records = Attendance.query.count()
    
    # Get recent attendance records
    recent_attendance = Attendance.query.order_by(Attendance.created_at.desc()).limit(5).all()
    
    # Get recent students
    recent_students = Student.query.limit(5).all()
    
    context = {
        'total_students': total_students,
        'total_attendance_records': total_attendance_records,
        'recent_attendance': recent_attendance,
        'recent_students': recent_students
    }
    
    return render_template('dashboard.html', **context)


@dashboard_bp.route('/clear-data', methods=['POST'])
@login_required
def clear_data():
    """Clear all student and attendance data from the database"""
    try:
        # Delete all attendance records first (due to foreign key constraint)
        Attendance.query.delete()
        
        # Delete all student records
        Student.query.delete()
        
        # Commit the changes to the database
        db.session.commit()
        
        # Clear the uploads folder
        from flask import current_app
        upload_folder = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
        upload_folder = os.path.abspath(upload_folder)
        
        if os.path.exists(upload_folder):
            uploaded_files = glob.glob(os.path.join(upload_folder, '*'))
            deleted_count = 0
            for file_path in uploaded_files:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError as e:
                    flash(f'Error deleting file {file_path}: {str(e)}', 'error')
            
            if deleted_count > 0:
                flash(f'All student and attendance data has been cleared from the system! ({deleted_count} uploaded files deleted)', 'success')
            else:
                flash('All student and attendance data has been cleared from the system!', 'success')
        else:
            flash('All student and attendance data has been cleared from the system!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing data: {str(e)}', 'error')
        
    return redirect(url_for('dashboard.index'))
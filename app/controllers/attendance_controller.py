import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app.models.models import Attendance, Student, db
from app.utils.excel_handler import process_attendance_excel, save_attendance_to_db
from flask import current_app as app

attendance_bp = Blueprint('attendance', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

UPLOAD_FOLDER = 'uploads'  # Default upload folder, will be configured in the main app

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@attendance_bp.route('/upload-attendance', methods=['GET', 'POST'])
def upload_attendance():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser submits an empty part without filename
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Get the actual upload folder from the current app context
            from flask import current_app
            actual_upload_folder = getattr(current_app, 'upload_folder', UPLOAD_FOLDER)
            file_path = os.path.join(actual_upload_folder, filename)
            file.save(file_path)
            
            # Process the Excel file
            result = process_attendance_excel(file_path)
            
            if result['success']:
                # Show preview of data before saving
                return render_template('attendance_upload_preview.html', 
                                     data=result['data'], 
                                     errors=result.get('errors', []),
                                     total_records=len(result['data']))
            else:
                flash(result['message'], 'error')
                return redirect(url_for('attendance.upload_attendance'))
        else:
            flash('Invalid file type. Please upload Excel files only (.xlsx, .xls)', 'error')
            return redirect(url_for('attendance.upload_attendance'))
    
    return render_template('upload_attendance.html')

@attendance_bp.route('/confirm-attendance-upload', methods=['POST'])
def confirm_attendance_upload():
    # Get the data from the form
    attendance_data = request.get_json()
    
    if not attendance_data:
        return jsonify({'success': False, 'message': 'No data to save'})
    
    # Save to database
    success, message = save_attendance_to_db(attendance_data)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message})

@attendance_bp.route('/attendance')
def list_attendance():
    attendance_records = Attendance.query.all()
    return render_template('attendance_list.html', attendance_records=attendance_records)

@attendance_bp.route('/attendance/student/<ticket_no>')
def get_student_attendance(ticket_no):
    student = Student.query.filter_by(ticket_no=ticket_no).first_or_404()
    attendance_records = Attendance.query.filter_by(ticket_no=ticket_no).all()
    return render_template('student_attendance.html', student=student, attendance_records=attendance_records)
import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app.models.models import Student, db
from app.utils.excel_handler import process_student_excel, save_students_to_db
from flask import current_app as app

student_bp = Blueprint('student', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

UPLOAD_FOLDER = 'uploads'  # Default upload folder, will be configured in the main app

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route('/upload-student-master', methods=['GET', 'POST'])
def upload_student_master():
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
            result = process_student_excel(file_path)
            
            if result['success']:
                # Show preview of data before saving
                return render_template('student_upload_preview.html', 
                                     data=result['data'], 
                                     errors=result.get('errors', []),
                                     total_records=len(result['data']))
            else:
                flash(result['message'], 'error')
                return redirect(url_for('student.upload_student_master'))
        else:
            flash('Invalid file type. Please upload Excel files only (.xlsx, .xls)', 'error')
            return redirect(url_for('student.upload_student_master'))
    
    return render_template('upload_student_master.html')

@student_bp.route('/confirm-student-upload', methods=['POST'])
def confirm_student_upload():
    # Get the data from the form
    students_data = request.get_json()
    
    if not students_data:
        return jsonify({'success': False, 'message': 'No data to save'})
    
    # Save to database
    success, message = save_students_to_db(students_data)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message})

@student_bp.route('/students')
def list_students():
    students = Student.query.all()
    return render_template('students_list.html', students=students)

@student_bp.route('/student/<ticket_no>')
def get_student(ticket_no):
    student = Student.query.filter_by(ticket_no=ticket_no).first_or_404()
    return render_template('student_detail.html', student=student)
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from app.models.models import Student, Attendance
from app.controllers.auth_controller import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Search for student by Ticket Number"""
    if request.method == 'POST':
        ticket_no = request.form.get('ticket_no', '').strip()
        
        if not ticket_no:
            flash('Please enter a Ticket Number', 'error')
            return redirect(url_for('search.search'))
        
        student = Student.query.filter_by(ticket_no=ticket_no).first()
        
        if not student:
            flash(f'No student found with Ticket Number: {ticket_no}', 'error')
            return redirect(url_for('search.search'))
        
        # Get all attendance records for this student
        attendance_records = Attendance.query.filter_by(ticket_no=ticket_no).order_by(Attendance.month).all()
        
        return render_template('student_search_result.html', 
                             student=student, 
                             attendance_records=attendance_records)
    
    return render_template('search.html')

@search_bp.route('/api/search/<ticket_no>')
@login_required
def search_api(ticket_no):
    """API endpoint to search for student by Ticket Number"""
    student = Student.query.filter_by(ticket_no=ticket_no).first()
    
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    # Get all attendance records for this student
    attendance_records = Attendance.query.filter_by(ticket_no=ticket_no).order_by(Attendance.month).all()
    
    student_data = {
        'ticket_no': student.ticket_no,
        'pno': student.pno,
        'name': student.name,
        'father_name': student.father_name,
        'dob': student.dob.isoformat() if student.dob else None,
        'gender': student.gender,
        'mobile': student.mobile,
        'address': student.address,
        'qualification_trade': student.qualification_trade,
        'passing_year': student.passing_year,
        'college_name': student.college_name,
        'ssc_percentage': student.ssc_percentage,
        'hsc_percentage': student.hsc_percentage,
        'email_id': student.email_id,
        'blood_group': student.blood_group,
        'current_address_route': student.current_address_route,
        'attendance_records': [
            {
                'month': att.month,
                'total_days': att.total_days,
                'present_days': att.present_days,
                'absent_days': att.absent_days,
                'attendance_percentage': att.attendance_percentage
            } for att in attendance_records
        ]
    }
    
    return jsonify({'success': True, 'student': student_data})

@search_bp.route('/quick-search')
@login_required
def quick_search():
    """Quick search page with auto-complete"""
    return render_template('quick_search.html')


@search_bp.route('/view-student/<ticket_no>')
@login_required
def view_student(ticket_no):
    """View student details by ticket number"""
    student = Student.query.filter_by(ticket_no=ticket_no).first()
    
    if not student:
        flash(f'No student found with Ticket Number: {ticket_no}', 'error')
        return redirect(url_for('search.search'))
    
    # Get all attendance records for this student
    attendance_records = Attendance.query.filter_by(ticket_no=ticket_no).order_by(Attendance.month).all()
    
    return render_template('student_search_result.html', 
                         student=student, 
                         attendance_records=attendance_records)
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from app.models.models import Student, Attendance
from app.controllers.auth_controller import login_required
from datetime import datetime
from collections import defaultdict

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis')
@login_required
def attendance_analysis():
    """Overall attendance analysis dashboard"""
    from datetime import datetime
    
    # Get current month name
    current_month = datetime.now().strftime('%B')
    
    # Load all data by default to show comprehensive analytics
    all_attendance = Attendance.query.all()
    
    # Check if current month data exists
    current_month_exists = Attendance.query.filter(Attendance.month == current_month).first() is not None
    showing_current_month = False  # Default to showing all data
    
    if not all_attendance:
        flash('No attendance data available for analysis', 'info')
        return render_template('analysis.html', 
                              overall_stats=None, 
                              monthly_stats=None, 
                              defaulter_list=None,
                              months=[],
                              chart_data=None,
                              daily_stats=None,
                              current_month=current_month,
                              showing_current_month=showing_current_month,
                              current_month_exists=current_month_exists)
    
    # Calculate overall statistics
    total_records = len(all_attendance)
    total_students = len(set([att.ticket_no for att in all_attendance]))
    
    # Calculate average attendance percentage
    total_percentage = sum([att.attendance_percentage for att in all_attendance])
    avg_attendance = total_percentage / total_records if total_records > 0 else 0
    
    # Calculate attendance categories
    excellent_count = len([att for att in all_attendance if att.attendance_percentage >= 90])
    good_count = len([att for att in all_attendance if 75 <= att.attendance_percentage < 90])
    defaulter_count = len([att for att in all_attendance if att.attendance_percentage < 75])
    
    # Get all unique months
    all_months = list(set([att.month for att in Attendance.query.all()]))  # Get all months from all records
    all_months.sort()  # Sort months alphabetically for now
    
    # Calculate monthly statistics
    monthly_stats = {}
    for month in all_months:
        month_attendance = [att for att in all_attendance if att.month == month]
        if month_attendance:
            month_avg = sum([att.attendance_percentage for att in month_attendance]) / len(month_attendance)
            monthly_stats[month] = {
                'avg_attendance': round(month_avg, 2),
                'total_records': len(month_attendance),
                'defaulter_count': len([att for att in month_attendance if att.attendance_percentage < 75])
            }
    
    # Get defaulter list (students with attendance < 75%)
    defaulter_tickets = set([att.ticket_no for att in all_attendance if att.attendance_percentage < 75])
    defaulter_students = []
    
    for ticket_no in defaulter_tickets:
        student = Student.query.filter_by(ticket_no=ticket_no).first()
        if student:
            # Get all attendance records for this defaulter
            student_attendance = Attendance.query.filter_by(ticket_no=ticket_no).all()
            avg_attendance = sum([att.attendance_percentage for att in student_attendance]) / len(student_attendance) if student_attendance else 0
            
            defaulter_students.append({
                'student': student,
                'avg_attendance': round(avg_attendance, 2),
                'attendance_records': student_attendance
            })
    
    # Prepare data for charts (defined once)
    attendance_categories = {
        'labels': ['Excellent (90%+)', 'Good (75-89%)', 'Defaulter (<75%)'],
        'data': [excellent_count, good_count, defaulter_count],
        'colors': ['#198754', '#ffc107', '#dc3545']  # Bootstrap colors: success, warning, danger
    }
    
    # Prepare monthly attendance data for chart
    monthly_attendance_data = []
    monthly_defaulter_data = []
    for month in all_months:
        if month in monthly_stats:
            monthly_attendance_data.append(monthly_stats[month]['avg_attendance'])
            monthly_defaulter_data.append(monthly_stats[month]['defaulter_count'])
    
    chart_data = {
        'attendance_categories': attendance_categories,
        'monthly_labels': all_months,
        'monthly_attendance': monthly_attendance_data,
        'monthly_defaulter': monthly_defaulter_data
    }
    
    # Prepare daily attendance statistics
    # Since we don't have actual daily records, we'll create a representation based on recent monthly data
    # Use the created_at field to represent when records were entered
    from collections import defaultdict
    daily_stats = defaultdict(list)
    
    # Group all attendance records by date of entry (created_at)
    for att in all_attendance:
        if att.created_at:
            date_key = att.created_at.strftime('%Y-%m-%d')
            daily_stats[date_key].append(att.attendance_percentage)
    
    # Calculate daily averages
    daily_averages = {}
    for date, percentages in daily_stats.items():
        daily_averages[date] = sum(percentages) / len(percentages) if percentages else 0
    
    # Sort by date, get most recent 15 days
    sorted_daily_averages = dict(sorted(daily_averages.items(), key=lambda x: x[0], reverse=True)[:15])
    
    overall_stats = {
        'total_records': total_records,
        'total_students': total_students,
        'avg_attendance': round(avg_attendance, 2),
        'excellent_count': excellent_count,
        'good_count': good_count,
        'defaulter_count': defaulter_count
    }
    
    return render_template('analysis.html', 
                          overall_stats=overall_stats, 
                          monthly_stats=monthly_stats, 
                          defaulter_list=defaulter_students,
                          months=all_months,
                          chart_data=chart_data,
                          daily_stats=sorted_daily_averages,
                          current_month=current_month,
                          showing_current_month=showing_current_month,
                          current_month_exists=current_month_exists)

@analysis_bp.route('/analysis/month/<month>')
@login_required
def monthly_analysis(month):
    """Monthly attendance analysis"""
    attendance_records = Attendance.query.filter_by(month=month).all()
    
    if not attendance_records:
        flash(f'No attendance data available for {month}', 'info')
        return redirect(url_for('analysis.attendance_analysis'))
    
    # Calculate statistics for this month
    total_records = len(attendance_records)
    total_students = len(set([att.ticket_no for att in attendance_records]))
    
    # Calculate average attendance percentage
    total_percentage = sum([att.attendance_percentage for att in attendance_records])
    avg_attendance = total_percentage / total_records if total_records > 0 else 0
    
    # Calculate attendance categories
    excellent_count = len([att for att in attendance_records if att.attendance_percentage >= 90])
    good_count = len([att for att in attendance_records if 75 <= att.attendance_percentage < 90])
    defaulter_count = len([att for att in attendance_records if att.attendance_percentage < 75])
    
    # Get defaulter list for this month
    month_defaulter_tickets = set([att.ticket_no for att in attendance_records if att.attendance_percentage < 75])
    month_defaulter_students = []
    
    for ticket_no in month_defaulter_tickets:
        student = Student.query.filter_by(ticket_no=ticket_no).first()
        if student:
            # Get this month's attendance for this student
            student_monthly_attendance = next((att for att in attendance_records if att.ticket_no == ticket_no), None)
            
            month_defaulter_students.append({
                'student': student,
                'attendance': student_monthly_attendance
            })
    
    monthly_stats = {
        'month': month,
        'total_records': total_records,
        'total_students': total_students,
        'avg_attendance': round(avg_attendance, 2),
        'excellent_count': excellent_count,
        'good_count': good_count,
        'defaulter_count': defaulter_count
    }
    
    return render_template('monthly_analysis.html', 
                          monthly_stats=monthly_stats, 
                          defaulter_list=month_defaulter_students)

@analysis_bp.route('/api/analysis/stats')
@login_required
def analysis_api():
    """API endpoint for attendance statistics"""
    all_attendance = Attendance.query.all()
    
    if not all_attendance:
        return jsonify({'success': False, 'message': 'No attendance data available'})
    
    # Calculate overall statistics
    total_records = len(all_attendance)
    total_students = len(set([att.ticket_no for att in all_attendance]))
    
    # Calculate average attendance percentage
    total_percentage = sum([att.attendance_percentage for att in all_attendance])
    avg_attendance = total_percentage / total_records if total_records > 0 else 0
    
    # Calculate attendance categories
    excellent_count = len([att for att in all_attendance if att.attendance_percentage >= 90])
    good_count = len([att for att in all_attendance if 75 <= att.attendance_percentage < 90])
    defaulter_count = len([att for att in all_attendance if att.attendance_percentage < 75])
    
    # Get all unique months
    months = list(set([att.month for att in all_attendance]))
    months.sort()
    
    # Calculate monthly statistics
    monthly_stats = {}
    for month in months:
        month_attendance = [att for att in all_attendance if att.month == month]
        if month_attendance:
            month_avg = sum([att.attendance_percentage for att in month_attendance]) / len(month_attendance)
            monthly_stats[month] = {
                'avg_attendance': round(month_avg, 2),
                'total_records': len(month_attendance),
                'defaulter_count': len([att for att in month_attendance if att.attendance_percentage < 75])
            }
    
    # Get defaulter count by month
    defaulter_by_month = {}
    for month in months:
        month_attendance = [att for att in all_attendance if att.month == month and att.attendance_percentage < 75]
        defaulter_by_month[month] = len(month_attendance)
    
    stats_data = {
        'overall': {
            'total_records': total_records,
            'total_students': total_students,
            'avg_attendance': round(avg_attendance, 2),
            'excellent_count': excellent_count,
            'good_count': good_count,
            'defaulter_count': defaulter_count
        },
        'monthly': monthly_stats,
        'defaulter_by_month': defaulter_by_month,
        'months': months
    }
    
    return jsonify({'success': True, 'stats': stats_data})
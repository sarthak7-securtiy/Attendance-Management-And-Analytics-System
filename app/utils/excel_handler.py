import pandas as pd
from datetime import datetime
from app.models.models import Student
from app.models.models import db
import re

def identify_student_columns(df):
    """
    Identify student data columns by looking for similar names in the Excel file
    Returns a mapping of required field names to actual column names in the file
    """
    import re
    
    # Define possible variations for each required column
    column_mappings = {
        'ticket_no': ['ticket', 'ticket no', 'ticket_no', 'ticket number', 'id', 'student id', 'student_id'],
        'pno': ['pno', 'personal number', 'personal_number', 'p number', 'emp id', 'emp_id'],
        'name': ['name', 'student name', 'full name', 'student_name', 'studentname', 'sname'],
        'medical_policy': ['medical policy', 'medical_policy', 'medical', 'health policy', 'insurance'],
        'father_name': ['father name', 'father_name', 'fathername', 'father s name', 'fathers name', 'parent name'],
        'dob': ['dob', 'date of birth', 'birth date', 'birth_date', 'date_of_birth', 'bday', 'birthday'],
        'gender': ['gender', 'sex', 'male/female', 'gender_male_female'],
        'mobile': ['mobile', 'mobile number', 'mobile_number', 'phone', 'phone number', 'contact', 'contact number'],
        'address': ['address', 'permanent address', 'current address', 'full address', 'home address'],
        'qualification_trade': ['qualification', 'trade', 'qualification trade', 'qualification_trade', 'course', 'field', 'stream'],
        'passing_year': ['passing year', 'passing_year', 'passingyear', 'year of passing', 'graduation year'],
        'college_name': ['college', 'college name', 'college_name', 'school', 'institution', 'university'],
        'ssc_percentage': ['ssc', 'ssc percentage', 'ssc_percentage', '10th percentage', '10th %'],
        'hsc_percentage': ['hsc', 'hsc percentage', 'hsc_percentage', '12th percentage', '12th %'],
        'aadhaar_no': ['aadhaar', 'aadhaar number', 'aadhaar_no', 'aadhaar_no', 'aadhar', 'aadhar number'],
        'pan_no': ['pan', 'pan number', 'pan_no', 'pan card', 'pancard'],
        'email_id': ['email', 'email id', 'email_id', 'email address', 'email_address'],
        'blood_group': ['blood group', 'blood_group', 'blood', 'blood type', 'blood_type'],
        'current_address_route': ['current address', 'route', 'bus stop', 'current_address_route', 'address route', 'location'],
        'batch': ['batch', 'batch no', 'batch_no', 'batch number', 'class', 'class name', 'class_name', 'section', 'division', 'year', 'year of admission', 'admission year']
    }
    
    # Normalize column names in the dataframe
    normalized_cols = {}
    for col in df.columns:
        # Convert column name to string and handle non-string types
        col_str = str(col)
        normalized = col_str.lower().strip().replace('_', ' ')
        normalized_cols[normalized] = col  # Store original column name
    
    # Find matches
    identified_cols = {}
    for field_name, possible_names in column_mappings.items():
        for name in possible_names:
            normalized_name = name.lower().strip()
            # Check for exact match
            if normalized_name in normalized_cols:
                identified_cols[field_name] = normalized_cols[normalized_name]
                break
            # Check for partial match
            else:
                for norm_col, orig_col in normalized_cols.items():
                    if normalized_name in norm_col or norm_col in normalized_name:
                        identified_cols[field_name] = orig_col
                        break
                if field_name in identified_cols:
                    break
    
    return identified_cols

def validate_student_excel_format(df):
    """
    Validate the Student Master Excel file format by identifying required columns
    """
    identified_cols = identify_student_columns(df)
    
    required_fields = ['ticket_no', 'pno', 'name']  # Minimum required fields
    missing_required = [field for field in required_fields if field not in identified_cols]
    
    if missing_required:
        return False, f"Missing required columns: {', '.join(missing_required)}"
    
    return True, "Excel format is valid"


def process_student_excel(file_path):
    """
    Process the Student Master Excel file and return validated data
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Identify columns
        identified_cols = identify_student_columns(df)
        
        # Validate format
        is_valid, message = validate_student_excel_format(df)
        if not is_valid:
            return {'success': False, 'message': message, 'data': []}
        
        # Prepare data for database insertion
        students_data = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Validate required fields using identified columns
                ticket_no = None
                pno = None
                name = None
                
                if 'ticket_no' in identified_cols:
                    ticket_no = str(row[identified_cols['ticket_no']]).strip() if pd.notna(row[identified_cols['ticket_no']]) else None
                if 'pno' in identified_cols:
                    pno = str(row[identified_cols['pno']]).strip() if pd.notna(row[identified_cols['pno']]) else None
                if 'name' in identified_cols:
                    name = str(row[identified_cols['name']]).strip() if pd.notna(row[identified_cols['name']]) else None
                
                if not ticket_no or not pno or not name:
                    errors.append(f"Row {index + 2}: Missing required fields (Ticket No, PNO, or Name)")
                    continue
                
                # Check for duplicate ticket numbers in the uploaded data
                if any(s['ticket_no'] == ticket_no for s in students_data):
                    errors.append(f"Row {index + 2}: Duplicate Ticket No '{ticket_no}' in uploaded data")
                    continue
                
                # Skip database checks when not in app context (these will be done during actual upload)
                # The duplicate check in the uploaded data was already done earlier, so we skip here
                
                # Process other fields using identified columns
                student_data = {
                    'ticket_no': ticket_no,
                    'pno': pno,
                    'name': name
                }
                
                # Add optional fields if they exist in the identified columns
                if 'medical_policy' in identified_cols:
                    medical_policy = str(row[identified_cols['medical_policy']]).strip() if pd.notna(row[identified_cols['medical_policy']]) else None
                    student_data['medical_policy'] = medical_policy
                
                if 'father_name' in identified_cols:
                    father_name = str(row[identified_cols['father_name']]).strip() if pd.notna(row[identified_cols['father_name']]) else None
                    student_data['father_name'] = father_name
                
                if 'dob' in identified_cols:
                    dob = None
                    dob_val = row[identified_cols['dob']]
                    if pd.notna(dob_val):
                        try:
                            if isinstance(dob_val, str):
                                dob = datetime.strptime(dob_val, '%Y-%m-%d').date()
                            else:
                                dob = dob_val.date() if hasattr(dob_val, 'date') else dob_val
                        except:
                            # Try other common date formats
                            for fmt in ['%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%d-%b-%Y', '%d/%m/%y']:
                                try:
                                    dob = datetime.strptime(str(dob_val), fmt).date()
                                    break
                                except:
                                    continue
                    student_data['dob'] = dob
                
                if 'gender' in identified_cols:
                    gender = str(row[identified_cols['gender']]).strip() if pd.notna(row[identified_cols['gender']]) else None
                    student_data['gender'] = gender
                
                if 'mobile' in identified_cols:
                    mobile = str(row[identified_cols['mobile']]).strip() if pd.notna(row[identified_cols['mobile']]) else None
                    student_data['mobile'] = mobile
                
                if 'address' in identified_cols:
                    address = str(row[identified_cols['address']]).strip() if pd.notna(row[identified_cols['address']]) else None
                    student_data['address'] = address
                
                if 'qualification_trade' in identified_cols:
                    qualification_trade = str(row[identified_cols['qualification_trade']]).strip() if pd.notna(row[identified_cols['qualification_trade']]) else None
                    student_data['qualification_trade'] = qualification_trade
                
                if 'passing_year' in identified_cols:
                    passing_year = None
                    passing_year_val = row[identified_cols['passing_year']]
                    if pd.notna(passing_year_val) and str(passing_year_val).isdigit():
                        passing_year = int(passing_year_val)
                    elif pd.notna(passing_year_val) and str(passing_year_val).replace('.', '').replace('-', '').isdigit():
                        # Handle years that might be stored as floats
                        passing_year = int(float(passing_year_val))
                    student_data['passing_year'] = passing_year
                
                if 'college_name' in identified_cols:
                    college_name = str(row[identified_cols['college_name']]).strip() if pd.notna(row[identified_cols['college_name']]) else None
                    student_data['college_name'] = college_name
                
                if 'ssc_percentage' in identified_cols:
                    ssc_percentage = None
                    ssc_val = row[identified_cols['ssc_percentage']]
                    if pd.notna(ssc_val) and str(ssc_val).replace('.', '').isdigit():
                        ssc_percentage = float(ssc_val)
                    elif pd.notna(ssc_val) and str(ssc_val).replace('.', '').replace('%', '').isdigit():
                        # Handle percentages with % symbol
                        ssc_percentage = float(str(ssc_val).replace('%', ''))
                    student_data['ssc_percentage'] = ssc_percentage
                
                if 'hsc_percentage' in identified_cols:
                    hsc_percentage = None
                    hsc_val = row[identified_cols['hsc_percentage']]
                    if pd.notna(hsc_val) and str(hsc_val).replace('.', '').isdigit():
                        hsc_percentage = float(hsc_val)
                    elif pd.notna(hsc_val) and str(hsc_val).replace('.', '').replace('%', '').isdigit():
                        # Handle percentages with % symbol
                        hsc_percentage = float(str(hsc_val).replace('%', ''))
                    student_data['hsc_percentage'] = hsc_percentage
                
                if 'aadhaar_no' in identified_cols:
                    aadhaar_no = str(row[identified_cols['aadhaar_no']]).strip() if pd.notna(row[identified_cols['aadhaar_no']]) else None
                    student_data['aadhaar_no'] = aadhaar_no
                
                if 'pan_no' in identified_cols:
                    pan_no = str(row[identified_cols['pan_no']]).strip() if pd.notna(row[identified_cols['pan_no']]) else None
                    student_data['pan_no'] = pan_no
                
                if 'email_id' in identified_cols:
                    email_id = str(row[identified_cols['email_id']]).strip() if pd.notna(row[identified_cols['email_id']]) else None
                    student_data['email_id'] = email_id
                
                if 'blood_group' in identified_cols:
                    blood_group = str(row[identified_cols['blood_group']]).strip() if pd.notna(row[identified_cols['blood_group']]) else None
                    student_data['blood_group'] = blood_group
                
                if 'current_address_route' in identified_cols:
                    current_address_route = str(row[identified_cols['current_address_route']]).strip() if pd.notna(row[identified_cols['current_address_route']]) else None
                    student_data['current_address_route'] = current_address_route
                
                if 'batch' in identified_cols:
                    batch = str(row[identified_cols['batch']]).strip() if pd.notna(row[identified_cols['batch']]) else None
                    student_data['batch'] = batch
                
                students_data.append(student_data)
                
            except Exception as e:
                errors.append(f"Row {index + 2}: Error processing row - {str(e)}")
                continue
        
        return {
            'success': True,
            'message': f"Processed {len(students_data)} records successfully",
            'data': students_data,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error reading Excel file: {str(e)}",
            'data': [],
            'errors': [f"File processing error: {str(e)}"]
        }


def save_students_to_db(students_data):
    """
    Save validated student data to the database
    """
    try:
        for student_data in students_data:
            # Prepare data with proper type conversions
            processed_data = {}
            for key, value in student_data.items():
                if value is None or (isinstance(value, float) and (value != value)):  # Check for NaN (value != value is true for NaN)
                    processed_data[key] = None
                elif key in ['passing_year'] and value is not None:
                    # Convert to integer for integer fields
                    try:
                        processed_data[key] = int(float(value)) if str(value).replace('.', '').replace('-', '').isdigit() else None
                    except:
                        processed_data[key] = None
                elif key in ['ssc_percentage', 'hsc_percentage'] and value is not None:
                    # Convert to float for float fields
                    try:
                        processed_data[key] = float(value) if str(value).replace('.', '').replace('-', '').replace('%', '').isdigit() else None
                    except:
                        processed_data[key] = None
                elif key == 'dob' and value is not None:
                    # Handle date fields - ensure it's a proper date object
                    from datetime import datetime, date
                    if isinstance(value, str):
                        try:
                            # Parse string date to datetime object and extract date
                            parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                            processed_data[key] = parsed_date
                        except ValueError:
                            # If the format is different, try other common formats
                            parsed_date = None
                            for fmt in ['%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%d-%b-%Y', '%d/%m/%y']:
                                try:
                                    parsed_date = datetime.strptime(value, fmt).date()
                                    break
                                except ValueError:
                                    continue
                            # If no format worked, set to None
                            processed_data[key] = parsed_date
                    elif hasattr(value, 'date') and callable(getattr(value, 'date')):
                        # If it's a pandas datetime object, convert to date
                        processed_data[key] = value.date()
                    elif isinstance(value, date) and not isinstance(value, datetime):
                        # If it's already a date object, keep as is
                        processed_data[key] = value
                    elif isinstance(value, datetime):
                        # If it's a datetime object, extract the date part
                        processed_data[key] = value.date()
                    else:
                        # For any other type, try to convert or set to None
                        processed_data[key] = None
                else:
                    # For string fields, convert to string and handle properly
                    processed_data[key] = str(value) if value is not None else None
            
            # Check if student with same ticket_no already exists
            existing_student = Student.query.filter_by(ticket_no=processed_data['ticket_no']).first()
            if existing_student:
                # Update existing student instead of creating duplicate
                for key, value in processed_data.items():
                    if hasattr(existing_student, key):
                        setattr(existing_student, key, value)
            else:
                # Create new Student object with processed data
                student = Student(**processed_data)
                db.session.add(student)
        
        db.session.commit()
        return True, f"Successfully saved {len(students_data)} students to database"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"


def identify_attendance_columns(df):
    """
    Identify attendance data columns by looking for similar names in the Excel file
    Returns a mapping of required field names to actual column names in the file
    """
    import re
    
    # Define possible variations for each required column
    column_mappings = {
        'ticket_no': ['ticket', 'ticket no', 'ticket_no', 'ticket number', 'id', 'student id', 'student_id'],
        'student_name': ['student name', 'name', 'student_name', 'studentname', 'sname', 'full name'],
        'month': ['month', 'attendance month', 'month_name', 'period', 'attendance period'],
        'total_days': ['total days', 'total_days', 'total working days', 'working days', 'total_working_days', 'days'],
        'present_days': ['present days', 'present_days', 'present_days', 'present', 'days present', 'present count'],
        'absent_days': ['absent days', 'absent_days', 'absent', 'days absent', 'absent count'],
        'attendance_percentage': ['attendance percentage', 'attendance_percentage', 'attendance %', 'attendance_percent', 'percentage', 'percent', '%']
    }
    
    # Normalize column names in the dataframe
    normalized_cols = {}
    for col in df.columns:
        # Convert column name to string and handle non-string types
        col_str = str(col)
        normalized = col_str.lower().strip().replace('_', ' ')
        normalized_cols[normalized] = col  # Store original column name
    
    # Find matches
    identified_cols = {}
    for field_name, possible_names in column_mappings.items():
        for name in possible_names:
            normalized_name = name.lower().strip()
            # Check for exact match
            if normalized_name in normalized_cols:
                identified_cols[field_name] = normalized_cols[normalized_name]
                break
            # Check for partial match
            else:
                for norm_col, orig_col in normalized_cols.items():
                    if normalized_name in norm_col or norm_col in normalized_name:
                        identified_cols[field_name] = orig_col
                        break
                if field_name in identified_cols:
                    break
    
    return identified_cols

def validate_attendance_excel_format(df):
    """
    Validate the Attendance Excel file format by identifying required columns
    """
    identified_cols = identify_attendance_columns(df)
    
    required_fields = ['ticket_no', 'month', 'total_days', 'present_days', 'attendance_percentage']  # Minimum required fields
    missing_required = [field for field in required_fields if field not in identified_cols]
    
    if missing_required:
        return False, f"Missing required columns: {', '.join(missing_required)}"
    
    return True, "Excel format is valid"


def process_attendance_excel(file_path):
    """
    Process the Attendance Excel file and return validated data
    Handles both monthly summary format and daily attendance format
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Check if this is a daily attendance format (has date columns)
        has_date_columns = any(isinstance(col, (pd.Timestamp, datetime)) for col in df.columns)
        
        if has_date_columns:
            # Process as daily attendance format
            return process_daily_attendance_format(df)
        
        # Otherwise, process as monthly summary format
        # Identify columns
        identified_cols = identify_attendance_columns(df)
        
        # Validate format
        is_valid, message = validate_attendance_excel_format(df)
        if not is_valid:
            return {'success': False, 'message': message, 'data': []}
        
        # Prepare data for database insertion
        attendance_data = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Validate required fields using identified columns
                ticket_no = None
                month = None
                
                if 'ticket_no' in identified_cols:
                    ticket_no = str(row[identified_cols['ticket_no']]).strip() if pd.notna(row[identified_cols['ticket_no']]) else None
                if 'month' in identified_cols:
                    month = str(row[identified_cols['month']]).strip() if pd.notna(row[identified_cols['month']]) else None
                
                if not ticket_no or not month:
                    errors.append(f"Row {index + 2}: Missing required fields (Ticket No or Month)")
                    continue
                
                # Check for duplicate ticket numbers in the uploaded data
                if any(a['ticket_no'] == ticket_no and a['month'] == month for a in attendance_data):
                    errors.append(f"Row {index + 2}: Duplicate record for Ticket No '{ticket_no}' and Month '{month}' in uploaded data")
                    continue
                
                # Process other fields using identified columns
                attendance_record = {
                    'ticket_no': ticket_no,
                    'month': month
                }
                
                # Add optional fields if they exist in the identified columns
                if 'total_days' in identified_cols:
                    total_days_val = row[identified_cols['total_days']]
                    total_days = int(float(total_days_val)) if pd.notna(total_days_val) and str(total_days_val).replace('.', '').replace('-', '').isdigit() else None
                    attendance_record['total_days'] = total_days
                
                if 'present_days' in identified_cols:
                    present_days_val = row[identified_cols['present_days']]
                    present_days = int(float(present_days_val)) if pd.notna(present_days_val) and str(present_days_val).replace('.', '').replace('-', '').isdigit() else None
                    attendance_record['present_days'] = present_days
                
                if 'absent_days' in identified_cols:
                    absent_days_val = row[identified_cols['absent_days']]
                    absent_days = int(float(absent_days_val)) if pd.notna(absent_days_val) and str(absent_days_val).replace('.', '').replace('-', '').isdigit() else None
                    attendance_record['absent_days'] = absent_days
                
                if 'attendance_percentage' in identified_cols:
                    attendance_percentage_val = row[identified_cols['attendance_percentage']]
                    attendance_percentage = float(attendance_percentage_val) if pd.notna(attendance_percentage_val) and str(attendance_percentage_val).replace('.', '').replace('-', '').isdigit() else None
                    attendance_record['attendance_percentage'] = attendance_percentage
                
                # If absent days is not provided, calculate it
                if absent_days is None and total_days is not None and present_days is not None:
                    attendance_record['absent_days'] = total_days - present_days
                
                # If attendance percentage is not provided, calculate it
                if attendance_record.get('attendance_percentage') is None:
                    if attendance_record.get('total_days') and attendance_record.get('present_days'):
                        total = attendance_record['total_days']
                        present = attendance_record['present_days']
                        if total > 0:
                            attendance_record['attendance_percentage'] = round((present / total) * 100, 2)
                
                # Validate attendance percentage range
                attendance_percentage = attendance_record.get('attendance_percentage')
                if attendance_percentage is not None and (attendance_percentage > 100 or attendance_percentage < 0):
                    errors.append(f"Row {index + 2}: Attendance percentage ({attendance_percentage}) is not within valid range (0-100)")
                
                # Skip duplicate attendance check when not in app context (this will be done during actual upload)
                # Duplicate check will happen during actual upload to the database
                
                attendance_data.append(attendance_record)
                
            except Exception as e:
                errors.append(f"Row {index + 2}: Error processing row - {str(e)}")
                continue
        
        return {
            'success': True,
            'message': f"Processed {len(attendance_data)} records successfully",
            'data': attendance_data,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error reading Excel file: {str(e)}",
            'data': [],
            'errors': [f"File processing error: {str(e)}"]
        }


def process_daily_attendance_format(df):
    """
    Process daily attendance format where columns are dates and values are attendance status
    Returns processed monthly attendance data
    """
    # Identify key columns
    ticket_col = None
    name_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'ticket' in col_str or 'id' in col_str:
            ticket_col = col
        elif 'name' in col_str:
            name_col = col
    
    if not ticket_col:
        return {'success': False, 'message': 'Could not identify ticket number column', 'data': []}
    
    processed_data = []
    errors = []
    
    for index, row in df.iterrows():
        ticket_no = str(row[ticket_col]).strip() if pd.notna(row[ticket_col]) else None
        student_name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else None
        
        if not ticket_no:
            errors.append(f"Row {index + 2}: Missing ticket number")
            continue
        
        # Count attendance for each day (excluding PNO, Ticket No, Name columns)
        date_columns = [col for col in df.columns if col not in [ticket_col, name_col]]
        total_days = len(date_columns)
        
        if total_days == 0:
            errors.append(f"Row {index + 2}: No date columns found for attendance")
            continue
        
        present_days = 0
        for date_col in date_columns:
            status = str(row[date_col]).strip().upper() if pd.notna(row[date_col]) else ''
            # Count as present if status is 'P', 'PRESENT', 'PR', 'PR ', etc.
            if status in ['P', 'PRESENT', 'PR', 'PR '] or (status and status.startswith('P')):
                present_days += 1
        
        # Calculate attendance percentage
        attendance_percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0
        
        # For now, assume it's for the current month
        # In a real implementation, you might want to get the month from the date columns
        import datetime
        month = datetime.date.today().strftime('%B')  # Current month
        
        attendance_record = {
            'ticket_no': ticket_no,
            'month': month,
            'total_days': total_days,  # Use correct field name for the model
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'attendance_percentage': attendance_percentage
        }
        
        processed_data.append(attendance_record)
    
    return {
        'success': True,
        'message': f"Processed {len(processed_data)} records successfully",
        'data': processed_data,
        'errors': errors
    }

def save_attendance_to_db(attendance_data):
    """
    Save validated attendance data to the database
    """
    try:
        from app.models.models import Attendance  # Import here to avoid circular import
        for attendance_data_item in attendance_data:
            # Prepare data with proper type conversions
            processed_data = {}
            for key, value in attendance_data_item.items():
                if value is None or (isinstance(value, float) and (value != value)):  # Check for NaN (value != value is true for NaN)
                    processed_data[key] = None
                elif key in ['total_days', 'present_days', 'absent_days'] and value is not None:
                    # Convert to integer for integer fields
                    try:
                        processed_data[key] = int(float(value)) if str(value).replace('.', '').replace('-', '').isdigit() else None
                    except:
                        processed_data[key] = None
                elif key in ['attendance_percentage'] and value is not None:
                    # Convert to float for float fields
                    try:
                        processed_data[key] = float(value) if str(value).replace('.', '').replace('-', '').replace('%', '').isdigit() else None
                    except:
                        processed_data[key] = None
                else:
                    # For string fields, convert to string and handle properly
                    processed_data[key] = str(value) if value is not None else None
            
            # Check if attendance record with same ticket_no and month already exists
            existing_attendance = Attendance.query.filter_by(
                ticket_no=processed_data['ticket_no'], 
                month=processed_data['month']
            ).first()
            if existing_attendance:
                # Update existing attendance instead of creating duplicate
                for key, value in processed_data.items():
                    if hasattr(existing_attendance, key):
                        setattr(existing_attendance, key, value)
            else:
                # Create new Attendance object
                attendance = Attendance(**processed_data)
                db.session.add(attendance)
        
        db.session.commit()
        return True, f"Successfully saved {len(attendance_data)} attendance records to database"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"

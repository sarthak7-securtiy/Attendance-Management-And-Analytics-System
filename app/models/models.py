from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

class User(db.Model):
    """
    User model for authentication
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # admin or officer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


class Student(db.Model):
    """
    Student model based on the SRS requirements
    """
    __tablename__ = 'students'
    
    # Primary key and required fields
    ticket_no = db.Column(db.String(50), primary_key=True, nullable=False)  # Unique ticket number
    pno = db.Column(db.String(50), nullable=False)  # Personal Number
    name = db.Column(db.String(100), nullable=False)  # Student Name
    
    # Additional fields as per SRS
    medical_policy = db.Column(db.String(100))
    father_name = db.Column(db.String(100))
    dob = db.Column(db.Date)  # Date of Birth
    gender = db.Column(db.String(10))
    mobile = db.Column(db.String(15))
    address = db.Column(db.Text)
    qualification_trade = db.Column(db.String(100))
    passing_year = db.Column(db.Integer)
    college_name = db.Column(db.String(100))
    ssc_percentage = db.Column(db.Float)
    hsc_percentage = db.Column(db.Float)
    aadhaar_no = db.Column(db.String(12))  # Will be encrypted
    pan_no = db.Column(db.String(10))  # Will be encrypted
    email_id = db.Column(db.String(100))
    blood_group = db.Column(db.String(5))
    current_address_route = db.Column(db.String(200))
    batch = db.Column(db.String(50))  # Batch/Class information
    
    # Relationship with attendance records
    attendances = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.name} - Ticket: {self.ticket_no}>'


class Attendance(db.Model):
    """
    Attendance model based on the SRS requirements
    """
    __tablename__ = 'attendance'
    
    attendance_id = db.Column(db.Integer, primary_key=True)
    ticket_no = db.Column(db.String(50), db.ForeignKey('students.ticket_no'), nullable=False)
    
    # Attendance fields as per SRS
    month = db.Column(db.String(20), nullable=False)  # Month name (e.g., January, February)
    total_days = db.Column(db.Integer, nullable=False)  # Total Working Days
    present_days = db.Column(db.Integer, nullable=False)  # Present Days
    absent_days = db.Column(db.Integer, nullable=False)  # Absent Days
    attendance_percentage = db.Column(db.Float, nullable=False)  # Attendance Percentage
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance {self.ticket_no} - {self.month}>'
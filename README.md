# Integrated Student Governance & Attendance Analytics System

A comprehensive web application for managing student records and attendance data using Excel uploads and Ticket Number-based search.

## Features

- **Excel Upload**: Upload Student Master and Attendance data from Excel files
- **Student Management**: Store and manage student information
- **Attendance Tracking**: Track attendance by month with percentage calculations
- **Search Functionality**: Search students by unique Ticket Number
- **Analysis Dashboard**: View overall attendance analytics and defaulter lists
- **Role-based Access**: Admin and Officer user roles
- **Responsive UI**: Clean, modern interface built with Bootstrap

## System Requirements

- Python 3.8+
- pip package manager

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

4. Access the application at `http://localhost:5000`

## Default Credentials

- Username: `admin`
- Password: `admin123`

## Excel File Formats

### Student Master File
Required columns:
- PNO
- Medical Policy
- Ticket No
- Name
- Father Name
- DOB
- Gender
- Mobile Number
- Address
- Qualification Trade
- Passing Year
- College Name
- SSC Percentage
- HSC Percentage
- Aadhaar Number
- PAN Number
- Email ID
- Blood Group
- Current Address (Bus Stop / Route)

### Attendance File
Required columns:
- Ticket No
- Student Name
- Month
- Total Working Days
- Present Days
- Absent Days
- Attendance Percentage

## Architecture

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite (default) or MySQL/PostgreSQL
- **Frontend**: Jinja2 templates with Bootstrap 5
- **File Processing**: Pandas for Excel handling

## Security Features

- Password hashing using SHA-256
- Session-based authentication
- Role-based access control
- Input validation and sanitization
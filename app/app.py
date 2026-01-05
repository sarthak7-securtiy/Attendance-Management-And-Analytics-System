from flask import Flask, render_template
from app.config import Config
from app.models.models import db, User
from app.controllers.auth_controller import auth_bp, init_admin_user
from app.controllers.student_controller import student_bp
from app.controllers.attendance_controller import attendance_bp
from app.controllers.search_controller import search_bp
from app.controllers.analysis_controller import analysis_bp
from app.controllers.dashboard_controller import dashboard_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Create upload folder if it doesn't exist
    upload_path = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(dashboard_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        init_admin_user()  # Initialize default admin user
    
    # Set upload folder attribute on app instance for controllers to access
    app.upload_folder = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app

# Create the Flask app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True, default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    datasets = db.relationship('Dataset', backref='owner', cascade='all, delete-orphan', lazy=True)
    reports = db.relationship('Report', backref='owner', cascade='all, delete-orphan', lazy=True)
    activities = db.relationship('ActivityLog', backref='user', cascade='all, delete-orphan', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Dataset(db.Model):
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_name = db.Column(db.String(200), nullable=False)
    row_count = db.Column(db.Integer, default=0)
    col_count = db.Column(db.Integer, default=0)
    file_size = db.Column(db.Integer, default=0) # in bytes
    columns_metadata = db.Column(db.Text, nullable=True) # JSON representation of column info
    is_cleaned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reports = db.relationship('Report', backref='dataset', cascade='all, delete-orphan', lazy=True)
    
    def get_columns_info(self):
        if self.columns_metadata:
            try:
                return json.loads(self.columns_metadata)
            except Exception:
                return []
        return []
        
    def set_columns_info(self, columns_info_list):
        self.columns_metadata = json.dumps(columns_info_list)

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(10), nullable=False) # 'pdf', 'excel', 'pptx'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'insightx_secret_key_12345'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'insightx.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    EXPORTS_FOLDER = os.path.join(BASE_DIR, 'exports')
    DATASET_FOLDER = os.path.join(BASE_DIR, 'dataset')
    
    # Max file size: 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Ensure folders exist
for folder in [Config.UPLOAD_FOLDER, Config.REPORTS_FOLDER, Config.EXPORTS_FOLDER, Config.DATASET_FOLDER]:
    os.makedirs(folder, exist_ok=True)

import os
import uuid
import logging
import pandas as pd
from werkzeug.utils import secure_filename
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InsightX")

def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def format_size(size_bytes):
    """Convert bytes to human-readable size string."""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

def get_safe_filename(filename):
    """Generate a unique secure filename."""
    base_name = secure_filename(filename)
    if not base_name:
        base_name = "dataset"
    name, ext = os.path.splitext(base_name)
    unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
    return unique_name

def load_dataset(filepath):
    """Load a dataset into a pandas DataFrame based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.csv':
            # Handle encoding issues (utf-8, latin1, cp1252)
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    return pd.read_csv(filepath, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            return pd.read_csv(filepath) # fallback
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Error loading dataset {filepath}: {str(e)}")
        raise e

def save_dataset(df, filepath):
    """Save a DataFrame to disk based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.csv':
            df.to_csv(filepath, index=False)
        elif ext in ['.xlsx', '.xls']:
            df.to_excel(filepath, index=False)
        else:
            raise ValueError(f"Unsupported file type for save: {ext}")
    except Exception as e:
        logger.error(f"Error saving dataset to {filepath}: {str(e)}")
        raise e

import pandas as pd
import numpy as np

def detect_issues(df):
    """
    Detect dataset issues: missing values, duplicates, outliers, incorrect data types, infinite values.
    Returns a dictionary of findings.
    """
    issues = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'duplicate_rows': int(df.duplicated().sum()),
        'missing_values_by_col': {},
        'infinite_values_by_col': {},
        'blank_strings_by_col': {},
        'outliers_by_col': {},
        'col_types': {}
    }
    
    for col in df.columns:
        issues['col_types'][col] = str(df[col].dtype)
        
        # Missing values
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            issues['missing_values_by_col'][col] = missing_count
            
        # Infinite values (only for numeric columns)
        if pd.api.types.is_numeric_dtype(df[col]):
            inf_count = int(np.isinf(df[col]).sum())
            if inf_count > 0:
                issues['infinite_values_by_col'][col] = inf_count
                
            # Outliers using IQR
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outlier_count = int(((df[col] < lower_bound) | (df[col] > upper_bound)).sum())
            if outlier_count > 0:
                issues['outliers_by_col'][col] = outlier_count
        else:
            # Blank strings (whitespace-only or empty strings)
            blank_count = int((df[col].astype(str).str.strip() == '').sum() - df[col].isna().sum())
            if blank_count > 0:
                issues['blank_strings_by_col'][col] = blank_count
                
    return issues

def fill_missing_value(df, column, strategy, fill_value=None):
    """
    Fills missing values in a specified column using a strategy:
    'mean', 'median', 'mode', 'constant', 'ffill', 'bfill'
    """
    df_clean = df.copy()
    if column not in df_clean.columns:
        return df_clean
        
    if strategy == 'mean':
        if pd.api.types.is_numeric_dtype(df_clean[column]):
            val = df_clean[column].mean()
            df_clean[column] = df_clean[column].fillna(val)
    elif strategy == 'median':
        if pd.api.types.is_numeric_dtype(df_clean[column]):
            val = df_clean[column].median()
            df_clean[column] = df_clean[column].fillna(val)
    elif strategy == 'mode':
        val = df_clean[column].mode()
        if not val.empty:
            df_clean[column] = df_clean[column].fillna(val[0])
    elif strategy == 'constant':
        if fill_value is not None:
            # Convert fill value to match dtype
            try:
                if pd.api.types.is_numeric_dtype(df_clean[column]):
                    fill_value = float(fill_value) if '.' in str(fill_value) else int(fill_value)
            except ValueError:
                pass
            df_clean[column] = df_clean[column].fillna(fill_value)
    elif strategy == 'ffill':
        df_clean[column] = df_clean[column].ffill()
    elif strategy == 'bfill':
        df_clean[column] = df_clean[column].bfill()
        
    return df_clean

def drop_missing_values(df, column=None):
    """Drops rows with missing values in a specific column or globally if column is None."""
    df_clean = df.copy()
    if column:
        if column in df_clean.columns:
            df_clean = df_clean.dropna(subset=[column])
    else:
        df_clean = df_clean.dropna()
    return df_clean

def remove_duplicate_rows(df):
    """Removes duplicate rows from the dataset."""
    return df.drop_duplicates().copy()

def convert_column_type(df, column, target_type):
    """
    Converts a column to a target data type:
    'int', 'float', 'str', 'category', 'datetime', 'bool'
    """
    df_clean = df.copy()
    if column not in df_clean.columns:
        return df_clean
        
    try:
        if target_type == 'int':
            df_clean[column] = pd.to_numeric(df_clean[column], errors='coerce').fillna(0).astype(int)
        elif target_type == 'float':
            df_clean[column] = pd.to_numeric(df_clean[column], errors='coerce').astype(float)
        elif target_type == 'str':
            df_clean[column] = df_clean[column].astype(str)
        elif target_type == 'category':
            df_clean[column] = df_clean[column].astype('category')
        elif target_type == 'datetime':
            df_clean[column] = pd.to_datetime(df_clean[column], errors='coerce')
        elif target_type == 'bool':
            # Map strings to boolean values properly
            if df_clean[column].dtype == 'object':
                mapping = {'true': True, 'false': False, 'yes': True, 'no': False, '1': True, '0': False, 't': True, 'f': False}
                df_clean[column] = df_clean[column].astype(str).str.lower().map(mapping).fillna(False)
            else:
                df_clean[column] = df_clean[column].astype(bool)
    except Exception as e:
        # Log exception and return original
        pass
        
    return df_clean

def handle_column_outliers(df, column, strategy='clip'):
    """
    Handles outliers in a column using IQR.
    Strategy: 'clip' (cap at boundaries) or 'drop' (remove rows).
    """
    df_clean = df.copy()
    if column not in df_clean.columns or not pd.api.types.is_numeric_dtype(df_clean[column]):
        return df_clean
        
    q1 = df_clean[column].quantile(0.25)
    q3 = df_clean[column].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    if strategy == 'clip':
        df_clean[column] = np.clip(df_clean[column], lower_bound, upper_bound)
    elif strategy == 'drop':
        df_clean = df_clean[(df_clean[column] >= lower_bound) & (df_clean[column] <= upper_bound)]
        
    return df_clean

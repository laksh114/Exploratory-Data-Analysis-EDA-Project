import pandas as pd
import numpy as np
from scipy import stats

def get_column_types(df):
    """
    Categorize columns into numeric, categorical, boolean, and datetime.
    """
    col_types = {
        'numeric': [],
        'categorical': [],
        'boolean': [],
        'datetime': []
    }
    
    for col in df.columns:
        dtype = df[col].dtype
        # Check datetime first
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            col_types['datetime'].append(col)
        # Check boolean
        elif pd.api.types.is_bool_dtype(df[col]) or (set(df[col].dropna().unique()) <= {0, 1, 0.0, 1.0, True, False} and len(df[col].dropna().unique()) <= 2 and pd.api.types.is_numeric_dtype(df[col])):
            col_types['boolean'].append(col)
        # Check numeric
        elif pd.api.types.is_numeric_dtype(df[col]):
            col_types['numeric'].append(col)
        # Fallback to categorical/object
        else:
            col_types['categorical'].append(col)
            
    return col_types

def calculate_summary_stats(df):
    """
    Generate complete summary statistics for numeric and categorical features.
    """
    types = get_column_types(df)
    stats_dict = {}
    
    # 1. Numeric Columns
    for col in types['numeric']:
        series = df[col].dropna()
        if series.empty:
            stats_dict[col] = {
                'type': 'numeric', 'count': 0, 'null_count': len(df), 'null_percentage': 100.0
            }
            continue
            
        q1 = float(series.quantile(0.25))
        q2 = float(series.quantile(0.50)) # median
        q3 = float(series.quantile(0.75))
        
        # Calculate skewness and kurtosis
        skewVal = float(series.skew()) if len(series) > 2 else 0.0
        kurtVal = float(series.kurt()) if len(series) > 3 else 0.0
        
        # Calculate mode
        mode_series = series.mode()
        mode_val = float(mode_series[0]) if not mode_series.empty else None
        
        stats_dict[col] = {
            'type': 'numeric',
            'count': int(series.count()),
            'null_count': int(df[col].isna().sum()),
            'null_percentage': float((df[col].isna().sum() / len(df)) * 100),
            'unique_count': int(df[col].nunique()),
            'mean': float(series.mean()),
            'median': float(q2),
            'mode': mode_val,
            'min': float(series.min()),
            'max': float(series.max()),
            'std': float(series.std()) if len(series) > 1 else 0.0,
            'variance': float(series.var()) if len(series) > 1 else 0.0,
            'range': float(series.max() - series.min()),
            'q1': q1,
            'q3': q3,
            'iqr': q3 - q1,
            'skewness': skewVal,
            'kurtosis': kurtVal
        }
        
    # 2. Categorical Columns
    for col in types['categorical']:
        series = df[col].dropna()
        null_count = int(df[col].isna().sum())
        null_percentage = float((null_count / len(df)) * 100)
        
        if series.empty:
            stats_dict[col] = {
                'type': 'categorical', 'count': 0, 'null_count': null_count, 'null_percentage': null_percentage
            }
            continue
            
        value_counts = series.value_counts()
        top_val = value_counts.index[0] if not value_counts.empty else None
        top_freq = int(value_counts.iloc[0]) if not value_counts.empty else 0
        
        # Limit the frequency distribution size to top 10
        freq_dist = {str(k): int(v) for k, v in value_counts.head(10).items()}
        
        stats_dict[col] = {
            'type': 'categorical',
            'count': int(series.count()),
            'null_count': null_count,
            'null_percentage': null_percentage,
            'unique_count': int(series.nunique()),
            'top_value': str(top_val),
            'top_frequency': top_freq,
            'frequency_distribution': freq_dist
        }
        
    # 3. Boolean Columns
    for col in types['boolean']:
        series = df[col].dropna()
        stats_dict[col] = {
            'type': 'boolean',
            'count': int(series.count()),
            'null_count': int(df[col].isna().sum()),
            'null_percentage': float((df[col].isna().sum() / len(df)) * 100),
            'unique_count': int(df[col].nunique()),
            'true_count': int((series == True).sum() + (series == 1).sum()),
            'false_count': int((series == False).sum() + (series == 0).sum())
        }
        
    return stats_dict

def calculate_correlations(df):
    """
    Calculate Pearson, Spearman, and Kendall correlation matrices for numeric features.
    Returns correlation dictionaries.
    """
    types = get_column_types(df)
    numeric_cols = types['numeric']
    
    if len(numeric_cols) < 2:
        return {
            'pearson': {},
            'spearman': {},
            'kendall': {},
            'top_positive': [],
            'top_negative': []
        }
        
    # Select only numeric data
    df_num = df[numeric_cols].dropna()
    
    if len(df_num) < 3:
        # Fallback to general dataframe, correlation needs rows
        df_num = df[numeric_cols]
        
    corr_p = df_num.corr(method='pearson').fillna(0).to_dict()
    corr_s = df_num.corr(method='spearman').fillna(0).to_dict()
    corr_k = df_num.corr(method='kendall').fillna(0).to_dict()
    
    # Find top correlation pairs
    pos_corrs = []
    neg_corrs = []
    
    cols = list(corr_p.keys())
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            c1, c2 = cols[i], cols[j]
            val = corr_p[c1][c2]
            if abs(val) >= 0.3:
                item = {'feature1': c1, 'feature2': c2, 'correlation': float(val)}
                if val > 0:
                    pos_corrs.append(item)
                else:
                    neg_corrs.append(item)
                    
    # Sort
    pos_corrs = sorted(pos_corrs, key=lambda x: x['correlation'], reverse=True)[:10]
    neg_corrs = sorted(neg_corrs, key=lambda x: x['correlation'])[:10]
    
    return {
        'pearson': corr_p,
        'spearman': corr_s,
        'kendall': corr_k,
        'top_positive': pos_corrs,
        'top_negative': neg_corrs
    }

def get_influential_features(df, target_col=None):
    """
    Identify highly influential features and weak features based on correlation or variance.
    """
    stats_summary = calculate_summary_stats(df)
    correlations = calculate_correlations(df)
    
    influential = []
    weak = []
    
    if target_col and target_col in df.columns:
        # If target column is specified, rank numeric features by absolute correlation to target
        if target_col in correlations['pearson']:
            target_corrs = correlations['pearson'][target_col]
            for col, val in target_corrs.items():
                if col == target_col:
                    continue
                abs_val = abs(val)
                item = {'feature': col, 'correlation': float(val), 'strength': abs_val}
                if abs_val >= 0.4:
                    influential.append(item)
                elif abs_val < 0.15:
                    weak.append(item)
            influential = sorted(influential, key=lambda x: x['strength'], reverse=True)
            weak = sorted(weak, key=lambda x: x['strength'])
    else:
        # No target column: look at feature variance (low variance is weak) and average correlation
        for col, meta in stats_summary.items():
            if meta['type'] == 'numeric':
                # Std close to zero or coefficient of variation is very small -> weak
                cv = (meta['std'] / abs(meta['mean'])) if meta['mean'] != 0 else 0
                if meta['std'] < 0.01 or (0 < cv < 0.05):
                    weak.append({'feature': col, 'reason': 'Very low variance / constant-like'})
                elif meta['unique_count'] == len(df):
                    weak.append({'feature': col, 'reason': 'High unique count ID-like feature'})
                    
        # Check correlations
        pears = correlations['pearson']
        for col, target_corrs in pears.items():
            avg_abs_corr = np.mean([abs(v) for k, v in target_corrs.items() if k != col])
            if avg_abs_corr > 0.4:
                influential.append({'feature': col, 'avg_correlation': float(avg_abs_corr)})
                
    return {
        'influential': influential,
        'weak': weak
    }

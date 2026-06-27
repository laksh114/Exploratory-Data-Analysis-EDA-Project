import pandas as pd
import numpy as np
import re
from utils.statistics import get_column_types, calculate_summary_stats, calculate_correlations

def generate_insights(df):
    """
    Generate automatic human-readable insights for a given dataframe.
    """
    insights_list = []
    
    col_types = get_column_types(df)
    stats_summary = calculate_summary_stats(df)
    correlations = calculate_correlations(df)
    
    # 1. Shape and Size
    insights_list.append({
        'category': 'Overview',
        'importance': 'high',
        'text': f"The dataset contains <b>{len(df):,}</b> records (rows) and <b>{len(df.columns)}</b> features (columns)."
    })
    
    insights_list.append({
        'category': 'Overview',
        'importance': 'medium',
        'text': f"Feature composition: <b>{len(col_types['numeric'])}</b> numeric, <b>{len(col_types['categorical'])}</b> categorical, <b>{len(col_types['boolean'])}</b> boolean, and <b>{len(col_types['datetime'])}</b> date features."
    })
    
    # 2. Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        insights_list.append({
            'category': 'Data Quality',
            'importance': 'high',
            'text': f"Found <b>{dup_count:,} duplicate records</b> ({(dup_count/len(df))*100:.2f}% of dataset). It is highly recommended to remove duplicates to avoid bias."
        })
    else:
        insights_list.append({
            'category': 'Data Quality',
            'importance': 'low',
            'text': "Excellent! The dataset contains <b>no duplicate rows</b>."
        })
        
    # 3. Missing values
    missing_by_col = {col: stats_summary[col]['null_count'] for col in df.columns if stats_summary[col].get('null_count', 0) > 0}
    if missing_by_col:
        # Sort to get column with most missing
        sorted_missing = sorted(missing_by_col.items(), key=lambda x: x[1], reverse=True)
        top_missing_col, top_missing_val = sorted_missing[0]
        top_missing_pct = (top_missing_val / len(df)) * 100
        
        insights_list.append({
            'category': 'Data Quality',
            'importance': 'high',
            'text': f"Feature <b>{top_missing_col}</b> has the highest concentration of missing data, with <b>{top_missing_val:,} empty records</b> ({top_missing_pct:.2f}% null)."
        })
        
        total_missing = sum(missing_by_col.values())
        total_cells = len(df) * len(df.columns)
        insights_list.append({
            'category': 'Data Quality',
            'importance': 'medium',
            'text': f"Across the entire dataset, <b>{total_missing:,} cells are null</b> ({ (total_missing/total_cells)*100:.2f}% of all cells)."
        })
    else:
        insights_list.append({
            'category': 'Data Quality',
            'importance': 'low',
            'text': "Perfect! The dataset has <b>zero missing values</b>."
        })
        
    # 4. Outliers
    numeric_outliers = {}
    for col in col_types['numeric']:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        out_cnt = ((df[col] < lower) | (df[col] > upper)).sum()
        if out_cnt > 0:
            numeric_outliers[col] = out_cnt
            
    if numeric_outliers:
        sorted_outliers = sorted(numeric_outliers.items(), key=lambda x: x[1], reverse=True)
        top_out_col, top_out_cnt = sorted_outliers[0]
        insights_list.append({
            'category': 'Outliers',
            'importance': 'high',
            'text': f"Feature <b>{top_out_col}</b> contains <b>{top_out_cnt:,} outliers</b> based on the IQR method. These represent potential anomalies or heavy-tailed bounds."
        })
        
    # 5. Correlation Insights
    pos_corrs = correlations.get('top_positive', [])
    if pos_corrs:
        strongest_pos = pos_corrs[0]
        insights_list.append({
            'category': 'Correlations',
            'importance': 'high',
            'text': f"Strongest positive relationship is between <b>{strongest_pos['feature1']}</b> and <b>{strongest_pos['feature2']}</b> with a Pearson coefficient of <b>{strongest_pos['correlation']:.3f}</b>."
        })
        
    neg_corrs = correlations.get('top_negative', [])
    if neg_corrs:
        strongest_neg = neg_corrs[0]
        insights_list.append({
            'category': 'Correlations',
            'importance': 'high',
            'text': f"Strongest negative relationship is between <b>{strongest_neg['feature1']}</b> and <b>{strongest_neg['feature2']}</b> with a Pearson coefficient of <b>{strongest_neg['correlation']:.3f}</b>."
        })
        
    # 6. Categorical imbalance
    for col in col_types['categorical']:
        col_meta = stats_summary[col]
        if 'top_frequency' in col_meta and col_meta['count'] > 0:
            pct = (col_meta['top_frequency'] / col_meta['count']) * 100
            if pct > 80.0:
                insights_list.append({
                    'category': 'Distribution',
                    'importance': 'medium',
                    'text': f"Feature <b>{col}</b> is highly imbalanced: category <b>'{col_meta['top_value']}'</b> represents <b>{pct:.1f}%</b> of all populated records."
                })
            elif 40.0 <= pct <= 60.0 and col_meta['unique_count'] == 2:
                insights_list.append({
                    'category': 'Distribution',
                    'importance': 'low',
                    'text': f"Binary feature <b>{col}</b> is well-balanced: main class <b>'{col_meta['top_value']}'</b> represents <b>{pct:.1f}%</b> of observations."
                })
                
    # 7. Numeric skewness
    skewed_cols = []
    for col in col_types['numeric']:
        col_meta = stats_summary[col]
        skew = col_meta.get('skewness', 0.0)
        if abs(skew) > 1.5:
            skewed_cols.append((col, skew))
            
    if skewed_cols:
        sorted_skew = sorted(skewed_cols, key=lambda x: abs(x[1]), reverse=True)
        top_skew_col, top_skew_val = sorted_skew[0]
        skew_dir = "right (positively skewed)" if top_skew_val > 0 else "left (negatively skewed)"
        insights_list.append({
            'category': 'Distribution',
            'importance': 'medium',
            'text': f"Feature <b>{top_skew_col}</b> is highly skewed <b>{skew_dir}</b> with a skewness index of <b>{top_skew_val:.2f}</b>."
        })
        
    return insights_list

# ----------------- NLQ (Natural Language Query) Engine -----------------

def query_dataset(df, user_query):
    """
    Parse a natural language query from user and return a descriptive text answer and optional data preview.
    """
    user_query_clean = user_query.lower().strip()
    
    # 1. Get column lists
    col_types = get_column_types(df)
    columns_map = {col.lower(): col for col in df.columns}
    
    # helper to find which column name is mentioned in user query
    def find_mentioned_columns(query):
        found = []
        # sort by length descending to match longer names first
        for name_lower in sorted(columns_map.keys(), key=len, reverse=True):
            # check boundaries or exact match
            if re.search(r'\b' + re.escape(name_lower) + r'\b', query):
                found.append(columns_map[name_lower])
                # remove to avoid double matching shorter sub-strings
                query = query.replace(name_lower, "")
        return found
        
    mentioned_cols = find_mentioned_columns(user_query_clean)
    
    # Strategy 1: Average/Mean Query
    if any(keyword in user_query_clean for keyword in ['average', 'mean', 'avg']):
        if mentioned_cols:
            num_mentions = [c for c in mentioned_cols if c in col_types['numeric']]
            if num_mentions:
                col = num_mentions[0]
                mean_val = df[col].mean()
                return {
                    'query': user_query,
                    'answer': f"The average value of <b>{col}</b> is <b>{mean_val:,.4f}</b>.",
                    'success': True
                }
            else:
                return {
                    'query': user_query,
                    'answer': f"I found the column(s) {mentioned_cols} in your query, but they are not numeric, so I cannot calculate the average.",
                    'success': False
                }
        else:
            # Fallback: list all column averages
            if col_types['numeric']:
                means = df[col_types['numeric']].mean().to_dict()
                ans = "Here are the averages for all numeric features:<br><ul>"
                for k, v in means.items():
                    ans += f"<li><b>{k}</b>: {v:,.4f}</li>"
                ans += "</ul>"
                return {'query': user_query, 'answer': ans, 'success': True}
                
    # Strategy 2: Max/Highest/Largest
    if any(keyword in user_query_clean for keyword in ['maximum', 'max', 'highest', 'largest', 'peak', 'top value']):
        if mentioned_cols:
            col = mentioned_cols[0]
            max_val = df[col].max()
            # If it's numeric/datetime
            if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]):
                return {
                    'query': user_query,
                    'answer': f"The maximum value of <b>{col}</b> is <b>{max_val:,}</b>.",
                    'success': True
                }
            else:
                return {
                    'query': user_query,
                    'answer': f"The highest alphabetical value of categorical feature <b>{col}</b> is <b>'{max_val}'</b>.",
                    'success': True
                }
        else:
            # global highest numeric max values
            if col_types['numeric']:
                maxs = df[col_types['numeric']].max().to_dict()
                ans = "Here are the maximum values for all numeric features:<br><ul>"
                for k, v in maxs.items():
                    ans += f"<li><b>{k}</b>: {v:,}</li>"
                ans += "</ul>"
                return {'query': user_query, 'answer': ans, 'success': True}
                
    # Strategy 3: Min/Lowest/Smallest
    if any(keyword in user_query_clean for keyword in ['minimum', 'min', 'lowest', 'smallest']):
        if mentioned_cols:
            col = mentioned_cols[0]
            min_val = df[col].min()
            if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]):
                return {
                    'query': user_query,
                    'answer': f"The minimum value of <b>{col}</b> is <b>{min_val:,}</b>.",
                    'success': True
                }
            else:
                return {
                    'query': user_query,
                    'answer': f"The lowest alphabetical value of categorical feature <b>{col}</b> is <b>'{min_val}'</b>.",
                    'success': True
                }
                
    # Strategy 4: Correlation
    if any(keyword in user_query_clean for keyword in ['correlation', 'correlate', 'related', 'relationship']):
        if len(mentioned_cols) >= 2:
            c1, c2 = mentioned_cols[0], mentioned_cols[1]
            if c1 in col_types['numeric'] and c2 in col_types['numeric']:
                corr_val = df[[c1, c2]].corr().iloc[0, 1]
                strength = "no correlation"
                if abs(corr_val) > 0.7:
                    strength = "strong"
                elif abs(corr_val) > 0.4:
                    strength = "moderate"
                elif abs(corr_val) > 0.1:
                    strength = "weak"
                    
                dir_word = "positive" if corr_val > 0 else "negative"
                return {
                    'query': user_query,
                    'answer': f"The Pearson correlation coefficient between <b>{c1}</b> and <b>{c2}</b> is <b>{corr_val:.4f}</b>. This indicates a <b>{strength} {dir_word}</b> relationship.",
                    'success': True
                }
            else:
                return {
                    'query': user_query,
                    'answer': "Correlation analysis requires both columns to be numeric. Please specify two numeric columns.",
                    'success': False
                }
        elif len(mentioned_cols) == 1:
            # find top correlations for this column
            col = mentioned_cols[0]
            if col in col_types['numeric']:
                corrs = df[col_types['numeric']].corr()[col].sort_values(ascending=False)
                ans = f"Correlations of <b>{col}</b> with other numeric features:<br><ul>"
                for k, v in corrs.items():
                    if k != col:
                        ans += f"<li><b>{k}</b>: {v:.4f}</li>"
                ans += "</ul>"
                return {'query': user_query, 'answer': ans, 'success': True}
                
    # Strategy 5: Missing / Nulls
    if any(keyword in user_query_clean for keyword in ['missing', 'null', 'nan', 'empty', 'blank']):
        if mentioned_cols:
            col = mentioned_cols[0]
            null_count = int(df[col].isna().sum())
            null_pct = (null_count / len(df)) * 100
            return {
                'query': user_query,
                'answer': f"Column <b>{col}</b> has <b>{null_count:,} missing values</b> ({null_pct:.2f}% of rows).",
                'success': True
            }
        else:
            # show summary of missing values
            null_sums = df.isna().sum()
            null_cols = null_sums[null_sums > 0]
            if null_cols.empty:
                return {'query': user_query, 'answer': "Excellent news! There are <b>no missing values</b> in the entire dataset.", 'success': True}
            ans = "Here are the missing value counts by feature:<br><ul>"
            for k, v in null_cols.items():
                ans += f"<li><b>{k}</b>: {v:,} missing ({ (v/len(df))*100:.2f}%)</li>"
            ans += "</ul>"
            return {'query': user_query, 'answer': ans, 'success': True}
            
    # Strategy 6: Row counts, Column counts, Basic info
    if any(keyword in user_query_clean for keyword in ['count', 'rows', 'columns', 'shape', 'size', 'records']):
        return {
            'query': user_query,
            'answer': f"The dataset has <b>{len(df):,} rows</b> and <b>{len(df.columns)} columns</b>.",
            'success': True
        }
        
    # Strategy 7: Unique values / categories
    if any(keyword in user_query_clean for keyword in ['unique', 'categories', 'classes', 'value counts', 'frequency']):
        if mentioned_cols:
            col = mentioned_cols[0]
            uniq_cnt = df[col].nunique()
            vc = df[col].value_counts().head(5)
            ans = f"Column <b>{col}</b> has <b>{uniq_cnt:,} unique values</b>.<br>"
            if uniq_cnt > 0:
                ans += "Top 5 most frequent values:<br><ul>"
                for k, v in vc.items():
                    ans += f"<li><b>'{k}'</b>: {v:,} times ({(v/len(df))*100:.2f}%)</li>"
                ans += "</ul>"
            return {'query': user_query, 'answer': ans, 'success': True}
            
    # Strategy 8: Row filtering (e.g. "where age > 50" or "filter salary > 100000")
    # regex matches: "filter <col> > <val>" or "<col> <operator> <val>"
    # Let's detect standard comparison pattern: [col_name] [operator] [value]
    # Operators: >, <, >=, <=, ==, =
    for col_raw in df.columns:
        col_esc = re.escape(col_raw.lower())
        match = re.search(col_esc + r'\s*(>=|<=|>|<|==|=)\s*([0-9\.]+)', user_query_clean)
        if match:
            op = match.group(1)
            val = float(match.group(2))
            col = col_raw
            
            # Translate operators
            if op == '=':
                op = '=='
                
            try:
                # Apply filter safely
                if op == '>':
                    filtered_df = df[df[col] > val]
                elif op == '<':
                    filtered_df = df[df[col] < val]
                elif op == '>=':
                    filtered_df = df[df[col] >= val]
                elif op == '<=':
                    filtered_df = df[df[col] <= val]
                elif op == '==':
                    filtered_df = df[df[col] == val]
                    
                count = len(filtered_df)
                preview = filtered_df.head(10).to_html(classes="table table-sm table-striped table-hover", index=False)
                return {
                    'query': user_query,
                    'answer': f"Found <b>{count:,} rows</b> where <b>{col} {op} {val}</b>. Here is a preview of the first 10 matching rows:",
                    'success': True,
                    'html_table': preview
                }
            except Exception as e:
                return {
                    'query': user_query,
                    'answer': f"Failed to filter dataset on expression '{col} {op} {val}': {str(e)}",
                    'success': False
                }
                
    # Strategy 9: Categorical filters (e.g. "where class is titanic" or "where gender = female")
    for col_raw in df.columns:
        col_esc = re.escape(col_raw.lower())
        # matches: "gender is male", "gender = male", "gender equals male"
        match = re.search(col_esc + r'\s*(is|=|equals)\s*[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?', user_query_clean)
        if match:
            val = match.group(2).strip()
            col = col_raw
            try:
                # Case insensitive match if string dtype
                if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    filtered_df = df[df[col].astype(str).str.lower() == val.lower()]
                else:
                    # convert value type to column dtype
                    casted_val = pd.Series([val]).astype(df[col].dtype).iloc[0]
                    filtered_df = df[df[col] == casted_val]
                    
                count = len(filtered_df)
                preview = filtered_df.head(10).to_html(classes="table table-sm table-striped table-hover", index=False)
                return {
                    'query': user_query,
                    'answer': f"Found <b>{count:,} rows</b> where <b>{col} is '{val}'</b>. Here is a preview of the first 10 matching rows:",
                    'success': True,
                    'html_table': preview
                }
            except Exception as e:
                pass
                
    # Fallback response
    return {
        'query': user_query,
        'answer': "I couldn't fully interpret that question. Try asking queries like:<br>"
                  "• <i>'What is the average of [column_name]?'</i><br>"
                  "• <i>'Find the highest value of [column_name]'</i><br>"
                  "• <i>'How many missing values in [column_name]?'</i><br>"
                  "• <i>'What is the correlation between [col1] and [col2]?'</i><br>"
                  "• <i>'Filter rows where [numeric_column] > [value]'</i>",
        'success': False
    }

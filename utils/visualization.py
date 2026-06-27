import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import io
import base64

# Configure seaborn style
sns.set_theme(style="whitegrid")

def df_plotly_to_json(fig):
    """Serialize plotly figure to json string."""
    return pio.to_json(fig)

def get_distribution_plot(df, column, theme='dark'):
    """Generates a Plotly distribution plot (histogram + box plot summary)."""
    fig = px.histogram(
        df, x=column, marginal="box", 
        title=f"Distribution of {column}",
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        color_discrete_sequence=['#6366F1'] # sleek violet
    )
    fig.update_layout(
        bargap=0.05,
        font=dict(family="Inter, sans-serif"),
        title_font=dict(size=18, color='#6366F1' if theme == 'light' else '#A5B4FC')
    )
    return df_plotly_to_json(fig)

def get_count_plot(df, column, theme='dark'):
    """Generates a Plotly bar chart for categorical counts."""
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'Count']
    
    # Limit to top 20 classes
    if len(counts) > 20:
        counts = counts.head(20)
        title = f"Top 20 Categories in {column}"
    else:
        title = f"Category Counts in {column}"
        
    fig = px.bar(
        counts, x=column, y='Count',
        title=title,
        text='Count',
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        color_discrete_sequence=['#3B82F6'] # sleek blue
    )
    fig.update_traces(textposition='auto')
    fig.update_layout(
        font=dict(family="Inter, sans-serif"),
        title_font=dict(size=18, color='#3B82F6' if theme == 'light' else '#93C5FD')
    )
    return df_plotly_to_json(fig)

def get_pie_chart(df, column, theme='dark'):
    """Generates a Plotly pie chart."""
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'Count']
    if len(counts) > 10:
        other_sum = counts.iloc[10:]['Count'].sum()
        counts = counts.head(10)
        # append 'Other' row
        counts = pd.concat([counts, pd.DataFrame([{column: 'Other', 'Count': other_sum}])], ignore_index=True)
        
    fig = px.pie(
        counts, values='Count', names=column,
        title=f"Proportions of {column}",
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(
        font=dict(family="Inter, sans-serif")
    )
    return df_plotly_to_json(fig)

def get_scatter_plot(df, x_col, y_col, color_col=None, theme='dark'):
    """Generates an interactive scatter plot."""
    kwargs = {
        'x': x_col, 'y': y_col,
        'title': f"Relationship between {x_col} and {y_col}",
        'template': "plotly_dark" if theme == 'dark' else "plotly_white",
    }
    if color_col and color_col in df.columns:
        kwargs['color'] = color_col
        
    fig = px.scatter(df, **kwargs)
    fig.update_layout(font=dict(family="Inter, sans-serif"))
    return df_plotly_to_json(fig)

def get_box_plot(df, cat_col, num_col, theme='dark'):
    """Generates an interactive Box plot."""
    fig = px.box(
        df, x=cat_col, y=num_col,
        title=f"{num_col} Grouped by {cat_col}",
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        color=cat_col
    )
    fig.update_layout(font=dict(family="Inter, sans-serif"))
    return df_plotly_to_json(fig)

def get_violin_plot(df, cat_col, num_col, theme='dark'):
    """Generates an interactive Violin plot."""
    fig = px.violin(
        df, x=cat_col, y=num_col, box=True, points="all",
        title=f"{num_col} Distribution across {cat_col}",
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        color=cat_col
    )
    fig.update_layout(font=dict(family="Inter, sans-serif"))
    return df_plotly_to_json(fig)

def get_line_plot(df, x_col, y_col, theme='dark'):
    """Generates a line plot."""
    # Ensure sorted by x_col if x_col is a time series or numeric index
    df_sorted = df.sort_values(by=x_col)
    fig = px.line(
        df_sorted, x=x_col, y=y_col,
        title=f"Trend of {y_col} over {x_col}",
        template="plotly_dark" if theme == 'dark' else "plotly_white"
    )
    fig.update_layout(font=dict(family="Inter, sans-serif"))
    return df_plotly_to_json(fig)

def get_correlation_heatmap(df, corr_matrix, theme='dark'):
    """Generates a Plotly Heatmap for the correlation matrix."""
    cols = list(corr_matrix.keys())
    if not cols:
        return None
        
    z_data = []
    for c1 in cols:
        row = []
        for c2 in cols:
            row.append(corr_matrix[c1][c2])
        z_data.append(row)
        
    fig = px.imshow(
        z_data, x=cols, y=cols,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Correlation Heatmap Matrix",
        template="plotly_dark" if theme == 'dark' else "plotly_white"
    )
    fig.update_layout(
        font=dict(family="Inter, sans-serif"),
        xaxis_title="Features",
        yaxis_title="Features"
    )
    return df_plotly_to_json(fig)

def get_missing_values_heatmap(df, theme='dark'):
    """Generates a heatmap illustrating missing values location."""
    if df.empty:
        return None
        
    # sample if huge dataset to prevent browser crash
    if len(df) > 1000:
        df_sample = df.sample(n=1000, random_state=42).sort_index()
    else:
        df_sample = df
        
    # boolean matrix of nulls
    null_matrix = df_sample.isna().astype(int)
    
    fig = px.imshow(
        null_matrix.values.T,
        x=null_matrix.index,
        y=null_matrix.columns,
        color_continuous_scale=["#1E293B", "#EF4444"] if theme == 'dark' else ["#FFFFFF", "#EF4444"],
        title="Missing Values Matrix Map (Red indicates missing values)",
        template="plotly_dark" if theme == 'dark' else "plotly_white"
    )
    fig.update_layout(
        font=dict(family="Inter, sans-serif"),
        coloraxis_showscale=False,
        xaxis_title="Row Index",
        yaxis_title="Columns"
    )
    return df_plotly_to_json(fig)

# ----------------- STATIC FIGURES FOR REPORT GENERATION (Matplotlib/Seaborn) -----------------

def generate_static_plot(df, plot_type, params):
    """
    Generates a static matplotlib/seaborn figure and returns it as a bytes object (PNG).
    """
    plt.figure(figsize=(8, 5))
    sns.set_theme(style="white")
    
    try:
        if plot_type == 'distribution':
            col = params['column']
            sns.histplot(df[col].dropna(), kde=True, color="#4F46E5")
            plt.title(f"Distribution of {col}")
            plt.xlabel(col)
            
        elif plot_type == 'bar':
            col = params['column']
            counts = df[col].value_counts().head(10)
            sns.barplot(x=counts.index, y=counts.values, palette="Blues_r")
            plt.title(f"Top 10 Categories in {col}")
            plt.xticks(rotation=45, ha='right')
            plt.ylabel("Count")
            
        elif plot_type == 'scatter':
            x, y = params['x'], params['y']
            sns.scatterplot(data=df, x=x, y=y, color="#3B82F6")
            plt.title(f"{x} vs {y}")
            
        elif plot_type == 'box':
            cat, num = params['cat'], params['num']
            sns.boxplot(data=df, x=cat, y=num, palette="Set2")
            plt.xticks(rotation=45, ha='right')
            plt.title(f"{num} by {cat}")
            
        elif plot_type == 'heatmap':
            corr_mat = df.select_dtypes(include=[np.number]).corr().fillna(0)
            sns.heatmap(corr_mat, annot=True, cmap="RdBu_r", vmin=-1, vmax=1, fmt=".2f")
            plt.title("Correlation Heatmap Matrix")
            
        elif plot_type == 'missing_map':
            # binary indicators of missing values
            sns.heatmap(df.isna(), cbar=False, cmap="viridis")
            plt.title("Missing Values Matrix Map (Yellow indicates missing values)")
            
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        buf.seek(0)
        return buf.getvalue()
        
    except Exception as e:
        plt.close()
        # Create empty error image
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.text(0.5, 0.5, f"Could not generate plot:\n{str(e)}", 
                color='red', ha='center', va='center')
        ax.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        return buf.getvalue()

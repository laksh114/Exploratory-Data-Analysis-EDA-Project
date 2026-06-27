import os
import shutil
import logging
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Config & Database Models
from config import Config
from models.models import db, User, Dataset, Report, ActivityLog

# Local data utilities
from utils.helpers import allowed_file, format_size, get_safe_filename, load_dataset, save_dataset, logger
from utils.preprocessing import (
    detect_issues, fill_missing_value, drop_missing_values, 
    remove_duplicate_rows, convert_column_type, handle_column_outliers
)
from utils.statistics import get_column_types, calculate_summary_stats, calculate_correlations, get_influential_features
from utils.visualization import (
    get_distribution_plot, get_count_plot, get_pie_chart, 
    get_scatter_plot, get_box_plot, get_violin_plot, get_line_plot, 
    get_correlation_heatmap, get_missing_values_heatmap
)
from utils.insights import generate_insights, query_dataset
from utils.report_generator import generate_pdf_report, generate_excel_report, generate_pptx_report

# Initialize App
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database & Login Manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Setup directories database on initial startup
with app.app_context():
    db.create_all()
    # Create default user if not exists for quick testing
    if not User.query.filter_by(username='demo').first():
        demo_user = User(username='demo', email='demo@insightx.com')
        demo_user.set_password('demo1234')
        db.session.add(demo_user)
        db.session.commit()
        logger.info("Created default demo user: demo/demo1234")

# ----------------- HOME & STATIC ROUTES -----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Simple flash response for demonstration
        flash(f"Thank you, {name}! Your message has been sent successfully. We will get back to you soon.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ----------------- AUTHENTICATION ROUTES -----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check existing
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.", "error")
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash("Email address already registered.", "error")
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Match by username or email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('dashboard_home'))
        else:
            flash("Invalid credentials. Please verify username and password.", "error")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out of your workspace.", "success")
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        
        # Verify uniques
        exist_user = User.query.filter(User.username == username, User.id != current_user.id).first()
        if exist_user:
            flash("Username already taken.", "error")
            return redirect(url_for('profile_page'))
            
        current_user.username = username
        current_user.email = email
        
        if new_password:
            current_user.set_password(new_password)
            
        db.session.commit()
        flash("Profile settings updated successfully!", "success")
        return redirect(url_for('profile_page'))
        
    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', datasets=datasets)

# ----------------- UPLOAD & SAMPLE LOADING -----------------

@app.route('/upload')
@login_required
def upload_page():
    return render_template('upload.html')

@app.route('/upload/submit', methods=['POST'])
@login_required
def upload_dataset_route():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part in upload.'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected.'}), 400
        
    if file and allowed_file(file.filename):
        try:
            filename = get_safe_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file to disk
            file.save(filepath)
            
            # Calculate metadata using pandas
            df = load_dataset(filepath)
            
            # Detect row/col size
            rows = len(df)
            cols = len(df.columns)
            size_bytes = os.path.getsize(filepath)
            
            # Generate initial column types metadata
            col_types = get_column_types(df)
            summary_stats = calculate_summary_stats(df)
            
            columns_meta = []
            for col in df.columns:
                columns_meta.append({
                    'name': col,
                    'type': summary_stats[col].get('type', 'unknown'),
                    'null_count': summary_stats[col].get('null_count', 0),
                    'null_percentage': summary_stats[col].get('null_percentage', 0.0),
                    'unique_count': summary_stats[col].get('unique_count', 0)
                })
                
            # Create Database object
            dataset = Dataset(
                user_id=current_user.id,
                filename=filename,
                original_name=file.filename,
                row_count=rows,
                col_count=cols,
                file_size=size_bytes
            )
            dataset.set_columns_info(columns_meta)
            
            db.session.add(dataset)
            
            # Log Activity
            log = ActivityLog(user_id=current_user.id, action="Uploaded Dataset", details=f"File: {file.filename}")
            db.session.add(log)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'dataset_id': dataset.id,
                'filename': file.filename
            })
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return jsonify({'success': False, 'error': f"Failed to read dataset: {str(e)}"}), 500
            
    return jsonify({'success': False, 'error': 'Allowed file types are CSV, XLSX, XLS.'}), 400

@app.route('/upload/sample/<sample_name>', methods=['POST'])
@login_required
def load_sample_dataset(sample_name):
    # Check if file exists in dataset/ folder
    sample_path = os.path.join(app.config['DATASET_FOLDER'], sample_name)
    if not os.path.exists(sample_path):
        flash(f"Sample dataset '{sample_name}' not found.", "error")
        return redirect(url_for('upload_page'))
        
    try:
        # Generate unique filename in upload directory
        unique_name = get_safe_filename(sample_name)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        
        # Copy file
        shutil.copy(sample_path, upload_path)
        
        # Read properties
        df = load_dataset(upload_path)
        
        # Generate column profiles
        summary_stats = calculate_summary_stats(df)
        columns_meta = []
        for col in df.columns:
            columns_meta.append({
                'name': col,
                'type': summary_stats[col].get('type', 'unknown'),
                'null_count': summary_stats[col].get('null_count', 0),
                'null_percentage': summary_stats[col].get('null_percentage', 0.0),
                'unique_count': summary_stats[col].get('unique_count', 0)
            })
            
        # Create database entry
        dataset = Dataset(
            user_id=current_user.id,
            filename=unique_name,
            original_name=sample_name.replace(".csv", "").title() + " Dataset",
            row_count=len(df),
            col_count=len(df.columns),
            file_size=os.path.getsize(upload_path)
        )
        dataset.set_columns_info(columns_meta)
        
        db.session.add(dataset)
        
        # Log Activity
        log = ActivityLog(user_id=current_user.id, action="Imported Demo Dataset", details=f"Sample: {sample_name}")
        db.session.add(log)
        
        db.session.commit()
        
        flash(f"Successfully loaded '{dataset.original_name}'!", "success")
        return redirect(url_for('dashboard_detail', dataset_id=dataset.id))
        
    except Exception as e:
        logger.error(f"Sample clone error: {str(e)}")
        flash(f"Failed to clone demo dataset: {str(e)}", "error")
        return redirect(url_for('upload_page'))

# ----------------- COCKPIT / ANALYTICS DASHBOARD -----------------

@app.route('/dashboard')
@login_required
def dashboard_home():
    # Redirect to profile or get first dataset
    first_dataset = Dataset.query.filter_by(user_id=current_user.id).order_by(Dataset.created_at.desc()).first()
    if first_dataset:
        return redirect(url_for('dashboard_detail', dataset_id=first_dataset.id))
    else:
        flash("You haven't uploaded any datasets yet. Please choose one to get started.", "info")
        return redirect(url_for('upload_page'))

@app.route('/dashboard/dataset/<int:dataset_id>')
@login_required
def dashboard_detail(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Security: user ownership check
    if dataset.user_id != current_user.id:
        flash("Unauthorized access to workspace.", "error")
        return redirect(url_for('index'))
        
    # Read dataset dataframe
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    if not os.path.exists(filepath):
        # Database cleanup in case file was deleted on disk
        db.session.delete(dataset)
        db.session.commit()
        flash("The requested dataset file is missing from local storage.", "error")
        return redirect(url_for('upload_page'))
        
    try:
        df = load_dataset(filepath)
        
        # Create summary metrics
        metrics = {
            'missing_cells': int(df.isna().sum().sum()),
            'duplicate_rows': int(df.duplicated().sum())
        }
        
        # Generate Plotly Missing heatmap
        missing_map_json = get_missing_values_heatmap(df)
        
        return render_template(
            'dashboard.html',
            dataset=dataset,
            columns_info=dataset.get_columns_info(),
            summary_metrics=metrics,
            missing_map_json=missing_map_json
        )
    except Exception as e:
        logger.error(f"Dashboard load error: {str(e)}")
        flash(f"Error reading dataset values: {str(e)}", "error")
        return redirect(url_for('upload_page'))

# ----------------- DATA CLEANING MODULE -----------------

@app.route('/dashboard/dataset/<int:dataset_id>/clean')
@login_required
def cleaning_page(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        flash("Access Denied.", "error")
        return redirect(url_for('index'))
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        
        # Descriptive Statistics
        stats_summary = calculate_summary_stats(df)
        
        # Search & pagination of row preview
        search_query = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 15
        
        # Apply simple string filters
        df_filtered = df.copy()
        if search_query:
            # Combine all string filters
            mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_filtered = df_filtered[mask]
            
        total_rows = len(df_filtered)
        total_pages = max(1, (total_rows + per_page - 1) // per_page)
        
        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        df_slice = df_filtered.iloc[start_idx:end_idx]
        
        # Format table preview elements
        headers = list(df.columns)
        rows_list = df_slice.fillna("NaN").astype(str).values.tolist()
        
        # Track duplicate rows count for red warnings
        dataset.duplicated_rows_count = int(df.duplicated().sum())
        
        return render_template(
            'analysis.html',
            dataset=dataset,
            columns_info=dataset.get_columns_info(),
            stats_summary=stats_summary,
            df_headers=headers,
            df_rows=rows_list,
            page=page,
            total_pages=total_pages,
            search_query=search_query
        )
    except Exception as e:
        logger.error(f"Analysis page error: {str(e)}")
        flash("Error loading cleaning workspace.", "error")
        return redirect(url_for('dashboard_detail', dataset_id=dataset.id))

# Cleaning Actions API endpoints

@app.route('/clean/impute', methods=['POST'])
@login_required
def clean_impute():
    data = request.json
    dataset_id = data.get('dataset_id')
    column = data.get('column')
    strategy = data.get('strategy')
    fill_value = data.get('fill_value')
    
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        df_clean = fill_missing_value(df, column, strategy, fill_value)
        save_dataset(df_clean, filepath)
        
        # Recalculate columns meta
        recalculate_dataset_meta(dataset, df_clean)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clean/duplicates', methods=['POST'])
@login_required
def clean_duplicates():
    data = request.json
    dataset_id = data.get('dataset_id')
    
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        df_clean = remove_duplicate_rows(df)
        save_dataset(df_clean, filepath)
        
        recalculate_dataset_meta(dataset, df_clean)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clean/outliers', methods=['POST'])
@login_required
def clean_outliers():
    data = request.json
    dataset_id = data.get('dataset_id')
    column = data.get('column')
    strategy = data.get('strategy')
    
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        df_clean = handle_column_outliers(df, column, strategy)
        save_dataset(df_clean, filepath)
        
        recalculate_dataset_meta(dataset, df_clean)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clean/convert-type', methods=['POST'])
@login_required
def clean_convert_type():
    data = request.json
    dataset_id = data.get('dataset_id')
    column = data.get('column')
    target_type = data.get('target_type')
    
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        df_clean = convert_column_type(df, column, target_type)
        save_dataset(df_clean, filepath)
        
        recalculate_dataset_meta(dataset, df_clean)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def recalculate_dataset_meta(dataset, df):
    """Utility to run profiles on cleaned dataframe and write to database."""
    stats_summary = calculate_summary_stats(df)
    columns_meta = []
    for col in df.columns:
        columns_meta.append({
            'name': col,
            'type': stats_summary[col].get('type', 'unknown'),
            'null_count': stats_summary[col].get('null_count', 0),
            'null_percentage': stats_summary[col].get('null_percentage', 0.0),
            'unique_count': stats_summary[col].get('unique_count', 0)
        })
    dataset.set_columns_info(columns_meta)
    dataset.row_count = len(df)
    dataset.col_count = len(df.columns)
    dataset.is_cleaned = True
    
    # Save file size
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    dataset.file_size = os.path.getsize(filepath)
    
    db.session.commit()

# ----------------- VISUALIZATIONS & CUSTOM CHARTS -----------------

@app.route('/dashboard/dataset/<int:dataset_id>/charts')
@login_required
def charts_page(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        flash("Access Denied.", "error")
        return redirect(url_for('index'))
        
    col_info = dataset.get_columns_info()
    
    # ----------------- AUTOMATIC CHART RECOMMENDATIONS Heuristic -----------------
    recs = []
    
    # Locate columns by types
    num_cols = [c['name'] for c in col_info if c['type'] == 'numeric']
    cat_cols = [c['name'] for c in col_info if c['type'] == 'categorical' or c['type'] == 'boolean']
    
    if num_cols:
        # Univariate distribution of first numeric
        recs.append({
            'title': f"Distribution of {num_cols[0]}",
            'type': 'distribution', 'x': num_cols[0], 'icon': 'fas fa-chart-bar',
            'reason': 'Primary continuous column distribution profile'
        })
        
        if len(num_cols) >= 2:
            # Scatter plot of first two numeric columns
            recs.append({
                'title': f"{num_cols[0]} vs {num_cols[1]}",
                'type': 'scatter', 'x': num_cols[0], 'y': num_cols[1], 'icon': 'fas fa-chart-line',
                'reason': 'Identify linear relationships or cluster distributions'
            })
            
    if cat_cols:
        # Category proportions
        recs.append({
            'title': f"Proportions of {cat_cols[0]}",
            'type': 'pie', 'x': cat_cols[0], 'icon': 'fas fa-chart-pie',
            'reason': 'Proportional representations of discrete values'
        })
        
        if num_cols:
            # Grouped Box Plot comparison
            recs.append({
                'title': f"{num_cols[0]} by {cat_cols[0]}",
                'type': 'box', 'x': cat_cols[0], 'y': num_cols[0], 'icon': 'fas fa-box',
                'reason': 'Continuous values range across distinct groups'
            })
            
    # Always recommend correlation matrix heatmap
    if len(num_cols) >= 2:
        recs.append({
            'title': "Feature Correlation Heatmap",
            'type': 'heatmap', 'x': '', 'icon': 'fas fa-th',
            'reason': 'Full correlation index among numeric columns'
        })
        
    return render_template(
        'charts.html',
        dataset=dataset,
        columns_info=col_info,
        recommendations=recs
    )

@app.route('/charts/render', methods=['POST'])
@login_required
def charts_render_json():
    data = request.json
    dataset_id = data.get('dataset_id')
    chart_type = data.get('type')
    x = data.get('x')
    y = data.get('y')
    color = data.get('color')
    
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        
        plotly_json = ""
        
        if chart_type == 'distribution':
            plotly_json = get_distribution_plot(df, x)
        elif chart_type == 'bar':
            plotly_json = get_count_plot(df, x)
        elif chart_type == 'pie':
            plotly_json = get_pie_chart(df, x)
        elif chart_type == 'scatter':
            plotly_json = get_scatter_plot(df, x, y, color)
        elif chart_type == 'box':
            plotly_json = get_box_plot(df, x, y)
        elif chart_type == 'violin':
            plotly_json = get_violin_plot(df, x, y)
        elif chart_type == 'line':
            plotly_json = get_line_plot(df, x, y)
        elif chart_type == 'heatmap':
            correlations = calculate_correlations(df)
            plotly_json = get_correlation_heatmap(df, correlations['pearson'])
            
        return jsonify({
            'success': True,
            'plotly_json': plotly_json
        })
        
    except Exception as e:
        logger.error(f"Plotting error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------- INSIGHTS ENGINE & REPORTS -----------------

@app.route('/dashboard/dataset/<int:dataset_id>/report')
@login_required
def reports_page(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        flash("Access Denied.", "error")
        return redirect(url_for('index'))
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        
        # Run automatic business insights heuristic
        insights = generate_insights(df)
        
        return render_template(
            'report.html',
            dataset=dataset,
            insights=insights
        )
    except Exception as e:
        logger.error(f"Insights audit error: {str(e)}")
        flash("Failed to run insight auditors.", "error")
        return redirect(url_for('dashboard_detail', dataset_id=dataset.id))

@app.route('/export/dataset/<int:dataset_id>')
@login_required
def export_dataset(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        flash("Access Denied.", "error")
        return redirect(url_for('index'))
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    if os.path.exists(filepath):
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f"clean_{dataset.original_name.lower().replace(' ', '_')}.csv"
        )
    else:
        flash("Dataset file not found.", "error")
        return redirect(url_for('dashboard_detail', dataset_id=dataset.id))

@app.route('/export/report/<int:dataset_id>/<string:report_type>')
@login_required
def export_report(dataset_id, report_type):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        flash("Access Denied.", "error")
        return redirect(url_for('index'))
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        
        # Build components
        stats = calculate_summary_stats(df)
        insights = generate_insights(df)
        correlations = calculate_correlations(df)
        
        # Format filename
        slug = dataset.original_name.lower().replace(" ", "_")
        
        if report_type == 'pdf':
            report_name = f"report_{slug}.pdf"
            report_path = os.path.join(app.config['REPORTS_FOLDER'], report_name)
            generate_pdf_report(df, dataset.original_name, stats, insights, correlations, report_path)
            mimetype = "application/pdf"
            
        elif report_type == 'excel':
            report_name = f"datasheet_{slug}.xlsx"
            report_path = os.path.join(app.config['REPORTS_FOLDER'], report_name)
            generate_excel_report(df, stats, correlations, report_path)
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
        elif report_type == 'pptx':
            report_name = f"slides_{slug}.pptx"
            report_path = os.path.join(app.config['REPORTS_FOLDER'], report_name)
            generate_pptx_report(df, dataset.original_name, stats, insights, report_path)
            mimetype = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            
        else:
            flash("Invalid report format requested.", "error")
            return redirect(url_for('reports_page', dataset_id=dataset.id))
            
        # Log activity
        log = ActivityLog(user_id=current_user.id, action=f"Generated {report_type.upper()} Report", details=f"Dataset: {dataset.original_name}")
        db.session.add(log)
        db.session.commit()
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_name,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Report export error: {str(e)}")
        flash(f"Failed to generate {report_type.upper()} report file: {str(e)}", "error")
        return redirect(url_for('reports_page', dataset_id=dataset.id))

# ----------------- NATURAL LANGUAGE QUERY ENGINE API -----------------

@app.route('/nlq', methods=['POST'])
@login_required
def run_nlq_query():
    data = request.json
    dataset_id = data.get('dataset_id')
    query = data.get('query')
    
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        return jsonify({'success': False, 'answer': 'Unauthorized'}), 403
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
    try:
        df = load_dataset(filepath)
        
        # Execute query parser
        res_data = query_dataset(df, query)
        
        return jsonify(res_data)
    except Exception as e:
        logger.error(f"NLQ error: {str(e)}")
        return jsonify({'success': False, 'answer': f"Query error: {str(e)}"}), 500

# ----------------- CLEANUP / DELETION -----------------

@app.route('/delete-dataset/<int:dataset_id>', methods=['POST'])
@login_required
def delete_dataset_route(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        flash("Unauthorized deletion attempt.", "error")
        return redirect(url_for('index'))
        
    try:
        # Delete file from disk
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
        # Delete database record
        db.session.delete(dataset)
        
        log = ActivityLog(user_id=current_user.id, action="Deleted Dataset", details=f"Name: {dataset.original_name}")
        db.session.add(log)
        
        db.session.commit()
        flash(f"Dataset '{dataset.original_name}' deleted successfully.", "success")
    except Exception as e:
        logger.error(f"Delete dataset error: {str(e)}")
        flash(f"Failed to delete dataset: {str(e)}", "error")
        
    return redirect(url_for('profile_page'))

# ----------------- RUN SCRIPT -----------------

if __name__ == '__main__':
    app.run(debug=True)

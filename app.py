from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import os
import json
import time
import uuid
from werkzeug.utils import secure_filename
import undetected_chromedriver as uc

# Import your scraper functions
from ShopeeTool import (
    scrape_search, 
    scrape_shop, 
    scrape_reviews_from_csv, 
    analyze_reviews
)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'csv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global driver instance
driver = None
driver_lock = threading.Lock()

# Task storage for polling
tasks = {}
tasks_lock = threading.Lock()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_task(task_id):
    """Create a new task entry"""
    with tasks_lock:
        tasks[task_id] = {
            'status': 'running',
            'logs': [],
            'result': None,
            'error': None,
            'created_at': time.time()
        }

def add_task_log(task_id, message, log_type='info'):
    """Add a log entry to a task"""
    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]['logs'].append({
                'message': message,
                'type': log_type,
                'time': time.strftime('%H:%M:%S')
            })
            print(f"[{task_id}] {message}")

def complete_task(task_id, result=None, error=None):
    """Mark task as completed"""
    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]['status'] = 'completed' if error is None else 'error'
            tasks[task_id]['result'] = result
            tasks[task_id]['error'] = error

def initialize_driver():
    """Initialize Chrome driver with session persistence"""
    global driver
    with driver_lock:
        if driver is None:
            print('Initializing Chrome driver...')
            options = uc.ChromeOptions()
            profile_path = os.path.join(os.getcwd(), "shopee_session")
            options.add_argument(f"--user-data-dir={profile_path}")
            driver = uc.Chrome(options=options)
            driver.get("https://shopee.ph/buyer/login")
            print('Chrome driver ready. Please login in the browser.')
    return driver

def run_scraper_task(task_id, task_func, *args, **kwargs):
    """Run scraper task in background thread"""
    def task():
        try:
            add_task_log(task_id, 'Starting task...', 'info')
            result = task_func(task_id, *args, **kwargs)
            add_task_log(task_id, 'Task completed successfully!', 'success')
            complete_task(task_id, result=result)
        except Exception as e:
            error_msg = str(e)
            add_task_log(task_id, f'Error: {error_msg}', 'error')
            complete_task(task_id, error=error_msg)
    
    thread = threading.Thread(target=task)
    thread.daemon = True
    thread.start()

# Modified scraper wrappers to add logging
def scrape_search_with_logging(task_id, keyword, pages, output_file):
    """Search wrapper with logging"""
    add_task_log(task_id, f'Searching for: {keyword}', 'info')
    add_task_log(task_id, f'Pages to scrape: {pages}', 'info')
    result = scrape_search(driver, keyword, pages, output_file)
    add_task_log(task_id, f'Found items saved to {output_file}', 'success')
    return {'output_file': result, 'keyword': keyword}

def scrape_shop_with_logging(task_id, shop_id, include_active, include_soldout, output_file):
    """Shop scraper wrapper with logging"""
    add_task_log(task_id, f'Scraping shop: {shop_id}', 'info')
    add_task_log(task_id, f'Active items: {include_active}, Sold-out: {include_soldout}', 'info')
    result = scrape_shop(driver, shop_id, include_active, include_soldout, output_file)
    add_task_log(task_id, f'Shop items saved to {output_file}', 'success')
    return {'output_file': result, 'shop_id': shop_id}

def scrape_reviews_with_logging(task_id, input_path, output_file, max_reviews):
    """Reviews scraper wrapper with logging"""
    add_task_log(task_id, f'Scraping reviews from {input_path}', 'info')
    add_task_log(task_id, f'Max reviews per product: {max_reviews}', 'info')
    result = scrape_reviews_from_csv(driver, input_path, output_file, max_reviews)
    add_task_log(task_id, f'Reviews saved to {output_file}', 'success')
    return {'output_file': result}

def analyze_with_logging(task_id, input_path, output_file):
    """Analysis wrapper with logging"""
    add_task_log(task_id, f'Analyzing reviews from {input_path}', 'info')
    result = analyze_reviews(input_path, output_file)
    add_task_log(task_id, f'Analysis saved to {output_file}', 'success')
    
    if result is not None:
        return {
            'total_products': len(result),
            'avg_rating': round(result['Average Rating'].mean(), 2),
            'avg_consensus': round(result['Consensus Score'].mean(), 2),
            'output_file': output_file
        }
    return {'output_file': output_file}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'driver_initialized': driver is not None})

@app.route('/api/initialize-driver', methods=['POST'])
def init_driver():
    """Initialize the Chrome driver"""
    try:
        initialize_driver()
        return jsonify({
            'success': True,
            'message': 'Driver initialized. Please login in the browser window.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_products():
    """Search for products by keyword"""
    try:
        data = request.json
        keyword = data.get('keyword')
        pages = data.get('pages', 10)
        
        if not keyword:
            return jsonify({'success': False, 'error': 'Keyword is required'}), 400
        
        if driver is None:
            return jsonify({'success': False, 'error': 'Driver not initialized'}), 400
        
        task_id = str(uuid.uuid4())
        output_file = os.path.join(OUTPUT_FOLDER, f"search_{keyword.replace(' ', '_')}.csv")
        
        create_task(task_id)
        run_scraper_task(task_id, scrape_search_with_logging, keyword, pages, output_file)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Search started. Poll /api/task-status/{task_id} for progress.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shop', methods=['POST'])
def scrape_shop_items():
    """Scrape items from a shop"""
    try:
        data = request.json
        shop_id = data.get('shop_id')
        include_active = data.get('include_active', True)
        include_soldout = data.get('include_soldout', True)
        
        if not shop_id:
            return jsonify({'success': False, 'error': 'Shop ID is required'}), 400
        
        if driver is None:
            return jsonify({'success': False, 'error': 'Driver not initialized'}), 400
        
        task_id = str(uuid.uuid4())
        output_file = os.path.join(OUTPUT_FOLDER, f"shop_{shop_id}.csv")
        
        create_task(task_id)
        run_scraper_task(task_id, scrape_shop_with_logging, shop_id, include_active, include_soldout, output_file)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Shop scraping started. Poll /api/task-status/{task_id} for progress.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def scrape_reviews():
    """Scrape reviews from uploaded CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        max_reviews = int(request.form.get('max_reviews', 1000))
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only CSV files allowed'}), 400
        
        if driver is None:
            return jsonify({'success': False, 'error': 'Driver not initialized'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        task_id = str(uuid.uuid4())
        output_file = os.path.join(OUTPUT_FOLDER, f"reviews_{int(time.time())}.csv")
        
        create_task(task_id)
        run_scraper_task(task_id, scrape_reviews_with_logging, input_path, output_file, max_reviews)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Review scraping started. Poll /api/task-status/{task_id} for progress.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_reviews_endpoint():
    """Analyze reviews from uploaded CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only CSV files allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        task_id = str(uuid.uuid4())
        output_file = os.path.join(OUTPUT_FOLDER, f"analysis_{int(time.time())}.csv")
        
        create_task(task_id)
        run_scraper_task(task_id, analyze_with_logging, input_path, output_file)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Analysis started. Poll /api/task-status/{task_id} for progress.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of a running task"""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = tasks[task_id]
        # Return logs since last check
        logs = task['logs']
        # Clear logs after sending (optional - keep them if you want history)
        # task['logs'] = []
        
        return jsonify({
            'status': task['status'],
            'logs': logs,
            'result': task['result'],
            'error': task['error']
        })

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download generated files"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all output files"""
    try:
        files = []
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith('.csv'):
                file_path = os.path.join(OUTPUT_FOLDER, filename)
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(file_path),
                    'created': os.path.getctime(file_path)
                })
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_driver():
    """Close the Chrome driver"""
    global driver
    try:
        with driver_lock:
            if driver:
                driver.quit()
                driver = None
        return jsonify({'success': True, 'message': 'Driver closed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CLEANUP OLD TASKS
# ============================================================================

def cleanup_old_tasks():
    """Clean up tasks older than 1 hour"""
    while True:
        time.sleep(300)  # Run every 5 minutes
        current_time = time.time()
        with tasks_lock:
            tasks_to_delete = [
                task_id for task_id, task in tasks.items()
                if current_time - task['created_at'] > 3600
            ]
            for task_id in tasks_to_delete:
                del tasks[task_id]
                print(f"Cleaned up old task: {task_id}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
cleanup_thread.start()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("🚀 Shopee Scraper API Server")
    print("="*60)
    print("📡 Server starting on http://localhost:5000")
    print("🔄 Using HTTP polling for real-time updates")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)
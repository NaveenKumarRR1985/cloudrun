from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import time
import random
import json
import logging
import sqlite3
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('app.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    # Insert sample data
    conn.execute("INSERT OR IGNORE INTO products (id, name, price, category) VALUES (1, 'Laptop', 999.99, 'Electronics')")
    conn.execute("INSERT OR IGNORE INTO products (id, name, price, category) VALUES (2, 'Coffee Mug', 12.99, 'Kitchen')")
    conn.execute("INSERT OR IGNORE INTO products (id, name, price, category) VALUES (3, 'Book', 29.99, 'Education')")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    logger.info("Homepage accessed")
    return render_template('index.html')

@app.route('/users')
def users():
    logger.info("Users page accessed")
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/products')
def products():
    logger.info("Products page accessed")
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/analytics')
def analytics():
    logger.info("Analytics page accessed")
    return render_template('analytics.html')

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    
    if not name or not email:
        logger.warning("Invalid user data provided")
        return jsonify({'error': 'Name and email required'}), 400
    
    logger.info(f"Creating user: {name} - {email}")
    
    conn = sqlite3.connect('app.db')
    conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
    conn.commit()
    conn.close()
    
    # Simulate some processing time
    time.sleep(random.uniform(0.1, 0.5))
    
    return jsonify({'message': 'User created successfully'})

@app.route('/api/external')
def external_api():
    """Make external API call to generate network traces"""
    logger.info("Making external API call")
    
    try:
        # Simulate external API call
        response = requests.get('https://jsonplaceholder.typicode.com/posts/1', timeout=5)
        logger.info(f"External API response status: {response.status_code}")
        return jsonify({
            'status': 'success',
            'external_data': response.json()
        })
    except requests.RequestException as e:
        logger.error(f"External API call failed: {str(e)}")
        return jsonify({'error': 'External API unavailable'}), 503

@app.route('/api/slow')
def slow_endpoint():
    """Slow endpoint to generate interesting traces"""
    logger.info("Slow endpoint called")
    
    # Simulate database operation
    time.sleep(random.uniform(1, 3))
    
    # Simulate some processing
    result = sum(range(100000))
    
    logger.info("Slow endpoint completed")
    return jsonify({
        'message': 'Slow operation completed',
        'result': result,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/error')
def error_endpoint():
    """Endpoint that generates errors for testing"""
    logger.error("Intentional error endpoint called")
    
    if random.choice([True, False]):
        raise Exception("Simulated application error")
    else:
        return jsonify({'error': 'Random error occurred'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

def generate_background_metrics():
    """Background task to generate metrics"""
    while True:
        # Generate some random metrics through logging
        cpu_usage = random.uniform(10, 90)
        memory_usage = random.uniform(200, 800)
        
        logger.info(f"System metrics - CPU: {cpu_usage:.2f}%, Memory: {memory_usage:.2f}MB")
        time.sleep(30)  # Log every 30 seconds

# Start background metrics generation
metrics_thread = threading.Thread(target=generate_background_metrics, daemon=True)
metrics_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
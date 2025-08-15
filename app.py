from flask import Flask, jsonify, request, g, render_template_string
import os
import time
import random
import sqlite3
import threading
import logging
import psutil
import requests
from datetime import datetime
from contextlib import closing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database setup for generating database metrics
DATABASE = 'test.db'

def init_db():
    """Initialize SQLite database"""
    with closing(sqlite3.connect(DATABASE)) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insert sample data if empty
        cursor = conn.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            sample_users = [
                ('John Doe', 'john@example.com'),
                ('Jane Smith', 'jane@example.com'),
                ('Bob Johnson', 'bob@example.com')
            ]
            conn.executemany('INSERT INTO users (name, email) VALUES (?, ?)', sample_users)
            
            sample_orders = [
                (1, 'Laptop', 999.99),
                (2, 'Mouse', 29.99),
                (3, 'Keyboard', 79.99)
            ]
            conn.executemany('INSERT INTO orders (user_id, product, amount) VALUES (?, ?, ?)', sample_orders)
        
        conn.commit()

def get_db():
    """Get database connection"""
    return sqlite3.connect(DATABASE)

# Initialize database on startup
init_db()

# HTML template for the UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynatrace Test Application</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 300;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .status-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .status-item {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 15px;
            color: white;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }

        .status-item h3 {
            font-size: 2rem;
            margin-bottom: 5px;
        }

        .status-item p {
            opacity: 0.9;
        }

        .endpoints-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .endpoint-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .endpoint-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }

        .endpoint-card h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .endpoint-card p {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }

        .btn-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            font-size: 14px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-secondary {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #333;
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            color: #333;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .result-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: none;
        }

        .result-panel h4 {
            color: #333;
            margin-bottom: 15px;
        }

        .result-content {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            overflow-x: auto;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .health-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #28a745;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .btn-group {
                justify-content: center;
            }
            
            .endpoints-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Dynatrace Test Application</h1>
            <p>Comprehensive testing suite for application monitoring</p>
        </div>

        <div class="status-panel">
            <div class="status-grid" id="statusGrid">
                <div class="status-item">
                    <h3 id="cpuUsage">--</h3>
                    <p>CPU Usage</p>
                </div>
                <div class="status-item">
                    <h3 id="memoryUsage">--</h3>
                    <p>Memory Usage</p>
                </div>
                <div class="status-item">
                    <h3 id="uptime">--</h3>
                    <p>Uptime</p>
                </div>
                <div class="status-item">
                    <h3><span class="health-indicator"></span>Healthy</h3>
                    <p>Service Status</p>
                </div>
            </div>
        </div>

        <div class="endpoints-grid">
            <div class="endpoint-card">
                <h3>🔥 CPU Intensive Operations</h3>
                <p>Generate CPU load to test performance monitoring and CPU metrics collection.</p>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="testEndpoint('/cpu-intensive?iterations=10000', 'Light CPU Load')">Light Load</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/cpu-intensive?iterations=50000', 'Medium CPU Load')">Medium Load</button>
                    <button class="btn btn-danger" onclick="testEndpoint('/cpu-intensive?iterations=100000', 'Heavy CPU Load')">Heavy Load</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>💾 Memory Testing</h3>
                <p>Allocate memory blocks to validate memory monitoring and garbage collection metrics.</p>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="testEndpoint('/memory-test?size_mb=5', 'Small Memory Test')">5MB</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/memory-test?size_mb=20', 'Medium Memory Test')">20MB</button>
                    <button class="btn btn-danger" onclick="testEndpoint('/memory-test?size_mb=50', 'Large Memory Test')">50MB</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>🗄️ Database Operations</h3>
                <p>Execute various database operations to test database monitoring and query performance.</p>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="testEndpoint('/database-ops?operation=select', 'Database SELECT')">SELECT</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/database-ops?operation=insert', 'Database INSERT')">INSERT</button>
                    <button class="btn btn-primary" onclick="testEndpoint('/database-ops?operation=update', 'Database UPDATE')">UPDATE</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>🌐 External API Calls</h3>
                <p>Make HTTP requests to external services to test outbound connection monitoring.</p>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="testEndpoint('/external-api', 'External API Call')">JSON API</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/external-api?url=https://httpbin.org/delay/2', 'Slow API Call')">Slow API</button>
                    <button class="btn btn-primary" onclick="testEndpoint('/external-api?url=https://httpbin.org/status/200', 'Status API')">Status Check</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>⚠️ Error Generation</h3>
                <p>Generate various types of errors to test error monitoring and alerting capabilities.</p>
                <div class="btn-group">
                    <button class="btn btn-danger" onclick="testEndpoint('/error-test?type=http_error', 'HTTP Error Test')">HTTP Error</button>
                    <button class="btn btn-danger" onclick="testEndpoint('/error-test?type=exception', 'Exception Test')">Exception</button>
                    <button class="btn btn-danger" onclick="testEndpoint('/error-test?type=db_error', 'Database Error Test')">DB Error</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>📊 Custom Metrics</h3>
                <p>Generate custom business and technical metrics for application monitoring.</p>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="testEndpoint('/custom-metrics?type=business', 'Business Metrics')">Business</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/custom-metrics?type=technical', 'Technical Metrics')">Technical</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>⚡ Async Tasks</h3>
                <p>Execute background tasks to test asynchronous processing monitoring.</p>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="testEndpoint('/async-task?duration=2', 'Quick Async Task', 'POST')">2 seconds</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/async-task?duration=5', 'Medium Async Task', 'POST')">5 seconds</button>
                    <button class="btn btn-danger" onclick="testEndpoint('/async-task?duration=10', 'Long Async Task', 'POST')">10 seconds</button>
                </div>
            </div>

            <div class="endpoint-card">
                <h3>🏋️ Load Testing</h3>
                <p>Comprehensive load test combining multiple operations to stress test the application.</p>
                <div class="btn-group">
                    <button class="btn btn-danger" onclick="testEndpoint('/load-test', 'Comprehensive Load Test')">Run Load Test</button>
                    <button class="btn btn-primary" onclick="runMultipleTests()">Multiple Tests</button>
                </div>
            </div>
        </div>

        <div id="resultPanel" class="result-panel">
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Processing request...</p>
            </div>
            <h4 id="resultTitle">Test Results</h4>
            <div id="resultContent" class="result-content"></div>
        </div>

        <div class="footer">
            <p>💡 Monitor these endpoints in your Dynatrace dashboard to validate metrics collection</p>
            <p>Built for GCP Cloud Run with OneAgent integration</p>
        </div>
    </div>

    <script>
        // Update system metrics
        function updateSystemMetrics() {
            fetch('/system-metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cpuUsage').textContent = data.cpu_percent + '%';
                    document.getElementById('memoryUsage').textContent = data.memory_percent + '%';
                    document.getElementById('uptime').textContent = data.uptime;
                })
                .catch(error => {
                    console.error('Error fetching system metrics:', error);
                });
        }

        // Test endpoint function
        function testEndpoint(endpoint, testName, method = 'GET') {
            const resultPanel = document.getElementById('resultPanel');
            const loading = document.getElementById('loading');
            const resultTitle = document.getElementById('resultTitle');
            const resultContent = document.getElementById('resultContent');
            
            // Show loading
            resultPanel.style.display = 'block';
            loading.style.display = 'block';
            resultTitle.style.display = 'none';
            resultContent.style.display = 'none';
            
            // Scroll to result panel
            resultPanel.scrollIntoView({ behavior: 'smooth' });
            
            const startTime = Date.now();
            
            fetch(endpoint, { method: method })
                .then(response => {
                    const endTime = Date.now();
                    const responseTime = endTime - startTime;
                    
                    return response.json().then(data => ({
                        status: response.status,
                        statusText: response.statusText,
                        data: data,
                        responseTime: responseTime
                    }));
                })
                .then(result => {
                    // Hide loading, show results
                    loading.style.display = 'none';
                    resultTitle.style.display = 'block';
                    resultContent.style.display = 'block';
                    
                    resultTitle.textContent = `${testName} - ${result.status} (${result.responseTime}ms)`;
                    resultContent.textContent = JSON.stringify(result.data, null, 2);
                })
                .catch(error => {
                    // Hide loading, show error
                    loading.style.display = 'none';
                    resultTitle.style.display = 'block';
                    resultContent.style.display = 'block';
                    
                    resultTitle.textContent = `${testName} - Error`;
                    resultContent.textContent = `Error: ${error.message}`;
                });
        }

        // Run multiple tests
        function runMultipleTests() {
            const tests = [
                { endpoint: '/cpu-intensive?iterations=20000', name: 'CPU Test' },
                { endpoint: '/memory-test?size_mb=10', name: 'Memory Test' },
                { endpoint: '/database-ops?operation=select', name: 'Database Test' },
                { endpoint: '/external-api', name: 'API Test' }
            ];
            
            tests.forEach((test, index) => {
                setTimeout(() => {
                    testEndpoint(test.endpoint, `Batch ${index + 1}: ${test.name}`);
                }, index * 2000);
            });
        }

        // Initialize
        updateSystemMetrics();
        setInterval(updateSystemMetrics, 5000); // Update every 5 seconds
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Home page with beautiful UI"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/system-metrics')
def system_metrics():
    """Get current system metrics for the UI"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_hours = int(uptime_seconds // 3600)
        
        return jsonify({
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'uptime': f"{uptime_hours}h",
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'cpu_percent': 0,
            'memory_percent': 0,
            'uptime': 'Unknown',
            'error': str(e)
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run startup probe"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'dynatrace_agent_path': os.environ.get('DT_AGENTPATH', 'Not set'),
        'service': 'dynatrace-test-app'
    }), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint"""
    try:
        # Test database connection
        with closing(get_db()) as conn:
            conn.execute('SELECT 1').fetchone()
        
        return jsonify({
            'status': 'ready',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not ready',
            'error': str(e)
        }), 503

@app.route('/cpu-intensive', methods=['GET'])
def cpu_intensive():
    """CPU intensive operation to generate CPU metrics"""
    start_time = time.time()
    iterations = int(request.args.get('iterations', 100000))
    
    logger.info(f"Starting CPU intensive task with {iterations} iterations")
    
    # CPU intensive calculation
    result = 0
    for i in range(iterations):
        result += i ** 2
        if i % 10000 == 0:
            # Simulate some variability
            time.sleep(0.001)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"CPU intensive task completed in {duration:.2f} seconds")
    
    return jsonify({
        'result': result,
        'iterations': iterations,
        'duration_seconds': round(duration, 3),
        'cpu_percent': psutil.cpu_percent(),
        'message': f'Completed {iterations:,} iterations in {duration:.3f}s'
    })

@app.route('/memory-test', methods=['GET'])
def memory_test():
    """Memory allocation test to generate memory metrics"""
    size_mb = int(request.args.get('size_mb', 10))
    logger.info(f"Allocating {size_mb}MB of memory")
    
    # Allocate memory
    data = []
    for _ in range(size_mb):
        # Allocate 1MB chunks
        chunk = 'x' * (1024 * 1024)
        data.append(chunk)
    
    # Get memory info
    memory_info = psutil.virtual_memory()
    
    # Clean up
    del data
    
    return jsonify({
        'allocated_mb': size_mb,
        'memory_percent': round(memory_info.percent, 1),
        'available_mb': memory_info.available // (1024 * 1024),
        'message': f'Successfully allocated and freed {size_mb}MB'
    })

@app.route('/database-ops', methods=['GET'])
def database_operations():
    """Perform database operations to generate DB metrics"""
    operation = request.args.get('operation', 'select')
    logger.info(f"Performing database operation: {operation}")
    
    start_time = time.time()
    
    try:
        with closing(get_db()) as conn:
            if operation == 'select':
                cursor = conn.execute('''
                    SELECT u.name, u.email, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
                    FROM users u 
                    LEFT JOIN orders o ON u.id = o.user_id 
                    GROUP BY u.id, u.name, u.email
                ''')
                results = cursor.fetchall()
                results = [{'name': r[0], 'email': r[1], 'orders': r[2], 'total': r[3]} for r in results]
                
            elif operation == 'insert':
                name = f"User_{random.randint(1000, 9999)}"
                email = f"user{random.randint(1000, 9999)}@example.com"
                conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
                conn.commit()
                results = [{'inserted_user': name, 'email': email}]
                
            elif operation == 'update':
                user_id = random.randint(1, 3)
                new_name = f"Updated_{random.randint(1000, 9999)}"
                conn.execute('UPDATE users SET name = ? WHERE id = ?', (new_name, user_id))
                conn.commit()
                results = [{'updated_user_id': user_id, 'new_name': new_name, 'changes': conn.total_changes}]
                
            else:
                results = [{'error': 'Invalid operation. Use: select, insert, or update'}]
        
        duration = time.time() - start_time
        logger.info(f"Database operation completed in {duration:.3f} seconds")
        
        return jsonify({
            'operation': operation,
            'duration_seconds': round(duration, 3),
            'results': results,
            'message': f'Database {operation} completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        return jsonify({'error': str(e), 'operation': operation}), 500

@app.route('/external-api', methods=['GET'])
def external_api_call():
    """Make external API call to generate HTTP client metrics"""
    url = request.args.get('url', 'https://httpbin.org/json')
    timeout = int(request.args.get('timeout', 5))
    
    logger.info(f"Making external API call to: {url}")
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=timeout)
        duration = time.time() - start_time
        
        logger.info(f"External API call completed in {duration:.3f} seconds")
        
        return jsonify({
            'url': url,
            'status_code': response.status_code,
            'duration_seconds': round(duration, 3),
            'response_size_bytes': len(response.content),
            'message': f'Successfully called {url}',
            'sample_headers': {
                'content-type': response.headers.get('content-type'),
                'content-length': response.headers.get('content-length')
            }
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"External API call failed: {e}")
        return jsonify({
            'error': str(e),
            'url': url,
            'duration_seconds': round(time.time() - start_time, 3),
            'message': f'Failed to call {url}'
        }), 500

@app.route('/error-test', methods=['GET'])
def error_test():
    """Generate different types of errors for error monitoring"""
    error_type = request.args.get('type', 'http_error')
    
    logger.warning(f"Generating test error of type: {error_type}")
    
    if error_type == 'http_error':
        return jsonify({
            'error': 'This is a test HTTP error',
            'error_type': 'http_error',
            'message': 'Intentional 500 error for testing'
        }), 500
    elif error_type == 'exception':
        raise ValueError("This is a test exception for Dynatrace monitoring")
    elif error_type == 'db_error':
        try:
            with closing(get_db()) as conn:
                conn.execute('SELECT * FROM non_existent_table')
        except Exception as e:
            return jsonify({
                'error': str(e),
                'error_type': 'database_error',
                'message': 'Intentional database error for testing'
            }), 500
    else:
        return jsonify({
            'error': 'Unknown error type',
            'valid_types': ['http_error', 'exception', 'db_error'],
            'message': 'Please specify a valid error type'
        }), 400

@app.route('/custom-metrics', methods=['GET'])
def custom_metrics():
    """Generate custom business metrics"""
    metric_type = request.args.get('type', 'business')
    
    if metric_type == 'business':
        # Simulate business metrics
        metrics = {
            'active_users': random.randint(100, 1000),
            'revenue': round(random.uniform(1000, 10000), 2),
            'conversion_rate': round(random.uniform(0.1, 0.3), 3),
            'avg_order_value': round(random.uniform(50, 200), 2),
            'customer_satisfaction': round(random.uniform(4.0, 5.0), 1)
        }
        
        logger.info(f"Generated business metrics: {metrics}")
        
    else:
        # Simulate technical metrics
        metrics = {
            'cache_hit_rate': round(random.uniform(0.8, 0.99), 3),
            'queue_depth': random.randint(0, 100),
            'processing_time_ms': random.randint(10, 500),
            'throughput_rps': random.randint(100, 1000),
            'error_rate': round(random.uniform(0.001, 0.05), 3)
        }
        
        logger.info(f"Generated technical metrics: {metrics}")
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'metric_type': metric_type,
        'metrics': metrics,
        'message': f'Generated {len(metrics)} {metric_type} metrics'
    })

@app.route('/async-task', methods=['POST'])
def async_task():
    """Simulate asynchronous task processing"""
    task_duration = int(request.args.get('duration', 3))
    task_id = f"task_{random.randint(1000, 9999)}"
    
    def background_task():
        logger.info(f"Starting background task {task_id} (duration: {task_duration}s)")
        time.sleep(task_duration)
        logger.info(f"Background task {task_id} completed")
    
    # Start background thread
    thread = threading.Thread(target=background_task)
    thread.start()
    
    return jsonify({
        'message': 'Async task started',
        'task_id': task_id,
        'duration': task_duration,
        'status': 'running',
        'started_at': datetime.now().isoformat()
    })

@app.route('/load-test', methods=['GET'])
def load_test():
    """Generate load for comprehensive testing"""
    logger.info("Starting comprehensive load test")
    
    # Perform multiple operations
    results = {}
    start_total = time.time()
    
    # CPU operation
    start = time.time()
    sum(i**2 for i in range(10000))
    results['cpu_time'] = round(time.time() - start, 3)
    
    # Database operation
    start = time.time()
    with closing(get_db()) as conn:
        conn.execute('SELECT COUNT(*) FROM users').fetchone()
        conn.execute('SELECT COUNT(*) FROM orders').fetchone()
    results['db_time'] = round(time.time() - start, 3)
    
    # Memory allocation
    start = time.time()
    data = ['x' * 1024 for _ in range(1000)]  # 1MB
    del data
    results['memory_time'] = round(time.time() - start, 3)
    
    # External API call (simulate)
    start = time.time()
    time.sleep(0.1)  # Simulate network delay
    results['api_time'] = round(time.time() - start, 3)
    
    total_time = round(time.time() - start_total, 3)
    
    logger.info(f"Load test completed in {total_time}s: {results}")
    
    return jsonify({
        'message': 'Comprehensive load test completed',
        'total_duration': total_time,
        'operations': results,
        'timestamp': datetime.now().isoformat(),
        'system_metrics': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': round(psutil.virtual_memory().percent, 1)
        }
    })

# Error handlers for better error tracking
@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 error: {request.url}")
    return jsonify({
        'error': 'Not found',
        'path': request.path,
        'message': 'The requested endpoint does not exist',
        'available_endpoints': [
            '/', '/health', '/ready', '/cpu-intensive', '/memory-test',
            '/database-ops', '/external-api', '/error-test', '/custom-metrics',
            '/async-task', '/load-test', '/system-metrics'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({
        'error': 'Application error',
        'type': type(e).__name__,
        'message': str(e),
        'timestamp': datetime.now().isoformat()
    }), 500

# Request logging middleware
@app.before_request
def before_request():
    g.start_time = time.time()
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    logger.info(f"Response: {response.status_code} ({duration:.3f}s) - {request.method} {request.path}")
    
    # Add CORS headers if needed
    response.headers['X-Response-Time'] = f"{duration:.3f}s"
    return response

if __name__ == '__main__':
    # Get port from environment variable (Cloud Run uses PORT)
    port = int(os.environ.get('PORT', 8080))
    
    logger.info(f"Starting Dynatrace test application on port {port}")
    logger.info(f"Dynatrace agent path: {os.environ.get('DT_AGENTPATH', 'Not set')}")
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    
    # Print available endpoints
    logger.info("Available endpoints:")
    logger.info("  GET  / - Main UI dashboard")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /ready - Readiness check")
    logger.info("  GET  /system-metrics - System metrics")
    logger.info("  GET  /cpu-intensive - CPU load testing")
    logger.info("  GET  /memory-test - Memory allocation testing")
    logger.info("  GET  /database-ops - Database operations")
    logger.info("  GET  /external-api - External API calls")
    logger.info("  GET  /error-test - Error generation")
    logger.info("  GET  /custom-metrics - Custom metrics")
    logger.info("  POST /async-task - Async task processing")
    logger.info("  GET  /load-test - Comprehensive load test")
    
    app.run(host='0.0.0.0', port=port, debug=False)

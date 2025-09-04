from flask import Flask, render_template, request, jsonify
import logging
import time
import random
import requests
import os
from datetime import datetime

# Import OpenTelemetry for manual instrumentation
from opentelemetry import trace

# Get the tracer for manual spans
tracer = trace.get_tracer(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

users = []
metrics_data = {'requests_count': 0, 'errors_count': 0, 'response_times': []}

@app.route('/')
def index():
    # Create a custom span for the entire operation
    with tracer.start_as_current_span("process_home_request") as span:
        span.set_attribute("route", "/")
        span.set_attribute("user_count", len(users))
        
        logger.info("Home page accessed")
        metrics_data['requests_count'] += 1
        
        # Add span for database simulation
        with tracer.start_as_current_span("simulate_database_query"):
            span.add_event("Starting database query")
            time.sleep(random.uniform(0.05, 0.15))
            span.add_event("Database query completed")
            span.set_attribute("query_type", "user_list")
        
        # Add span for cache operations
        with tracer.start_as_current_span("cache_lookup"):
            span.add_event("Cache lookup started")
            time.sleep(random.uniform(0.01, 0.05))
            span.add_event("Cache hit", {"cache_key": "user_metrics"})
            
        # Add span for business logic
        with tracer.start_as_current_span("business_logic_processing"):
            span.set_attribute("processing_type", "metrics_calculation")
            processing_time = random.uniform(0.02, 0.08)
            time.sleep(processing_time)
            metrics_data['response_times'].append(processing_time)
            span.set_attribute("processing_time_ms", processing_time * 1000)
    
    return render_template('index.html', users=users, metrics=metrics_data)

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    with tracer.start_as_current_span("handle_users_request") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("endpoint", "/api/users")
        
        logger.info(f"API users endpoint accessed via {request.method}")
        metrics_data['requests_count'] += 1
        
        if request.method == 'POST':
            return create_user()
        else:
            return get_all_users()

def create_user():
    """Separate function with its own span"""
    with tracer.start_as_current_span("create_user_operation") as span:
        try:
            # Validation span
            with tracer.start_as_current_span("validate_user_data"):
                time.sleep(random.uniform(0.01, 0.03))
                user_data = request.json
                span.add_event("User data validation completed")
                span.set_attribute("user_name", user_data.get('name', 'unknown'))
            
            # Database write simulation
            with tracer.start_as_current_span("database_write_user") as db_span:
                db_span.add_event("Starting database write")
                time.sleep(random.uniform(0.05, 0.12))
                
                user = {
                    'id': len(users) + 1,
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'created_at': datetime.now().isoformat()
                }
                users.append(user)
                
                db_span.set_attribute("user_id", user['id'])
                db_span.set_attribute("database_operation", "INSERT")
                db_span.add_event("Database write completed")
                
            # Cache update span
            with tracer.start_as_current_span("update_cache"):
                time.sleep(random.uniform(0.01, 0.02))
                span.add_event("Cache updated after user creation")
                
            logger.info(f"Created user: {user['name']} with ID: {user['id']}")
            span.set_attribute("operation_result", "success")
            
            return jsonify(user), 201
            
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("operation_result", "error")
            logger.error(f"Error creating user: {str(e)}")
            metrics_data['errors_count'] += 1
            return jsonify({'error': 'Failed to create user'}), 400

def get_all_users():
    """Get users with detailed tracing"""
    with tracer.start_as_current_span("get_all_users_operation") as span:
        # Simulate database read
        with tracer.start_as_current_span("database_read_users"):
            span.add_event("Executing SELECT query")
            time.sleep(random.uniform(0.03, 0.08))
            span.set_attribute("records_found", len(users))
            span.add_event("Query execution completed")
        
        logger.info("Users list retrieved from database")
        return jsonify(users)

@app.route('/api/external')
def call_external():
    """External API calls with detailed tracing"""
    with tracer.start_as_current_span("external_api_calls") as span:
        logger.info("Making external API calls")
        metrics_data['requests_count'] += 1
        
        try:
            results = {}
            
            # First external call
            with tracer.start_as_current_span("call_mock_service") as call_span:
                call_span.set_attribute("service.name", "mock-external-service")
                call_span.set_attribute("http.url", "http://mock-external-service/json")
                
                start_time = time.time()
                response1 = requests.get('http://mock-external-service/json', timeout=5)
                duration = time.time() - start_time
                
                call_span.set_attribute("http.status_code", response1.status_code)
                call_span.set_attribute("http.response_time_ms", duration * 1000)
                results['mock_service'] = response1.json()
            
            # Second external call  
            with tracer.start_as_current_span("call_public_service") as call_span:
                call_span.set_attribute("service.name", "httpbin.org")
                call_span.set_attribute("http.url", "https://httpbin.org/uuid")
                
                start_time = time.time()
                response2 = requests.get('https://httpbin.org/uuid', timeout=5)
                duration = time.time() - start_time
                
                call_span.set_attribute("http.status_code", response2.status_code)
                call_span.set_attribute("http.response_time_ms", duration * 1000)
                results['public_service'] = response2.json()
            
            # Internal processing
            with tracer.start_as_current_span("process_external_responses"):
                time.sleep(random.uniform(0.02, 0.05))
                span.add_event("Response processing completed")
                span.set_attribute("services_called", 2)
            
            return jsonify({
                'status': 'success',
                'external_data': results,
                'services_called': 2
            })
            
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("operation_result", "error")
            logger.error(f"External API call failed: {str(e)}")
            metrics_data['errors_count'] += 1
            return jsonify({'error': 'External API call failed'}), 500

@app.route('/health')
def health():
    with tracer.start_as_current_span("health_check") as span:
        # Simulate health checks
        with tracer.start_as_current_span("check_database"):
            time.sleep(random.uniform(0.005, 0.015))
            span.add_event("Database ping successful")
            
        with tracer.start_as_current_span("check_cache"):
            time.sleep(random.uniform(0.005, 0.015))
            span.add_event("Cache ping successful")
        
        span.set_attribute("health_status", "healthy")
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

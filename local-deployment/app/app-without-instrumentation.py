from flask import Flask, render_template, request, jsonify
import logging
import time
import random
import requests
import json
import os
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

# Manual OpenTelemetry imports for code-level tracing
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Get tracer and meter for manual instrumentation
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Custom metrics
request_counter = meter.create_counter(
    "http_requests_total",
    description="Total number of HTTP requests"
)

response_time_histogram = meter.create_histogram(
    "http_request_duration_seconds",
    description="HTTP request duration in seconds"
)

error_counter = meter.create_counter(
    "errors_total",
    description="Total number of errors"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory storage for demo
users = []
orders = []
products = [
    {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
    {"id": 2, "name": "Phone", "price": 699.99, "stock": 25},
    {"id": 3, "name": "Tablet", "price": 399.99, "stock": 15},
    {"id": 4, "name": "Headphones", "price": 199.99, "stock": 50}
]

# App metrics
app_metrics = {
    'total_requests': 0,
    'total_errors': 0,
    'total_users': 0,
    'total_orders': 0,
    'response_times': []
}

def simulate_database_operation(operation_type, duration_range=(0.05, 0.2)):
    """Simulate database operations with tracing"""
    with tracer.start_as_current_span(f"database_{operation_type}") as span:
        span.set_attribute("db.operation", operation_type)
        span.set_attribute("db.name", "demo_db")
        span.add_event(f"Starting {operation_type} operation")
        
        duration = random.uniform(*duration_range)
        time.sleep(duration)
        
        span.set_attribute("db.duration_ms", duration * 1000)
        span.add_event(f"Completed {operation_type} operation")
        return duration

def simulate_cache_operation(cache_key, hit_rate=0.7):
    """Simulate cache operations with tracing"""
    with tracer.start_as_current_span("cache_lookup") as span:
        span.set_attribute("cache.key", cache_key)
        
        is_hit = random.random() < hit_rate
        span.set_attribute("cache.hit", is_hit)
        
        if is_hit:
            time.sleep(random.uniform(0.001, 0.005))  # Fast cache hit
            span.add_event("Cache hit")
            return True
        else:
            time.sleep(random.uniform(0.01, 0.03))   # Cache miss, slower
            span.add_event("Cache miss")
            return False

def process_business_logic(operation_name, complexity="medium"):
    """Simulate business logic with nested spans"""
    with tracer.start_as_current_span(f"business_logic_{operation_name}") as span:
        span.set_attribute("operation.name", operation_name)
        span.set_attribute("operation.complexity", complexity)
        
        # Simulate validation
        with tracer.start_as_current_span("validation") as validation_span:
            validation_span.add_event("Starting validation")
            time.sleep(random.uniform(0.01, 0.03))
            validation_span.set_attribute("validation.result", "passed")
            validation_span.add_event("Validation completed")
        
        # Simulate processing steps
        steps = ["initialize", "process", "finalize"]
        for i, step in enumerate(steps):
            with tracer.start_as_current_span(f"step_{step}") as step_span:
                step_span.set_attribute("step.number", i + 1)
                step_span.set_attribute("step.name", step)
                
                if step == "process" and complexity == "high":
                    time.sleep(random.uniform(0.1, 0.3))
                else:
                    time.sleep(random.uniform(0.02, 0.05))
                
                step_span.add_event(f"Completed {step}")
        
        span.add_event("Business logic completed")

@app.route('/')
def index():
    with tracer.start_as_current_span("homepage_request") as span:
        start_time = time.time()
        span.set_attribute("http.route", "/")
        span.set_attribute("user.count", len(users))
        
        # Increment custom metrics
        request_counter.add(1, {"endpoint": "/", "method": "GET"})
        
        logger.info("Homepage accessed")
        app_metrics['total_requests'] += 1
        
        # Simulate cache check
        cache_hit = simulate_cache_operation("homepage_data")
        span.set_attribute("cache.hit", cache_hit)
        
        if not cache_hit:
            # Simulate database queries for homepage data
            simulate_database_operation("select_users", (0.03, 0.08))
            simulate_database_operation("select_recent_orders", (0.02, 0.06))
        
        # Process homepage business logic
        process_business_logic("homepage_render", "low")
        
        # Calculate response time
        response_time = time.time() - start_time
        app_metrics['response_times'].append(response_time)
        response_time_histogram.record(response_time, {"endpoint": "/", "method": "GET"})
        
        span.set_attribute("response.time_ms", response_time * 1000)
        span.set_status(Status(StatusCode.OK))
        
        return render_template('index.html', 
                             users=users, 
                             orders=orders,
                             products=products,
                             metrics=app_metrics)

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    with tracer.start_as_current_span("users_api") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.route", "/api/users")
        
        request_counter.add(1, {"endpoint": "/api/users", "method": request.method})
        app_metrics['total_requests'] += 1
        
        if request.method == 'POST':
            return create_user()
        else:
            return get_users()

def create_user():
    """Create a new user with detailed tracing"""
    with tracer.start_as_current_span("create_user_operation") as span:
        try:
            # Input validation
            with tracer.start_as_current_span("validate_user_input") as validation_span:
                user_data = request.json
                if not user_data or 'name' not in user_data or 'email' not in user_data:
                    validation_span.set_status(Status(StatusCode.ERROR, "Invalid input"))
                    error_counter.add(1, {"type": "validation_error"})
                    return jsonify({'error': 'Invalid user data'}), 400
                
                validation_span.set_attribute("user.name", user_data['name'])
                validation_span.set_attribute("user.email", user_data['email'])
                validation_span.add_event("Input validation successful")
            
            # Check for duplicate email
            with tracer.start_as_current_span("check_duplicate_email") as check_span:
                simulate_database_operation("select_by_email", (0.02, 0.05))
                existing_user = next((u for u in users if u['email'] == user_data['email']), None)
                if existing_user:
                    check_span.set_status(Status(StatusCode.ERROR, "Email exists"))
                    error_counter.add(1, {"type": "duplicate_email"})
                    return jsonify({'error': 'Email already exists'}), 409
                check_span.add_event("Email check passed")
            
            # Create user object
            with tracer.start_as_current_span("create_user_object") as create_span:
                user = {
                    'id': len(users) + 1,
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                }
                create_span.set_attribute("user.id", user['id'])
                create_span.add_event("User object created")
            
            # Save to database
            with tracer.start_as_current_span("save_user_to_database") as save_span:
                simulate_database_operation("insert_user", (0.08, 0.15))
                users.append(user)
                app_metrics['total_users'] = len(users)
                save_span.set_attribute("user.id", user['id'])
                save_span.add_event("User saved to database")
            
            # Update cache
            with tracer.start_as_current_span("update_user_cache") as cache_span:
                time.sleep(random.uniform(0.01, 0.03))
                cache_span.add_event("User cache updated")
            
            # Send notification (async simulation)
            with tracer.start_as_current_span("send_welcome_notification") as notify_span:
                notify_span.set_attribute("notification.type", "welcome_email")
                notify_span.set_attribute("user.email", user['email'])
                time.sleep(random.uniform(0.05, 0.1))
                notify_span.add_event("Welcome notification sent")
            
            logger.info(f"Created user: {user['name']} (ID: {user['id']})")
            span.set_attribute("operation.result", "success")
            span.set_attribute("user.id", user['id'])
            
            return jsonify(user), 201
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            error_counter.add(1, {"type": "server_error"})
            app_metrics['total_errors'] += 1
            logger.error(f"Error creating user: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

def get_users():
    """Get all users with tracing"""
    with tracer.start_as_current_span("get_users_operation") as span:
        # Check cache first
        cache_hit = simulate_cache_operation("all_users")
        
        if not cache_hit:
            # Simulate database query
            simulate_database_operation("select_all_users", (0.04, 0.10))
        
        span.set_attribute("users.count", len(users))
        span.set_attribute("cache.hit", cache_hit)
        
        return jsonify(users)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order with complex business logic"""
    with tracer.start_as_current_span("create_order_operation") as span:
        try:
            start_time = time.time()
            request_counter.add(1, {"endpoint": "/api/orders", "method": "POST"})
            
            order_data = request.json
            span.set_attribute("order.user_id", order_data.get('user_id'))
            span.set_attribute("order.product_ids", str(order_data.get('product_ids', [])))
            
            # Validate order
            with tracer.start_as_current_span("validate_order") as validation_span:
                if not order_data or 'user_id' not in order_data or 'product_ids' not in order_data:
                    validation_span.set_status(Status(StatusCode.ERROR, "Invalid order data"))
                    return jsonify({'error': 'Invalid order data'}), 400
                validation_span.add_event("Order validation passed")
            
            # Check user exists
            with tracer.start_as_current_span("verify_user") as user_span:
                simulate_database_operation("select_user_by_id")
                user = next((u for u in users if u['id'] == order_data['user_id']), None)
                if not user:
                    user_span.set_status(Status(StatusCode.ERROR, "User not found"))
                    return jsonify({'error': 'User not found'}), 404
                user_span.set_attribute("user.name", user['name'])
            
            # Process each product
            total_amount = 0
            order_items = []
            
            for product_id in order_data['product_ids']:
                with tracer.start_as_current_span(f"process_product_{product_id}") as product_span:
                    product = next((p for p in products if p['id'] == product_id), None)
                    if not product:
                        product_span.set_status(Status(StatusCode.ERROR, "Product not found"))
                        continue
                    
                    # Check inventory
                    with tracer.start_as_current_span("check_inventory") as inventory_span:
                        simulate_database_operation("select_inventory")
                        if product['stock'] <= 0:
                            inventory_span.set_status(Status(StatusCode.ERROR, "Out of stock"))
                            continue
                        inventory_span.set_attribute("product.stock", product['stock'])
                    
                    # Calculate pricing
                    with tracer.start_as_current_span("calculate_pricing") as pricing_span:
                        process_business_logic("pricing_calculation", "medium")
                        item_total = product['price']
                        total_amount += item_total
                        pricing_span.set_attribute("item.price", item_total)
                    
                    order_items.append({
                        'product_id': product_id,
                        'name': product['name'],
                        'price': product['price']
                    })
                    
                    product_span.set_attribute("product.name", product['name'])
                    product_span.set_attribute("product.price", product['price'])
            
            # Create order
            with tracer.start_as_current_span("create_order_record") as create_span:
                order = {
                    'id': len(orders) + 1,
                    'user_id': order_data['user_id'],
                    'user_name': user['name'],
                    'items': order_items,
                    'total_amount': total_amount,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat()
                }
                
                # Save order
                simulate_database_operation("insert_order", (0.1, 0.2))
                orders.append(order)
                app_metrics['total_orders'] = len(orders)
                
                create_span.set_attribute("order.id", order['id'])
                create_span.set_attribute("order.total", total_amount)
                create_span.add_event("Order record created")
            
            # Process payment (simulation)
            with tracer.start_as_current_span("process_payment") as payment_span:
                payment_span.set_attribute("payment.amount", total_amount)
                payment_span.set_attribute("payment.method", "credit_card")
                
                # Simulate payment processing time
                time.sleep(random.uniform(0.2, 0.5))
                
                # Simulate payment success/failure
                payment_success = random.random() > 0.1  # 90% success rate
                if payment_success:
                    order['status'] = 'paid'
                    payment_span.set_attribute("payment.status", "success")
                    payment_span.add_event("Payment processed successfully")
                else:
                    order['status'] = 'payment_failed'
                    payment_span.set_status(Status(StatusCode.ERROR, "Payment failed"))
                    error_counter.add(1, {"type": "payment_error"})
            
            # Update inventory
            with tracer.start_as_current_span("update_inventory") as inventory_span:
                for item in order_items:
                    product = next(p for p in products if p['id'] == item['product_id'])
                    product['stock'] -= 1
                
                simulate_database_operation("update_inventory")
                inventory_span.add_event("Inventory updated")
            
            response_time = time.time() - start_time
            response_time_histogram.record(response_time, {"endpoint": "/api/orders", "method": "POST"})
            
            span.set_attribute("order.id", order['id'])
            span.set_attribute("response.time_ms", response_time * 1000)
            
            logger.info(f"Created order: {order['id']} for user: {user['name']}")
            return jsonify(order), 201
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            error_counter.add(1, {"type": "server_error"})
            app_metrics['total_errors'] += 1
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/external-service')
def call_external_service():
    """Simulate calling external services with distributed tracing"""
    with tracer.start_as_current_span("external_service_calls") as span:
        try:
            request_counter.add(1, {"endpoint": "/api/external-service", "method": "GET"})
            
            # Call to external payment service
            with tracer.start_as_current_span("payment_service_call") as payment_span:
                payment_span.set_attribute("service.name", "payment-gateway")
                payment_span.set_attribute("http.url", "https://httpbin.org/delay/1")
                
                start_time = time.time()
                response = requests.get('https://httpbin.org/delay/1', timeout=10)
                duration = time.time() - start_time
                
                payment_span.set_attribute("http.status_code", response.status_code)
                payment_span.set_attribute("http.response_time_ms", duration * 1000)
                payment_span.add_event("Payment service call completed")
            
            # Call to external inventory service
            with tracer.start_as_current_span("inventory_service_call") as inventory_span:
                inventory_span.set_attribute("service.name", "inventory-service")
                inventory_span.set_attribute("http.url", "https://httpbin.org/json")
                
                start_time = time.time()
                response2 = requests.get('https://httpbin.org/json', timeout=5)
                duration2 = time.time() - start_time
                
                inventory_span.set_attribute("http.status_code", response2.status_code)
                inventory_span.set_attribute("http.response_time_ms", duration2 * 1000)
                inventory_span.add_event("Inventory service call completed")
            
            # Process responses
            with tracer.start_as_current_span("process_external_responses") as process_span:
                process_business_logic("external_data_processing", "high")
                process_span.add_event("External responses processed")
            
            return jsonify({
                'status': 'success',
                'payment_service': {'status': response.status_code, 'duration': duration},
                'inventory_service': {'status': response2.status_code, 'duration': duration2}
            })
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            error_counter.add(1, {"type": "external_service_error"})
            return jsonify({'error': 'External service call failed'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint with monitoring"""
    with tracer.start_as_current_span("health_check") as span:
        # Check database connection
        with tracer.start_as_current_span("check_database") as db_span:
            simulate_database_operation("health_check", (0.01, 0.03))
            db_span.add_event("Database health check passed")
        
        # Check cache connection
        with tracer.start_as_current_span("check_cache") as cache_span:
            time.sleep(random.uniform(0.005, 0.015))
            cache_span.add_event("Cache health check passed")
        
        span.set_attribute("health.status", "healthy")
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'metrics': app_metrics
        })

@app.route('/metrics')
def get_metrics():
    """Custom application metrics"""
    return jsonify({
        'application_metrics': app_metrics,
        'system_info': {
            'users_count': len(users),
            'orders_count': len(orders),
            'products_count': len(products)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

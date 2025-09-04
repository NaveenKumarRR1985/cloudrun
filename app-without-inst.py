from flask import Flask, render_template, request, jsonify
import logging
import time
import random
import requests
import os
from datetime import datetime

# NO manual OpenTelemetry imports or code!
# All tracing happens automatically through opentelemetry-instrument

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

app_metrics = {
    'total_requests': 0,
    'total_errors': 0,
    'response_times': []
}

def simulate_database_operation(operation_type, duration_range=(0.05, 0.2)):
    """Simulate database operations - auto-instrumented"""
    logger.info(f"Starting {operation_type} operation")
    duration = random.uniform(*duration_range)
    time.sleep(duration)  # This will be automatically captured as a span
    logger.info(f"Completed {operation_type} operation in {duration:.3f}s")
    return duration

def simulate_cache_operation(cache_key, hit_rate=0.7):
    """Simulate cache operations - auto-instrumented"""
    logger.info(f"Cache lookup for key: {cache_key}")
    is_hit = random.random() < hit_rate
    
    if is_hit:
        time.sleep(random.uniform(0.001, 0.005))  # Fast cache hit
        logger.info("Cache hit")
        return True
    else:
        time.sleep(random.uniform(0.01, 0.03))   # Cache miss
        logger.info("Cache miss")
        return False

def process_business_logic(operation_name, complexity="medium"):
    """Business logic processing - auto-instrumented"""
    logger.info(f"Processing {operation_name} with {complexity} complexity")
    
    # Simulate validation
    logger.info("Starting validation")
    time.sleep(random.uniform(0.01, 0.03))
    logger.info("Validation completed")
    
    # Simulate processing steps
    steps = ["initialize", "process", "finalize"]
    for step in steps:
        logger.info(f"Executing step: {step}")
        if step == "process" and complexity == "high":
            time.sleep(random.uniform(0.1, 0.3))
        else:
            time.sleep(random.uniform(0.02, 0.05))
        logger.info(f"Completed {step}")
    
    logger.info("Business logic completed")

@app.route('/')
def index():
    """Homepage - automatically traced by Flask instrumentation"""
    start_time = time.time()
    logger.info("Homepage accessed")
    app_metrics['total_requests'] += 1
    
    # These operations will be automatically captured
    cache_hit = simulate_cache_operation("homepage_data")
    
    if not cache_hit:
        # Database operations automatically traced
        simulate_database_operation("select_users", (0.03, 0.08))
        simulate_database_operation("select_recent_orders", (0.02, 0.06))
    
    # Business logic automatically traced
    process_business_logic("homepage_render", "low")
    
    response_time = time.time() - start_time
    app_metrics['response_times'].append(response_time)
    
    return render_template('index.html', 
                         users=users, 
                         orders=orders,
                         products=products,
                         metrics=app_metrics)

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    """Users API - automatically traced"""
    logger.info(f"Users API accessed via {request.method}")
    app_metrics['total_requests'] += 1
    
    if request.method == 'POST':
        return create_user()
    else:
        return get_users()

def create_user():
    """Create user with simulated operations - all auto-traced"""
    try:
        # Input validation
        user_data = request.json
        if not user_data or 'name' not in user_data or 'email' not in user_data:
            logger.error("Invalid user data")
            app_metrics['total_errors'] += 1
            return jsonify({'error': 'Invalid user data'}), 400
        
        logger.info(f"Creating user: {user_data['name']}")
        
        # Check for duplicate email - simulated DB operation
        simulate_database_operation("select_by_email", (0.02, 0.05))
        existing_user = next((u for u in users if u['email'] == user_data['email']), None)
        if existing_user:
            logger.warning(f"Email already exists: {user_data['email']}")
            app_metrics['total_errors'] += 1
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create user object
        user = {
            'id': len(users) + 1,
            'name': user_data['name'],
            'email': user_data['email'],
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Save to database - simulated operation
        simulate_database_operation("insert_user", (0.08, 0.15))
        users.append(user)
        
        # Update cache - simulated operation
        time.sleep(random.uniform(0.01, 0.03))
        logger.info("User cache updated")
        
        # Send notification - simulated operation
        time.sleep(random.uniform(0.05, 0.1))
        logger.info(f"Welcome notification sent to {user['email']}")
        
        logger.info(f"Created user: {user['name']} (ID: {user['id']})")
        return jsonify(user), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        app_metrics['total_errors'] += 1
        return jsonify({'error': 'Internal server error'}), 500

def get_users():
    """Get all users - auto-traced"""
    logger.info("Fetching all users")
    
    # Check cache first
    cache_hit = simulate_cache_operation("all_users")
    
    if not cache_hit:
        # Database query automatically traced
        simulate_database_operation("select_all_users", (0.04, 0.10))
    
    logger.info(f"Returning {len(users)} users")
    return jsonify(users)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create order with complex business logic - all auto-traced"""
    try:
        start_time = time.time()
        order_data = request.json
        logger.info(f"Creating order for user: {order_data.get('user_id')}")
        
        # Validation
        if not order_data or 'user_id' not in order_data or 'product_ids' not in order_data:
            logger.error("Invalid order data")
            return jsonify({'error': 'Invalid order data'}), 400
        
        # Check user exists - DB operation
        simulate_database_operation("select_user_by_id")
        user = next((u for u in users if u['id'] == order_data['user_id']), None)
        if not user:
            logger.error("User not found")
            return jsonify({'error': 'User not found'}), 404
        
        # Process each product
        total_amount = 0
        order_items = []
        
        for product_id in order_data['product_ids']:
            logger.info(f"Processing product {product_id}")
            product = next((p for p in products if p['id'] == product_id), None)
            if not product:
                logger.warning(f"Product {product_id} not found")
                continue
            
            # Check inventory - DB operation
            simulate_database_operation("select_inventory")
            if product['stock'] <= 0:
                logger.warning(f"Product {product_id} out of stock")
                continue
            
            # Calculate pricing - business logic
            process_business_logic("pricing_calculation", "medium")
            item_total = product['price']
            total_amount += item_total
            
            order_items.append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price']
            })
        
        # Create order
        order = {
            'id': len(orders) + 1,
            'user_id': order_data['user_id'],
            'user_name': user['name'],
            'items': order_items,
            'total_amount': total_amount,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        # Save order - DB operation
        simulate_database_operation("insert_order", (0.1, 0.2))
        orders.append(order)
        
        # Process payment simulation
        logger.info(f"Processing payment of ${total_amount}")
        time.sleep(random.uniform(0.2, 0.5))  # Payment processing time
        
        payment_success = random.random() > 0.1  # 90% success rate
        if payment_success:
            order['status'] = 'paid'
            logger.info("Payment processed successfully")
        else:
            order['status'] = 'payment_failed'
            logger.error("Payment failed")
            app_metrics['total_errors'] += 1
        
        # Update inventory - DB operation
        simulate_database_operation("update_inventory")
        for item in order_items:
            product = next(p for p in products if p['id'] == item['product_id'])
            product['stock'] -= 1
        
        logger.info(f"Created order: {order['id']} for user: {user['name']}")
        return jsonify(order), 201
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        app_metrics['total_errors'] += 1
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/external-service')
def call_external_service():
    """Call external services - automatically traced by requests instrumentation"""
    try:
        logger.info("Calling external services")
        
        # These HTTP calls will be automatically traced by requests instrumentation
        logger.info("Calling payment service")
        response1 = requests.get('https://httpbin.org/delay/1', timeout=10)
        logger.info(f"Payment service responded: {response1.status_code}")
        
        logger.info("Calling inventory service") 
        response2 = requests.get('https://httpbin.org/json', timeout=5)
        logger.info(f"Inventory service responded: {response2.status_code}")
        
        # Process responses
        logger.info("Processing external service responses")
        process_business_logic("external_data_processing", "high")
        
        return jsonify({
            'status': 'success',
            'payment_service': {'status': response1.status_code},
            'inventory_service': {'status': response2.status_code}
        })
        
    except Exception as e:
        logger.error(f"External service call failed: {str(e)}")
        app_metrics['total_errors'] += 1
        return jsonify({'error': 'External service call failed'}), 500

@app.route('/health')
def health_check():
    """Health check - automatically traced"""
    logger.info("Health check requested")
    
    # Check database connection
    simulate_database_operation("health_check", (0.01, 0.03))
    
    # Check cache connection  
    time.sleep(random.uniform(0.005, 0.015))
    logger.info("Cache health check passed")
    
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

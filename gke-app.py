#!/usr/bin/env python3

import http.server
import socketserver
import json
import time
import random
import threading
import requests
import logging
import os
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynatraceTestHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)
        
        logger.info(f"Received GET request: {path}")
        
        if path == '/':
            self.send_hello_world()
        elif path == '/health':
            self.send_health()
        elif path == '/work':
            self.send_work()
        elif path == '/external':
            self.send_external_call()
        elif path == '/error':
            self.send_error()
        else:
            self.send_404()
    
    def send_hello_world(self):
        """Simple hello world response"""
        response_data = {
            "message": "Hello World from Dynatrace Test App!",
            "timestamp": time.time(),
            "hostname": os.environ.get('HOSTNAME', 'unknown'),
            "pid": os.getpid()
        }
        
        self.send_json_response(response_data)
    
    def send_health(self):
        """Health check endpoint"""
        response_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - start_time
        }
        
        self.send_json_response(response_data)
    
    def send_work(self):
        """Simulate some work to generate traces"""
        logger.info("Performing work simulation")
        
        # Simulate CPU work
        start = time.time()
        result = 0
        for i in range(100000):
            result += i * i
        
        # Random delay
        time.sleep(random.uniform(0.1, 0.5))
        
        duration = time.time() - start
        
        response_data = {
            "message": "Work completed",
            "duration": duration,
            "result": result,
            "timestamp": time.time()
        }
        
        logger.info(f"Work completed in {duration:.3f} seconds")
        self.send_json_response(response_data)
    
    def send_external_call(self):
        """Make external HTTP call"""
        logger.info("Making external API call")
        
        try:
            response = requests.get('https://httpbin.org/json', timeout=5)
            response_data = {
                "message": "External call successful",
                "status_code": response.status_code,
                "external_data": response.json(),
                "timestamp": time.time()
            }
            self.send_json_response(response_data)
        except Exception as e:
            logger.error(f"External call failed: {str(e)}")
            error_data = {
                "message": "External call failed",
                "error": str(e),
                "timestamp": time.time()
            }
            self.send_json_response(error_data, status=500)
    
    def send_error(self):
        """Generate an error for testing"""
        logger.error("Generating test error")
        
        # This will cause an exception
        try:
            x = 1 / 0
        except Exception as e:
            error_data = {
                "message": "Test error generated",
                "error": str(e),
                "timestamp": time.time()
            }
            self.send_json_response(error_data, status=500)
    
    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_data = {
            "message": "Not Found",
            "path": self.path,
            "timestamp": time.time()
        }
        
        self.wfile.write(json.dumps(response_data).encode())
    
    def send_json_response(self, data, status=200):
        """Helper to send JSON response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode())
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def background_worker():
    """Background thread that does periodic work"""
    while True:
        logger.info("Background worker running")
        time.sleep(30)
        
        # Simulate some background processing
        time.sleep(random.uniform(0.1, 0.3))

def main():
    global start_time
    start_time = time.time()
    
    # Get port from environment or default to 8000
    port = int(os.environ.get('PORT', 8000))
    
    # Start background worker thread
    worker_thread = threading.Thread(target=background_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Create and start server
    with socketserver.TCPServer(("", port), DynatraceTestHandler) as httpd:
        logger.info(f"Server starting on port {port}")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info("Available endpoints:")
        logger.info("  GET /         - Hello World")
        logger.info("  GET /health   - Health check")
        logger.info("  GET /work     - Simulate work")
        logger.info("  GET /external - External API call")
        logger.info("  GET /error    - Generate error")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
            httpd.shutdown()

if __name__ == "__main__":
    main()

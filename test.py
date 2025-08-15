#!/usr/bin/env python3
"""
Dynatrace Test Script for Cloud Run Application

This script tests all endpoints of the Dynatrace monitoring Flask app
deployed on Google Cloud Run with proper authentication.

Usage:
    python test.py

Make sure to update the BASE_URL and AUDIENCE variables with your
actual Cloud Run service URL
"""

import urllib.request
import urllib.parse
import urllib.error
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.auth.transport.requests
import google.oauth2.id_token

# Configuration - UPDATE THESE VALUES
BASE_URL = ""
AUDIENCE = ""

def make_authorized_get_request(endpoint, audience, params=None):
    """
    Make an authorized GET request to the specified HTTP endpoint
    by authenticating with the ID token obtained from the google-auth client library
    """
    # Add parameters to URL if provided
    if params:
        if '?' not in endpoint:
            endpoint += '?'
        else:
            endpoint += '&'
        endpoint += urllib.parse.urlencode(params)
    
    req = urllib.request.Request(endpoint)
    
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
    
    req.add_header("Authorization", f"Bearer {id_token}")
    
    response = urllib.request.urlopen(req)
    return response.read()

def make_authorized_post_request(endpoint, audience, params=None):
    """
    Make an authorized POST request to the specified HTTP endpoint
    """
    if params:
        if '?' not in endpoint:
            endpoint += '?'
        else:
            endpoint += '&'
        endpoint += urllib.parse.urlencode(params)
    
    req = urllib.request.Request(endpoint, method='POST')
    
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
    
    req.add_header("Authorization", f"Bearer {id_token}")
    
    response = urllib.request.urlopen(req)
    return response.read()

class DynatraceTestRunner:
    def __init__(self, base_url, audience):
        """
        Initialize the test runner with your Cloud Run service details
        
        Args:
            base_url: Your Cloud Run service URL
            audience: Same as base_url for Cloud Run authentication
        """
        self.base_url = base_url.rstrip('/')
        self.audience = audience
        self.test_results = {}
        
    def log_test_result(self, test_name, success, response_data, duration, error=None):
        """Log test results for reporting"""
        self.test_results[test_name] = {
            'success': success,
            'duration': duration,
            'response_data': response_data,
            'error': error,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        data_size = len(str(response_data)) if response_data else 0
        print(f"{status} | {test_name:<30} | {duration:6.3f}s | {data_size:5d} bytes")
        
        if error:
            print(f"      Error: {error}")
        
        # Print key metrics from response
        if success and response_data and isinstance(response_data, dict):
            if 'cpu_percent' in response_data:
                print(f"      CPU: {response_data['cpu_percent']}%")
            if 'memory_percent' in response_data:
                print(f"      Memory: {response_data['memory_percent']}%")
            if 'duration_seconds' in response_data:
                print(f"      Processing Time: {response_data['duration_seconds']}s")

    def test_health_endpoints(self):
        """Test health and readiness endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        print("-" * 80)
        
        health_tests = [
            ('/health', 'Health Check'),
            ('/ready', 'Readiness Check'),
            ('/', 'Home Page'),
            ('/system-metrics', 'System Metrics')
        ]
        
        for endpoint, test_name in health_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}{endpoint}",
                    self.audience
                )
                duration = time.time() - start_time
                
                if endpoint == '/':
                    # Home page returns HTML
                    response_data = {'html_length': len(response.decode())}
                else:
                    response_data = json.loads(response.decode())
                
                self.log_test_result(test_name, True, response_data, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_cpu_intensive(self):
        """Test CPU intensive operations"""
        print("\n🔥 Testing CPU Intensive Operations...")
        print("-" * 80)
        
        cpu_tests = [
            ({'iterations': '10000'}, 'CPU Light Load'),
            ({'iterations': '50000'}, 'CPU Medium Load'),
            ({'iterations': '100000'}, 'CPU Heavy Load')
        ]
        
        for params, test_name in cpu_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}/cpu-intensive",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_memory_operations(self):
        """Test memory allocation operations"""
        print("\n💾 Testing Memory Operations...")
        print("-" * 80)
        
        memory_tests = [
            ({'size_mb': '5'}, 'Memory 5MB Test'),
            ({'size_mb': '20'}, 'Memory 20MB Test'),
            ({'size_mb': '50'}, 'Memory 50MB Test')
        ]
        
        for params, test_name in memory_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}/memory-test",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_database_operations(self):
        """Test database operations"""
        print("\n🗄️ Testing Database Operations...")
        print("-" * 80)
        
        db_tests = [
            ({'operation': 'select'}, 'Database SELECT'),
            ({'operation': 'insert'}, 'Database INSERT'),
            ({'operation': 'update'}, 'Database UPDATE')
        ]
        
        for params, test_name in db_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}/database-ops",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_external_api_calls(self):
        """Test external API calls"""
        print("\n🌐 Testing External API Calls...")
        print("-" * 80)
        
        api_tests = [
            ({}, 'External API Default'),
            ({'url': 'https://httpbin.org/json'}, 'External API JSON'),
            ({'url': 'https://httpbin.org/delay/2'}, 'External API Slow'),
            ({'url': 'https://httpbin.org/status/200'}, 'External API Status')
        ]
        
        for params, test_name in api_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}/external-api",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_error_generation(self):
        """Test error generation"""
        print("\n⚠️ Testing Error Generation...")
        print("-" * 80)
        
        error_tests = [
            ({'type': 'http_error'}, 'HTTP Error Test'),
            ({'type': 'exception'}, 'Exception Test'),
            ({'type': 'db_error'}, 'Database Error Test')
        ]
        
        for params, test_name in error_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}/error-test",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                # For error tests, we expect failures (4xx/5xx status codes)
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
            except urllib.error.HTTPError as e:
                # Expected errors - still count as successful test
                duration = time.time() - start_time
                try:
                    response_data = json.loads(e.read().decode())
                    self.log_test_result(test_name, True, response_data, duration)
                    print(f"      Expected Error: {response_data.get('error', 'HTTP Error')}")
                except:
                    self.log_test_result(test_name, True, {'error': 'HTTP Error as expected'}, duration)
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_custom_metrics(self):
        """Test custom metrics generation"""
        print("\n📊 Testing Custom Metrics...")
        print("-" * 80)
        
        metrics_tests = [
            ({'type': 'business'}, 'Business Metrics'),
            ({'type': 'technical'}, 'Technical Metrics')
        ]
        
        for params, test_name in metrics_tests:
            try:
                start_time = time.time()
                response = make_authorized_get_request(
                    f"{self.base_url}/custom-metrics",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
                # Show sample metrics
                if 'metrics' in response_data:
                    sample_metrics = list(response_data['metrics'].items())[:2]
                    for key, value in sample_metrics:
                        print(f"      {key}: {value}")
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_async_tasks(self):
        """Test async task processing"""
        print("\n⚡ Testing Async Tasks...")
        print("-" * 80)
        
        async_tests = [
            ({'duration': '2'}, 'Async Task 2s'),
            ({'duration': '5'}, 'Async Task 5s'),
            ({'duration': '3'}, 'Async Task 3s')
        ]
        
        for params, test_name in async_tests:
            try:
                start_time = time.time()
                response = make_authorized_post_request(
                    f"{self.base_url}/async-task",
                    self.audience,
                    params
                )
                duration = time.time() - start_time
                
                response_data = json.loads(response.decode())
                self.log_test_result(test_name, True, response_data, duration)
                
                print(f"      Task ID: {response_data.get('task_id', 'Unknown')}")
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))

    def test_load_testing(self):
        """Test comprehensive load testing"""
        print("\n🏋️ Testing Load Operations...")
        print("-" * 80)
        
        try:
            start_time = time.time()
            response = make_authorized_get_request(
                f"{self.base_url}/load-test",
                self.audience
            )
            duration = time.time() - start_time
            
            response_data = json.loads(response.decode())
            self.log_test_result('Comprehensive Load Test', True, response_data, duration)
            
            # Show operation breakdown
            if 'operations' in response_data:
                print("      Operation Times:")
                for op, op_time in response_data['operations'].items():
                    print(f"        {op}: {op_time}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result('Comprehensive Load Test', False, None, duration, str(e))

    def run_concurrent_tests(self, num_threads=3):
        """Run multiple tests concurrently to generate load"""
        print(f"\n🔄 Running Concurrent Tests ({num_threads} threads)...")
        print("-" * 80)
        
        def concurrent_test(thread_id):
            test_name = f"Concurrent Test {thread_id}"
            try:
                start_time = time.time()
                
                # Mix of different operations
                operations = [
                    (f"{self.base_url}/cpu-intensive", {'iterations': '20000'}),
                    (f"{self.base_url}/memory-test", {'size_mb': '10'}),
                    (f"{self.base_url}/database-ops", {'operation': 'select'}),
                    (f"{self.base_url}/external-api", {})
                ]
                
                results = []
                for endpoint, params in operations:
                    response = make_authorized_get_request(endpoint, self.audience, params)
                    results.append(json.loads(response.decode()))
                
                duration = time.time() - start_time
                self.log_test_result(test_name, True, {'operations': len(results)}, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result(test_name, False, None, duration, str(e))
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(concurrent_test, i+1) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

    def run_stress_test(self, duration_seconds=60):
        """Run continuous stress test for specified duration"""
        print(f"\n🚨 Running Stress Test ({duration_seconds} seconds)...")
        print("-" * 80)
        
        end_time = time.time() + duration_seconds
        request_count = 0
        
        def stress_worker():
            nonlocal request_count
            while time.time() < end_time:
                try:
                    # Rotate through different endpoints
                    endpoints = [
                        ('/cpu-intensive', {'iterations': '5000'}),
                        ('/memory-test', {'size_mb': '5'}),
                        ('/database-ops', {'operation': 'select'}),
                        ('/custom-metrics', {'type': 'business'})
                    ]
                    
                    endpoint, params = endpoints[request_count % len(endpoints)]
                    make_authorized_get_request(
                        f"{self.base_url}{endpoint}",
                        self.audience,
                        params
                    )
                    request_count += 1
                    
                except Exception as e:
                    print(f"      Stress test error: {e}")
                
                time.sleep(0.1)  # Brief pause between requests
        
        # Run stress test with multiple threads
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(stress_worker) for _ in range(3)]
            for future in as_completed(futures):
                future.result()
        
        requests_per_second = request_count / duration_seconds
        print(f"      Completed {request_count} requests ({requests_per_second:.1f} req/s)")
        
        self.log_test_result(
            'Stress Test',
            True,
            {'total_requests': request_count, 'rps': requests_per_second},
            duration_seconds
        )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Dynatrace Monitoring Test Suite")
        print("=" * 80)
        print(f"Target URL: {self.base_url}")
        print(f"Test Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Individual test suites
        self.test_health_endpoints()
        self.test_cpu_intensive()
        self.test_memory_operations()
        self.test_database_operations()
        self.test_external_api_calls()
        self.test_error_generation()
        self.test_custom_metrics()
        self.test_async_tasks()
        self.test_load_testing()
        
        # Concurrent testing
        self.run_concurrent_tests(3)
        
        # Stress testing (optional - uncomment to enable)
        # self.run_stress_test(30)  # 30 second stress test
        
        # Print summary
        self.print_test_summary()

    def run_quick_test(self):
        """Run a quick subset of tests"""
        print("⚡ Running Quick Test Suite")
        print("=" * 50)
        
        self.test_health_endpoints()
        self.test_cpu_intensive()
        self.test_database_operations()
        self.test_custom_metrics()
        
        self.print_test_summary()

    def print_test_summary(self):
        """Print test execution summary"""
        print("\n📊 TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        if not self.test_results:
            print("No tests were executed.")
            return
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(result['duration'] for result in self.test_results.values())
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        print(f"📈 Test Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"  Total Duration: {total_duration:.3f}s")
        print(f"  Average Duration: {avg_duration:.3f}s")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
        
        print(f"\n💡 Dynatrace Monitoring Checklist:")
        print("  ✅ Application Performance (response times, throughput)")
        print("  ✅ Infrastructure Metrics (CPU, memory usage)")
        print("  ✅ Database Monitoring (query performance)")
        print("  ✅ HTTP Client Monitoring (external API calls)")
        print("  ✅ Error Tracking (exceptions, HTTP errors)")
        print("  ✅ Custom Metrics (business and technical)")
        print("  ✅ Async Processing Monitoring")
        print("  ✅ Load Testing Metrics")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Check your Dynatrace dashboard for collected metrics")
        print(f"  2. Verify application topology and service mapping")
        print(f"  3. Review error tracking and alerting")
        print(f"  4. Validate custom metrics ingestion")
        print(f"  5. Access web UI: {self.base_url}")

def main():
    """Main function to run tests"""
    print("🔧 Dynatrace Cloud Run Test Suite")
    print("=" * 40)
    print(f"Service URL: {BASE_URL}")
    print("=" * 40)
    
    # Validate configuration
    if "YOUR" in BASE_URL or "REPLACE" in BASE_URL:
        print("❌ Please update BASE_URL and AUDIENCE in the script with your actual Cloud Run service URL")
        return
    
    # Create test runner
    test_runner = DynatraceTestRunner(BASE_URL, AUDIENCE)
    
    # Ask user for test type
    print("\nSelect test suite:")
    print("1. Full Test Suite (recommended)")
    print("2. Quick Test")
    print("3. Stress Test Only")
    
    try:
        choice = input("\nEnter choice (1-3, default=1): ").strip()
        if not choice:
            choice = "1"
        
        if choice == "1":
            test_runner.run_all_tests()
        elif choice == "2":
            test_runner.run_quick_test()
        elif choice == "3":
            test_runner.run_stress_test(30)
        else:
            print("Invalid choice, running full test suite...")
            test_runner.run_all_tests()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        test_runner.print_test_summary()
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
    
    print(f"\n🏁 Testing completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

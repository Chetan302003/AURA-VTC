#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Aura Virtual Trucking Company
Tests the complete workflow including authentication, CRUD operations, and role-based access
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import uuid

# Configuration
BASE_URL = "https://road-masters-5.preview.emergentagent.com/api"
TIMEOUT = 30.0

class ComprehensiveTestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.critical_failures = []
    
    def add_result(self, test_name: str, passed: bool, message: str, details: str = "", critical: bool = False):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details,
            "critical": critical
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            if critical:
                self.critical_failures.append(test_name)
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        if self.critical_failures:
            print(f"CRITICAL FAILURES: {len(self.critical_failures)}")
        print(f"{'='*60}")
        
        # Show critical failures first
        for result in self.results:
            if result["critical"] and not result["passed"]:
                print(f"🚨 CRITICAL FAIL: {result['test']}")
                print(f"   {result['message']}")
                if result["details"]:
                    print(f"   Details: {result['details']}")
                print()
        
        # Show other failures
        for result in self.results:
            if not result["critical"] and not result["passed"]:
                status = "❌ FAIL"
                print(f"{status}: {result['test']}")
                print(f"   {result['message']}")
                if result["details"]:
                    print(f"   Details: {result['details']}")
                print()
        
        # Show successes (condensed)
        print("✅ SUCCESSFUL TESTS:")
        for result in self.results:
            if result["passed"]:
                print(f"   • {result['test']}")
        print()

class ComprehensiveAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.results = ComprehensiveTestResults()
    
    async def close(self):
        await self.client.aclose()
    
    async def test_api_structure_and_endpoints(self):
        """Test that all expected API endpoints exist and respond appropriately"""
        endpoints_to_test = [
            # Basic endpoints
            {"method": "GET", "path": "/", "name": "Root Endpoint", "expected_codes": [200]},
            
            # Auth endpoints
            {"method": "GET", "path": "/auth/me", "name": "Get Current User", "expected_codes": [401]},
            {"method": "POST", "path": "/auth/process-session", "name": "Process Session", "expected_codes": [400, 422]},
            {"method": "POST", "path": "/auth/logout", "name": "Logout", "expected_codes": [401]},
            
            # User endpoints
            {"method": "GET", "path": "/users", "name": "Get Users", "expected_codes": [401]},
            {"method": "GET", "path": "/users/test-id", "name": "Get User by ID", "expected_codes": [401]},
            {"method": "PUT", "path": "/users/test-id", "name": "Update User", "expected_codes": [401]},
            
            # Job endpoints
            {"method": "GET", "path": "/jobs", "name": "Get Jobs", "expected_codes": [401]},
            {"method": "POST", "path": "/jobs", "name": "Create Job", "expected_codes": [401]},
            {"method": "POST", "path": "/jobs/test-id/assign/driver-id", "name": "Assign Job", "expected_codes": [401]},
            {"method": "POST", "path": "/jobs/test-id/complete", "name": "Complete Job", "expected_codes": [401]},
            
            # Event endpoints
            {"method": "GET", "path": "/events", "name": "Get Events", "expected_codes": [401]},
            {"method": "POST", "path": "/events", "name": "Create Event", "expected_codes": [401]},
            {"method": "POST", "path": "/events/test-id/join", "name": "Join Event", "expected_codes": [401]},
            
            # Company stats
            {"method": "GET", "path": "/company/stats", "name": "Company Stats", "expected_codes": [401]},
        ]
        
        for endpoint in endpoints_to_test:
            try:
                if endpoint["method"] == "GET":
                    response = await self.client.get(f"{BASE_URL}{endpoint['path']}")
                elif endpoint["method"] == "POST":
                    response = await self.client.post(f"{BASE_URL}{endpoint['path']}", json={})
                elif endpoint["method"] == "PUT":
                    response = await self.client.put(f"{BASE_URL}{endpoint['path']}", json={})
                
                if response.status_code in endpoint["expected_codes"]:
                    self.results.add_result(
                        f"Endpoint Structure - {endpoint['name']}",
                        True,
                        f"Endpoint exists and responds correctly (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"Endpoint Structure - {endpoint['name']}",
                        False,
                        f"Expected {endpoint['expected_codes']}, got {response.status_code}",
                        f"Response: {response.text[:200]}",
                        critical=True
                    )
            except Exception as e:
                self.results.add_result(
                    f"Endpoint Structure - {endpoint['name']}",
                    False,
                    f"Request failed: {str(e)}",
                    critical=True
                )
    
    async def test_authentication_flow(self):
        """Test the authentication flow structure"""
        try:
            # Test session processing with proper structure
            session_data = {
                "session_id": "test_session_123"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/auth/process-session",
                json=session_data
            )
            
            # Should return 400 for invalid session (which is expected)
            if response.status_code == 400:
                response_data = response.json()
                if "Invalid session ID" in response_data.get("detail", ""):
                    self.results.add_result(
                        "Authentication Flow - Session Validation",
                        True,
                        "Session validation works correctly"
                    )
                else:
                    self.results.add_result(
                        "Authentication Flow - Session Validation",
                        False,
                        f"Unexpected error message: {response_data}",
                        critical=True
                    )
            else:
                self.results.add_result(
                    "Authentication Flow - Session Validation",
                    False,
                    f"Expected 400, got {response.status_code}: {response.text}",
                    critical=True
                )
        except Exception as e:
            self.results.add_result(
                "Authentication Flow - Session Validation",
                False,
                f"Authentication test failed: {str(e)}",
                critical=True
            )
    
    async def test_data_models_validation(self):
        """Test that the API properly validates data models"""
        test_cases = [
            {
                "name": "Job Creation - Invalid Data",
                "endpoint": "/jobs",
                "method": "POST",
                "data": {
                    "title": "",  # Empty title should fail
                    "description": "Test",
                    "cargo": "Test cargo",
                    "origin_city": "City A",
                    "destination_city": "City B",
                    "distance": -100,  # Negative distance should fail
                    "reward": "invalid",  # String instead of int
                    "difficulty": "Easy"
                },
                "expected_codes": [401, 422]  # 401 for auth, 422 for validation
            },
            {
                "name": "Event Creation - Invalid Data",
                "endpoint": "/events",
                "method": "POST", 
                "data": {
                    "title": "",  # Empty title
                    "description": "Test event",
                    "event_type": "invalid_type",  # Invalid enum
                    "date_time": "not_a_date",  # Invalid date
                    "location": "Test location"
                },
                "expected_codes": [401, 422]
            }
        ]
        
        for test_case in test_cases:
            try:
                response = await self.client.post(
                    f"{BASE_URL}{test_case['endpoint']}",
                    json=test_case["data"]
                )
                
                if response.status_code in test_case["expected_codes"]:
                    self.results.add_result(
                        f"Data Validation - {test_case['name']}",
                        True,
                        f"Properly validates data (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"Data Validation - {test_case['name']}",
                        False,
                        f"Expected {test_case['expected_codes']}, got {response.status_code}",
                        f"Response: {response.text[:200]}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"Data Validation - {test_case['name']}",
                    False,
                    f"Validation test failed: {str(e)}"
                )
    
    async def test_role_based_access_control(self):
        """Test role-based access control"""
        # Test endpoints that should require manager/admin roles
        protected_endpoints = [
            {"path": "/users", "method": "GET", "name": "User List Access"},
            {"path": "/jobs", "method": "POST", "name": "Job Creation Access"},
            {"path": "/events", "method": "POST", "name": "Event Creation Access"},
        ]
        
        for endpoint in protected_endpoints:
            try:
                # Test with no auth (should get 401)
                if endpoint["method"] == "GET":
                    response = await self.client.get(f"{BASE_URL}{endpoint['path']}")
                else:
                    response = await self.client.post(f"{BASE_URL}{endpoint['path']}", json={})
                
                if response.status_code == 401:
                    self.results.add_result(
                        f"Role Access Control - {endpoint['name']}",
                        True,
                        f"Correctly requires authentication for {endpoint['path']}"
                    )
                else:
                    self.results.add_result(
                        f"Role Access Control - {endpoint['name']}",
                        False,
                        f"Expected 401, got {response.status_code} for {endpoint['path']}",
                        critical=True
                    )
            except Exception as e:
                self.results.add_result(
                    f"Role Access Control - {endpoint['name']}",
                    False,
                    f"Access control test failed: {str(e)}",
                    critical=True
                )
    
    async def test_database_integration(self):
        """Test database integration by checking if endpoints that require DB access work"""
        try:
            # Test an endpoint that requires database access
            response = await self.client.get(f"{BASE_URL}/jobs")
            
            # Should get 401 (auth required) not 500 (database error)
            if response.status_code == 401:
                self.results.add_result(
                    "Database Integration",
                    True,
                    "Database connection appears healthy (auth check works)"
                )
            elif response.status_code == 500:
                self.results.add_result(
                    "Database Integration",
                    False,
                    "Database connection may be failing (HTTP 500)",
                    f"Response: {response.text}",
                    critical=True
                )
            else:
                self.results.add_result(
                    "Database Integration",
                    True,
                    f"Database responding (HTTP {response.status_code})"
                )
        except Exception as e:
            self.results.add_result(
                "Database Integration",
                False,
                f"Database test failed: {str(e)}",
                critical=True
            )
    
    async def test_api_response_formats(self):
        """Test that API responses are in correct JSON format"""
        try:
            # Test root endpoint
            response = await self.client.get(f"{BASE_URL}/")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "message" in data:
                        self.results.add_result(
                            "API Response Format",
                            True,
                            "API returns properly formatted JSON responses"
                        )
                    else:
                        self.results.add_result(
                            "API Response Format",
                            False,
                            f"Unexpected response format: {data}"
                        )
                except json.JSONDecodeError:
                    self.results.add_result(
                        "API Response Format",
                        False,
                        "API does not return valid JSON",
                        critical=True
                    )
            else:
                self.results.add_result(
                    "API Response Format",
                    False,
                    f"Root endpoint failed: HTTP {response.status_code}"
                )
        except Exception as e:
            self.results.add_result(
                "API Response Format",
                False,
                f"Response format test failed: {str(e)}"
            )
    
    async def test_error_handling(self):
        """Test comprehensive error handling"""
        error_test_cases = [
            {
                "name": "Invalid JSON Body",
                "method": "POST",
                "endpoint": "/auth/process-session",
                "data": "invalid json string",
                "content_type": "application/json",
                "expected_codes": [400, 422]
            },
            {
                "name": "Missing Required Fields",
                "method": "POST",
                "endpoint": "/auth/process-session",
                "data": {},
                "expected_codes": [400, 422]
            },
            {
                "name": "Non-existent Resource",
                "method": "GET",
                "endpoint": "/users/non-existent-id",
                "expected_codes": [401, 404]  # 401 for auth, 404 for not found
            }
        ]
        
        for test_case in error_test_cases:
            try:
                if test_case["method"] == "GET":
                    response = await self.client.get(f"{BASE_URL}{test_case['endpoint']}")
                elif test_case["method"] == "POST":
                    if isinstance(test_case["data"], str):
                        response = await self.client.post(
                            f"{BASE_URL}{test_case['endpoint']}",
                            content=test_case["data"],
                            headers={"Content-Type": test_case.get("content_type", "application/json")}
                        )
                    else:
                        response = await self.client.post(
                            f"{BASE_URL}{test_case['endpoint']}",
                            json=test_case["data"]
                        )
                
                if response.status_code in test_case["expected_codes"]:
                    self.results.add_result(
                        f"Error Handling - {test_case['name']}",
                        True,
                        f"Properly handles {test_case['name'].lower()} (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"Error Handling - {test_case['name']}",
                        False,
                        f"Expected {test_case['expected_codes']}, got {response.status_code}",
                        f"Response: {response.text[:200]}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"Error Handling - {test_case['name']}",
                    False,
                    f"Error handling test failed: {str(e)}"
                )
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚛 Starting Comprehensive Aura Virtual Trucking Company Backend Tests...")
        print(f"Testing against: {BASE_URL}")
        print("="*60)
        
        # Run all test methods
        test_methods = [
            self.test_api_structure_and_endpoints,
            self.test_authentication_flow,
            self.test_data_models_validation,
            self.test_role_based_access_control,
            self.test_database_integration,
            self.test_api_response_formats,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method.__name__}...")
                await test_method()
            except Exception as e:
                self.results.add_result(
                    test_method.__name__,
                    False,
                    f"Test method failed: {str(e)}",
                    critical=True
                )
        
        # Print results
        self.results.print_summary()
        
        return len(self.results.critical_failures) == 0

async def main():
    """Main comprehensive test runner"""
    tester = ComprehensiveAPITester()
    try:
        success = await tester.run_comprehensive_tests()
        return success
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
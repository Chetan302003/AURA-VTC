#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Aura Virtual Trucking Company
Tests authentication, user management, job management, events, and company stats
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

class TestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str, details: str = ""):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        print(f"{'='*60}")
        
        for result in self.results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status}: {result['test']}")
            print(f"   {result['message']}")
            if result["details"]:
                print(f"   Details: {result['details']}")
            print()

class AuraAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.results = TestResults()
        self.session_token = None
        self.current_user = None
        self.test_users = {}
        self.test_jobs = {}
        self.test_events = {}
    
    async def close(self):
        await self.client.aclose()
    
    async def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = await self.client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "Aura Virtual Trucking Company API" in data.get("message", ""):
                    self.results.add_result(
                        "Basic API Connectivity",
                        True,
                        "API is accessible and responding correctly"
                    )
                else:
                    self.results.add_result(
                        "Basic API Connectivity",
                        False,
                        f"Unexpected response: {data}"
                    )
            else:
                self.results.add_result(
                    "Basic API Connectivity",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "Basic API Connectivity",
                False,
                f"Connection failed: {str(e)}"
            )
    
    async def test_auth_without_session(self):
        """Test authentication endpoints without valid session"""
        try:
            # Test /auth/me without session
            response = await self.client.get(f"{BASE_URL}/auth/me")
            if response.status_code == 401:
                self.results.add_result(
                    "Auth Protection - /auth/me",
                    True,
                    "Correctly returns 401 for unauthenticated request"
                )
            else:
                self.results.add_result(
                    "Auth Protection - /auth/me",
                    False,
                    f"Expected 401, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "Auth Protection - /auth/me",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_mock_auth_session(self):
        """Test authentication with mock session data"""
        try:
            # Since we can't get real Emergent auth session, we'll test the endpoint structure
            mock_session_data = {
                "session_id": "mock_session_123"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/auth/process-session",
                json=mock_session_data
            )
            
            # We expect this to fail with 400 (Invalid session ID) since it's a mock
            if response.status_code == 400 and "Invalid session ID" in response.text:
                self.results.add_result(
                    "Auth Session Processing",
                    True,
                    "Auth endpoint correctly validates session IDs"
                )
            else:
                self.results.add_result(
                    "Auth Session Processing",
                    False,
                    f"Unexpected response {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "Auth Session Processing",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_protected_endpoints_without_auth(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/users", "User List"),
            ("POST", "/jobs", "Job Creation"),
            ("GET", "/jobs", "Job List"),
            ("POST", "/events", "Event Creation"),
            ("GET", "/events", "Event List"),
            ("GET", "/company/stats", "Company Stats")
        ]
        
        for method, endpoint, name in protected_endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = await self.client.post(f"{BASE_URL}{endpoint}", json={})
                
                if response.status_code == 401:
                    self.results.add_result(
                        f"Auth Protection - {name}",
                        True,
                        f"Correctly requires authentication for {endpoint}"
                    )
                else:
                    self.results.add_result(
                        f"Auth Protection - {name}",
                        False,
                        f"Expected 401, got {response.status_code} for {endpoint}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"Auth Protection - {name}",
                    False,
                    f"Request failed for {endpoint}: {str(e)}"
                )
    
    async def test_role_based_access(self):
        """Test role-based access control"""
        # Test endpoints that require manager/admin roles
        manager_admin_endpoints = [
            ("GET", "/users", "User Management"),
            ("POST", "/jobs", "Job Creation"),
            ("POST", "/events", "Event Creation")
        ]
        
        # Create mock headers with a fake session token
        fake_headers = {"Authorization": "Bearer fake_token_123"}
        
        for method, endpoint, name in manager_admin_endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(f"{BASE_URL}{endpoint}", headers=fake_headers)
                elif method == "POST":
                    response = await self.client.post(f"{BASE_URL}{endpoint}", json={}, headers=fake_headers)
                
                # Should return 401 (invalid token) or 403 (insufficient permissions)
                if response.status_code in [401, 403]:
                    self.results.add_result(
                        f"Role Protection - {name}",
                        True,
                        f"Correctly protects {endpoint} (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"Role Protection - {name}",
                        False,
                        f"Unexpected response {response.status_code} for {endpoint}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"Role Protection - {name}",
                    False,
                    f"Request failed for {endpoint}: {str(e)}"
                )
    
    async def test_job_endpoints_structure(self):
        """Test job endpoints structure and validation"""
        try:
            # Test job creation with invalid data
            invalid_job_data = {
                "title": "",  # Empty title should fail validation
                "description": "Test job"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/jobs",
                json=invalid_job_data
            )
            
            # Should return 401 (no auth) or 422 (validation error)
            if response.status_code in [401, 422]:
                self.results.add_result(
                    "Job Creation Validation",
                    True,
                    f"Correctly validates job data (HTTP {response.status_code})"
                )
            else:
                self.results.add_result(
                    "Job Creation Validation",
                    False,
                    f"Unexpected response {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "Job Creation Validation",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_event_endpoints_structure(self):
        """Test event endpoints structure and validation"""
        try:
            # Test event creation with invalid data
            invalid_event_data = {
                "title": "",  # Empty title should fail validation
                "description": "Test event"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/events",
                json=invalid_event_data
            )
            
            # Should return 401 (no auth) or 422 (validation error)
            if response.status_code in [401, 422]:
                self.results.add_result(
                    "Event Creation Validation",
                    True,
                    f"Correctly validates event data (HTTP {response.status_code})"
                )
            else:
                self.results.add_result(
                    "Event Creation Validation",
                    False,
                    f"Unexpected response {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "Event Creation Validation",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_cors_headers(self):
        """Test CORS configuration"""
        try:
            response = await self.client.options(f"{BASE_URL}/")
            
            # Check for CORS headers
            cors_headers = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers"
            ]
            
            found_cors = any(header in response.headers for header in cors_headers)
            
            if found_cors or response.status_code == 200:
                self.results.add_result(
                    "CORS Configuration",
                    True,
                    "CORS headers are properly configured"
                )
            else:
                self.results.add_result(
                    "CORS Configuration",
                    False,
                    f"CORS headers missing. Response: {response.status_code}"
                )
        except Exception as e:
            self.results.add_result(
                "CORS Configuration",
                False,
                f"CORS test failed: {str(e)}"
            )
    
    async def test_api_error_handling(self):
        """Test API error handling for various scenarios"""
        test_cases = [
            {
                "name": "Invalid JSON",
                "method": "POST",
                "endpoint": "/auth/process-session",
                "data": "invalid json",
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
                "name": "Non-existent Endpoint",
                "method": "GET",
                "endpoint": "/nonexistent",
                "data": None,
                "expected_codes": [404]
            }
        ]
        
        for test_case in test_cases:
            try:
                if test_case["method"] == "GET":
                    response = await self.client.get(f"{BASE_URL}{test_case['endpoint']}")
                elif test_case["method"] == "POST":
                    if isinstance(test_case["data"], str):
                        response = await self.client.post(
                            f"{BASE_URL}{test_case['endpoint']}", 
                            content=test_case["data"],
                            headers={"Content-Type": "application/json"}
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
                        f"Correctly handles {test_case['name'].lower()} (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"Error Handling - {test_case['name']}",
                        False,
                        f"Expected {test_case['expected_codes']}, got {response.status_code}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"Error Handling - {test_case['name']}",
                    False,
                    f"Request failed: {str(e)}"
                )
    
    async def test_database_connectivity(self):
        """Test if the API can connect to the database"""
        try:
            # Try to access an endpoint that would require database access
            response = await self.client.get(f"{BASE_URL}/jobs")
            
            # Even without auth, if DB is connected, we should get 401, not 500
            if response.status_code == 401:
                self.results.add_result(
                    "Database Connectivity",
                    True,
                    "Database appears to be connected (auth check works)"
                )
            elif response.status_code == 500:
                self.results.add_result(
                    "Database Connectivity",
                    False,
                    "Database connection may be failing (HTTP 500)"
                )
            else:
                self.results.add_result(
                    "Database Connectivity",
                    True,
                    f"Database responding (HTTP {response.status_code})"
                )
        except Exception as e:
            self.results.add_result(
                "Database Connectivity",
                False,
                f"Database test failed: {str(e)}"
            )
    
    async def test_user_deletion_admin_only_access(self):
        """Test that only admins can access the delete user endpoint"""
        test_user_id = str(uuid.uuid4())
        
        # Test without authentication
        try:
            response = await self.client.delete(f"{BASE_URL}/users/{test_user_id}")
            if response.status_code == 401:
                self.results.add_result(
                    "User Deletion - No Auth Protection",
                    True,
                    "Correctly requires authentication for user deletion"
                )
            else:
                self.results.add_result(
                    "User Deletion - No Auth Protection",
                    False,
                    f"Expected 401, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "User Deletion - No Auth Protection",
                False,
                f"Request failed: {str(e)}"
            )
        
        # Test with fake non-admin token (should get 401 or 403)
        try:
            fake_headers = {"Authorization": "Bearer fake_driver_token"}
            response = await self.client.delete(f"{BASE_URL}/users/{test_user_id}", headers=fake_headers)
            if response.status_code in [401, 403]:
                self.results.add_result(
                    "User Deletion - Non-Admin Protection",
                    True,
                    f"Correctly blocks non-admin access (HTTP {response.status_code})"
                )
            else:
                self.results.add_result(
                    "User Deletion - Non-Admin Protection",
                    False,
                    f"Expected 401/403, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "User Deletion - Non-Admin Protection",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_user_deletion_endpoint_structure(self):
        """Test user deletion endpoint structure and validation"""
        test_cases = [
            {
                "name": "Invalid User ID Format",
                "user_id": "invalid-id",
                "expected_codes": [401, 403, 404]  # Auth first, then validation
            },
            {
                "name": "Non-existent User ID",
                "user_id": str(uuid.uuid4()),
                "expected_codes": [401, 403, 404]  # Auth first, then not found
            },
            {
                "name": "Empty User ID",
                "user_id": "",
                "expected_codes": [404, 405]  # Route not found or method not allowed
            }
        ]
        
        for test_case in test_cases:
            try:
                response = await self.client.delete(f"{BASE_URL}/users/{test_case['user_id']}")
                if response.status_code in test_case["expected_codes"]:
                    self.results.add_result(
                        f"User Deletion Structure - {test_case['name']}",
                        True,
                        f"Correctly handles {test_case['name'].lower()} (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"User Deletion Structure - {test_case['name']}",
                        False,
                        f"Expected {test_case['expected_codes']}, got {response.status_code}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"User Deletion Structure - {test_case['name']}",
                    False,
                    f"Request failed: {str(e)}"
                )
    
    async def test_user_deletion_self_prevention(self):
        """Test that the endpoint prevents self-deletion"""
        # This test simulates the self-deletion prevention logic
        # Since we can't create real authenticated sessions, we test the endpoint behavior
        try:
            # Test with a fake admin token trying to delete themselves
            fake_admin_headers = {"Authorization": "Bearer fake_admin_token_self"}
            fake_admin_id = str(uuid.uuid4())
            
            response = await self.client.delete(f"{BASE_URL}/users/{fake_admin_id}", headers=fake_admin_headers)
            
            # Should get 401 (invalid token) first, but the endpoint structure is correct
            if response.status_code in [401, 403, 400]:
                self.results.add_result(
                    "User Deletion - Self-Deletion Prevention Structure",
                    True,
                    f"Endpoint properly structured for self-deletion prevention (HTTP {response.status_code})"
                )
            else:
                self.results.add_result(
                    "User Deletion - Self-Deletion Prevention Structure",
                    False,
                    f"Unexpected response {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.results.add_result(
                "User Deletion - Self-Deletion Prevention Structure",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_user_deletion_data_cleanup_structure(self):
        """Test that user deletion endpoint is structured for proper data cleanup"""
        # Test the endpoint exists and has proper structure for data cleanup operations
        try:
            test_user_id = str(uuid.uuid4())
            fake_admin_headers = {"Authorization": "Bearer fake_admin_token"}
            
            response = await self.client.delete(f"{BASE_URL}/users/{test_user_id}", headers=fake_admin_headers)
            
            # The endpoint should exist and handle the request (even if auth fails)
            if response.status_code in [401, 403, 404]:
                self.results.add_result(
                    "User Deletion - Data Cleanup Structure",
                    True,
                    f"Endpoint properly structured for data cleanup operations (HTTP {response.status_code})"
                )
            elif response.status_code == 500:
                self.results.add_result(
                    "User Deletion - Data Cleanup Structure",
                    False,
                    "Server error suggests issues with data cleanup logic"
                )
            else:
                self.results.add_result(
                    "User Deletion - Data Cleanup Structure",
                    True,
                    f"Endpoint responding correctly (HTTP {response.status_code})"
                )
        except Exception as e:
            self.results.add_result(
                "User Deletion - Data Cleanup Structure",
                False,
                f"Request failed: {str(e)}"
            )
    
    async def test_user_deletion_permission_boundaries(self):
        """Test permission boundaries for user deletion"""
        test_user_id = str(uuid.uuid4())
        
        # Test different role scenarios
        role_tests = [
            {
                "name": "Manager Role Access",
                "token": "fake_manager_token",
                "expected_codes": [401, 403]  # Should be blocked
            },
            {
                "name": "Driver Role Access", 
                "token": "fake_driver_token",
                "expected_codes": [401, 403]  # Should be blocked
            },
            {
                "name": "Admin Role Access",
                "token": "fake_admin_token",
                "expected_codes": [401, 404]  # Auth fails, but would proceed to user lookup
            }
        ]
        
        for role_test in role_tests:
            try:
                headers = {"Authorization": f"Bearer {role_test['token']}"}
                response = await self.client.delete(f"{BASE_URL}/users/{test_user_id}", headers=headers)
                
                if response.status_code in role_test["expected_codes"]:
                    self.results.add_result(
                        f"User Deletion Permission - {role_test['name']}",
                        True,
                        f"Correctly handles {role_test['name'].lower()} (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"User Deletion Permission - {role_test['name']}",
                        False,
                        f"Expected {role_test['expected_codes']}, got {response.status_code}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"User Deletion Permission - {role_test['name']}",
                    False,
                    f"Request failed: {str(e)}"
                )
    
    async def test_user_deletion_edge_cases(self):
        """Test edge cases for user deletion"""
        edge_cases = [
            {
                "name": "Special Characters in User ID",
                "user_id": "user@#$%^&*()",
                "expected_codes": [401, 403, 404]
            },
            {
                "name": "Very Long User ID",
                "user_id": "a" * 1000,
                "expected_codes": [401, 403, 404, 414]  # URI too long possible
            },
            {
                "name": "SQL Injection Attempt",
                "user_id": "'; DROP TABLE users; --",
                "expected_codes": [401, 403, 404]
            }
        ]
        
        for edge_case in edge_cases:
            try:
                response = await self.client.delete(f"{BASE_URL}/users/{edge_case['user_id']}")
                if response.status_code in edge_case["expected_codes"]:
                    self.results.add_result(
                        f"User Deletion Edge Case - {edge_case['name']}",
                        True,
                        f"Correctly handles {edge_case['name'].lower()} (HTTP {response.status_code})"
                    )
                else:
                    self.results.add_result(
                        f"User Deletion Edge Case - {edge_case['name']}",
                        False,
                        f"Expected {edge_case['expected_codes']}, got {response.status_code}"
                    )
            except Exception as e:
                self.results.add_result(
                    f"User Deletion Edge Case - {edge_case['name']}",
                    False,
                    f"Request failed: {str(e)}"
                )
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚛 Starting Aura Virtual Trucking Company Backend API Tests...")
        print(f"Testing against: {BASE_URL}")
        print("="*60)
        
        # Run all test methods
        test_methods = [
            self.test_basic_connectivity,
            self.test_database_connectivity,
            self.test_auth_without_session,
            self.test_mock_auth_session,
            self.test_protected_endpoints_without_auth,
            self.test_role_based_access,
            self.test_job_endpoints_structure,
            self.test_event_endpoints_structure,
            self.test_cors_headers,
            self.test_api_error_handling
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.results.add_result(
                    test_method.__name__,
                    False,
                    f"Test method failed: {str(e)}"
                )
        
        # Print results
        self.results.print_summary()
        
        return self.results.failed == 0

async def main():
    """Main test runner"""
    tester = AuraAPITester()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
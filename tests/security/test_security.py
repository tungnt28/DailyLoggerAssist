"""
Security Tests - Daily Logger Assist

Tests for security vulnerabilities, authentication, authorization, and data protection.
"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.models.user import User


class TestSecurity:
    """Test suite for security vulnerabilities and protections."""

    @pytest.mark.security
    def test_sql_injection_protection(self, client: TestClient, authenticated_headers, malicious_payloads):
        """Test protection against SQL injection attacks."""
        
        sql_payloads = malicious_payloads["sql_injection"]
        
        for payload in sql_payloads:
            # Test in various endpoints that accept parameters
            endpoints = [
                f"/api/v1/data/work-items?search={payload}",
                f"/api/v1/reports?title={payload}",
                f"/api/v1/data/messages?content={payload}"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint, headers=authenticated_headers)
                
                # Should not return internal server error or expose SQL errors
                assert response.status_code != 500, f"SQL injection may be possible in {endpoint}"
                
                if response.status_code == 422:  # Validation error is acceptable
                    continue
                
                # Response should not contain SQL error messages
                response_text = response.text.lower()
                sql_error_indicators = ["sql", "syntax error", "mysql", "postgresql", "sqlite"]
                for indicator in sql_error_indicators:
                    assert indicator not in response_text, f"SQL error exposed in {endpoint}"

    @pytest.mark.security
    def test_xss_protection(self, client: TestClient, authenticated_headers, malicious_payloads):
        """Test protection against Cross-Site Scripting (XSS) attacks."""
        
        xss_payloads = malicious_payloads["xss"]
        
        for payload in xss_payloads:
            # Test XSS in POST requests
            test_data = {
                "description": payload,
                "title": f"Test report {payload}",
                "content": f"Report content with {payload}"
            }
            
            response = client.post(
                "/api/v1/reports",
                json=test_data,
                headers=authenticated_headers
            )
            
            # Should handle malicious input gracefully
            if response.status_code in [200, 201]:
                response_data = response.json()
                
                # Ensure XSS payload is properly escaped/sanitized
                for field in ["description", "title", "content"]:
                    if field in response_data:
                        field_value = str(response_data[field])
                        assert "<script>" not in field_value, f"XSS payload not sanitized in {field}"
                        assert "javascript:" not in field_value.lower(), f"XSS payload not sanitized in {field}"

    @pytest.mark.security
    def test_path_traversal_protection(self, client: TestClient, authenticated_headers, malicious_payloads):
        """Test protection against path traversal attacks."""
        
        path_payloads = malicious_payloads["path_traversal"]
        
        for payload in path_payloads:
            # Test path traversal in file-related endpoints
            endpoints = [
                f"/api/v1/reports/export?filename={payload}",
                f"/api/v1/data/export?path={payload}"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint, headers=authenticated_headers)
                
                # Should not return file contents or expose file system
                assert response.status_code != 200 or "root:" not in response.text, \
                    f"Path traversal possible in {endpoint}"
                
                # Should not expose internal file paths
                response_text = response.text.lower()
                sensitive_paths = ["/etc/passwd", "/windows/system32", "c:\\windows"]
                for path in sensitive_paths:
                    assert path not in response_text, f"Sensitive path exposed in {endpoint}"

    @pytest.mark.security
    def test_command_injection_protection(self, client: TestClient, authenticated_headers, malicious_payloads):
        """Test protection against command injection attacks."""
        
        command_payloads = malicious_payloads["command_injection"]
        
        for payload in command_payloads:
            test_data = {
                "export_format": payload,
                "filename": f"report{payload}.txt",
                "command": payload
            }
            
            response = client.post(
                "/api/v1/reports/export",
                json=test_data,
                headers=authenticated_headers
            )
            
            # Should not execute system commands
            if response.status_code == 200:
                response_text = response.text.lower()
                command_outputs = ["uid=", "gid=", "groups=", "total ", "directory of"]
                for output in command_outputs:
                    assert output not in response_text, f"Command injection possible with payload: {payload}"

    @pytest.mark.security
    def test_authentication_bypass(self, client: TestClient):
        """Test for authentication bypass vulnerabilities."""
        
        protected_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/data/work-items",
            "/api/v1/reports",
            "/api/v1/admin/users"
        ]
        
        bypass_attempts = [
            {},  # No headers
            {"Authorization": ""},  # Empty authorization
            {"Authorization": "Bearer "},  # Empty token
            {"Authorization": "Basic invalid"},  # Wrong auth type
            {"Authorization": "Bearer invalid_token"},  # Invalid token
            {"X-User-ID": "admin"},  # Custom header injection
            {"X-Admin": "true"},  # Admin privilege escalation attempt
        ]
        
        for endpoint in protected_endpoints:
            for headers in bypass_attempts:
                response = client.get(endpoint, headers=headers)
                
                # Should consistently return 401 for unauthenticated requests
                assert response.status_code == 401, \
                    f"Authentication bypass possible in {endpoint} with headers {headers}"

    @pytest.mark.security
    def test_authorization_enforcement(self, client: TestClient, sample_user: User):
        """Test proper authorization enforcement for different user roles."""
        
        # Test with regular user token
        user_headers = {"Authorization": f"Bearer user_token_{sample_user.id}"}
        
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/system-stats",
            "/api/v1/admin/audit-logs"
        ]
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            for endpoint in admin_endpoints:
                response = client.get(endpoint, headers=user_headers)
                
                # Regular users should not access admin endpoints
                assert response.status_code in [403, 404], \
                    f"Authorization bypass possible in admin endpoint {endpoint}"

    @pytest.mark.security
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting implementation."""
        
        # Test login rate limiting
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "test@example.com", "password": "wrong_password"}
            )
            
            if i < 5:
                assert response.status_code in [401, 422], "Expected authentication failure"
            else:
                # Should be rate limited after too many attempts
                assert response.status_code == 429, f"Rate limiting not working on attempt {i+1}"
                break

    @pytest.mark.security
    def test_password_security(self, client: TestClient):
        """Test password security requirements."""
        
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "qwerty",
            "abc123",
            "password123"
        ]
        
        for weak_password in weak_passwords:
            registration_data = {
                "email": f"test_{weak_password}@example.com",
                "password": weak_password,
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = client.post("/api/v1/auth/register", json=registration_data)
            
            # Should reject weak passwords
            assert response.status_code == 422, f"Weak password accepted: {weak_password}"

    @pytest.mark.security
    def test_session_security(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test session management security."""
        
        # Test that JWT tokens have proper claims
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            response = client.get("/api/v1/auth/me", headers=authenticated_headers)
            
            assert response.status_code == 200
            
            # Test token reuse after logout
            logout_response = client.post("/api/v1/auth/logout", headers=authenticated_headers)
            assert logout_response.status_code == 200
            
            # Token should be invalidated after logout
            post_logout_response = client.get("/api/v1/auth/me", headers=authenticated_headers)
            assert post_logout_response.status_code == 401, "Token still valid after logout"

    @pytest.mark.security
    def test_data_exposure_protection(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test protection against sensitive data exposure."""
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            response = client.get("/api/v1/auth/me", headers=authenticated_headers)
            
            assert response.status_code == 200
            user_data = response.json()
            
            # Sensitive fields should not be exposed
            sensitive_fields = ["password", "password_hash", "salt", "secret_key"]
            for field in sensitive_fields:
                assert field not in user_data, f"Sensitive field {field} exposed in API response"
            
            # API tokens should be masked or not exposed
            if "teams_credentials" in user_data:
                credentials = user_data["teams_credentials"]
                if "access_token" in credentials:
                    token = credentials["access_token"]
                    assert len(token) < 20 or "*" in token, "Full API token exposed"

    @pytest.mark.security
    def test_input_validation(self, client: TestClient, authenticated_headers):
        """Test comprehensive input validation."""
        
        # Test oversized inputs
        large_input = "A" * 10000
        test_data = {
            "description": large_input,
            "title": large_input,
            "content": large_input
        }
        
        response = client.post("/api/v1/reports", json=test_data, headers=authenticated_headers)
        assert response.status_code == 422, "Large input not properly validated"
        
        # Test invalid data types
        invalid_data = {
            "time_spent_minutes": "not_a_number",
            "confidence_score": "not_a_float",
            "report_date": "not_a_date",
            "user_id": "not_a_uuid"
        }
        
        response = client.post("/api/v1/data/work-items", json=invalid_data, headers=authenticated_headers)
        assert response.status_code == 422, "Invalid data types not properly validated"

    @pytest.mark.security
    def test_cors_security(self, client: TestClient):
        """Test CORS configuration security."""
        
        # Test CORS headers
        response = client.options("/api/v1/auth/login")
        
        cors_headers = response.headers
        
        # Should not allow all origins in production
        if "Access-Control-Allow-Origin" in cors_headers:
            origin = cors_headers["Access-Control-Allow-Origin"]
            assert origin != "*", "CORS allows all origins (security risk)"
        
        # Should not expose sensitive headers
        if "Access-Control-Expose-Headers" in cors_headers:
            exposed_headers = cors_headers["Access-Control-Expose-Headers"].lower()
            sensitive_headers = ["authorization", "x-api-key", "x-secret"]
            for header in sensitive_headers:
                assert header not in exposed_headers, f"Sensitive header {header} exposed via CORS"

    @pytest.mark.security
    def test_error_information_disclosure(self, client: TestClient, authenticated_headers):
        """Test that error messages don't disclose sensitive information."""
        
        # Test with malformed requests
        malformed_requests = [
            ("/api/v1/nonexistent", {}),
            ("/api/v1/data/work-items", {"invalid": "json"}),
            ("/api/v1/reports/999999", {})  # Non-existent resource
        ]
        
        for endpoint, data in malformed_requests:
            if data:
                response = client.post(endpoint, json=data, headers=authenticated_headers)
            else:
                response = client.get(endpoint, headers=authenticated_headers)
            
            response_text = response.text.lower()
            
            # Should not expose internal paths or technical details
            sensitive_info = [
                "/app/",
                "traceback",
                "sqlalchemy",
                "postgresql://",
                "mysql://",
                "secret_key",
                "api_key"
            ]
            
            for info in sensitive_info:
                assert info not in response_text, f"Sensitive information exposed: {info}"

    @pytest.mark.security
    def test_file_upload_security(self, client: TestClient, authenticated_headers):
        """Test file upload security if applicable."""
        
        # Test malicious file uploads
        malicious_files = [
            ("test.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("test.exe", b"\x4d\x5a\x90\x00", "application/x-executable"),
            ("test.jsp", "<%@ page import=\"java.io.*\" %>", "application/x-jsp"),
            ("test.sh", "#!/bin/bash\nrm -rf /", "application/x-sh")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            
            # Assuming there's a file upload endpoint
            response = client.post(
                "/api/v1/data/upload",
                files=files,
                headers=authenticated_headers
            )
            
            # Should reject malicious file types
            assert response.status_code in [400, 422, 415], \
                f"Malicious file {filename} was accepted"

    @pytest.mark.security
    def test_timing_attack_protection(self, client: TestClient, sample_user: User):
        """Test protection against timing attacks."""
        
        # Test login timing for valid vs invalid users
        valid_timings = []
        invalid_timings = []
        
        for _ in range(5):
            # Time valid user login attempt
            start_time = time.time()
            response = client.post(
                "/api/v1/auth/login",
                data={"username": sample_user.email, "password": "wrong_password"}
            )
            valid_timings.append(time.time() - start_time)
            
            # Time invalid user login attempt
            start_time = time.time()
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "nonexistent@example.com", "password": "wrong_password"}
            )
            invalid_timings.append(time.time() - start_time)
        
        avg_valid_time = sum(valid_timings) / len(valid_timings)
        avg_invalid_time = sum(invalid_timings) / len(invalid_timings)
        
        # Timing difference should not be significant (within 50%)
        timing_ratio = abs(avg_valid_time - avg_invalid_time) / max(avg_valid_time, avg_invalid_time)
        assert timing_ratio < 0.5, f"Timing attack possible: {timing_ratio:.2f} ratio"

    @pytest.mark.security
    def test_api_versioning_security(self, client: TestClient):
        """Test API versioning doesn't expose old vulnerable endpoints."""
        
        # Test that old API versions are not accessible
        old_versions = ["v0", "beta", "test", "debug"]
        
        for version in old_versions:
            response = client.get(f"/api/{version}/auth/login")
            assert response.status_code == 404, f"Old API version {version} still accessible"

    @pytest.mark.security
    def test_debug_mode_disabled(self, client: TestClient):
        """Test that debug mode is disabled in production."""
        
        # Test that debug endpoints are not accessible
        debug_endpoints = [
            "/debug",
            "/api/debug",
            "/api/v1/debug",
            "/_debug",
            "/dev",
            "/test"
        ]
        
        for endpoint in debug_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404, f"Debug endpoint {endpoint} is accessible"

    @pytest.mark.security
    def test_http_security_headers(self, client: TestClient):
        """Test that proper HTTP security headers are set."""
        
        response = client.get("/health")
        headers = response.headers
        
        # Check for important security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age="
        }
        
        for header, expected_values in security_headers.items():
            if header in headers:
                header_value = headers[header]
                if isinstance(expected_values, list):
                    assert any(val in header_value for val in expected_values), \
                        f"Security header {header} has unexpected value: {header_value}"
                else:
                    assert expected_values in header_value, \
                        f"Security header {header} has unexpected value: {header_value}"

    @pytest.mark.security
    def test_privilege_escalation_protection(self, client: TestClient, sample_user: User):
        """Test protection against privilege escalation."""
        
        # Attempt to modify user role through API
        escalation_attempts = [
            {"is_admin": True},
            {"role": "admin"},
            {"permissions": ["admin", "superuser"]},
            {"user_type": "administrator"}
        ]
        
        user_headers = {"Authorization": f"Bearer user_token_{sample_user.id}"}
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            for attempt in escalation_attempts:
                response = client.put(
                    "/api/v1/auth/profile",
                    json=attempt,
                    headers=user_headers
                )
                
                # Should not allow privilege escalation
                if response.status_code == 200:
                    updated_user = response.json()
                    for field, value in attempt.items():
                        assert updated_user.get(field) != value, \
                            f"Privilege escalation possible via field {field}"

    @pytest.mark.security
    def test_data_validation_edge_cases(self, client: TestClient, authenticated_headers):
        """Test data validation with edge cases and boundary values."""
        
        edge_cases = [
            {"time_spent_minutes": -1},  # Negative time
            {"time_spent_minutes": 999999},  # Extremely large time
            {"confidence_score": -0.1},  # Invalid confidence score
            {"confidence_score": 1.1},  # Invalid confidence score
            {"report_date": "9999-12-31"},  # Future date
            {"report_date": "1900-01-01"},  # Very old date
        ]
        
        for edge_case in edge_cases:
            response = client.post(
                "/api/v1/data/work-items",
                json=edge_case,
                headers=authenticated_headers
            )
            
            # Should validate edge cases properly
            assert response.status_code == 422, f"Edge case not validated: {edge_case}" 
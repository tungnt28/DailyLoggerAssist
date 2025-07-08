"""
Integration Tests for Authentication API - Daily Logger Assist

Tests for login, registration, token management, and authentication flows.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from app.models.user import User


class TestAuthenticationAPI:
    """Test suite for Authentication API endpoints."""

    @pytest.mark.integration
    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Daily Logger Assist"
        assert "phase" in data
        assert "features" in data

    @pytest.mark.integration
    def test_login_success(self, client: TestClient, sample_user: User):
        """Test successful login with valid credentials."""
        
        # Mock the password verification
        with patch('app.core.security.verify_password', return_value=True):
            with patch('app.core.security.create_access_token', return_value="test_jwt_token"):
                response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": sample_user.email,
                        "password": "correct_password"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.integration
    def test_login_invalid_credentials(self, client: TestClient, sample_user: User):
        """Test login with invalid credentials."""
        
        with patch('app.core.security.verify_password', return_value=False):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": sample_user.email,
                    "password": "wrong_password"
                }
            )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "any_password"
            }
        )
        
        assert response.status_code == 401

    @pytest.mark.integration
    def test_login_inactive_user(self, client: TestClient, db_session, sample_user: User):
        """Test login with inactive user account."""
        
        # Deactivate the user
        sample_user.is_active = False
        db_session.commit()
        
        with patch('app.core.security.verify_password', return_value=True):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": sample_user.email,
                    "password": "correct_password"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["detail"].lower()

    @pytest.mark.integration
    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        
        registration_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "New",
            "last_name": "User"
        }
        
        with patch('app.core.security.get_password_hash', return_value="hashed_password"):
            response = client.post("/api/v1/auth/register", json=registration_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == registration_data["email"]
        assert data["first_name"] == registration_data["first_name"]
        assert data["last_name"] == registration_data["last_name"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned

    @pytest.mark.integration
    def test_register_duplicate_email(self, client: TestClient, sample_user: User):
        """Test registration with duplicate email."""
        
        registration_data = {
            "email": sample_user.email,  # Use existing user's email
            "password": "SecurePassword123!",
            "first_name": "Duplicate",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    @pytest.mark.integration
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        
        registration_data = {
            "email": "invalid_email_format",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        
        registration_data = {
            "email": "test@example.com",
            "password": "123",  # Too weak
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    def test_get_current_user(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test getting current user information."""
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            response = client.get("/api/v1/auth/me", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["first_name"] == sample_user.first_name
        assert data["last_name"] == sample_user.last_name
        assert "password" not in data

    @pytest.mark.integration
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.integration
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/auth/me", headers=invalid_headers)
        
        assert response.status_code == 401

    @pytest.mark.integration
    def test_refresh_token(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test token refresh functionality."""
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            with patch('app.core.security.create_access_token', return_value="new_jwt_token"):
                response = client.post("/api/v1/auth/refresh", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.integration
    def test_logout(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test logout functionality."""
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            response = client.post("/api/v1/auth/logout", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.integration
    def test_change_password(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test password change functionality."""
        
        password_data = {
            "current_password": "old_password",
            "new_password": "NewSecurePassword123!"
        }
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            with patch('app.core.security.verify_password', return_value=True):
                with patch('app.core.security.get_password_hash', return_value="new_hashed_password"):
                    response = client.put(
                        "/api/v1/auth/change-password",
                        json=password_data,
                        headers=authenticated_headers
                    )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.integration
    def test_change_password_wrong_current(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test password change with wrong current password."""
        
        password_data = {
            "current_password": "wrong_password",
            "new_password": "NewSecurePassword123!"
        }
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            with patch('app.core.security.verify_password', return_value=False):
                response = client.put(
                    "/api/v1/auth/change-password",
                    json=password_data,
                    headers=authenticated_headers
                )
        
        assert response.status_code == 400
        data = response.json()
        assert "current password" in data["detail"].lower()

    @pytest.mark.integration
    def test_update_profile(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test user profile update."""
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "preferences": {
                "ai_confidence_threshold": 0.8,
                "auto_approve_reports": True
            }
        }
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            response = client.put(
                "/api/v1/auth/profile",
                json=update_data,
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    @pytest.mark.integration
    def test_delete_account(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test account deletion."""
        
        delete_data = {"password": "correct_password"}
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            with patch('app.core.security.verify_password', return_value=True):
                response = client.delete(
                    "/api/v1/auth/account",
                    json=delete_data,
                    headers=authenticated_headers
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

    @pytest.mark.integration
    def test_delete_account_wrong_password(self, client: TestClient, sample_user: User, authenticated_headers):
        """Test account deletion with wrong password."""
        
        delete_data = {"password": "wrong_password"}
        
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            with patch('app.core.security.verify_password', return_value=False):
                response = client.delete(
                    "/api/v1/auth/account",
                    json=delete_data,
                    headers=authenticated_headers
                )
        
        assert response.status_code == 400

    @pytest.mark.integration
    def test_password_reset_request(self, client: TestClient, sample_user: User):
        """Test password reset request."""
        
        reset_data = {"email": sample_user.email}
        
        with patch('app.services.email_service.send_password_reset_email', return_value=True):
            response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "reset email sent" in data["message"].lower()

    @pytest.mark.integration
    def test_password_reset_nonexistent_email(self, client: TestClient):
        """Test password reset request for non-existent email."""
        
        reset_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200

    @pytest.mark.integration
    def test_password_reset_confirm(self, client: TestClient, sample_user: User):
        """Test password reset confirmation."""
        
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "NewSecurePassword123!"
        }
        
        with patch('app.core.security.verify_password_reset_token', return_value=sample_user.email):
            with patch('app.core.security.get_password_hash', return_value="new_hashed_password"):
                response = client.post("/api/v1/auth/password-reset/confirm", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "password reset successful" in data["message"].lower()

    @pytest.mark.integration
    def test_password_reset_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        
        reset_data = {
            "token": "invalid_reset_token",
            "new_password": "NewSecurePassword123!"
        }
        
        with patch('app.core.security.verify_password_reset_token', return_value=None):
            response = client.post("/api/v1/auth/password-reset/confirm", json=reset_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()

    @pytest.mark.integration
    def test_rate_limiting_login(self, client: TestClient, sample_user: User):
        """Test rate limiting on login attempts."""
        
        # Make multiple failed login attempts
        for _ in range(6):  # Assuming rate limit is 5 attempts
            with patch('app.core.security.verify_password', return_value=False):
                response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": sample_user.email,
                        "password": "wrong_password"
                    }
                )
        
        # The last attempt should be rate limited
        assert response.status_code == 429

    @pytest.mark.integration
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers in responses."""
        
        response = client.options("/api/v1/auth/login")
        
        # Check for CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

    @pytest.mark.integration
    def test_token_expiration_handling(self, client: TestClient, sample_user: User):
        """Test handling of expired tokens."""
        
        # Create an expired token
        expired_token = "Bearer expired_jwt_token"
        expired_headers = {"Authorization": expired_token}
        
        with patch('app.dependencies.get_current_user') as mock_get_user:
            from app.core.security import TokenExpiredError
            mock_get_user.side_effect = TokenExpiredError("Token has expired")
            
            response = client.get("/api/v1/auth/me", headers=expired_headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.integration
    def test_concurrent_login_sessions(self, client: TestClient, sample_user: User):
        """Test multiple concurrent login sessions for the same user."""
        
        # Simulate multiple concurrent logins
        with patch('app.core.security.verify_password', return_value=True):
            with patch('app.core.security.create_access_token') as mock_create_token:
                mock_create_token.side_effect = ["token1", "token2", "token3"]
                
                responses = []
                for i in range(3):
                    response = client.post(
                        "/api/v1/auth/login",
                        data={
                            "username": sample_user.email,
                            "password": "correct_password"
                        }
                    )
                    responses.append(response)
        
        # All logins should succeed
        for response in responses:
            assert response.status_code == 200
            assert "access_token" in response.json()

    @pytest.mark.integration
    def test_authentication_middleware(self, client: TestClient, sample_user: User):
        """Test authentication middleware functionality."""
        
        # Test accessing protected endpoint without token
        response = client.get("/api/v1/data/work-items")
        assert response.status_code == 401
        
        # Test accessing protected endpoint with valid token
        with patch('app.dependencies.get_current_user', return_value=sample_user):
            response = client.get(
                "/api/v1/data/work-items",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        # Should not return 401 (may return other status codes based on implementation)
        assert response.status_code != 401 
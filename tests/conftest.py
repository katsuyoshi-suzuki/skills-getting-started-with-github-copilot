"""
Pytest configuration and fixtures for testing the FastAPI app.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient instance for making requests to the app.
    Returns a fresh client for each test function.
    """
    return TestClient(app)

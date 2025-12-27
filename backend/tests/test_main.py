"""
Tests for FastAPI main application endpoints.

This module tests the API endpoints for syncing API-Football data.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient


class TestSyncAPIFootballEndpoint:
    """Test suite for /api/sync-api-football endpoint."""

    def test_sync_api_football_endpoint_teams(self):
        """
        Test POST /api/sync-api-football endpoint for teams.

        EXPECTED: ❌ Test FAILS (endpoint doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. /api/sync-api-football endpoint doesn't exist in main.py
        2. This drives the implementation in Phase 3
        """
        # Arrange: Import app and create test client
        from src.main import app

        client = TestClient(app)

        # Mock sync result
        mock_sync_result = {
            "status": "success",
            "entity_type": "teams",
            "entities_added": 5,
            "entities_updated": 10,
            "changes_detected": 15,
            "synced_at": "2026-01-01T00:00:00Z",
        }

        # Act: Send POST request to sync endpoint
        with patch("src.main.APIFootballSync") as mock_sync_class:
            mock_sync_instance = Mock()
            mock_sync_class.return_value = mock_sync_instance
            mock_sync_instance.sync_teams.return_value = mock_sync_result

            response = client.post(
                "/api/sync-api-football",
                json={"entity_type": "teams", "league_id": 1, "season": 2026},
            )

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains sync result
        data = response.json()
        assert data["status"] == "success"
        assert data["entity_type"] == "teams"
        assert data["changes_detected"] == 15
        assert "synced_at" in data

    def test_sync_api_football_endpoint_fixtures(self):
        """
        Test POST /api/sync-api-football endpoint for fixtures.

        EXPECTED: ❌ Test FAILS (endpoint doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. /api/sync-api-football endpoint doesn't exist in main.py
        2. This drives the implementation in Phase 3
        """
        # Arrange: Import app and create test client
        from src.main import app

        client = TestClient(app)

        # Mock sync result
        mock_sync_result = {
            "status": "success",
            "entity_type": "fixtures",
            "entities_added": 20,
            "entities_updated": 5,
            "changes_detected": 25,
            "synced_at": "2026-01-01T00:00:00Z",
        }

        # Act: Send POST request to sync endpoint
        with patch("src.main.APIFootballSync") as mock_sync_class:
            mock_sync_instance = Mock()
            mock_sync_class.return_value = mock_sync_instance
            mock_sync_instance.sync_fixtures.return_value = mock_sync_result

            response = client.post(
                "/api/sync-api-football",
                json={"entity_type": "fixtures", "league_id": 1, "season": 2026},
            )

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains sync result
        data = response.json()
        assert data["status"] == "success"
        assert data["entity_type"] == "fixtures"
        assert data["changes_detected"] == 25
        assert "synced_at" in data

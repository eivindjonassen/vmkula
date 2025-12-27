"""
Tests for API-Football sync module.

This module tests the APIFootballSync class which handles:
- Storing raw API-Football responses in Firestore
- Detecting changes between API data and existing Firestore data
- Resolving conflicts with manual overrides
- Syncing teams and fixtures from API-Football
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


class TestAPIFootballSync:
    """Test suite for APIFootballSync class."""

    def test_sync_teams_stores_raw_response(self):
        """
        Test that sync_teams stores raw API-Football response in Firestore.

        EXPECTED: ❌ Test FAILS (APIFootballSync class doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. APIFootballSync class doesn't exist
        2. sync_teams method doesn't exist
        3. This drives the implementation in Phase 3
        """
        # Arrange: Create mock dependencies
        mock_firestore = Mock()
        mock_data_aggregator = Mock()

        # Mock API-Football teams response
        mock_api_response = {
            "response": [
                {
                    "team": {
                        "id": 1,
                        "name": "Manchester United",
                        "code": "MUN",
                        "country": "England",
                        "founded": 1878,
                        "logo": "https://media.api-sports.io/football/teams/1.png",
                    }
                },
                {
                    "team": {
                        "id": 2,
                        "name": "Liverpool",
                        "code": "LIV",
                        "country": "England",
                        "founded": 1892,
                        "logo": "https://media.api-sports.io/football/teams/2.png",
                    }
                },
            ]
        }

        mock_data_aggregator.fetch_teams.return_value = mock_api_response
        mock_firestore.store_raw_api_response.return_value = "teams_1_2026"

        # Import will fail - APIFootballSync doesn't exist yet
        from src.api_football_sync import APIFootballSync

        # Act: Create sync instance and call sync_teams
        sync = APIFootballSync(
            firestore_manager=mock_firestore, data_aggregator=mock_data_aggregator
        )

        result = sync.sync_teams(league_id=1, season=2026)

        # Assert: Verify raw response was stored
        mock_firestore.store_raw_api_response.assert_called_once_with(
            entity_type="teams",
            league_id=1,
            season=2026,
            raw_response=mock_api_response,
        )

        # Assert: Verify sync result returned
        assert result is not None
        assert result.entity_type == "teams"
        assert result.raw_document_id == "teams_1_2026"

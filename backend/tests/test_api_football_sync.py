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

    def test_detect_changes_identifies_new_teams(self):
        """
        Test that detect_changes identifies new teams added to API response.

        EXPECTED: ❌ Test FAILS (detect_changes method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. APIFootballSync.detect_changes method doesn't exist
        2. This drives the implementation in Phase 3
        """
        # Arrange: Create mock dependencies
        mock_firestore = Mock()
        mock_data_aggregator = Mock()

        # Existing teams in Firestore
        existing_teams = [
            {
                "id": 1,
                "name": "Manchester United",
                "api_football_id": 1,
                "fifa_code": "MUN",
            },
            {
                "id": 2,
                "name": "Liverpool",
                "api_football_id": 2,
                "fifa_code": "LIV",
            },
        ]

        # Raw API response with NEW team added (Chelsea)
        raw_entities = [
            {
                "team": {
                    "id": 1,
                    "name": "Manchester United",
                    "code": "MUN",
                }
            },
            {
                "team": {
                    "id": 2,
                    "name": "Liverpool",
                    "code": "LIV",
                }
            },
            {
                "team": {
                    "id": 3,
                    "name": "Chelsea",
                    "code": "CHE",
                }
            },
        ]

        # Import will fail - APIFootballSync doesn't exist yet
        from src.api_football_sync import APIFootballSync

        # Act: Create sync instance and call detect_changes
        sync = APIFootballSync(
            firestore_manager=mock_firestore, data_aggregator=mock_data_aggregator
        )

        changes = sync.detect_changes(raw_entities, existing_teams)

        # Assert: Verify new team identified
        assert len(changes.entities_to_add) == 1
        assert changes.entities_to_add[0]["team"]["id"] == 3
        assert changes.entities_to_add[0]["team"]["name"] == "Chelsea"

        # Assert: Verify unchanged teams identified
        assert len(changes.entities_unchanged) == 2

    def test_resolve_conflicts_preserves_manual_overrides(self):
        """
        Test that resolve_conflicts preserves manual overrides when force_update=False.

        EXPECTED: ❌ Test FAILS (resolve_conflicts method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. APIFootballSync.resolve_conflicts method doesn't exist
        2. Conflict dataclass doesn't exist
        3. This drives the implementation in Phase 3
        """
        # Arrange: Create mock dependencies
        mock_firestore = Mock()
        mock_data_aggregator = Mock()

        # Import will fail - APIFootballSync doesn't exist yet
        from src.api_football_sync import APIFootballSync, Conflict

        # Create conflict with manual override
        conflict = Conflict(
            entity_id=1,
            entity_type="teams",
            field="name",
            firestore_value="Man United (Custom)",
            api_value="Manchester United",
            manual_override=True,
        )

        # Act: Create sync instance and resolve conflicts
        sync = APIFootballSync(
            firestore_manager=mock_firestore, data_aggregator=mock_data_aggregator
        )

        resolution = sync.resolve_conflicts([conflict], force_update=False)

        # Assert: Verify manual override preserved
        assert resolution[0].action == "preserve_override"
        assert resolution[0].entity_id == 1

    def test_resolve_conflicts_forces_update_when_requested(self):
        """
        Test that resolve_conflicts forces update when force_update=True.

        EXPECTED: ❌ Test FAILS (resolve_conflicts method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. APIFootballSync.resolve_conflicts method doesn't exist
        2. This drives the implementation in Phase 3
        """
        # Arrange: Create mock dependencies
        mock_firestore = Mock()
        mock_data_aggregator = Mock()

        # Import will fail - APIFootballSync doesn't exist yet
        from src.api_football_sync import APIFootballSync, Conflict

        # Create conflict with manual override
        conflict = Conflict(
            entity_id=1,
            entity_type="teams",
            field="name",
            firestore_value="Man United (Custom)",
            api_value="Manchester United",
            manual_override=True,
        )

        # Act: Create sync instance and resolve conflicts with force update
        sync = APIFootballSync(
            firestore_manager=mock_firestore, data_aggregator=mock_data_aggregator
        )

        resolution = sync.resolve_conflicts([conflict], force_update=True)

        # Assert: Verify API update applied
        assert resolution[0].action == "apply_api_update"
        assert resolution[0].manual_override_cleared == True

    def test_sync_teams_end_to_end(self):
        """
        Test sync_teams end-to-end flow.

        EXPECTED: ❌ Test FAILS (sync_teams method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. APIFootballSync.sync_teams method doesn't exist
        2. This drives the implementation in Phase 3
        """
        # Arrange: Create mock dependencies
        mock_firestore = Mock()
        mock_data_aggregator = Mock()

        # Mock complete API-Football teams response
        mock_api_response = {
            "response": [
                {
                    "team": {
                        "id": 1,
                        "name": "Manchester United",
                        "code": "MUN",
                        "country": "England",
                    }
                },
                {
                    "team": {
                        "id": 2,
                        "name": "Liverpool",
                        "code": "LIV",
                        "country": "England",
                    }
                },
            ]
        }

        # Mock existing Firestore teams
        existing_teams = [
            {
                "id": 1,
                "name": "Manchester United",
                "api_football_id": 1,
                "fifa_code": "MUN",
            }
        ]

        mock_data_aggregator.fetch_teams.return_value = mock_api_response
        mock_firestore.get_all_teams.return_value = existing_teams
        mock_firestore.store_raw_api_response.return_value = "teams_1_2026"

        # Import will fail - APIFootballSync doesn't exist yet
        from src.api_football_sync import APIFootballSync

        # Act: Create sync instance and call sync_teams
        sync = APIFootballSync(
            firestore_manager=mock_firestore, data_aggregator=mock_data_aggregator
        )

        result = sync.sync_teams(league_id=1, season=2026)

        # Assert: Verify raw response stored
        mock_firestore.store_raw_api_response.assert_called_once()

        # Assert: Verify teams collection updated
        assert result.entities_added == 1  # Liverpool is new
        assert result.entities_updated == 1  # Manchester United exists
        assert result.entity_type == "teams"

    def test_sync_fixtures_end_to_end(self):
        """
        Test sync_fixtures end-to-end flow.

        EXPECTED: ❌ Test FAILS (sync_fixtures method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. APIFootballSync.sync_fixtures method doesn't exist
        2. This drives the implementation in Phase 3
        """
        # Arrange: Create mock dependencies
        mock_firestore = Mock()
        mock_data_aggregator = Mock()

        # Mock complete API-Football fixtures response
        mock_api_response = {
            "response": [
                {
                    "fixture": {
                        "id": 100,
                        "date": "2026-06-11T15:00:00+00:00",
                        "venue": {"name": "Old Trafford"},
                    },
                    "teams": {
                        "home": {"id": 1, "name": "Manchester United"},
                        "away": {"id": 2, "name": "Liverpool"},
                    },
                }
            ]
        }

        # Mock existing Firestore matches
        existing_matches = []

        mock_data_aggregator.fetch_fixtures.return_value = mock_api_response
        mock_firestore.get_all_matches.return_value = existing_matches
        mock_firestore.store_raw_api_response.return_value = "fixtures_1_2026"

        # Import will fail - APIFootballSync doesn't exist yet
        from src.api_football_sync import APIFootballSync

        # Act: Create sync instance and call sync_fixtures
        sync = APIFootballSync(
            firestore_manager=mock_firestore, data_aggregator=mock_data_aggregator
        )

        result = sync.sync_fixtures(league_id=1, season=2026)

        # Assert: Verify raw response stored
        mock_firestore.store_raw_api_response.assert_called_once()

        # Assert: Verify matches collection updated
        assert result.entities_added == 1  # New fixture
        assert result.entity_type == "fixtures"

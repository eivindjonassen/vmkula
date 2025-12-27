"""
Tests for FirestoreManager raw API response storage methods.

This module tests the new methods for storing and retrieving raw API-Football
responses in Firestore.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta


class TestFirestoreManagerRawAPIMethods:
    """Test suite for FirestoreManager raw API storage methods."""

    def test_store_raw_api_response(self):
        """
        Test that store_raw_api_response creates document with correct structure.

        EXPECTED: ❌ Test FAILS (store_raw_api_response method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. FirestoreManager.store_raw_api_response method doesn't exist
        2. This drives the implementation in Phase 3
        """
        # Arrange: Create mock Firestore client
        with patch("src.firestore_manager.firestore.Client") as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db
            mock_collection = MagicMock()
            mock_db.collection.return_value = mock_collection
            mock_document = MagicMock()
            mock_collection.document.return_value = mock_document

            from src.firestore_manager import FirestoreManager

            manager = FirestoreManager()

            # Mock API response
            raw_response = {
                "response": [
                    {
                        "team": {
                            "id": 1,
                            "name": "Manchester United",
                            "code": "MUN",
                        }
                    }
                ]
            }

            # Act: Store raw API response
            document_id = manager.store_raw_api_response(
                entity_type="teams",
                league_id=1,
                season=2026,
                raw_response=raw_response,
            )

            # Assert: Verify collection accessed
            mock_db.collection.assert_called_with("raw_api_responses")

            # Assert: Verify document created with correct structure
            mock_document.set.assert_called_once()
            call_args = mock_document.set.call_args[0][0]

            assert call_args["entity_type"] == "teams"
            assert call_args["league_id"] == 1
            assert call_args["season"] == 2026
            assert call_args["raw_response"] == raw_response
            assert "fetched_at" in call_args
            assert isinstance(call_args["fetched_at"], datetime)

            # Assert: Verify document ID returned
            assert document_id is not None

    def test_get_raw_api_response(self):
        """
        Test that get_raw_api_response retrieves document by ID.

        EXPECTED: ❌ Test FAILS (get_raw_api_response method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. FirestoreManager.get_raw_api_response method doesn't exist
        2. This drives the implementation in Phase 3
        """
        # Arrange: Create mock Firestore client
        with patch("src.firestore_manager.firestore.Client") as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db
            mock_collection = MagicMock()
            mock_db.collection.return_value = mock_collection
            mock_document_ref = MagicMock()
            mock_collection.document.return_value = mock_document_ref
            mock_document_snap = MagicMock()
            mock_document_ref.get.return_value = mock_document_snap
            mock_document_snap.exists = True

            # Mock stored data
            stored_data = {
                "entity_type": "teams",
                "league_id": 1,
                "season": 2026,
                "raw_response": {
                    "response": [{"team": {"id": 1, "name": "Manchester United"}}]
                },
                "fetched_at": datetime.utcnow(),
            }
            mock_document_snap.to_dict.return_value = stored_data

            from src.firestore_manager import FirestoreManager

            manager = FirestoreManager()

            # Act: Retrieve raw API response
            result = manager.get_raw_api_response("teams_1_2026")

            # Assert: Verify collection accessed
            mock_db.collection.assert_called_with("raw_api_responses")

            # Assert: Verify document retrieved
            mock_collection.document.assert_called_with("teams_1_2026")
            mock_document_ref.get.assert_called_once()

            # Assert: Verify data returned
            assert result is not None
            assert result["entity_type"] == "teams"
            assert result["league_id"] == 1
            assert result["season"] == 2026
            assert "raw_response" in result

    # T012: FIFA Rankings Firestore Methods Tests

    def test_get_fifa_rankings_success(self):
        """
        Test that get_fifa_rankings retrieves rankings document.

        EXPECTED: ❌ Test FAILS (get_fifa_rankings method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. FirestoreManager.get_fifa_rankings method doesn't exist
        2. This drives the implementation in Phase 2
        """
        # Arrange: Create mock Firestore client
        with patch("src.firestore_manager.firestore.Client") as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db
            mock_collection = MagicMock()
            mock_db.collection.return_value = mock_collection
            mock_document_ref = MagicMock()
            mock_collection.document.return_value = mock_document_ref
            mock_document_snap = MagicMock()
            mock_document_ref.get.return_value = mock_document_snap
            mock_document_snap.exists = True

            # Mock stored FIFA rankings data
            mock_fetched_at = datetime.utcnow()
            mock_expires_at = mock_fetched_at + timedelta(days=30)
            stored_data = {
                "rankings": [
                    {
                        "rank": 1,
                        "team_name": "Argentina",
                        "fifa_code": "ARG",
                        "confederation": "CONMEBOL",
                        "points": 1855.2,
                        "previous_rank": 1,
                        "rank_change": 0,
                    },
                    {
                        "rank": 2,
                        "team_name": "France",
                        "fifa_code": "FRA",
                        "confederation": "UEFA",
                        "points": 1845.44,
                        "previous_rank": 3,
                        "rank_change": 1,
                    },
                ],
                "fetched_at": mock_fetched_at,
                "expires_at": mock_expires_at,
                "total_teams": 211,
            }
            mock_document_snap.to_dict.return_value = stored_data

            from src.firestore_manager import FirestoreManager

            manager = FirestoreManager()

            # Act: Retrieve FIFA rankings
            result = manager.get_fifa_rankings()

            # Assert: Verify collection accessed
            mock_db.collection.assert_called_with("fifa_rankings")

            # Assert: Verify document retrieved (should use known doc ID like "current")
            mock_document_ref.get.assert_called_once()

            # Assert: Verify data returned
            assert result is not None
            assert "rankings" in result
            assert len(result["rankings"]) == 2
            assert result["total_teams"] == 211
            assert "fetched_at" in result
            assert "expires_at" in result

            # Verify rankings structure
            assert result["rankings"][0]["fifa_code"] == "ARG"
            assert result["rankings"][1]["fifa_code"] == "FRA"

    def test_update_fifa_rankings_with_ttl(self):
        """
        Test that update_fifa_rankings stores rankings with TTL timestamps.

        EXPECTED: ❌ Test FAILS (update_fifa_rankings method doesn't exist yet)

        This is TDD Red Phase - we expect this test to fail because:
        1. FirestoreManager.update_fifa_rankings method doesn't exist
        2. This drives the implementation in Phase 2

        Verifies:
        - Rankings data stored to Firestore
        - fetched_at timestamp set to current time
        - expires_at = fetched_at + timedelta(days=30)
        """
        # Arrange: Create mock Firestore client
        with patch("src.firestore_manager.firestore.Client") as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db
            mock_collection = MagicMock()
            mock_db.collection.return_value = mock_collection
            mock_document = MagicMock()
            mock_collection.document.return_value = mock_document

            from src.firestore_manager import FirestoreManager

            manager = FirestoreManager()

            # Mock rankings data
            rankings_data = [
                {
                    "rank": 1,
                    "team_name": "Argentina",
                    "fifa_code": "ARG",
                    "confederation": "CONMEBOL",
                    "points": 1855.2,
                    "previous_rank": 1,
                    "rank_change": 0,
                },
                {
                    "rank": 2,
                    "team_name": "France",
                    "fifa_code": "FRA",
                    "confederation": "UEFA",
                    "points": 1845.44,
                    "previous_rank": 3,
                    "rank_change": 1,
                },
            ]

            # Act: Update FIFA rankings
            before_call = datetime.utcnow()
            manager.update_fifa_rankings(rankings_data)
            after_call = datetime.utcnow()

            # Assert: Verify collection accessed
            mock_db.collection.assert_called_with("fifa_rankings")

            # Assert: Verify document set called
            mock_document.set.assert_called_once()
            call_args = mock_document.set.call_args[0][0]

            # Assert: Verify rankings data stored
            assert call_args["rankings"] == rankings_data
            assert call_args["total_teams"] == len(rankings_data)

            # Assert: Verify fetched_at timestamp
            assert "fetched_at" in call_args
            fetched_at = call_args["fetched_at"]
            assert isinstance(fetched_at, datetime)
            assert before_call <= fetched_at <= after_call

            # Assert: Verify expires_at = fetched_at + 30 days
            assert "expires_at" in call_args
            expires_at = call_args["expires_at"]
            assert isinstance(expires_at, datetime)

            # Verify TTL calculation (30 days)
            delta = expires_at - fetched_at
            assert delta.days == 30
            assert delta.seconds == 0  # Should be exactly 30 days, no extra hours/minutes

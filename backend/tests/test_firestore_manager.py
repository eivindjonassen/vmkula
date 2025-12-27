"""
Tests for FirestoreManager raw API response storage methods.

This module tests the new methods for storing and retrieving raw API-Football
responses in Firestore.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


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

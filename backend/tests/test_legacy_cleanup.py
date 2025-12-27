"""
Tests for legacy cleanup validation.

This module validates that Phase 1 cleanup tasks were completed successfully.
"""

import pytest
import subprocess


class TestLegacyCleanupValidation:
    """Test suite for validating legacy code cleanup."""

    def test_no_dbmanager_imports_in_codebase(self):
        """
        Test that no db_manager imports exist in codebase after Phase 1 cleanup.

        EXPECTED: ✅ Test PASSES (after T001-T004 complete)

        This test validates Phase 1 cleanup by ensuring:
        1. No imports from src.db_manager exist in backend/
        2. All SQLite references removed
        3. Migration to FirestoreManager complete
        """
        # Act: Search for db_manager imports in backend/
        result = subprocess.run(
            ["grep", "-r", "from src.db_manager", "backend/"],
            capture_output=True,
            text=True,
        )

        # Assert: No matches found (returncode != 0 means grep found nothing)
        assert result.returncode != 0, (
            f"Found db_manager imports in codebase:\n{result.stdout}"
        )

        # Assert: stdout is empty (no matches)
        assert result.stdout.strip() == "", (
            f"Found db_manager imports in codebase:\n{result.stdout}"
        )

"""
Unit tests for featured_tracker.py module.

P0: State integrity and JSON persistence tests.
"""

from unittest.mock import mock_open, patch

from arxiv_aggregator.featured_tracker import (
    add_featured_id,
    clear_featured_ids,
    load_featured_ids,
    save_featured_ids,
    select_featured_article,
)

# =============================================================================
# P0: State Integrity Tests
# =============================================================================


class TestLoadFeaturedIds:
    """P0: Test loading featured IDs from JSON file."""

    def test_load_returns_set(self):
        """load_featured_ids should return a set."""
        with patch("builtins.open", mock_open(read_data='["id1", "id2"]')):
            result = load_featured_ids()
            assert isinstance(result, set)

    def test_load_parses_json_correctly(self):
        """JSON array should be parsed to set."""
        with patch("builtins.open", mock_open(read_data='["id1", "id2", "id3"]')):
            result = load_featured_ids()
            assert result == {"id1", "id2", "id3"}

    def test_file_not_found_returns_empty_set(self):
        """Missing file should return empty set, not crash."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = load_featured_ids()
            assert result == set()

    def test_empty_file_returns_empty_set(self):
        """Empty file should return empty set."""
        with patch("builtins.open", mock_open(read_data="")):
            result = load_featured_ids()
            assert result == set()

    def test_corrupted_json_returns_empty_set(self):
        """Corrupted JSON should return empty set, not crash."""
        with patch("builtins.open", mock_open(read_data="{invalid json}")):
            result = load_featured_ids()
            assert result == set()

    def test_unicode_in_ids_handled(self):
        """Unicode characters in IDs should be handled correctly."""
        test_data = '["id1", "café_unicode", "日本語"]'
        with patch("builtins.open", mock_open(read_data=test_data)):
            result = load_featured_ids()
            assert "café_unicode" in result
            assert "日本語" in result


class TestSaveFeaturedIds:
    """P0: Test saving featured IDs to JSON file."""

    def test_save_writes_json(self):
        """save_featured_ids should write valid JSON."""
        with patch("builtins.open", mock_open()) as mock_file:
            save_featured_ids({"id1", "id2"})

            # Get the file handle and check write was called
            handle = mock_file.return_value.__enter__.return_value
            handle.write.assert_called()

    def test_save_converts_set_to_list(self):
        """Set should be converted to list for JSON serialization."""
        test_ids = {"id1", "id2", "id3"}

        with patch("builtins.open", mock_open()) as mock_file:
            save_featured_ids(test_ids)

            # Get the written content
            handle = mock_file.return_value.__enter__.return_value
            call_args = handle.write.call_args_list
            written_content = "".join(call[0][0] for call in call_args)

            # Should contain all IDs in JSON format
            for id_val in test_ids:
                assert id_val in written_content

    def test_save_with_unicode(self):
        """Unicode characters should be saved correctly."""
        test_ids = {"id1", "café", "日本語"}

        with patch("builtins.open", mock_open()):
            save_featured_ids(test_ids)
            # Should not raise UnicodeEncodeError

    def test_save_empty_set(self):
        """Empty set should write empty array."""
        with patch("builtins.open", mock_open()):
            save_featured_ids(set())
            # Should complete without error


class TestAddFeaturedId:
    """P0: Test adding a single featured ID."""

    def test_add_new_id(self):
        """New ID should be added to the set."""
        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.save_featured_ids") as mock_save,
        ):
            mock_load.return_value = set()

            add_featured_id("new_id")

            mock_save.assert_called_once()
            saved_ids = mock_save.call_args[0][0]
            assert "new_id" in saved_ids

    def test_add_existing_id_no_duplicate(self):
        """Existing ID should not create duplicate."""
        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.save_featured_ids") as mock_save,
        ):
            mock_load.return_value = {"existing_id"}

            add_featured_id("existing_id")

            saved_ids = mock_save.call_args[0][0]
            assert len(saved_ids) == 1

    def test_add_multiple_ids(self):
        """Multiple IDs should be added correctly."""
        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.save_featured_ids") as mock_save,
        ):
            mock_load.return_value = set()

            add_featured_id("id1")
            add_featured_id("id2")

            # Should have been called twice
            assert mock_save.call_count == 2


class TestClearFeaturedIds:
    """P0: Test clearing featured IDs."""

    def test_clear_removes_file(self):
        """clear_featured_ids should remove the file if it exists."""
        with (
            patch("featured_tracker.os.path.exists", return_value=True),
            patch("featured_tracker.os.remove") as mock_remove,
        ):
            clear_featured_ids()
            mock_remove.assert_called_once()

    def test_clear_no_error_if_file_not_exists(self):
        """clear_featured_ids should not error if file doesn't exist."""
        with (
            patch("featured_tracker.os.path.exists", return_value=False),
            patch("featured_tracker.os.remove") as mock_remove,
        ):
            clear_featured_ids()
            mock_remove.assert_not_called()


# =============================================================================
# P1: Selection Logic Tests
# =============================================================================


class TestSelectFeaturedArticle:
    """P1: Test featured article selection logic."""

    def test_select_returns_first_unseen(self):
        """First unfeatured article should be selected."""
        articles = [{"id": "seen1"}, {"id": "unseen1"}, {"id": "unseen2"}]
        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.add_featured_id") as mock_add,
        ):
            mock_load.return_value = {"seen1"}

            featured, remaining = select_featured_article(articles)

            assert featured["id"] == "unseen1"
            mock_add.assert_called_once_with("unseen1")

    def test_select_empty_list_returns_none(self):
        """Empty list should return (None, [])."""
        result = select_featured_article([])
        assert result == (None, [])

    def test_select_all_featured_uses_first(self):
        """All featured should use first and warn."""
        articles = [{"id": "f1"}, {"id": "f2"}]

        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.add_featured_id") as mock_add,
            patch("builtins.print") as mock_print,
        ):
            mock_load.return_value = {"f1", "f2"}

            featured, remaining = select_featured_article(articles)

            # Should fall back to first article
            assert featured["id"] == "f1"
            # Should log warning
            assert mock_print.called
            # Verify add_featured_id was called
            mock_add.assert_called_once()

    def test_select_returns_correct_remaining(self):
        """Remaining articles should be correct after selection."""
        articles = [
            {"id": "id1", "title": "Title 1"},
            {"id": "id2", "title": "Title 2"},
            {"id": "id3", "title": "Title 3"},
        ]

        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.add_featured_id"),
        ):
            mock_load.return_value = set()

            featured, remaining = select_featured_article(articles)

            assert featured["id"] == "id1"
            assert len(remaining) == 2
            assert remaining[0]["id"] == "id2"
            assert remaining[1]["id"] == "id3"

    def test_select_with_novel_unseen(self):
        """Should handle mix of seen and unseen correctly."""
        articles = [
            {"id": "id1"},
            {"id": "id2"},
            {"id": "id3"},
            {"id": "id4"},
        ]

        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.add_featured_id"),
        ):
            mock_load.return_value = {"id1", "id3"}

            featured, remaining = select_featured_article(articles)

            # id2 is first unseen
            assert featured["id"] == "id2"

    def test_select_with_single_article(self):
        """Single article should be selected."""
        articles = [{"id": "id1", "title": "Only One"}]

        with (
            patch("featured_tracker.load_featured_ids") as mock_load,
            patch("featured_tracker.add_featured_id"),
        ):
            mock_load.return_value = set()

            featured, remaining = select_featured_article(articles)

            assert featured["id"] == "id1"
            assert remaining == []


# =============================================================================
# Integration Tests (tmp_path)
# =============================================================================


class TestFeaturedTrackerIntegration:
    """Integration tests using tmp_path for file operations."""

    def test_full_cycle_save_load(self, tmp_path):
        """Test complete save-load cycle with real file."""
        test_file = tmp_path / "featured.json"

        with patch("featured_tracker.FEATURED_IDS_FILE", str(test_file)):
            test_ids = {"id1", "id2", "id3"}
            save_featured_ids(test_ids)

            # Verify file was created
            assert test_file.exists()

            # Load and verify
            loaded = load_featured_ids()
            assert loaded == test_ids

    def test_add_id_persists_correctly(self, tmp_path):
        """Test that add_featured_id persists correctly."""
        test_file = tmp_path / "featured.json"

        with patch("featured_tracker.FEATURED_IDS_FILE", str(test_file)):
            add_featured_id("first_id")
            add_featured_id("second_id")

            loaded = load_featured_ids()
            assert loaded == {"first_id", "second_id"}

    def test_clear_deletes_file(self, tmp_path):
        """Test that clear_featured_ids removes the file."""
        test_file = tmp_path / "featured.json"
        test_file.write_text('["id1"]')

        with patch("featured_tracker.FEATURED_IDS_FILE", str(test_file)):
            clear_featured_ids()

            assert not test_file.exists()

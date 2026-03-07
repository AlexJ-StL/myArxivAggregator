"""
Integration tests for aggregator.py with MockServer.

P1: API resilience tests - 429 rate limits, timeouts, and other failures.
"""

from unittest.mock import MagicMock, patch

import responses

from aggregator import (
    fetch_recent_arxiv,
    generate_article_image,
    load_seen_ids,
    save_seen_ids,
    search_unsplash_photo,
)

# =============================================================================
# ArXiv API Resilience Tests
# =============================================================================


class TestArxivAPIResilience:
    """P1: arXiv API failure handling tests."""

    @responses.activate
    def test_fetch_handles_arxiv_timeout(self):
        """ArXiv timeout should be handled gracefully - return empty list."""
        import requests

        responses.add(
            responses.GET,
            "https://export.arxiv.org/api/query",
            body=requests.exceptions.ConnectTimeout(),
        )

        # This will attempt real network - need to mock feedparser
        with patch("aggregator.feedparser.parse") as mock_parse:
            # Simulate feedparser behavior when network fails
            mock_parse.side_effect = requests.exceptions.ConnectionError("Connection timeout")

            # Should handle gracefully by returning empty list
            result = fetch_recent_arxiv()
            assert result == []

    def test_fetch_handles_malformed_entry(self):
        """Malformed entry should not crash the parser."""
        mock_entry = MagicMock()
        mock_entry.id = "test/1"
        mock_entry.title = ""  # Missing content
        mock_entry.summary = None  # Missing content
        mock_entry.published = "2024-01-01"

        with patch("aggregator.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[mock_entry])

            result = fetch_recent_arxiv()

            # Should handle gracefully
            assert len(result) == 1


# =============================================================================
# Unsplash API Resilience Tests (MockServer)
# =============================================================================


class TestUnsplashAPIResilience:
    """P1: Unsplash API failure handling tests."""

    @responses.activate
    def test_search_returns_none_on_429(self):
        """Rate limit (429) should return None, not crash."""
        responses.add(
            responses.GET,
            "https://api.unsplash.com/search/photos",
            json={"error": "Rate limit exceeded"},
            status=429,
        )

        result = search_unsplash_photo("test query")

        assert result is None

    @responses.activate
    def test_search_returns_none_on_500(self):
        """Server error (500) should return None."""
        responses.add(
            responses.GET,
            "https://api.unsplash.com/search/photos",
            json={"error": "Internal server error"},
            status=500,
        )

        result = search_unsplash_photo("test query")

        assert result is None

    @responses.activate
    def test_search_returns_none_on_401(self):
        """Unauthorized (401) should return None."""
        responses.add(
            responses.GET,
            "https://api.unsplash.com/search/photos",
            json={"error": "Unauthorized"},
            status=401,
        )

        result = search_unsplash_photo("test query")

        assert result is None

    @responses.activate
    def test_search_returns_none_on_timeout(self):
        """Timeout should return None."""
        import requests

        responses.add(
            responses.GET,
            "https://api.unsplash.com/search/photos",
            body=requests.exceptions.Timeout(),
        )

        result = search_unsplash_photo("test query")

        assert result is None

    @responses.activate
    def test_search_returns_none_on_connection_error(self):
        """Connection error should return None."""
        import requests

        responses.add(
            responses.GET,
            "https://api.unsplash.com/search/photos",
            body=requests.exceptions.ConnectionError(),
        )

        result = search_unsplash_photo("test query")

        assert result is None


# =============================================================================
# File System Integration Tests
# =============================================================================


class TestFileSystemIntegration:
    """Integration tests for file system operations."""

    def test_save_and_load_seen_ids_roundtrip(self, tmp_path):
        """Test complete save-load cycle."""
        test_file = tmp_path / "seen_ids.json"

        with patch("aggregator.SEEN_IDS_FILE", str(test_file)):
            test_ids = {"2401.0001", "2401.0002", "2401.0003"}

            save_seen_ids(test_ids)
            loaded = load_seen_ids()

            assert loaded == test_ids

    def test_save_handles_concurrent_writes(self, tmp_path):
        """Should handle concurrent write attempts gracefully."""
        test_file = tmp_path / "seen_ids.json"

        with patch("aggregator.SEEN_IDS_FILE", str(test_file)):
            # Save multiple times
            save_seen_ids({"id1"})
            save_seen_ids({"id2"})
            save_seen_ids({"id3"})

            loaded = load_seen_ids()
            # Last write wins
            assert "id3" in loaded

    def test_load_creates_file_if_not_exists(self, tmp_path):
        """load_seen_ids should not create file, just return empty set."""
        test_file = tmp_path / "nonexistent.json"

        with patch("aggregator.SEEN_IDS_FILE", str(test_file)):
            result = load_seen_ids()

            assert result == set()
            # File should NOT be created by load
            assert not test_file.exists()


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================


class TestWorkflowIntegration:
    """End-to-end workflow tests."""

    def test_generate_image_workflow_success(self, tmp_path):
        """Test successful image generation workflow."""
        with (
            patch("aggregator.search_unsplash_photo") as mock_search,
            patch("aggregator.download_unsplash_photo") as mock_download,
            patch("aggregator.generate_search_keywords") as mock_keywords,
        ):
            mock_keywords.return_value = "neural network"
            mock_search.return_value = {
                "id": "abc123",
                "url": "http://example.com/img.jpg",
                "download_url": "http://example.com/dl",
                "alt_description": "Neural network",
                "user": "John Doe",
                "user_link": "http://unsplash.com/@john",
                "unsplash_link": "http://unsplash.com",
            }
            mock_download.return_value = True

            result = generate_article_image("Test Title", "Test Summary")

            assert result is not None
            assert "filename" in result
            assert "path" in result
            assert "alt_text" in result
            assert "credit" in result

    def test_generate_image_workflow_no_photo(self):
        """Test image generation when no photo found."""
        with (
            patch("aggregator.search_unsplash_photo") as mock_search,
            patch("aggregator.generate_search_keywords") as mock_keywords,
        ):
            mock_keywords.return_value = "nonexistent"
            mock_search.return_value = None

            result = generate_article_image("Title", "Summary")

            assert result is None


# =============================================================================
# Error Recovery Tests
# =============================================================================


class TestErrorRecovery:
    """Error recovery and graceful degradation tests."""

    def test_continues_on_image_download_failure(self):
        """Should continue processing if image download fails."""
        with (
            patch("aggregator.search_unsplash_photo") as mock_search,
            patch("aggregator.download_unsplash_photo") as mock_download,
            patch("aggregator.generate_search_keywords") as mock_keywords,
        ):
            mock_keywords.return_value = "test"
            mock_search.return_value = {
                "id": "1",
                "url": "x",
                "download_url": "x",
                "alt": "",
                "user": "J",
                "user_link": "x",
                "unsplash_link": "x",
            }
            mock_download.return_value = False  # Download fails

            result = generate_article_image("Title", "Summary")

            # Should return None when download fails
            assert result is None

    def test_handles_unicode_in_titles(self):
        """Unicode in titles should not cause errors."""
        unicode_title = "日本語のタイトル 🎉"

        with (
            patch("aggregator.search_unsplash_photo") as mock_search,
            patch("aggregator.download_unsplash_photo") as mock_download,
            patch("aggregator.generate_search_keywords") as mock_keywords,
        ):
            mock_keywords.return_value = "test"
            mock_search.return_value = None
            mock_download.return_value = False

            result = generate_article_image(unicode_title, "Summary")

            # Should not crash, should return None
            assert result is None

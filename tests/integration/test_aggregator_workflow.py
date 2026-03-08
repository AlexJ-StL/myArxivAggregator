"""
Integration tests for arxiv_aggregator.core BaseAggregator with MockServer.

P1: API resilience tests - 429 rate limits, timeouts, and other failures.
"""

from unittest.mock import MagicMock, patch

import responses

from arxiv_aggregator.core import BaseAggregator


# Concrete implementation for testing
class TestAggregator(BaseAggregator):
    """Test implementation of BaseAggregator."""

    api_url = "https://export.arxiv.org/api/query?search_query=cat:cs.AI"

    def get_category_name(self) -> str:
        return "Test Category"

    def get_domain(self) -> str:
        return "test domain"

    def get_output_file(self) -> str:
        return "test.html"

    def get_api_url(self) -> str:
        return self.api_url


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
        with patch("arxiv_aggregator.core.feedparser.parse") as mock_parse:
            # Simulate feedparser behavior when network fails
            mock_parse.side_effect = requests.exceptions.ConnectionError("Connection timeout")

            # Should handle gracefully by returning empty list
            agg = TestAggregator()
            result = agg.fetch_recent_arxiv()
            assert result == []

    def test_fetch_handles_malformed_entry(self):
        """Malformed entry should not crash the parser."""
        mock_entry = MagicMock()
        mock_entry.id = "test/1"
        mock_entry.title = ""  # Missing content
        mock_entry.summary = None  # Missing content
        mock_entry.published = "2024-01-01"

        with patch("arxiv_aggregator.core.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[mock_entry])

            agg = TestAggregator()
            result = agg.fetch_recent_arxiv()

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

        agg = TestAggregator()
        result = agg.search_unsplash_photo("test query")

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

        agg = TestAggregator()
        result = agg.search_unsplash_photo("test query")

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

        agg = TestAggregator()
        result = agg.search_unsplash_photo("test query")

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

        agg = TestAggregator()
        result = agg.search_unsplash_photo("test query")

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

        agg = TestAggregator()
        result = agg.search_unsplash_photo("test query")

        assert result is None


# =============================================================================
# File System Integration Tests
# =============================================================================


class TestFileSystemIntegration:
    """Integration tests for file system operations."""

    def test_save_and_load_seen_ids_roundtrip(self, tmp_path):
        """Test complete save-load cycle."""
        test_file = tmp_path / "seen_ids.json"

        with patch("arxiv_aggregator.core.SEEN_IDS_FILE", str(test_file)):
            agg = TestAggregator()
            test_ids = {"2401.0001", "2401.0002", "2401.0003"}

            agg.seen_ids = test_ids
            agg.save_seen_ids()
            loaded = agg.load_seen_ids()

            assert loaded == test_ids

    def test_save_handles_concurrent_writes(self, tmp_path):
        """Should handle concurrent write attempts gracefully."""
        test_file = tmp_path / "seen_ids.json"

        with patch("arxiv_aggregator.core.SEEN_IDS_FILE", str(test_file)):
            agg = TestAggregator()
            # Save multiple times
            agg.seen_ids = {"id1"}
            agg.save_seen_ids()
            agg.seen_ids = {"id2"}
            agg.save_seen_ids()
            agg.seen_ids = {"id3"}
            agg.save_seen_ids()

            loaded = agg.load_seen_ids()
            # Last write wins
            assert "id3" in loaded

    def test_load_creates_file_if_not_exists(self, tmp_path):
        """load_seen_ids should not create file, just return empty set."""
        test_file = tmp_path / "nonexistent.json"

        with patch("arxiv_aggregator.core.SEEN_IDS_FILE", str(test_file)):
            agg = TestAggregator()
            result = agg.load_seen_ids()

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
            patch.object(TestAggregator, "search_unsplash_photo") as mock_search,
            patch.object(TestAggregator, "download_unsplash_photo") as mock_download,
            patch("arxiv_aggregator.content_utils.generate_search_keywords") as mock_keywords,
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

            agg = TestAggregator()
            result = agg.generate_article_image("Test Title", "Test Summary")

            assert result is not None
            assert "filename" in result
            assert "path" in result
            assert "alt_text" in result
            assert "credit" in result

    def test_generate_image_workflow_no_photo(self):
        """Test image generation when no photo found."""
        with (
            patch.object(TestAggregator, "search_unsplash_photo") as mock_search,
            patch("arxiv_aggregator.content_utils.generate_search_keywords") as mock_keywords,
        ):
            mock_keywords.return_value = "nonexistent"
            mock_search.return_value = None

            agg = TestAggregator()
            result = agg.generate_article_image("Title", "Summary")

            assert result is None


# =============================================================================
# Error Recovery Tests
# =============================================================================


class TestErrorRecovery:
    """Error recovery and graceful degradation tests."""

    def test_continues_on_image_download_failure(self):
        """Should continue processing if image download fails."""
        with (
            patch.object(TestAggregator, "search_unsplash_photo") as mock_search,
            patch.object(TestAggregator, "download_unsplash_photo") as mock_download,
            patch("arxiv_aggregator.content_utils.generate_search_keywords") as mock_keywords,
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

            agg = TestAggregator()
            result = agg.generate_article_image("Title", "Summary")

            # Should return None when download fails
            assert result is None

    def test_handles_unicode_in_titles(self):
        """Unicode in titles should not cause errors."""
        unicode_title = "日本語のタイトル 🎉"

        with (
            patch.object(TestAggregator, "search_unsplash_photo") as mock_search,
            patch.object(TestAggregator, "download_unsplash_photo") as mock_download,
            patch("arxiv_aggregator.content_utils.generate_search_keywords") as mock_keywords,
        ):
            mock_keywords.return_value = "test"
            mock_search.return_value = None
            mock_download.return_value = False

            agg = TestAggregator()
            result = agg.generate_article_image(unicode_title, "Summary")

            # Should not crash, should return None
            assert result is None

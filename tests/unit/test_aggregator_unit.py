"""
Unit tests for aggregator.py module.

P1: Workflow and resilience tests with mocks.
"""

from unittest.mock import MagicMock, mock_open, patch

from aggregator import (
    download_unsplash_photo,
    fetch_recent_arxiv,
    generate_article_image,
    load_seen_ids,
    save_seen_ids,
    search_unsplash_photo,
    upload_via_ftp,
)

# =============================================================================
# Test load_seen_ids
# =============================================================================


class TestLoadSeenIds:
    """Tests for load_seen_ids function."""

    def test_load_returns_set(self):
        """load_seen_ids should return a set."""
        with patch("builtins.open", mock_open(read_data='["id1", "id2"]')):
            result = load_seen_ids()
            assert isinstance(result, set)

    def test_load_parses_json(self):
        """JSON should be parsed correctly."""
        with patch("builtins.open", mock_open(read_data='["id1", "id2"]')):
            result = load_seen_ids()
            assert result == {"id1", "id2"}

    def test_file_not_found_returns_empty_set(self):
        """Missing file should return empty set."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = load_seen_ids()
            assert result == set()

    def test_empty_file_returns_empty_set(self):
        """Empty file should return empty set."""
        with patch("builtins.open", mock_open(read_data="")):
            result = load_seen_ids()
            assert result == set()


# =============================================================================
# Test save_seen_ids
# =============================================================================


class TestSaveSeenIds:
    """Tests for save_seen_ids function."""

    def test_save_writes_json(self):
        """save_seen_ids should write JSON."""
        with patch("builtins.open", mock_open()) as mock_file:
            save_seen_ids({"id1", "id2"})

            handle = mock_file.return_value.__enter__.return_value
            handle.write.assert_called()

    def test_save_empty_set(self):
        """Empty set should write empty array."""
        with patch("builtins.open", mock_open()):
            save_seen_ids(set())
            # Should not raise error


# =============================================================================
# Test fetch_recent_arxiv
# =============================================================================


class TestFetchRecentArxiv:
    """Tests for fetch_recent_arxiv function."""

    def test_returns_list(self):
        """Should return a list of articles."""
        with patch("aggregator.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[])

            result = fetch_recent_arxiv()
            assert isinstance(result, list)

    def test_parses_entry_correctly(self):
        """Entry should be parsed to dict."""
        mock_entry = MagicMock()
        mock_entry.id = "http://arxiv.org/abs/2401.00001v1"
        mock_entry.title = "Test Title"
        mock_entry.summary = "Test Summary"
        mock_entry.published = "2024-01-15T12:00:00Z"

        with patch("aggregator.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[mock_entry])

            result = fetch_recent_arxiv()

            assert len(result) == 1
            assert result[0]["id"] == "http://arxiv.org/abs/2401.00001v1"
            assert result[0]["title"] == "Test Title"
            assert result[0]["summary"] == "Test Summary"

    def test_handles_missing_title(self):
        """Missing title should use default."""
        mock_entry = MagicMock()
        mock_entry.id = "http://arxiv.org/abs/2401.00001v1"
        mock_entry.title = ""
        mock_entry.summary = "Summary"
        mock_entry.published = "2024-01-15"

        with patch("aggregator.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[mock_entry])

            result = fetch_recent_arxiv()

            # Should handle gracefully
            assert len(result) == 1
            assert result[0]["title"] == ""

    def test_handles_missing_summary(self):
        """Missing summary should use default."""
        mock_entry = MagicMock()
        mock_entry.id = "http://arxiv.org/abs/2401.00001v1"
        mock_entry.title = "Title"
        mock_entry.summary = None
        mock_entry.published = "2024-01-15"

        with patch("aggregator.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[mock_entry])

            result = fetch_recent_arxiv()

            assert len(result) == 1
            assert result[0]["summary"] is None

    def test_empty_feed_returns_empty_list(self):
        """Empty feed should return empty list."""
        with patch("aggregator.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[])

            result = fetch_recent_arxiv()
            assert result == []


# =============================================================================
# Test search_unsplash_photo
# =============================================================================


class TestSearchUnsplashPhoto:
    """Tests for search_unsplash_photo function."""

    def test_returns_none_on_error(self):
        """Error should return None."""
        import requests

        with patch("aggregator.requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError()

            result = search_unsplash_photo("test query")
            assert result is None

    def test_returns_none_on_http_error(self):
        """HTTP error should return None."""
        import requests

        with patch("aggregator.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError()
            mock_get.return_value = mock_response

            result = search_unsplash_photo("test query")
            assert result is None

    def test_returns_none_on_no_results(self):
        """No results should return None."""
        with patch("aggregator.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"total": 0, "results": []}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = search_unsplash_photo("nonexistent query")
            assert result is None

    def test_parses_photo_correctly(self):
        """Photo data should be parsed correctly."""
        mock_photo = {
            "id": "abc123",
            "urls": {"small": "small.jpg", "regular": "regular.jpg"},
            "links": {"download_location": "download_url"},
            "alt_description": "Test image",
            "user": {"name": "John Doe", "links": {"html": "https://unsplash.com/@john"}},
        }

        with patch("aggregator.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": [mock_photo]}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = search_unsplash_photo("test query", is_featured=True)

            assert result is not None
            assert result["id"] == "abc123"
            assert result["user"] == "John Doe"
            assert "utm_source" in result["user_link"]

    def test_uses_regular_for_featured(self):
        """Featured should use regular size URL."""
        mock_photo = {
            "id": "abc123",
            "urls": {"small": "small.jpg", "regular": "regular.jpg"},
            "links": {"download_location": "download_url"},
            "alt_description": "",
            "user": {"name": "John", "links": {"html": "https://unsplash.com/@john"}},
        }

        with patch("aggregator.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": [mock_photo]}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = search_unsplash_photo("test", is_featured=True)

            assert result["url"] == "regular.jpg"

    def test_uses_small_for_non_featured(self):
        """Non-featured should use small size URL."""
        mock_photo = {
            "id": "abc123",
            "urls": {"small": "small.jpg", "regular": "regular.jpg"},
            "links": {"download_location": "download_url"},
            "alt_description": "",
            "user": {"name": "John", "links": {"html": "https://unsplash.com/@john"}},
        }

        with patch("aggregator.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": [mock_photo]}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = search_unsplash_photo("test", is_featured=False)

            assert result["url"] == "small.jpg"


# =============================================================================
# Test download_unsplash_photo
# =============================================================================


class TestDownloadUnsplashPhoto:
    """Tests for download_unsplash_photo function."""

    def test_returns_false_on_download_error(self):
        """Download error should return False."""
        import requests

        with patch("aggregator.requests.get") as mock_get:
            # First call (download trigger) succeeds, second fails
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # Make the second get raise error
            mock_get.side_effect = [mock_response, requests.HTTPError()]

            photo_data = {
                "id": "test",
                "url": "http://example.com/image.jpg",
                "download_url": "http://example.com/download",
            }

            result = download_unsplash_photo(photo_data, "test.jpg")
            assert result is False


# =============================================================================
# Test generate_article_image
# =============================================================================


class TestGenerateArticleImage:
    """Tests for generate_article_image function."""

    def test_returns_none_when_no_photo_found(self):
        """No photo found should return None."""
        with patch("aggregator.search_unsplash_photo") as mock_search:
            mock_search.return_value = None

            result = generate_article_image("Title", "Summary")
            assert result is None

    def test_creates_filename_from_hash(self):
        """Filename should be based on MD5 hash of title."""
        with (
            patch("aggregator.search_unsplash_photo") as mock_search,
            patch("aggregator.download_unsplash_photo") as mock_download,
        ):
            mock_search.return_value = {
                "id": "abc",
                "url": "http://x.com/img.jpg",
                "download_url": "http://x.com/dl",
                "alt_description": "test",
                "user": "John",
                "user_link": "http://x.com/john",
                "unsplash_link": "http://unsplash.com",
            }
            mock_download.return_value = True

            result = generate_article_image("Test Title", "Summary")

            assert result is not None
            assert "filename" in result
            assert result["filename"].startswith("article_")
            assert result["filename"].endswith(".jpg")


# =============================================================================
# Test upload_via_ftp
# =============================================================================


class TestUploadViaFTP:
    """Tests for upload_via_ftp function."""

    def test_logs_error_on_missing_credentials(self):
        """Missing credentials should log error and not upload."""
        with (
            patch("aggregator.FTP_HOST", None),
            patch("aggregator.FTP_USER", ""),
            patch("aggregator.FTP_PASS", ""),
            patch("builtins.print") as mock_print,
        ):
            upload_via_ftp("output")

            # Should log error
            assert any("missing" in str(c).lower() for c in mock_print.call_args_list)

    def test_does_not_crash_on_missing_credentials(self):
        """Missing credentials should not crash."""
        with (
            patch("aggregator.FTP_HOST", None),
            patch("aggregator.FTP_USER", ""),
            patch("aggregator.FTP_PASS", ""),
        ):
            # Should not raise
            upload_via_ftp("output")

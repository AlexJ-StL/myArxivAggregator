"""
Pytest configuration and shared fixtures for myArxivAggregator test suite.

This module provides:
- MockNetwork: Intercepts network calls to ensure deterministic testing
- Fixtures for file system isolation
- Sample data for tests
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import responses

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up test environment variables BEFORE importing project modules
os.environ.setdefault("FTP_HOST", "test.example.com")
os.environ.setdefault("FTP_USER", "testuser")
os.environ.setdefault("FTP_PASS", "testpass")
os.environ.setdefault("UNSPLASH_ACCESS_KEY", "test_key")
os.environ.setdefault("UNSPLASH_SECRET_KEY", "test_secret")
os.environ.setdefault("UNSPLASH_APPLICATION_ID", "test_app_id")
os.environ.setdefault("OLLAMA_MODEL", "test_model")
os.environ.setdefault("OLLAMA_API_URL", "http://localhost:11434/api/generate")


# =============================================================================
# Network Resilience Mocks (MockServer)
# =============================================================================


@pytest.fixture(autouse=True)
def mock_network_responses():
    """
    Globally intercepts network calls during tests to ensure no
    real API requests are made (First Principles: Determinism).
    """
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def mock_arxiv_timeout(mock_network_responses):
    """Simulates a 3rd-order consequence: arXiv API timing out."""
    import requests

    mock_network_responses.add(
        responses.GET,
        "https://export.arxiv.org/api/query",
        body=requests.exceptions.ConnectTimeout(),
    )


@pytest.fixture
def mock_arxiv_connection_error(mock_network_responses):
    """Simulates arXiv API connection error."""
    import requests

    mock_network_responses.add(
        responses.GET,
        "https://export.arxiv.org/api/query",
        body=requests.exceptions.ConnectionError(),
    )


@pytest.fixture
def mock_unsplash_rate_limit(mock_network_responses):
    """Simulates Unsplash API rate limiting (HTTP 429)."""
    mock_network_responses.add(
        responses.GET,
        "https://api.unsplash.com/search/photos",
        json={"error": "Rate limit exceeded", "errors": ["Rate limit exceeded"]},
        status=429,
    )


@pytest.fixture
def mock_unsplash_server_error(mock_network_responses):
    """Simulates Unsplash API 500 error."""
    mock_network_responses.add(
        responses.GET,
        "https://api.unsplash.com/search/photos",
        json={"error": "Internal server error"},
        status=500,
    )


@pytest.fixture
def mock_unsplash_not_found(mock_network_responses):
    """Simulates Unsplash API 404 error (no results)."""
    mock_network_responses.add(
        responses.GET,
        "https://api.unsplash.com/search/photos",
        json={"total": 0, "total_pages": 0, "results": []},
        status=200,
    )


# =============================================================================
# State & File System Integrity
# =============================================================================


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provides a clean, isolated directory for generated HTML and images."""
    d = tmp_path / "output"
    d.mkdir()
    (d / "images").mkdir()
    return d


@pytest.fixture
def mock_seen_ids_file(tmp_path):
    """Creates an isolated state file to prevent 're-publishing' spam during tests."""
    file_path = tmp_path / "seen_arxiv_ids.json"
    initial_data = ["2401.0001", "2401.0002"]
    file_path.write_text(json.dumps(initial_data))
    return str(file_path)


@pytest.fixture
def mock_featured_ids_file(tmp_path):
    """Creates an isolated featured IDs file for testing."""
    file_path = tmp_path / "featured_arxiv_ids.json"
    initial_data = ["2401.0001"]
    file_path.write_text(json.dumps(initial_data))
    return str(file_path)


@pytest.fixture
def temp_working_dir(tmp_path, monkeypatch):
    """Creates a temporary working directory with all required subdirectories."""
    working_dir = tmp_path / "arxiv_aggregator"
    working_dir.mkdir()
    (working_dir / "output").mkdir()
    (working_dir / "output" / "images").mkdir()
    (working_dir / "templates").mkdir()

    # Create a minimal template for testing
    template_content = """<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<main><!--ARTICLES_PLACEHOLDER--></main>
<aside><!--SIDEBAR_ARTICLES_PLACEHOLDER--></aside>
</body>
</html>"""
    (working_dir / "templates" / "base_template.html").write_text(template_content)

    # Change to temp directory
    monkeypatch.chdir(working_dir)
    return working_dir


# =============================================================================
# LLM & API Mocking
# =============================================================================


@pytest.fixture
def mock_ollama_success():
    """Mock successful Ollama API response."""

    def create_response(text: str):
        def generate():
            yield b'{"response": "' + text.encode() + b'", "done": true}'

        return generate

    return create_response


@pytest.fixture
def mock_ollama_failure():
    """Mock failed Ollama API call."""
    import requests

    def raise_error():
        raise requests.RequestException("Connection refused")

    return raise_error


@pytest.fixture
def sample_llm_response():
    """Standard 'noisy' LLM output for testing cleaning logic."""
    return (
        "Sure! Here is a headline: The Future of Neural Networks. (I removed the jargon for you.)"
    )


@pytest.fixture
def sample_arxiv_entry():
    """Standard arXiv API entry."""
    return {
        "id": "http://arxiv.org/abs/2401.00001v1",
        "title": "Advances in Neural Network Architecture Search",
        "summary": "We present a novel method for automated machine learning...",
        "published": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def sample_arxiv_feed(sample_arxiv_entry):
    """Complete arXiv feed structure."""
    return {
        "entries": [sample_arxiv_entry],
    }


# =============================================================================
# Mock Objects
# =============================================================================


@pytest.fixture
def mock_feed_entry():
    """Create a mock feedparser entry."""
    entry = MagicMock()
    entry.id = "http://arxiv.org/abs/2401.00001v1"
    entry.title = "Advances in Neural Network Architecture Search"
    entry.summary = "We present a novel method for automated machine learning..."
    entry.published = "2024-01-15T12:00:00Z"
    return entry


@pytest.fixture
def mock_article_dict():
    """Standard article dictionary structure."""
    return {
        "id": "2401.00001",
        "title": "Test Article Title",
        "blurb": "This is a test summary blurb for the article.",
        "url": "http://arxiv.org/abs/2401.00001",
        "featured": False,
    }


@pytest.fixture
def mock_article_with_image(mock_article_dict):
    """Article with image metadata."""
    return {
        **mock_article_dict,
        "image": {
            "filename": "article_abc123.jpg",
            "path": "images/article_abc123.jpg",
            "alt_text": "Neural network diagram",
            "credit": "Photo by John Doe on Unsplash",
            "credit_link": "https://unsplash.com/@johndoe",
            "unsplash_link": "https://unsplash.com/",
        },
    }


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def clean_config():
    """Reload config module with test environment."""
    # Save original environment
    original_env = os.environ.copy()

    # Set test environment variables
    test_env = {
        "FTP_HOST": "test.example.com",
        "FTP_USER": "testuser",
        "FTP_PASS": "testpass",
        "UNSPLASH_ACCESS_KEY": "test_key",
        "UNSPLASH_SECRET_KEY": "test_secret",
        "UNSPLASH_APPLICATION_ID": "test_app_id",
        "OLLAMA_MODEL": "test_model",
        "OLLAMA_API_URL": "http://localhost:11434/api/generate",
    }
    os.environ.update(test_env)

    # Reload config
    import importlib

    from arxiv_aggregator import config

    importlib.reload(config)

    yield config

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def missing_env_vars():
    """Fixture that simulates missing environment variables."""
    # Save original environment
    original_env = os.environ.copy()

    # Remove critical vars
    critical_vars = [
        "FTP_HOST",
        "FTP_USER",
        "FTP_PASS",
        "UNSPLASH_ACCESS_KEY",
        "UNSPLASH_SECRET_KEY",
        "UNSPLASH_APPLICATION_ID",
    ]
    for var in critical_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# =============================================================================
# Helper Fixtures
# =============================================================================


@pytest.fixture
def sample_articles_list():
    """Generate a list of sample articles for testing."""
    return [
        {
            "id": f"2401.0000{i}",
            "title": f"Test Article Title {i}",
            "blurb": f"Test summary for article {i}. This describes the research.",
            "url": f"http://arxiv.org/abs/2401.0000{i}",
        }
        for i in range(1, 8)
    ]


@pytest.fixture
def sample_articles_with_featured(sample_articles_list):
    """Articles list with one marked as featured."""
    articles = sample_articles_list.copy()
    articles[0]["featured"] = True
    return articles


# =============================================================================
# Patch Targets
# =============================================================================


@pytest.fixture
def patch_ollama():
    """Patch Ollama API calls."""
    return patch("arxiv_aggregator.content_utils.call_ollama")


@pytest.fixture
def patch_featured_tracker_file():
    """Patch featured tracker file path."""
    return patch("arxiv_aggregator.featured_tracker.FEATURED_IDS_FILE")


@pytest.fixture
def patch_seen_ids_file():
    """Patch seen IDs file path."""
    return patch("arxiv_aggregator.config.SEEN_IDS_FILE")


@pytest.fixture
def patch_template_path():
    """Patch template paths."""
    return patch("arxiv_aggregator.generate_html.TEMPLATE_PATH")

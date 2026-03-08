"""
Unit tests for config.py module.

P0: Critical tests for configuration validation and typo fixes.
"""

import importlib
import os


class TestConfigTypoFix:
    """
    P0: Test that the pysortBy typo in ARXIV_CR_URL is fixed.
    This test will FAIL before the fix and PASS after.
    """

    def test_arxiv_cr_url_has_sortby_parameter(self):
        """ARXIV_CR_URL must use 'sortBy' parameter, not 'pysortBy'."""
        # Import fresh to avoid cached imports
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert "sortBy=" in config.ARXIV_CR_URL, "ARXIV_CR_URL must contain 'sortBy=' parameter"

    def test_arxiv_cr_url_has_no_typo(self):
        """ARXIV_CR_URL must NOT contain the 'pysortBy' typo."""
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert "pysortBy" not in config.ARXIV_CR_URL, (
            "ARXIV_CR_URL contains the typo 'pysortBy' - should be 'sortBy'"
        )


class TestConfigURLProtocol:
    """P1: Test URL protocol consistency."""

    def test_arxiv_api_url_uses_https(self):
        """ARXIV_API_URL should use HTTPS."""
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert config.ARXIV_API_URL.startswith("https://"), (
            "ARXIV_API_URL should use HTTPS for secure data transport"
        )

    def test_arxiv_ml_url_uses_https(self):
        """ARXIV_ML_URL should use HTTPS."""
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert config.ARXIV_ML_URL.startswith("https://"), "ARXIV_ML_URL should use HTTPS"

    def test_arxiv_cv_url_uses_https(self):
        """ARXIV_CV_URL should use HTTPS."""
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert config.ARXIV_CV_URL.startswith("https://"), "ARXIV_CV_URL should use HTTPS"

    def test_arxiv_ro_url_uses_https(self):
        """ARXIV_RO_URL should use HTTPS."""
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert config.ARXIV_RO_URL.startswith("https://"), "ARXIV_RO_URL should use HTTPS"

    def test_arxiv_cr_url_uses_https(self):
        """ARXIV_CR_URL should use HTTPS."""
        import arxiv_aggregator.config as config

        importlib.reload(config)

        assert config.ARXIV_CR_URL.startswith("https://"), "ARXIV_CR_URL should use HTTPS"


class TestConfigDefaults:
    """P1: Test fallback default values."""

    def test_ollama_model_has_default(self):
        """OLLAMA_MODEL should have a default value."""
        # Save original environment
        original_env = os.environ.copy()

        # Set required env vars for config to load
        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert config.OLLAMA_MODEL is not None
            assert isinstance(config.OLLAMA_MODEL, str)
            assert len(config.OLLAMA_MODEL) > 0
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_ollama_api_url_has_default(self):
        """OLLAMA_API_URL should have a default value."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert config.OLLAMA_API_URL is not None
            assert "localhost" in config.OLLAMA_API_URL or "127.0.0.1" in config.OLLAMA_API_URL
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_ftp_remote_dir_has_default(self):
        """FTP_REMOTE_DIR should have a default value."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert config.FTP_REMOTE_DIR is not None
            assert config.FTP_REMOTE_DIR == "."
        finally:
            os.environ.clear()
            os.environ.update(original_env)


class TestConfigURLs:
    """P1: Test URL structure validity."""

    def test_arxiv_api_url_contains_query(self):
        """arXiv API URLs should contain search query parameters."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            # Check that URL contains expected parameters
            assert "cat:cs.AI" in config.ARXIV_API_URL
            assert "sortBy=" in config.ARXIV_API_URL or "sortBy" in config.ARXIV_API_URL
            assert "max_results=" in config.ARXIV_API_URL
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_arxiv_ml_url_category(self):
        """ARXIV_ML_URL should query cs.LG category."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert "cat:cs.LG" in config.ARXIV_ML_URL
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_arxiv_cv_url_category(self):
        """ARXIV_CV_URL should query cs.CV category."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert "cat:cs.CV" in config.ARXIV_CV_URL
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_arxiv_ro_url_category(self):
        """ARXIV_RO_URL should query cs.RO category."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert "cat:cs.RO" in config.ARXIV_RO_URL
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_arxiv_cr_url_category(self):
        """ARXIV_CR_URL should query cs.CR category."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert "cat:cs.CR" in config.ARXIV_CR_URL
        finally:
            os.environ.clear()
            os.environ.update(original_env)


class TestConfigUnsplash:
    """P1: Test Unsplash configuration."""

    def test_unsplash_api_url_correct(self):
        """UNSPLASH_API_URL should point to correct endpoint."""
        original_env = os.environ.copy()

        os.environ["FTP_HOST"] = "test.com"
        os.environ["FTP_USER"] = "test"
        os.environ["FTP_PASS"] = "test"
        os.environ["UNSPLASH_ACCESS_KEY"] = "key"
        os.environ["UNSPLASH_SECRET_KEY"] = "secret"
        os.environ["UNSPLASH_APPLICATION_ID"] = "app"

        try:
            import arxiv_aggregator.config as config

            importlib.reload(config)

            assert "api.unsplash.com" in config.UNSPLASH_API_URL
            assert config.UNSPLASH_API_URL == "https://api.unsplash.com"
        finally:
            os.environ.clear()
            os.environ.update(original_env)

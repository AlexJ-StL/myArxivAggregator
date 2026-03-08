"""
Unit tests for generate_html.py module.

P0: XSS prevention tests
P1: HTML generation functionality tests
"""

from unittest.mock import mock_open, patch

import pytest

from arxiv_aggregator.generate_html import (
    clean_headline,
    convert_to_pdf_url,
    generate_html,
    load_template,
)

# =============================================================================
# P0: XSS Prevention Tests
# =============================================================================


class TestGenerateHTMLXSS:
    """P0: XSS prevention in HTML generation."""

    def test_xss_in_title_is_escaped(self):
        """XSS attempts in titles must be neutralized."""
        articles = [
            {
                "id": "1",
                "title": "<script>alert('xss')</script>",
                "blurb": "Test blurb",
                "url": "http://arxiv.org/abs/1",
            }
        ]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "<script>" not in html
            assert "</script>" not in html
            assert "alert" not in html.lower()

    def test_xss_in_blurb_is_escaped(self):
        """XSS in blurbs must be neutralized."""
        articles = [
            {
                "id": "1",
                "title": "Title",
                "blurb": "<img onerror=alert(1) src=x>",
                "url": "http://arxiv.org/abs/1",
            }
        ]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "<img" not in html
            assert "onerror" not in html.lower()

    def test_javascript_url_rejected(self):
        """javascript: URLs should not appear in output."""
        articles = [{"id": "1", "title": "Title", "blurb": "Blurb", "url": "javascript:alert(1)"}]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "javascript:" not in html.lower()

    def test_svg_onload_is_blocked(self):
        """SVG onload events should be blocked."""
        articles = [
            {
                "id": "1",
                "title": "Title",
                "blurb": "<svg onload=alert(1)>",
                "url": "http://arxiv.org/abs/1",
            }
        ]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "<svg" not in html
            assert "onload" not in html.lower()

    def test_iframe_is_blocked(self):
        """iframe tags should be blocked."""
        articles = [
            {
                "id": "1",
                "title": "Title",
                "blurb": "<iframe src='evil.com'></iframe>",
                "url": "http://arxiv.org/abs/1",
            }
        ]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "<iframe" not in html


# =============================================================================
# P1: HTML Structure Tests
# =============================================================================


class TestCleanHeadline:
    """P1: Headline cleaning tests."""

    def test_removes_trailing_period(self):
        """Headlines should not end with periods."""
        assert clean_headline("Title.") == "Title"

    def test_preserves_no_period(self):
        """Headlines without periods should be unchanged."""
        assert clean_headline("No Period") == "No Period"

    def test_multiple_trailing_dots(self):
        """Multiple trailing dots should be handled."""
        assert clean_headline("Multiple..") == "Multiple."
        assert clean_headline("Multiple...") == "Multiple.."

    def test_preserves_trailing_spaces(self):
        """Internal spaces should be preserved (not leading/trailing)."""
        # Note: This tests that we only strip trailing periods, not all trailing whitespace
        assert clean_headline("Title.") == "Title"
        assert clean_headline("Title.  ") == "Title"

    def test_unicode_handled(self):
        """Unicode characters should be handled correctly."""
        assert clean_headline("タイトル.") == "タイトル"
        assert clean_headline("Café.") == "Café"


class TestConvertToPdfUrl:
    """P1: URL conversion tests."""

    def test_converts_abs_to_pdf(self):
        """Standard /abs/ to /pdf/ conversion."""
        result = convert_to_pdf_url("http://arxiv.org/abs/2301.12345")
        assert result == "http://arxiv.org/pdf/2301.12345"

    def test_preserves_https(self):
        """HTTPS URLs should be preserved."""
        result = convert_to_pdf_url("https://arxiv.org/abs/2301.12345")
        assert result.startswith("https://")

    def test_preserves_already_pdf(self):
        """PDF URLs should be unchanged."""
        result = convert_to_pdf_url("http://arxiv.org/pdf/2301.12345")
        assert result == "http://arxiv.org/pdf/2301.12345"

    def test_handles_version_suffix(self):
        """URLs with version suffixes should work."""
        result = convert_to_pdf_url("http://arxiv.org/abs/2301.12345v2")
        assert result == "http://arxiv.org/pdf/2301.12345v2"

    def test_handles_different_formats(self):
        """Different arXiv URL formats should be handled."""
        # Old format
        result = convert_to_pdf_url("http://arxiv.org/abs/cond-mat/0601001")
        assert result == "http://arxiv.org/pdf/cond-mat/0601001"


class TestGenerateHTMLStructure:
    """P1: HTML structure validation."""

    @pytest.fixture
    def minimal_template(self):
        """Minimal template for testing."""
        return """<!DOCTYPE html>
<html>
<head><title>{date} - AI Research</title></head>
<body>
<main><!--ARTICLES_PLACEHOLDER--></main>
<aside><!--SIDEBAR_ARTICLES_PLACEHOLDER--></aside>
</body>
</html>"""

    def test_creates_featured_section(self, minimal_template):
        """Featured article should be in featured section."""
        articles = [
            {
                "id": "1",
                "title": "Featured Title",
                "blurb": "Featured blurb",
                "url": "http://arxiv.org/abs/1",
                "featured": True,
            }
        ]

        with patch("generate_html.load_template", return_value=minimal_template):
            html = generate_html(articles)

            assert "FEATURED" in html
            assert "featured-article" in html

    def test_default_first_as_featured(self, minimal_template):
        """When no featured flag, first article should be featured."""
        articles = [
            {"id": "1", "title": "First", "blurb": "Blurb 1", "url": "http://x.com/1"},
            {"id": "2", "title": "Second", "blurb": "Blurb 2", "url": "http://x.com/2"},
        ]

        with patch("generate_html.load_template", return_value=minimal_template):
            html = generate_html(articles)

            assert "FEATURED" in html

    def test_sidebar_contains_last_three(self, minimal_template):
        """When >3 articles, last 3 should be in sidebar."""
        articles = [
            {
                "id": str(i),
                "title": f"Title {i}",
                "blurb": f"Blurb {i}",
                "url": f"http://x.com/{i}",
            }
            for i in range(7)
        ]

        with patch("generate_html.load_template", return_value=minimal_template):
            html = generate_html(articles)

            # Should have sidebar articles
            assert "sidebar-article" in html

    def test_no_sidebar_for_three_or_fewer(self, minimal_template):
        """Three or fewer articles should not have sidebar."""
        articles = [
            {"id": "1", "title": "T1", "blurb": "B1", "url": "http://x.com/1"},
            {"id": "2", "title": "T2", "blurb": "B2", "url": "http://x.com/2"},
            {"id": "3", "title": "T3", "blurb": "B3", "url": "http://x.com/3"},
        ]

        with patch("generate_html.load_template", return_value=minimal_template):
            html = generate_html(articles)

            # Should have articles in main grid, not sidebar
            assert "sidebar-article" not in html or html.count("sidebar-article") == 0

    def test_converts_to_pdf_link(self, minimal_template):
        """Article links should be converted to PDF."""
        articles = [
            {
                "id": "1",
                "title": "Title",
                "blurb": "Blurb",
                "url": "http://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("generate_html.load_template", return_value=minimal_template):
            html = generate_html(articles)

            assert "/pdf/" in html
            assert "/abs/" not in html or "/pdf/" in html

    def test_includes_date(self, minimal_template):
        """Generated HTML should include current date."""
        with patch("generate_html.load_template", return_value=minimal_template):
            html = generate_html([{"id": "1", "title": "T", "blurb": "B", "url": "http://x.com/1"}])

            # Should have a month name
            import datetime

            month_name = datetime.datetime.now().strftime("%B")
            assert month_name in html


class TestImagePathValidation:
    """P1: Image path validation tests."""

    def test_image_path_in_html(self):
        """Image paths in HTML should match article data."""
        articles = [
            {
                "id": "abc123",
                "title": "Title",
                "blurb": "Blurb",
                "url": "http://x.com/1",
                "image": {
                    "filename": "article_abc123.jpg",
                    "path": "images/article_abc123.jpg",
                    "alt_text": "Test image",
                },
            }
        ]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "images/article_abc123.jpg" in html

    def test_credit_included_when_present(self):
        """Photographer credit should be included when image present."""
        articles = [
            {
                "id": "1",
                "title": "Title",
                "blurb": "Blurb",
                "url": "http://x.com/1",
                "image": {
                    "filename": "test.jpg",
                    "path": "images/test.jpg",
                    "credit": "Photo by John Doe",
                    "credit_link": "https://unsplash.com/@johndoe",
                    "unsplash_link": "https://unsplash.com/",
                },
            }
        ]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            assert "John Doe" in html
            assert "unsplash.com" in html.lower()

    def test_no_image_section_when_no_image(self):
        """No image section when article has no image."""
        articles = [{"id": "1", "title": "Title", "blurb": "Blurb", "url": "http://x.com/1"}]

        with patch("generate_html.load_template") as mock_template:
            mock_template.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            html = generate_html(articles)

            # Should not have image tag for article
            assert 'class="article-img"' not in html


class TestLoadTemplate:
    """P1: Template loading tests."""

    def test_load_default_template(self):
        """Default template should load for AI Research category."""
        with patch("builtins.open", mock_open(read_data="test content")):
            result = load_template("AI Research")
            assert result == "test content"

    def test_load_ml_template(self):
        """Machine Learning category should use ML template."""
        with (
            patch("generate_html.ML_TEMPLATE_PATH", "/fake/path/ml.html"),
            patch("builtins.open", mock_open(read_data="ml content")),
        ):
            result = load_template("Machine Learning")
            assert result == "ml content"

    def test_load_cv_template(self):
        """Computer Vision category should use CV template."""
        with (
            patch("generate_html.CV_TEMPLATE_PATH", "/fake/path/cv.html"),
            patch("builtins.open", mock_open(read_data="cv content")),
        ):
            result = load_template("Computer Vision")
            assert result == "cv content"

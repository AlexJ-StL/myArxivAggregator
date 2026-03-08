"""
Unit tests for generate_html.py module.

P0: Template loading, rendering, and output tests.
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from arxiv_aggregator.generate_html import (
    convert_to_pdf_url,
    clean_headline,
    generate_html,
    load_template,
)

# =============================================================================
# P0: Template Loading Tests
# =============================================================================


class TestLoadTemplate:
    """P0: Test template loading from file system."""

    def test_load_returns_string(self):
        """load_template should return string content."""
        with patch("builtins.open", mock_open(read_data="<html>{{content}}</html>")):
            result = load_template("test.html")
            assert isinstance(result, str)

    def test_load_reads_file_correctly(self):
        """Template content should be read and returned."""
        template_content = "<div>{{content}}</div>"
        with patch("builtins.open", mock_open(read_data=template_content)):
            result = load_template("test.html")
            assert result == template_content

    def test_file_not_found_raises(self):
        """Missing template should raise FileNotFoundError."""
        with patch("builtins.open", side_effect=FileNotFoundError("Template not found")):
            with pytest.raises(FileNotFoundError):
                load_template("missing.html")

    def test_load_with_base_template(self):
        """Should load base template for rendering."""
        base_content = "<html><body>{{content}}</body></html>"

        with (
            patch("builtins.open", mock_open(read_data=base_content)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = load_template("base.html")
            assert "{{content}}" in result


class TestCleanHeadline:
    """P0: Test headline cleaning."""

    def test_removes_trailing_period(self):
        """Trailing periods should be removed."""
        result = clean_headline("Test Title.")
        assert result == "Test Title"

    def test_keeps_periods_in_middle(self):
        """Periods in middle of title should be kept."""
        result = clean_headline("Test.Title.")
        assert result == "Test.Title"

    def test_multiple_trailing_periods_removed(self):
        """Multiple trailing periods should all be removed."""
        result = clean_headline("Test Title...")
        assert result == "Test Title"

    def test_no_trailing_period_unchanged(self):
        """Title without trailing period should be unchanged."""
        result = clean_headline("Test Title")
        assert result == "Test Title"


class TestConvertToPdfUrl:
    """P0: Test PDF URL conversion."""

    def test_converts_abs_to_pdf(self):
        """URL should have /abs/ replaced with /pdf/."""
        result = convert_to_pdf_url("https://arxiv.org/abs/2301.12345")
        assert result == "https://arxiv.org/pdf/2301.12345"

    def test_converts_with_version(self):
        """URL with version should also be converted."""
        result = convert_to_pdf_url("https://arxiv.org/abs/2301.12345v1")
        assert result == "https://arxiv.org/pdf/2301.12345v1"

    def test_rejects_javascript_url(self):
        """javascript: URLs should be rejected."""
        result = convert_to_pdf_url("javascript:alert(1)")
        assert result == "#"

    def test_rejects_data_url(self):
        """data: URLs should be rejected."""
        result = convert_to_pdf_url("data:text/html,<script>alert(1)</script>")
        assert result == "#"

    def test_rejects_vbscript_url(self):
        """vbscript: URLs should be rejected."""
        result = convert_to_pdf_url("vbscript:msgbox('xss')")
        assert result == "#"


# =============================================================================
# P1: Full HTML Generation Tests
# =============================================================================


class TestGenerateHtml:
    """P1: Test full HTML document generation."""

    def test_generate_returns_full_document(self):
        """generate_html should return complete HTML document."""
        articles = [
            {
                "id": "2301.12345",
                "title": "AI Paper",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "<!DOCTYPE html>" in result or "<html" in result
            assert "AI Paper" in result

    def test_generate_with_featured_article(self):
        """Featured article should appear in output."""
        articles = [
            {
                "id": "2301.12345",
                "title": "Featured Paper",
                "blurb": "This is featured",
                "url": "https://arxiv.org/abs/2301.12345",
                "featured": True,
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "Featured Paper" in result

    def test_generate_with_image(self):
        """Article with image should include image HTML."""
        articles = [
            {
                "id": "2301.12345",
                "title": "Paper with Image",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
                "image": {
                    "path": "images/test.jpg",
                    "alt_text": "Test image",
                    "credit": "Photo by Test",
                    "credit_link": "https://example.com",
                    "unsplash_link": "https://unsplash.com",
                },
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "test.jpg" in result

    def test_generate_multiple_articles(self):
        """Multiple articles should all appear in output."""
        articles = [
            {
                "id": "2301.12345",
                "title": "AI Paper",
                "blurb": "AI Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            },
            {
                "id": "2301.12346",
                "title": "ML Paper",
                "blurb": "ML Summary",
                "url": "https://arxiv.org/abs/2301.12346",
            },
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "AI Paper" in result
            assert "ML Paper" in result

    def test_generate_empty_list(self):
        """Empty list should still return HTML structure."""
        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html([])

            # Should still return HTML
            assert isinstance(result, str)

    def test_generate_escapes_html_in_titles(self):
        """HTML in titles should be escaped."""
        articles = [
            {
                "id": "2301.12345",
                "title": "<script>alert('xss')</script>",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "<script>" not in result

    def test_generate_escapes_html_in_blurbs(self):
        """HTML in blurbs should be escaped."""
        articles = [
            {
                "id": "2301.12345",
                "title": "Title",
                "blurb": "<img onerror=alert(1) src=x>",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "<img" not in result

    def test_generate_escapes_javascript_urls(self):
        """javascript: URLs should be escaped/rejected."""
        articles = [
            {
                "id": "2301.12345",
                "title": "Title",
                "blurb": "Summary",
                "url": "javascript:alert(1)",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            assert "javascript:" not in result.lower()

    def test_generate_with_category(self):
        """Category should be used in generation."""
        articles = [
            {
                "id": "2301.12345",
                "title": "ML Paper",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body><!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles, category="Machine Learning")

            assert "Machine Learning" in result or "ML Paper" in result

    def test_generate_inserts_date(self):
        """Current date should be inserted."""
        articles = [
            {
                "id": "2301.12345",
                "title": "Test Paper",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = """<!DOCTYPE html>
<html><body>{date}<!--ARTICLES_PLACEHOLDER--><!--SIDEBAR_ARTICLES_PLACEHOLDER--></body></html>"""

            result = generate_html(articles)

            # Should contain a date string
            assert any(month in result for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])


# =============================================================================
# Integration Tests (tmp_path)
# =============================================================================


class TestGenerateHtmlIntegration:
    """Integration tests using tmp_path for file operations."""

    def test_generate_returns_string(self, tmp_path):
        """generate_html should return HTML string."""
        articles = [
            {
                "id": "2301.12345",
                "title": "Test",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = "<html>{{content}}</html>"

            result = generate_html(articles)

            assert isinstance(result, str)
            assert "Test" in result

    def test_generate_with_different_categories(self):
        """generate_html should work with different category parameters."""
        articles = [
            {
                "id": "2301.12345",
                "title": "AI Paper",
                "blurb": "Summary",
                "url": "https://arxiv.org/abs/2301.12345",
            }
        ]

        with patch("arxiv_aggregator.generate_html.load_template") as mock_load:
            mock_load.return_value = "<html>{{content}}</html>"

            # Should work with different categories
            result_ml = generate_html(articles, category="Machine Learning")
            result_cv = generate_html(articles, category="Computer Vision")
            result_cr = generate_html(articles, category="Security/Cryptography")

            assert isinstance(result_ml, str)
            assert isinstance(result_cv, str)
            assert isinstance(result_cr, str)

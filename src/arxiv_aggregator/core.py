"""ArXiv Aggregator Core Module.

This module provides the base class for all arXiv aggregators,
eliminating code duplication across individual aggregator scripts.
"""

import contextlib
import ftplib
import hashlib
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import feedparser
import requests
from PIL import Image

from config import (
    FTP_HOST,
    FTP_PASS,
    FTP_REMOTE_DIR,
    FTP_USER,
    SEEN_IDS_FILE,
    UNSPLASH_ACCESS_KEY,
    UNSPLASH_API_URL,
    validate_credentials,
)
from content_utils import generate_search_keywords, rewrite_blurb, rewrite_title
from featured_tracker import select_featured_article
from generate_html import generate_html


def log(message: str) -> None:
    """Print timestamped log message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


class BaseAggregator(ABC):
    """Base class for arXiv aggregators.

    This class provides shared functionality for fetching papers from arXiv,
    generating images from Unsplash, creating HTML pages, and uploading via FTP.

    Subclasses must define:
        api_url: str - The arXiv API URL for this category
        category: str - The display name for this category
        output_file: str - The output HTML filename
        domain: str - The domain name for AI prompts
    """

    # Subclasses must define these class attributes
    api_url: str = ""
    category: str = ""
    output_file: str = ""
    domain: str = ""

    MAX_ARTICLES: int = 8

    def __init__(self) -> None:
        """Initialize the aggregator."""
        self.seen_ids: set[str] = set()

    @abstractmethod
    def get_category_name(self) -> str:
        """Return the display name for this category."""
        pass

    @abstractmethod
    def get_domain(self) -> str:
        """Return the domain name for AI prompts."""
        pass

    @abstractmethod
    def get_output_file(self) -> str:
        """Return the output HTML filename."""
        pass

    @abstractmethod
    def get_api_url(self) -> str:
        """Return the arXiv API URL."""
        pass

    def load_seen_ids(self) -> set[str]:
        """Load previously seen arXiv article IDs from JSON file.

        Returns:
            set: A set of previously seen arXiv article IDs, or empty set.
        """
        try:
            with open(SEEN_IDS_FILE, encoding="utf-8") as f:
                self.seen_ids = set(json.load(f))
        except FileNotFoundError:
            self.seen_ids = set()
        return self.seen_ids

    def save_seen_ids(self) -> None:
        """Save the set of seen arXiv article IDs to a JSON file."""
        with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self.seen_ids), f)

    def fetch_recent_arxiv(self) -> list[dict[str, Any]]:
        """Fetch recent arXiv entries from the configured API URL.

        Returns:
            list: A list of dictionaries containing article information.
        """
        log(f"Fetching recent {self.get_category_name()} arXiv entries...")
        try:
            feed = feedparser.parse(self.get_api_url())
        except Exception as e:
            log(f"Error fetching arXiv feed: {e}")
            return []

        if feed.bozo:
            log(f"Warning: Feed may be malformed: {feed.bozo_exception}")

        articles = []
        for idx, entry in enumerate(feed.entries):
            if idx >= self.MAX_ARTICLES:
                break
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            articles.append(
                {
                    "id": entry.id,
                    "title": title.strip() if title else "",
                    "summary": summary.strip() if summary else "",
                    "published": entry.get("published", ""),
                }
            )
        log(f"Fetched {len(articles)} {self.get_category_name()} entries from arXiv.")
        return articles

    def search_unsplash_photo(self, query: str, is_featured: bool = False) -> dict[str, Any] | None:
        """Search for a photo on Unsplash and return photo data.

        Args:
            query: The search query for the photo.
            is_featured: Whether this is for a featured article.

        Returns:
            dict or None: Photo data dictionary or None if not found.
        """
        # Validate credentials at runtime
        try:
            validate_credentials()
        except ValueError as e:
            log(f"Credential validation failed: {e}")
            return None

        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        search_url = f"{UNSPLASH_API_URL}/search/photos"
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape" if is_featured else "squarish",
        }

        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                photo = data["results"][0]
                base_url = photo["user"]["links"]["html"]
                user_link_with_utm = f"{base_url}?utm_source=arxiv_aggregator&utm_medium=referral"

                return {
                    "id": photo["id"],
                    "url": photo["urls"]["small"] if not is_featured else photo["urls"]["regular"],
                    "download_url": photo["links"]["download_location"],
                    "alt_description": photo.get("alt_description", ""),
                    "user": photo["user"]["name"],
                    "user_link": user_link_with_utm,
                    "unsplash_link": "https://unsplash.com/?utm_source=arxiv_aggregator&utm_medium=referral",
                }
        except requests.RequestException as e:
            log(f"Error searching Unsplash: {e}")

        return None

    def download_unsplash_photo(
        self, photo_data: dict[str, Any], filename: str, is_featured: bool = False
    ) -> bool:
        """Download a photo from Unsplash and save it locally.

        Args:
            photo_data: The photo data from search_unsplash_photo.
            filename: The filename to save as.
            is_featured: Whether this is for a featured article.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Trigger download endpoint as required by Unsplash API guidelines
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            download_response = requests.get(
                photo_data["download_url"], headers=headers, timeout=10
            )
            download_response.raise_for_status()
            log(f"Triggered Unsplash download endpoint for photo {photo_data['id']}")

            # Download the actual image
            response = requests.get(photo_data["url"], timeout=10)
            response.raise_for_status()

            # Save the image
            os.makedirs("output/images", exist_ok=True)
            image_path = os.path.join("output", "images", filename)

            with open(image_path, "wb") as f:
                f.write(response.content)

            # Resize if needed
            if not is_featured:
                with Image.open(image_path) as img:
                    img.thumbnail((120, 80), Image.Resampling.LANCZOS)
                    img.save(image_path, "JPEG", quality=85)
            else:
                with Image.open(image_path) as img:
                    img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                    img.save(image_path, "JPEG", quality=90)

            log(f"Downloaded and saved image: {filename}")
            return True

        except Exception as e:
            log(f"Error downloading image: {e}")
            return False

    def generate_article_image(
        self, title: str, summary: str, is_featured: bool = False
    ) -> dict[str, Any] | None:
        """Get an image from Unsplash for an article.

        Args:
            title: The article title.
            summary: The article summary.
            is_featured: Whether this is for a featured article.

        Returns:
            dict or None: Image metadata or None if failed.
        """
        search_query = generate_search_keywords(title, summary)
        log(f"Searching Unsplash for: {search_query}")

        photo_data = self.search_unsplash_photo(search_query, is_featured)

        if not photo_data:
            log(f"No photo found for query: {search_query}")
            return None

        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        filename = f"article_{title_hash}.jpg"

        if self.download_unsplash_photo(photo_data, filename, is_featured):
            return {
                "filename": filename,
                "path": f"images/{filename}",
                "alt_text": photo_data.get("alt_description", f"Photo related to: {title}"),
                "credit": f"Photo by {photo_data['user']} on Unsplash",
                "credit_link": photo_data["user_link"],
                "unsplash_link": photo_data["unsplash_link"],
            }

        return None

    def upload_via_ftp(self, local_dir: str, remote_filename: str | None = None) -> None:
        """Upload generated HTML and images to FTP server.

        Args:
            local_dir: The local directory containing files to upload.
            remote_filename: Optional specific filename to upload.
        """
        # Validate credentials at runtime
        try:
            validate_credentials()
        except ValueError as e:
            log(f"Credential validation failed: {e}")
            return

        host = FTP_HOST if FTP_HOST is not None else ""
        user = FTP_USER if FTP_USER is not None else ""
        password = FTP_PASS if FTP_PASS is not None else ""

        if not host or not user or not password:
            log("Error: FTP credentials are missing. Cannot upload.")
            return

        with ftplib.FTP(host, user, password) as ftp:
            ftp.encoding = "utf-8"
            ftp.cwd(FTP_REMOTE_DIR)

            # Upload specific file or all HTML files
            if remote_filename:
                file_path = os.path.join(local_dir, remote_filename)
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        ftp.storbinary(f"STOR {remote_filename}", f)
                        log(f"Uploaded {remote_filename}")
            else:
                for filename in os.listdir(local_dir):
                    filepath = os.path.join(local_dir, filename)
                    if os.path.isfile(filepath):
                        with open(filepath, "rb") as f:
                            ftp.storbinary(f"STOR {filename}", f)
                            log(f"Uploaded {filename}")

            # Upload images directory
            images_dir = os.path.join(local_dir, "images")
            if os.path.exists(images_dir) and os.path.isdir(images_dir):
                with contextlib.suppress(ftplib.error_perm):
                    ftp.mkd("images")

                ftp.cwd("images")
                for filename in os.listdir(images_dir):
                    filepath = os.path.join(images_dir, filename)
                    if os.path.isfile(filepath):
                        with open(filepath, "rb") as f:
                            ftp.storbinary(f"STOR {filename}", f)
                            log(f"Uploaded images/{filename}")
                ftp.cwd("..")

    def process_article(
        self, article: dict[str, Any], index: int, is_featured: bool = False
    ) -> dict[str, Any]:
        """Process a single article - rewrite title, summary, generate image.

        Args:
            article: The article dictionary.
            index: The article index in the list.
            is_featured: Whether this is the featured article.

        Returns:
            dict: Processed article data.
        """
        title = article["title"]
        summary = article["summary"]
        domain = self.get_domain()

        log(f"Processing {self.get_category_name()} article {index}: {title}")
        new_summary = rewrite_blurb(title, summary, domain)
        new_headline = rewrite_title(title, domain, summary, new_summary)

        image_data = None
        if is_featured or ((index - 1) % 3 == 0 and index > 1):
            log(f"Generating {'featured' if is_featured else 'thumbnail'} image")
            image_data = self.generate_article_image(new_headline, new_summary, is_featured)

        article_data = {
            "id": article["id"].split("/")[-1],
            "title": new_headline,
            "blurb": new_summary,
            "url": article["id"],
        }

        if is_featured:
            article_data["featured"] = True

        if image_data:
            article_data["image"] = image_data

        return article_data

    def should_filter_seen_ids(self) -> bool:
        """Determine if this aggregator should filter by seen IDs.

        The main AI aggregator filters by seen IDs to avoid reprocessing,
        while specialized aggregators always process fresh content.

        Returns:
            bool: True to filter by seen IDs, False to process all.
        """
        return False  # Default: process fresh content

    def run(self) -> None:
        """Run the aggregator - fetch, process, generate HTML, upload."""
        self.load_seen_ids()
        all_articles = self.fetch_recent_arxiv()

        # Determine which articles to process
        if self.should_filter_seen_ids():
            articles_to_process = [a for a in all_articles if a["id"] not in self.seen_ids]
        else:
            articles_to_process = all_articles[: self.MAX_ARTICLES]

        if not articles_to_process:
            log(f"No {self.get_category_name()} articles found. Exiting.")
            return

        # Select featured article
        featured_article, remaining_articles = select_featured_article(articles_to_process)

        if not featured_article:
            log("No suitable featured article found. Exiting.")
            return

        processed = []

        # Process featured article
        log(f"Processing featured {self.get_category_name()} article: {featured_article['title']}")
        featured_data = self.process_article(featured_article, 1, is_featured=True)
        processed.append(featured_data)
        self.seen_ids.add(featured_article["id"])

        # Process remaining articles
        for idx, art in enumerate(remaining_articles, start=2):
            article_data = self.process_article(art, idx)
            processed.append(article_data)
            self.seen_ids.add(art["id"])

        self.save_seen_ids()

        # Generate HTML
        html_content = generate_html(processed, category=self.get_category_name())

        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", self.get_output_file())
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        log(f"Generated {self.get_category_name()} HTML at {output_path}")

        # Upload
        self.upload_via_ftp("output", self.get_output_file())

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log(f"Finished processing {len(articles_to_process)} articles at {timestamp}")

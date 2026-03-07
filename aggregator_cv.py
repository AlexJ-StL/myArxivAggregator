# aggregator_cv.py - Computer Vision specific aggregator

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_aggregator.core import BaseAggregator


class CVAggregator(BaseAggregator):
    """ArXiv aggregator for Computer Vision papers."""

    api_url = "http://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"

    def get_category_name(self) -> str:
        return "Computer Vision"

    def get_domain(self) -> str:
        return "computer vision"

    def get_output_file(self) -> str:
        return "cv.html"

    def get_api_url(self) -> str:
        return self.api_url


def main():
    """Run the Computer Vision aggregator."""
    aggregator = CVAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

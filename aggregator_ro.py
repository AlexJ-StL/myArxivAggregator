# aggregator_ro.py - Robotics specific aggregator

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_aggregator.core import BaseAggregator


class ROAggregator(BaseAggregator):
    """ArXiv aggregator for Robotics papers."""

    api_url = "https://export.arxiv.org/api/query?search_query=cat:cs.RO&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"

    def get_category_name(self) -> str:
        return "Robotics"

    def get_domain(self) -> str:
        return "robotics"

    def get_output_file(self) -> str:
        return "ro.html"

    def get_api_url(self) -> str:
        return self.api_url


def main():
    """Run the Robotics aggregator."""
    aggregator = ROAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

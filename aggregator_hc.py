# aggregator_hc.py - Human-Computer Interaction specific aggregator

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_aggregator.core import BaseAggregator


class HCAggregator(BaseAggregator):
    """ArXiv aggregator for Human-Computer Interaction papers."""

    api_url = "http://export.arxiv.org/api/query?search_query=cat:cs.HC&start=0&max_results=8&sortBy=submittedDate&sortOrder=descending"

    def get_category_name(self) -> str:
        return "Human-Computer Interaction"

    def get_domain(self) -> str:
        return "human-computer interaction"

    def get_output_file(self) -> str:
        return "hc.html"

    def get_api_url(self) -> str:
        return self.api_url


def main():
    """Run the Human-Computer Interaction aggregator."""
    aggregator = HCAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

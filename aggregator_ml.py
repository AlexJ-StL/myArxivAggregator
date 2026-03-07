# aggregator_ml.py - Machine Learning specific aggregator

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_aggregator.core import BaseAggregator


class MLAggregator(BaseAggregator):
    """ArXiv aggregator for Machine Learning papers."""

    api_url = "http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"

    def get_category_name(self) -> str:
        return "Machine Learning"

    def get_domain(self) -> str:
        return "machine learning"

    def get_output_file(self) -> str:
        return "ml.html"

    def get_api_url(self) -> str:
        return self.api_url


def main():
    """Run the Machine Learning aggregator."""
    aggregator = MLAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

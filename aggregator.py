# aggregator.py - Main arXiv aggregator for AI research

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_aggregator.core import BaseAggregator


class AIAggregator(BaseAggregator):
    """ArXiv aggregator for AI research papers."""

    api_url = "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"

    def get_category_name(self) -> str:
        return "AI Research"

    def get_domain(self) -> str:
        return "artificial intelligence"

    def get_output_file(self) -> str:
        return "index.html"

    def get_api_url(self) -> str:
        return self.api_url

    def should_filter_seen_ids(self) -> bool:
        """The main AI aggregator filters by seen IDs to avoid reprocessing."""
        return True


def main():
    """Run the AI aggregator."""
    aggregator = AIAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

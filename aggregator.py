# aggregator.py - Main arXiv aggregator for AI research

from arxiv_aggregator.config import ARXIV_API_URL
from arxiv_aggregator.core import BaseAggregator


class AIAggregator(BaseAggregator):
    """ArXiv aggregator for AI research papers."""

    def get_category_name(self) -> str:
        return "AI Research"

    def get_domain(self) -> str:
        return "artificial intelligence"

    def get_output_file(self) -> str:
        return "index.html"

    def get_api_url(self) -> str:
        return ARXIV_API_URL

    def should_filter_seen_ids(self) -> bool:
        """The main AI aggregator filters by seen IDs to avoid reprocessing."""
        return True


def main():
    """Run the AI aggregator."""
    aggregator = AIAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

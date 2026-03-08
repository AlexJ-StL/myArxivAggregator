# aggregator_hc.py - Human-Computer Interaction specific aggregator

from arxiv_aggregator.config import ARXIV_HC_URL
from arxiv_aggregator.core import BaseAggregator


class HCAggregator(BaseAggregator):
    """ArXiv aggregator for Human-Computer Interaction papers."""

    def get_category_name(self) -> str:
        return "Human-Computer Interaction"

    def get_domain(self) -> str:
        return "human-computer interaction"

    def get_output_file(self) -> str:
        return "hc.html"

    def get_api_url(self) -> str:
        return ARXIV_HC_URL


def main():
    """Run the Human-Computer Interaction aggregator."""
    aggregator = HCAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

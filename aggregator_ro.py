# aggregator_ro.py - Robotics specific aggregator

from arxiv_aggregator.config import ARXIV_RO_URL
from arxiv_aggregator.core import BaseAggregator


class ROAggregator(BaseAggregator):
    """ArXiv aggregator for Robotics papers."""

    def get_category_name(self) -> str:
        return "Robotics"

    def get_domain(self) -> str:
        return "robotics"

    def get_output_file(self) -> str:
        return "ro.html"

    def get_api_url(self) -> str:
        return ARXIV_RO_URL


def main():
    """Run the Robotics aggregator."""
    aggregator = ROAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

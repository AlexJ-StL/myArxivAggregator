# aggregator_ml.py - Machine Learning specific aggregator

from arxiv_aggregator.config import ARXIV_ML_URL
from arxiv_aggregator.core import BaseAggregator


class MLAggregator(BaseAggregator):
    """ArXiv aggregator for Machine Learning papers."""

    def get_category_name(self) -> str:
        return "Machine Learning"

    def get_domain(self) -> str:
        return "machine learning"

    def get_output_file(self) -> str:
        return "ml.html"

    def get_api_url(self) -> str:
        return ARXIV_ML_URL


def main():
    """Run the Machine Learning aggregator."""
    aggregator = MLAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

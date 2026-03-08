# aggregator_cv.py - Computer Vision specific aggregator

from arxiv_aggregator.config import ARXIV_CV_URL
from arxiv_aggregator.core import BaseAggregator


class CVAggregator(BaseAggregator):
    """ArXiv aggregator for Computer Vision papers."""

    def get_category_name(self) -> str:
        return "Computer Vision"

    def get_domain(self) -> str:
        return "computer vision"

    def get_output_file(self) -> str:
        return "cv.html"

    def get_api_url(self) -> str:
        return ARXIV_CV_URL


def main():
    """Run the Computer Vision aggregator."""
    aggregator = CVAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

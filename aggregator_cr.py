# aggregator_cr.py - Security/Cryptography specific aggregator

from arxiv_aggregator.config import ARXIV_CR_URL
from arxiv_aggregator.core import BaseAggregator


class CRAggregator(BaseAggregator):
    """ArXiv aggregator for Security/Cryptography papers."""

    def get_category_name(self) -> str:
        return "Security/Cryptography"

    def get_domain(self) -> str:
        return "security and cryptography"

    def get_output_file(self) -> str:
        return "cr.html"

    def get_api_url(self) -> str:
        return ARXIV_CR_URL


def main():
    """Run the Security/Cryptography aggregator."""
    aggregator = CRAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

# aggregator_cr.py - Security/Cryptography specific aggregator

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_aggregator.core import BaseAggregator


class CRAggregator(BaseAggregator):
    """ArXiv aggregator for Security/Cryptography papers."""

    api_url = "https://export.arxiv.org/api/query?search_query=cat:cs.CR&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"

    def get_category_name(self) -> str:
        return "Security/Cryptography"

    def get_domain(self) -> str:
        return "security and cryptography"

    def get_output_file(self) -> str:
        return "cr.html"

    def get_api_url(self) -> str:
        return self.api_url


def main():
    """Run the Security/Cryptography aggregator."""
    aggregator = CRAggregator()
    aggregator.run()


if __name__ == "__main__":
    main()

"""
A module that defines a search tool for querying a data index.
"""

from typing import Any, List


class SearchTool:
    """
    A search tool that interfaces with the data index to perform text-based searches.
    """

    def __init__(self, index):
        self.index = index

    def search(self, query: str) -> List[Any]:
        """
        Perform a text-based search on the data index.

        Args:
            query (str): The search query string.

        Returns:
            List[Any]: A list of up to 5 search results returned by the data index.
        """
        return self.index.search(query, num_results=5)
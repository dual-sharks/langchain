"""Tool for the SEC API."""

from typing import Any, Dict, List, Optional, Union
from typing_extensions import Literal

from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, SecretStr

from langchain_community.utilities.secapi import CustomSECAPI


class SECAPIInput(BaseModel):
    """Input for SEC API tool."""

    query: str = Field(description="The search query or ticker symbol")


class SECAPITool(BaseTool):
    """Tool that provides access to various SEC API endpoints."""

    name: str = "sec_api"
    description: str = (
        "Use this tool to search SEC filings. "
        "For company filings, provide a ticker symbol like 'TSLA' or 'AAPL'. "
        "For text search, provide keywords like 'artificial intelligence'. "
        "You can optionally specify form types (10-K, 10-Q, 8-K) and date ranges."
    )
    api_key: str = Field(description="API key for SEC API access")
    args_schema: type[BaseModel] = SECAPIInput

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize the SEC API tool."""
        super().__init__(api_key=api_key, **kwargs)
        api_key_value = api_key or self.api_key
        self._api_wrapper = CustomSECAPI(api_key=SecretStr(api_key_value))

    @property
    def api_wrapper(self) -> CustomSECAPI:
        """Get the API wrapper."""
        return self._api_wrapper

    def full_text_search(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Search the full text content of SEC filings."""
        try:
            results = self.api_wrapper.full_text_search(
                search_query=query,
                form_types=form_types,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
            )
            return results
        except Exception as e:
            raise ValueError(f"Error in full text search: {str(e)}")

    def filing_search(
        self,
        ticker: str,
        form_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Search SEC filings by company ticker."""
        try:
            results = self.api_wrapper.get_filings(
                ticker=ticker,
                form_type=form_type,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
            )
            return results
        except Exception as e:
            raise ValueError(f"Error in filing search: {str(e)}")

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process natural language query for SEC filings.

        Args:
            query: The search query or ticker symbol
            run_manager: Optional callback manager
            **kwargs: Additional keyword arguments

        Returns:
            Dict containing search results
        """
        if query.isupper() and len(query) <= 5:
            try:
                results = self.api_wrapper.get_filings(ticker=query, limit=5)
                return results
            except Exception as e:
                raise ToolException(f"Error searching filings: {str(e)}")

        try:
            results = self.api_wrapper.full_text_search(search_query=query, limit=5)
            return results
        except Exception as e:
            raise ToolException(f"Error searching text: {str(e)}")

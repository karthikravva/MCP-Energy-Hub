"""
Base collector class for data ingestion
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors
    """

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        self.session = session
        self.api_key = api_key
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.source_name = "base"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from the source
        Returns list of normalized records
        """
        pass

    @abstractmethod
    async def transform(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Transform raw data into normalized schema format
        """
        pass

    @abstractmethod
    async def load(self, records: List[Dict[str, Any]]) -> int:
        """
        Load transformed records into database
        Returns number of records inserted/updated
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """
        Execute full ETL pipeline: collect → transform → load
        """
        start_time = datetime.utcnow()
        result = {
            "source": self.source_name,
            "started_at": start_time.isoformat(),
            "status": "running",
            "records_processed": 0,
            "error": None,
        }

        try:
            logger.info(f"Starting collection from {self.source_name}")

            # Collect
            raw_data = await self.collect()
            logger.info(
                f"Collected {len(raw_data)} raw records from {self.source_name}")

            # Transform
            transformed = await self.transform(raw_data)
            logger.info(f"Transformed {len(transformed)} records")

            # Load
            count = await self.load(transformed)

            result["status"] = "success"
            result["records_processed"] = count

        except Exception as e:
            logger.error(f"Error in {self.source_name} collector: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        result["completed_at"] = datetime.utcnow().isoformat()
        return result

    async def fetch_json(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Helper to fetch JSON from URL
        """
        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        return response.json()

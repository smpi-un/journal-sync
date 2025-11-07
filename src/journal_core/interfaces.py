from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class JournalEntry:
    """
    Abstract representation of a journal entry.
    Concrete implementations will define specific fields.
    """
    pass

class AbstractJournalClient(ABC):
    """
    Abstract base class for journal operation clients (e.g., Teable, NocoDB).
    Defines the interface for registering journal data.
    """
    @abstractmethod
    def register_entry(self, entry: JournalEntry) -> Any:
        """
        Registers a single journal entry to the target platform.
        """
        pass

    @abstractmethod
    def register_entries(self, entries: List[JournalEntry]) -> List[Any]:
        """
        Registers multiple journal entries to the target platform.
        """
        pass

    @abstractmethod
    def get_existing_entry_ids(self) -> List[str]:
        """
        Fetches a list of IDs of all existing journal entries in the target platform.
        """
        pass

    @abstractmethod
    def get_existing_entries_with_modified_at(self) -> Dict[str, datetime]:
        """
        Fetches a dictionary of existing journal entry IDs mapped to their last modified datetime.
        """
        pass

    @abstractmethod
    def update_entry(self, entry: JournalEntry) -> Any:
        """
        Updates a single journal entry in the target platform.
        """
        pass

    @abstractmethod
    def update_entries(self, entries: List[JournalEntry]) -> List[Any]:
        """
        Updates multiple journal entries in the target platform.
        """
        pass

class AbstractJournalDataSource(ABC):
    """
    Abstract base class for journal data sources (e.g., JourneyCloud, local files).
    Defines the interface for fetching journal data.
    """
    @abstractmethod
    def fetch_entries(self, **kwargs) -> List[JournalEntry]:
        """
        Fetches journal entries from the data source.
        Keyword arguments can be used for filtering, pagination, etc.
        """
        pass

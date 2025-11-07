from typing import List, Any

from .interfaces import AbstractJournalClient, AbstractJournalDataSource
from .models import JournalEntry

class JournalManager:
    """
    Manages the process of fetching journal entries from a data source
    and registering them with a journal client.
    """
    def __init__(self, data_source: AbstractJournalDataSource, journal_client: AbstractJournalClient):
        self.data_source = data_source
        self.journal_client = journal_client

    def import_and_register_entries(self, **kwargs) -> List[Any]:
        """
        Fetches entries from the configured data source and registers them
        with the configured journal client.
        """
        print(f"Fetching entries from data source: {type(self.data_source).__name__}")
        entries: List[JournalEntry] = self.data_source.fetch_entries(**kwargs)
        print(f"Fetched {len(entries)} entries from data source.")

        if not entries:
            print("No new entries to process.")
            return []

        print(f"Checking for existing entries in {type(self.journal_client).__name__}...")
        existing_entries_data = self.journal_client.get_existing_entries_with_modified_at()
        print(f"Found {len(existing_entries_data)} existing entries.")

        entries_to_register = []
        entries_to_update = []

        for entry in entries:
            if entry.id and entry.id in existing_entries_data:
                existing_modified_at = existing_entries_data[entry.id]
                # Only update if the incoming entry is newer
                if entry.modified_at and existing_modified_at and entry.modified_at > existing_modified_at:
                    print(f"Updating entry with ID: {entry.id} (newer modified_at)")
                    entries_to_update.append(entry)
                else:
                    print(f"Skipping entry with ID: {entry.id} (already exists and not newer)")
            else:
                entries_to_register.append(entry)
        
        registered_results = []
        if entries_to_register:
            print(f"Registering {len(entries_to_register)} new entries with journal client: {type(self.journal_client).__name__}")
            registered_results.extend(self.journal_client.register_entries(entries_to_register))
            print(f"Successfully registered {len(registered_results)} new entries.")
        else:
            print("No new entries to register.")

        updated_results = []
        if entries_to_update:
            print(f"Updating {len(entries_to_update)} existing entries with journal client: {type(self.journal_client).__name__}")
            updated_results.extend(self.journal_client.update_entries(entries_to_update))
            print(f"Successfully updated {len(updated_results)} existing entries.")
        else:
            print("No entries to update.")

        return registered_results + updated_results

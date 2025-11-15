

import json
import os
from datetime import datetime
from typing import Any, List, Dict
from urllib.parse import urljoin

import requests

from clients.grist_client_config import (
    JOURNAL_TABLE_NAME,
    GRIST_JOURNAL_TABLE_COLUMNS,
)
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry
from journal_core.converters import journal_to_journey


def _journal_entry_to_grist_record(entry: JournalEntry) -> dict[str, Any]:
    """Converts a JournalEntry object to a dictionary for a Grist record."""
    record = {}
    # Use a consistent mapping from snake_case to PascalCase for Grist columns
    for key, value in entry.__dict__.items():
        if value is None:
            continue
        
        # A simple snake_case to PascalCase conversion
        grist_key = ''.join(word.capitalize() for word in key.split('_'))
        
        if isinstance(value, datetime):
            record[grist_key] = value.isoformat()
        elif isinstance(value, list) or isinstance(value, dict):
            record[grist_key] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            record[grist_key] = str(value)
        else:
            record[grist_key] = value
            
    # Grist uses 'fields' to wrap the record data. The 'id' for linking/updating is separate.
    # The primary ID for our journal is 'JournalId', which should be part of the fields.
    if 'id' in entry.__dict__:
        record['JournalId'] = entry.id
        if 'Id' in record: # remove the generic 'Id' if it was created
            del record['Id']
    
    # Populate the new CalendarEntryAt field
    if entry.entry_at:
        record['CalendarEntryAt'] = entry.entry_at.isoformat()

    return record

def _grist_record_to_journal_entry(grist_record: dict) -> JournalEntry:
    """Converts a Grist record dictionary to a JournalEntry object."""
    fields = grist_record.get("fields", {})
    entry_data = {}

    # Create a mapping from Grist's PascalCase to Python's snake_case
    snake_case_map = {
        ''.join(word.capitalize() for word in key.split('_')): key 
        for key in JournalEntry.__annotations__
    }
    snake_case_map['JournalId'] = 'id' # Manual override for the primary ID

    for grist_key, value in fields.items():
        if value is None or value == "" or grist_key not in snake_case_map:
            continue

        model_key = snake_case_map[grist_key]
        target_type = JournalEntry.__annotations__.get(model_key)

        try:
            if "datetime" in str(target_type):
                entry_data[model_key] = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            elif "bool" in str(target_type):
                entry_data[model_key] = str(value).lower() in ["true", "1"]
            elif "list" in str(target_type) or "dict" in str(target_type):
                entry_data[model_key] = json.loads(value) if isinstance(value, str) else value
            elif "int" in str(target_type):
                entry_data[model_key] = int(value)
            elif "float" in str(target_type):
                entry_data[model_key] = float(value)
            else:
                entry_data[model_key] = value
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            print(f"Warning: Could not convert field '{grist_key}' with value '{value}'. Error: {e}")

    # The record's own ID in Grist is also needed for updates.
    # We can store it in a transient field if necessary, but for now, we rely on JournalId.
    return JournalEntry(**entry_data)


class GristJournalClient(AbstractJournalClient):
    """A wrapper class for the Grist API."""

    def __init__(self, grist_api_url, grist_api_key, grist_doc_id):

        if not all([grist_api_url, grist_api_key, grist_doc_id]):
            raise ValueError("Grist API environment variables are not fully set.")

        self.base_url = grist_api_url
        self.headers = {"Authorization": f"Bearer {grist_api_key}", "Content-Type": "application/json"}
        self.doc_id = grist_doc_id
        self.journal_table_name = JOURNAL_TABLE_NAME
        self._ensure_tables_exist()

    def _make_request(self, method, path, json_data=None):
        url = urljoin(self.base_url, path.lstrip("/"))
        response = requests.request(method, url, headers=self.headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def _ensure_tables_exist(self):
        print("Ensuring Grist table exists...")
        tables = self._make_request("GET", f"api/docs/{self.doc_id}/tables")
        
        found_table = None
        if "tables" in tables:
            for table in tables["tables"]:
                if table.get("id") == self.journal_table_name:
                    found_table = table
                    break
        
        if not found_table:
            print(f"Table '{self.journal_table_name}' not found, creating it...")
            self.create_table()
        else:
            print(f"Table '{self.journal_table_name}' already exists.")

    def create_table(self):
        """Creates the journal table in Grist based on the config."""
        path = f"api/docs/{self.doc_id}/tables"
        payload = {
            "tables": [{
                "id": self.journal_table_name,
                "columns": GRIST_JOURNAL_TABLE_COLUMNS
            }]
        }
        try:
            self._make_request("POST", path, json_data=payload)
            print(f"Successfully sent request to create table '{self.journal_table_name}'.")
        except requests.exceptions.RequestException as e:
            print(f"Error creating table '{self.journal_table_name}': {e}")
            raise

    def register_entry(self, entry: JournalEntry) -> Any:
        return self.register_entries([entry])

    def register_entries(self, entries: List[JournalEntry]) -> List[Any]:
        records_to_create = [{"fields": _journal_entry_to_grist_record(entry)} for entry in entries]
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        payload = {"records": records_to_create}
        response = self._make_request("POST", path, json_data=payload)
        return response.get("records", [])

    def update_entry(self, entry: JournalEntry) -> Any:
        return self.update_entries([entry])

    def update_entries(self, entries: List[JournalEntry]) -> List[Any]:
        # For updates, Grist requires the Grist record ID. We use JournalId as the lookup key.
        records_to_update = [{"require": {"JournalId": entry.id}, "fields": _journal_entry_to_grist_record(entry)} for entry in entries]
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        payload = {"records": records_to_update}
        return self._make_request("PATCH", path, json_data=payload)

    def get_existing_entry_ids(self) -> List[str]:
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        response = self._make_request("GET", path)
        if response and "records" in response:
            return [
                str(record["fields"]["JournalId"])
                for record in response["records"]
                if "JournalId" in record["fields"]
            ]
        return []

    def get_existing_entries_with_modified_at(self) -> Dict[str, datetime]:
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        response = self._make_request("GET", path)
        existing_data = {}
        if response and "records" in response:
            for record in response["records"]:
                fields = record.get("fields", {})
                record_id = fields.get("JournalId")
                modified_at_str = fields.get("ModifiedAt")
                if record_id and modified_at_str:
                    try:
                        existing_data[str(record_id)] = datetime.fromisoformat(modified_at_str)
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse modified_at for entry {record_id}: {modified_at_str}")
        return existing_data

    def download_journal_entries(self) -> List[JournalEntry]:
        """Downloads all journal entries and parses them into JournalEntry objects."""
        print("Downloading and parsing journal entries from Grist...")
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        try:
            response_data = self._make_request("GET", path)
            if response_data and "records" in response_data:
                return [_grist_record_to_journal_entry(rec) for rec in response_data["records"]]
            return []
        except requests.exceptions.HTTPError as e:
            print(f"Failed to download journal entries: {e}")
            return []


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    print("Running GristJournalClient test...")

    try:
        client = GristJournalClient()
        
        # 1. Download from Grist and convert to internal JournalEntry objects
        journal_entries = client.download_journal_entries()
        print(f"Successfully downloaded and parsed {len(journal_entries)} entries.")

        if not journal_entries:
            print("No entries to process.")
        else:
            # 2. Convert JournalEntry objects back to JourneyCloudEntry objects
            journey_cloud_entries = [journal_to_journey(entry) for entry in journal_entries]
            
            # 3. Serialize JourneyCloudEntry objects to dictionaries for JSON output
            journey_cloud_dicts = [entry.to_dict() for entry in journey_cloud_entries]

            # 4. Print the final JSON output
            print("\n--- Journey Cloud Formatted JSON ---")
            print(json.dumps(journey_cloud_dicts, indent=2, ensure_ascii=False))
            print("------------------------------------")

        print("\nTest finished successfully.")

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"An error occurred during the test: {e}")

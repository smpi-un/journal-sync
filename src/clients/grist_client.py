
import json
import os
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

from clients.grist_client_config import (
    GRIST_API_KEY,
    GRIST_API_URL,
    GRIST_DOC_ID,
    GRIST_FIELD_NAMES,
    JOURNAL_TABLE_NAME,
    GRIST_JOURNAL_TABLE_COLUMNS,
)
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry


class GristJournalClient(AbstractJournalClient):
    """A wrapper class for the Grist API."""

    def __init__(self):
        grist_api_url = os.getenv("GRIST_API_URL")
        grist_api_key = os.getenv("GRIST_API_KEY")
        grist_doc_id = os.getenv("GRIST_DOC_ID")

        if not grist_api_url:
            raise ValueError("GRIST_API_URL is not set in the environment or .env file.")
        if not grist_api_key:
            raise ValueError("GRIST_API_KEY is not set in the environment or .env file.")
        if not grist_doc_id:
            raise ValueError("GRIST_DOC_ID is not set in the environment or .env file.")

        self.base_url = grist_api_url
        self.headers = {
            "Authorization": f"Bearer {grist_api_key}",
            "Content-Type": "application/json",
        }
        self.doc_id = grist_doc_id
        self.journal_table_name = JOURNAL_TABLE_NAME
        self._ensure_tables_exist()

    def _make_request(self, method, path, json_data=None):
        url = urljoin(self.base_url, path.lstrip("/"))
        response = requests.request(method, url, headers=self.headers, json=json_data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("--- SERVER ERROR RESPONSE ---")
            print(response.text)
            print("---------------------------")
            raise e
        return response.json()

    def _ensure_tables_exist(self):
        print("Ensuring Grist tables exist...")
        # Try to get the table by its user-defined name
        journal_table_meta = self.get_table_by_name(self.journal_table_name)
        print(f"get_table_by_name response: {journal_table_meta}") # Debug print
        
        if not journal_table_meta:
            print(f"Table '{self.journal_table_name}' not found, attempting to create it...")
            table_definition = {
                "id": self.journal_table_name,
                "columns": GRIST_JOURNAL_TABLE_COLUMNS,
            }
            created_table_meta = self.create_table(table_definition)
            print(f"create_table response: {created_table_meta}") # Debug print
            if not created_table_meta:
                raise ValueError(f"Failed to create table '{self.journal_table_name}'.")
            print(f"Table '{self.journal_table_name}' created successfully.")
        else:
            print(f"Table '{self.journal_table_name}' already exists.")

    def get_table_by_name(self, table_name: str) -> dict | None:
        """Fetches table metadata by name (user-defined/normalized)."""
        path = f"/api/docs/{self.doc_id}/tables"
        response = self._make_request("GET", path)
        print(f"Raw response from Grist API for listing tables: {response}") # Debug print
        
        tables_list = []
        if isinstance(response, list):
            tables_list = response
        elif isinstance(response, dict) and "tables" in response:
            tables_list = response["tables"]
        
        for table in tables_list:
            # The 'id' field in the listing response is the normalized user-defined name
            print(f"Checking table: {table.get('id')}") # Debug print
            if table.get("id") == table_name:
                return table
        return None

    def create_table(self, table_definition: dict) -> dict | None:
        """Creates a new table in the Grist document."""
        path = f"/api/docs/{self.doc_id}/tables"
        print(path)
        payload = {"tables": [table_definition]}
        print(payload)
        response = self._make_request("POST", path, json_data=payload)
        if response and "tables" in response:
            return response["tables"][0]
        return None

    def _journal_entry_to_grist_record(self, entry: JournalEntry) -> dict[str, Any]:
        record_fields = {}

        # Map JournalEntry fields to Grist column names
        for model_field, grist_field in GRIST_FIELD_NAMES.items():
            value = getattr(entry, model_field, None)
            if value is not None:
                if isinstance(value, datetime):
                    record_fields[grist_field] = value.isoformat()
                elif isinstance(value, list):
                    if model_field == "media_attachments": # Special handling for media_attachments
                        record_fields[grist_field] = json.dumps(value)
                    else:
                        record_fields[grist_field] = ", ".join(value)
                elif isinstance(value, dict):
                    record_fields[grist_field] = json.dumps(value)
                else:
                    record_fields[grist_field] = value
        return record_fields

    def register_entry(self, entry: JournalEntry) -> Any:
        return self.register_entries([entry])

    def register_entries(self, entries: list[JournalEntry]) -> list[Any]:
        print("a:", len(entries))
        records_to_create = [
            {"fields": self._journal_entry_to_grist_record(entry)} for entry in entries
        ]
        print("b:", len(records_to_create))
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        
        payload = {"records": records_to_create}
        print(path)
        print(payload)
        # print(f"Sending payload to Grist API: {json.dumps(payload, indent=2)}") # Debug print
        
        response = self._make_request(
            "POST", path, json_data=payload
        )
        print(f"Response from Grist API for record creation: {json.dumps(response, indent=2)}") # Debug print
        return response.get("records", []) # Return the list of created record IDs

    def get_existing_entry_ids(self) -> list[str]:
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        response = self._make_request("GET", path)
        if response and "records" in response:
            return [
                str(record["fields"][GRIST_FIELD_NAMES["id"]])
                for record in response["records"]
                if GRIST_FIELD_NAMES["id"] in record["fields"]
            ]
        return []

    def get_existing_entries_with_modified_at(self) -> dict[str, datetime]:
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        response = self._make_request("GET", path)
        existing_data = {}
        if response and "records" in response:
            for record in response["records"]:
                record_id = record["fields"].get(GRIST_FIELD_NAMES["id"])
                modified_at_str = record["fields"].get(GRIST_FIELD_NAMES["modified_at"])
                if record_id and modified_at_str:
                    try:
                        existing_data[str(record_id)] = datetime.fromisoformat(
                            modified_at_str
                        )
                    except (ValueError, TypeError):
                        print(
                            f"Warning: Could not parse modified_at for entry {record_id}: {modified_at_str}"
                        )
        return existing_data

    def update_entry(self, entry: JournalEntry) -> Any:
        return self.update_entries([entry])

    def update_entries(self, entries: list[JournalEntry]) -> list[Any]:
        records_to_update = [
            self._journal_entry_to_grist_record(entry) for entry in entries
        ]
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        response = self._make_request(
            "PATCH", path, json_data={"records": records_to_update}
        )
        return response

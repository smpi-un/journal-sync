import json
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

from clients.grist_client_config import (
    GRIST_JOURNAL_TABLE_COLUMNS,
    JOURNAL_TABLE_NAME,
)
from journal_core.converters import journal_to_journey
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry


def _journal_entry_to_grist_record(entry: JournalEntry) -> dict[str, Any]:
    """Converts a JournalEntry object to a dictionary for a Grist record."""
    record = {}
    # Use a consistent mapping from snake_case to PascalCase for Grist columns
    for key, value in entry.__dict__.items():
        if value is None:
            continue

        # A simple snake_case to PascalCase conversion
        grist_key = "".join(word.capitalize() for word in key.split("_"))

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
    if "id" in entry.__dict__:
        record["JournalId"] = entry.id
        if "Id" in record:  # remove the generic 'Id' if it was created
            del record["Id"]

    # Populate the new CalendarEntryAt field
    if entry.entry_at:
        record["CalendarEntryAt"] = entry.entry_at.isoformat()

    return record


def _grist_record_to_journal_entry(grist_record: dict[str, Any]) -> JournalEntry:
    """Converts a Grist record dictionary to a JournalEntry object."""
    entry_data: dict[str, Any] = {}
    fields = grist_record.get("fields", {})

    def get_val(key: str, type_converter=None, default=None):
        value = fields.get(key)
        if value is None:
            return default
        if type_converter:
            try:
                # Grist stores some types as strings, e.g., boolean as "True"/"False"
                if type_converter is bool and isinstance(value, str):
                    return value.lower() == "true"
                return type_converter(value)
            except (ValueError, TypeError, json.JSONDecodeError):
                print(f"Warning: Could not convert Grist field '{key}' with value '{value}' to target type.")
                return default
        return value

    # Helper for safe datetime parsing
    def parse_dt(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    # --- Basic Identification ---
    entry_data["id"] = get_val("JournalId", str, "")

    # --- Time Information ---
    entry_at = parse_dt(get_val("EntryAt", str))
    if entry_at is None:
        raise ValueError("Grist record missing 'EntryAt' field for JournalEntry.")
    entry_data["entry_at"] = entry_at

    entry_data["timezone"] = get_val("Timezone", str)
    entry_data["created_at"] = parse_dt(get_val("CreatedAt", str))
    entry_data["modified_at"] = parse_dt(get_val("ModifiedAt", str))

    # --- Content ---
    entry_data["text_content"] = get_val("TextContent", str)
    entry_data["rich_text_content"] = get_val("RichTextContent", str)
    entry_data["title"] = get_val("Title", str)

    # --- Organization / Categorization ---
    # Grist stores multi-select tags as JSON array strings
    tags_raw = get_val("Tags", str, "[]")
    if tags_raw.startswith("["):
        entry_data["tags"] = get_val("Tags", lambda x: json.loads(x) if isinstance(x, str) else [], [])
    else:
        entry_data["tags"] = [s.strip() for s in tags_raw.split(",")] if tags_raw else []

    entry_data["notebook"] = get_val("Notebook", str)
    entry_data["is_favorite"] = get_val("IsFavorite", bool, False)
    entry_data["is_pinned"] = get_val("IsPinned", bool, False)

    # --- Context Information (Mood / Activity) ---
    entry_data["mood_label"] = get_val("Mood", str)
    entry_data["mood_score"] = get_val("MoodScore", float)
    activities_raw = get_val("Activities", str, "[]")
    if activities_raw.startswith("["):
        entry_data["activities"] = get_val("Activities", lambda x: json.loads(x) if isinstance(x, str) else [], [])
    else:
        entry_data["activities"] = [s.strip() for s in activities_raw.split(",")] if activities_raw else []

    # --- Location Information (Flattened) ---
    entry_data["location_lat"] = get_val("LocationLat", float)
    entry_data["location_lon"] = get_val("LocationLon", float)
    entry_data["location_name"] = get_val("LocationName", str)
    entry_data["location_address"] = get_val("LocationAddress", str)
    entry_data["location_altitude"] = get_val("LocationAltitude", float)

    # --- Weather Information (Flattened) ---
    entry_data["weather_temperature"] = get_val("WeatherTemp", float)
    entry_data["weather_condition"] = get_val("WeatherCondition", str)
    entry_data["weather_humidity"] = get_val("WeatherHumidity", float)
    entry_data["weather_pressure"] = get_val("WeatherPressure", float)

    # --- Device & Other Metadata ---
    entry_data["device_name"] = get_val("DeviceName", str)
    entry_data["step_count"] = get_val("StepCount", int)

    # --- Media Information ---
    media_attachments_raw = get_val("MediaAttachments", str, "[]")  # Assuming media attachments are JSON string
    if media_attachments_raw.startswith("["):
        entry_data["media_attachments"] = get_val(
            "MediaAttachments", lambda x: json.loads(x) if isinstance(x, str) else [], []
        )
    else:
        entry_data["media_attachments"] = []

    # --- Source Information (Flattened) ---
    entry_data["source_app_name"] = get_val("SourceAppName", str, "Grist")
    entry_data["source_original_id"] = get_val("SourceOriginalId", str)
    source_imported_at_val = parse_dt(get_val("SourceImportedAt", str))
    if source_imported_at_val:
        entry_data["source_imported_at"] = source_imported_at_val
    entry_data["source_raw_data"] = get_val("SourceRawData", str)  # Assuming raw data is stored as a string

    return JournalEntry(**entry_data)


class GristJournalClient(AbstractJournalClient):
    """A wrapper class for the Grist API."""

    def __init__(self, grist_api_url, grist_api_key, grist_doc_id):
        if not all([grist_api_url, grist_api_key, grist_doc_id]):
            raise ValueError("Grist API environment variables are not fully set.")

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
        payload = {"tables": [{"id": self.journal_table_name, "columns": GRIST_JOURNAL_TABLE_COLUMNS}]}
        try:
            self._make_request("POST", path, json_data=payload)
            print(f"Successfully sent request to create table '{self.journal_table_name}'.")
        except requests.exceptions.RequestException as e:
            print(f"Error creating table '{self.journal_table_name}': {e}")
            raise

    def register_entry(self, entry: JournalEntry) -> Any:
        return self.register_entries([entry])

    def register_entries(self, entries: list[JournalEntry]) -> list[Any]:
        records_to_create = [{"fields": _journal_entry_to_grist_record(entry)} for entry in entries]
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        payload = {"records": records_to_create}
        response = self._make_request("POST", path, json_data=payload)
        return response.get("records", [])

    def update_entry(self, entry: JournalEntry) -> Any:
        return self.update_entries([entry])

    def update_entries(self, entries: list[JournalEntry]) -> list[Any]:
        # For updates, Grist requires the Grist record ID. We use JournalId as the lookup key.
        records_to_update = [
            {
                "require": {"JournalId": entry.id},
                "fields": _journal_entry_to_grist_record(entry),
            }
            for entry in entries
        ]
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        payload = {"records": records_to_update}
        return self._make_request("PATCH", path, json_data=payload)

    def get_existing_entry_ids(self) -> list[str]:
        path = f"/api/docs/{self.doc_id}/tables/{self.journal_table_name}/records"
        response = self._make_request("GET", path)
        if response and "records" in response:
            return [
                str(record["fields"]["JournalId"]) for record in response["records"] if "JournalId" in record["fields"]
            ]
        return []

    def get_existing_entries_with_modified_at(self) -> dict[str, datetime]:
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

    def download_journal_entries(self) -> list[JournalEntry]:
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
    from dotenv import dotenv_values, load_dotenv

    load_dotenv()
    print("Running GristJournalClient test...")

    config = dotenv_values()
    api_url = config.get("GRIST_API_URL")
    api_key = config.get("GRIST_API_KEY")
    doc_id = config.get("GRIST_DOC_ID")

    if not api_url or not api_key or not doc_id:
        print("Error: GRIST_API_URL, GRIST_API_KEY, and GRIST_DOC_ID must be set in your .env file.")
        exit(1)

    try:
        client = GristJournalClient(api_url, api_key, doc_id)

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

            print("\n--- Journey Cloud Formatted JSON ---")
            print(json.dumps(journey_cloud_dicts, indent=2, ensure_ascii=False))
            print("------------------------------------")

        print("\nTest finished successfully.")

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"An error occurred during the test: {e}")

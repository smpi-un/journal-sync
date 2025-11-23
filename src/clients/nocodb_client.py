import json
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

from clients.nocodb_client_config import (
    NOCODB_JOURNAL_TABLE_COLUMNS,
    NOCODB_JOURNAL_TABLE_NAME,
)
from journal_core.converters import journal_to_journey
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry

# --- v3 Conversion Functions ---

# Mapping from JournalEntry snake_case attributes to NocoDB Column Titles
SNAKE_TO_TITLE_MAP = {
    "id": "JournalId",
    "entry_at": "EntryAt",
    "created_at": "JournalCreatedAt",
    "modified_at": "JournalModifiedAt",
    "mood_label": "Mood",
    "media_attachments": "MediaAttachments",
    "text_content": "TextContent",
    "rich_text_content": "RichTextContent",
    "is_favorite": "IsFavorite",
    "is_pinned": "IsPinned",
    "mood_score": "MoodScore",
    "location_lat": "LocationLat",
    "location_lon": "LocationLon",
    "location_name": "LocationName",
    "location_address": "LocationAddress",
    "location_altitude": "LocationAltitude",
    "weather_temperature": "WeatherTemp",
    "weather_condition": "WeatherCondition",
    "weather_humidity": "WeatherHumidity",
    "weather_pressure": "WeatherPressure",
    "device_name": "DeviceName",
    "step_count": "StepCount",
    "source_app_name": "SourceAppName",
    "source_original_id": "SourceOriginalId",
    "source_imported_at": "SourceImportedAt",
    "source_raw_data": "SourceRawData",
    "calendar_entry_at": "CalendarEntryAt",
    "timezone": "Timezone",
    "title": "Title",
    "tags": "Tags",
    "notebook": "Notebook",
    "activities": "Activities",
}
TITLE_TO_SNAKE_MAP = {v: k for k, v in SNAKE_TO_TITLE_MAP.items()}


def _journal_entry_to_nocodb_fields(entry: JournalEntry) -> dict[str, Any]:
    """Converts a JournalEntry object to a dictionary of fields for a NocoDB v3 record."""
    fields = {}
    for snake_case_attr, value in entry.__dict__.items():
        if value is None:
            continue

        title_key = SNAKE_TO_TITLE_MAP.get(snake_case_attr)
        if not title_key:
            continue

        if isinstance(value, datetime):
            if title_key == "CalendarEntryAt":  # Store as ISO string in SingleLineText
                fields[title_key] = value.isoformat()
            else:
                fields[title_key] = value.isoformat()
        elif isinstance(value, bool):
            fields[title_key] = str(value)
        elif isinstance(value, list) or isinstance(value, dict):
            fields[title_key] = json.dumps(value, ensure_ascii=False)
        else:
            fields[title_key] = value

    return fields


def _nocodb_record_to_journal_entry(record: dict[str, Any]) -> JournalEntry:
    """Converts a NocoDB v3 record dictionary to a JournalEntry object."""
    entry_data: dict[str, Any] = {}
    fields = record

    def get_val(key: str, type_converter=None, default=None):
        value = fields.get(key)
        if value is None:
            return default
        if type_converter:
            try:
                return type_converter(value)
            except (ValueError, TypeError, json.JSONDecodeError):
                print(f"Warning: Could not convert NocoDB field '{key}' with value '{value}' to target type.")
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
        # JournalEntry requires entry_at to be present. Fallback to now or raise error.
        # For now, let's make it raise an error to indicate missing crucial data.
        raise ValueError("NocoDB record missing 'EntryAt' field for JournalEntry.")
    entry_data["entry_at"] = entry_at

    entry_data["timezone"] = get_val("Timezone", str)
    entry_data["created_at"] = parse_dt(get_val("JournalCreatedAt", str))
    entry_data["modified_at"] = parse_dt(get_val("JournalModifiedAt", str))

    # --- Content ---
    entry_data["text_content"] = get_val("TextContent", str)
    entry_data["rich_text_content"] = get_val("RichTextContent", str)
    entry_data["title"] = get_val("Title", str)

    # --- Organization / Categorization ---
    # NocoDB stores lists as JSON strings if multi-select, or comma-separated if single-line text
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
    media_attachments_raw = get_val("MediaAttachments", str, "[]")
    if media_attachments_raw.startswith("["):
        entry_data["media_attachments"] = get_val(
            "MediaAttachments", lambda x: json.loads(x) if isinstance(x, str) else [], []
        )
    else:
        # Assuming single file attachment or similar; adjust as needed
        entry_data["media_attachments"] = []

    # --- Source Information (Flattened) ---
    entry_data["source_app_name"] = get_val("SourceAppName", str, "NocoDB")
    entry_data["source_original_id"] = get_val("SourceOriginalId", str)
    source_imported_at_val = parse_dt(get_val("SourceImportedAt", str))
    if source_imported_at_val:
        entry_data["source_imported_at"] = source_imported_at_val
    # else, let JournalEntry's default_factory handle it
    entry_data["source_raw_data"] = get_val("SourceRawData", str)  # Assuming raw data is stored as a string

    return JournalEntry(**entry_data)


class NocoDBJournalClient(AbstractJournalClient):
    def __init__(self, api_token: str, project_id: str, url: str = "http://localhost:8080"):
        self.api_base_url = urljoin(url, "api/v3/")  # Using v3 API
        self.headers = {"xc-token": api_token}
        self.project_id = project_id

        # Get the correct table ID for data operations
        self.journal_table_id = self._get_data_table_id(NOCODB_JOURNAL_TABLE_NAME)

    def _get_data_table_id(self, table_name: str) -> str:
        """
        Retrieves the correct table ID for data operations.
        Ensures table exists and extracts basic metadata.
        """
        print(f"Ensuring NocoDB table '{table_name}' exists and getting data ID ...")

        basic_table_meta = self._get_basic_table_meta(table_name)
        if not basic_table_meta:
            print(f"Table '{table_name}' not found, creating it...")
            basic_table_meta = self.create_table(table_name, NOCODB_JOURNAL_TABLE_COLUMNS)
            if not basic_table_meta:
                raise ValueError(f"Failed to create table '{table_name}'.")

        data_table_id = basic_table_meta.get("id")
        if not data_table_id:
            raise ValueError(f"Could not retrieve ID from basic metadata for table '{table_name}'.")

        print(f"Using data table ID : {data_table_id}")
        return data_table_id

    def _get_basic_table_meta(self, table_name: str) -> dict[str, Any] | None:
        """Fetches basic table metadata (id, title) using v3 meta API."""
        path = f"meta/bases/{self.project_id}/tables"
        try:
            tables = self._make_request("GET", path).get("list", [])
            for table in tables:
                if table.get("title") == table_name:
                    return table
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching basic table metadata for '{table_name}': {e}")
            return None

    def _get_detailed_table_meta(self, table_id: str) -> dict[str, Any] | None:
        """Fetches detailed table metadata (including UUID) using v3 meta API."""
        path = f"meta/tables/{table_id}"
        try:
            return self._make_request("GET", path)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching detailed table metadata for ID '{table_id}': {e}")
            return None

    def _make_request(self, method, path, **kwargs):
        url = urljoin(self.api_base_url, path.lstrip("/"))
        response = requests.request(method, url, headers=self.headers, **kwargs)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                print(f"NocoDB API Error Details ({e.response.status_code}): {e.response.text}")
            raise e
        return response.json()

    def create_table(self, table_name: str, columns_definition: list[dict]) -> dict[str, Any]:
        path = f"meta/bases/{self.project_id}/tables"
        payload = {"title": table_name, "fields": columns_definition}
        print(f"Sending request to create table '{table_name}'...")
        return self._make_request("POST", path, json=payload)

    def download_journal_entries(self) -> list[JournalEntry]:
        print("Downloading and parsing journal entries from NocoDB...")
        records = self.get_all_records()

        parsed_entries = []
        for i, rec in enumerate(records):
            try:
                entry = _nocodb_record_to_journal_entry(rec)  # Pass raw record
                if not entry.entry_at:
                    raise ValueError("'entry_at' field is missing or invalid.")
                parsed_entries.append(entry)
            except Exception as e:
                record_id_str = rec.get("JournalId", f"at index {i}")
                print(f"Warning: Skipping record '{record_id_str}' due to a conversion error: {e}")
        return parsed_entries

    def get_all_records(self) -> list[dict]:
        path = f"data/{self.project_id}/{self.journal_table_id}/records"
        return self._make_request("GET", path).get("list", [])

    def register_entry(self, entry: JournalEntry) -> Any:
        return self.register_entries([entry])

    def register_entries(self, entries: list[JournalEntry]) -> list[Any]:
        all_registered_records = []
        chunk_size = 10
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i : i + chunk_size]
            records_payload = [{"fields": _journal_entry_to_nocodb_fields(entry)} for entry in chunk]
            path = f"data/{self.project_id}/{self.journal_table_id}/records"
            try:
                response = self._make_request("POST", path, json=records_payload)
                if isinstance(response, list):
                    all_registered_records.extend(response)
                else:
                    all_registered_records.append(response)
            except requests.exceptions.RequestException as e:
                print(f"Error registering records in chunk {i // chunk_size + 1}: {e}")
                if e.response:
                    print(f"Response Body: {e.response.text}")
                raise e
        return all_registered_records

    def update_entry(self, entry: JournalEntry) -> Any:
        return self.update_entries([entry])

    def update_entries(self, entries: list[JournalEntry]) -> list[Any]:
        records_payload = [{"fields": _journal_entry_to_nocodb_fields(entry)} for entry in entries]
        path = f"data/{self.project_id}/{self.journal_table_id}/records"
        return self._make_request("PATCH", path, json=records_payload)

    def get_existing_entry_ids(self) -> list[str]:
        records = self.get_all_records()
        return [str(rec.get("JournalId")) for rec in records if rec.get("JournalId")]

    def get_existing_entries_with_modified_at(self) -> dict[str, datetime]:
        records = self.get_all_records()
        existing_data = {}
        for rec in records:
            record_id = rec.get("JournalId")
            modified_at_str = rec.get("JournalModifiedAt")
            if record_id and modified_at_str:
                try:
                    existing_data[str(record_id)] = datetime.fromisoformat(modified_at_str)
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse JournalModifiedAt for entry {record_id}: {modified_at_str}")
        return existing_data


if __name__ == "__main__":
    from dotenv import dotenv_values

    print("Running NocoDBJournalClient test...")
    config = dotenv_values()

    token = config.get("NOCODB_API_TOKEN")
    project_id = config.get("NOCODB_PROJECT_ID")
    url = config.get("NOCODB_URL", "http://localhost:8080")

    if not token or not project_id or not url:
        print("Error: NOCODB_API_TOKEN, NOCODB_PROJECT_ID, and NOCODB_URL must be set in your .env file.")
        exit(1)

    try:
        client = NocoDBJournalClient(api_token=token, project_id=project_id, url=url)

        journal_entries = client.download_journal_entries()
        print(f"Successfully downloaded and parsed {len(journal_entries)} entries.")

        if not journal_entries:
            print("No entries to process.")
        else:
            journey_cloud_entries = [journal_to_journey(entry) for entry in journal_entries]
            journey_cloud_dicts = [entry.to_dict() for entry in journey_cloud_entries]

            print("\n--- Journey Cloud Formatted JSON (from NocoDB) ---")
            print(json.dumps(journey_cloud_dicts, indent=2, ensure_ascii=False))
            print("----------------------------------------------------")

        print("\nTest finished successfully.")

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"An error occurred during the test: {e}")

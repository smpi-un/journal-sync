import json
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

from clients.teable_client_config import (
    JOURNAL_TABLE_COLUMNS,
    JOURNAL_TABLE_NAME,
)
from journal_core.converters import journal_to_journey
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry

# --- Conversion Functions ---


def _journal_entry_to_teable_fields(entry: JournalEntry) -> dict[str, Any]:
    """Converts a JournalEntry object to a dictionary of fields for Teable."""
    fields = {}

    def add_field(key, value):
        if value is not None:
            fields[key] = value

    add_field("Id", entry.id)
    if entry.entry_at:
        add_field("EntryAt", entry.entry_at.isoformat())
        add_field("CalendarEntryAt", entry.entry_at.isoformat())
    add_field("Timezone", entry.timezone)
    if entry.created_at:
        add_field("CreatedAt", entry.created_at.isoformat())
    if entry.modified_at:
        add_field("ModifiedAt", entry.modified_at.isoformat())

    add_field("TextContent", entry.text_content)
    add_field("RichTextContent", entry.rich_text_content)
    add_field("Title", entry.title)

    if entry.tags:
        add_field("Tags", ", ".join(entry.tags))

    add_field("Notebook", entry.notebook)
    add_field("IsFavorite", entry.is_favorite)
    add_field("IsPinned", entry.is_pinned)
    add_field("Mood", entry.mood_label)
    add_field("MoodScore", entry.mood_score)

    if entry.activities:
        add_field("Activities", ", ".join(entry.activities))

    add_field("LocationLat", entry.location_lat)
    add_field("LocationLon", entry.location_lon)
    add_field("LocationName", entry.location_name)
    add_field("LocationAddress", entry.location_address)
    add_field("LocationAltitude", entry.location_altitude)

    add_field("WeatherTemp", entry.weather_temperature)
    add_field("WeatherCondition", entry.weather_condition)
    add_field("WeatherHumidity", entry.weather_humidity)
    add_field("WeatherPressure", entry.weather_pressure)

    add_field("DeviceName", entry.device_name)
    add_field("StepCount", entry.step_count)

    add_field("SourceAppName", entry.source_app_name)
    add_field("SourceOriginalId", entry.source_original_id)
    if entry.source_imported_at:
        add_field("SourceImportedAt", entry.source_imported_at.isoformat())

    if entry.source_raw_data:
        raw_data_str = (
            entry.source_raw_data if isinstance(entry.source_raw_data, str) else json.dumps(entry.source_raw_data)
        )
        add_field("SourceRawData", raw_data_str)

    return fields


def _teable_record_to_journal_entry(record: dict) -> JournalEntry:
    """Converts a Teable record dictionary to a JournalEntry object."""
    fields = record.get("fields", {})
    entry_data = {}

    def get_val(key, type_converter=None):
        val = fields.get(key)
        if val is None:
            return None
        if type_converter:
            try:
                return type_converter(val)
            except (ValueError, TypeError, json.JSONDecodeError):
                print(f"Warning: Could not convert field '{key}' with value: {val}")
                raise
                return None
        return val

    def to_datetime(val: str) -> datetime | None:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))

    def to_str_list(val: str) -> list[str]:
        return [s.strip() for s in val.split(",")] if val else []

    def to_attachment_list(val: list[dict]) -> list[dict]:
        return [{"type": "file", "filename": att.get("name"), "url": att.get("url")} for att in val]

    entry_data["id"] = get_val("Id")
    entry_data["entry_at"] = get_val("EntryAt", to_datetime)
    entry_data["timezone"] = get_val("Timezone")
    entry_data["created_at"] = get_val("CreatedAt", to_datetime)
    entry_data["modified_at"] = get_val("ModifiedAt", to_datetime)
    entry_data["text_content"] = get_val("TextContent")
    entry_data["rich_text_content"] = get_val("RichTextContent")
    entry_data["title"] = get_val("Title")
    entry_data["tags"] = get_val("Tags", to_str_list)
    entry_data["notebook"] = get_val("Notebook")
    entry_data["is_favorite"] = get_val("IsFavorite", bool)
    entry_data["is_pinned"] = get_val("IsPinned", bool)
    entry_data["mood_label"] = get_val("Mood")
    entry_data["mood_score"] = get_val("MoodScore", float)
    entry_data["activities"] = get_val("Activities", to_str_list)
    entry_data["location_lat"] = get_val("LocationLat", float)
    entry_data["location_lon"] = get_val("LocationLon", float)
    entry_data["location_name"] = get_val("LocationName")
    entry_data["location_address"] = get_val("LocationAddress")
    entry_data["location_altitude"] = get_val("LocationAltitude", float)
    entry_data["weather_temperature"] = get_val("WeatherTemp", float)
    entry_data["weather_condition"] = get_val("WeatherCondition")
    entry_data["weather_humidity"] = get_val("WeatherHumidity", float)
    entry_data["weather_pressure"] = get_val("WeatherPressure", float)
    entry_data["device_name"] = get_val("DeviceName")
    entry_data["step_count"] = get_val("StepCount", int)
    entry_data["media_attachments"] = get_val("Attachments", to_attachment_list)
    entry_data["source_app_name"] = get_val("SourceAppName")
    entry_data["source_original_id"] = get_val("SourceOriginalId")
    entry_data["source_imported_at"] = get_val("SourceImportedAt", to_datetime)
    entry_data["source_raw_data"] = get_val("SourceRawData")

    final_entry_data = {k: v for k, v in entry_data.items() if v is not None}

    return JournalEntry(**final_entry_data)


class TeableJournalClient(AbstractJournalClient):
    """A wrapper class for the Teable API, using requests directly."""

    def __init__(self, api_token: str, base_id: str, api_url: str = "https://app.teable.ai"):
        if not api_token or not base_id:
            raise ValueError("API token and base ID must be provided.")

        self.base_url = urljoin(api_url, "api/")
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        self.base_id = base_id

        table_id = self._get_table_id_by_name(JOURNAL_TABLE_NAME)
        if not table_id:
            print(f"Table '{JOURNAL_TABLE_NAME}' not found, creating it...")
            table_id = self.create_table(JOURNAL_TABLE_NAME, JOURNAL_TABLE_COLUMNS)
            if not table_id:
                raise ValueError(f"Failed to create table '{JOURNAL_TABLE_NAME}'.")
        self.journal_table_id = table_id

    def create_table(self, table_name: str, fields: list[dict[str, Any]]) -> str | None:
        """Creates a new table in the Teable base and returns its ID."""
        path = f"/base/{self.base_id}/table"
        print(fields)
        payload = {"name": table_name, "fields": fields}
        try:
            response = self._make_request("POST", path, json=payload)
            return response.get("id")
        except requests.exceptions.RequestException as e:
            print(f"Error creating table '{table_name}': {e}")
            raise
            return None

    def _get_table_id_by_name(self, table_name: str) -> str | None:
        """Finds a table by its name and returns its ID."""
        print(f"Fetching ID for table '{table_name}'...")
        tables = self._make_request("GET", f"/base/{self.base_id}/table")
        for table in tables:
            if table["name"] == table_name:
                print(f"Found table ID: {table['id']}")
                return table["id"]
        return None

    def _make_request(self, method, path, **kwargs):
        url = urljoin(self.base_url, path.lstrip("/"))
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def download_journal_entries(self) -> list[JournalEntry]:
        """Downloads all journal entries and parses them into JournalEntry objects."""
        print("Downloading and parsing journal entries from Teable...")
        path = f"/table/{self.journal_table_id}/record"
        response_data = self._make_request("GET", path)

        parsed_entries = []
        if response_data and "records" in response_data:
            for i, rec in enumerate(response_data["records"]):
                try:
                    entry = _teable_record_to_journal_entry(rec)
                    # A journal entry without a date is not valid, so we enforce it here.
                    if not entry.entry_at:
                        raise ValueError("'entry_at' field is missing or invalid.")
                    parsed_entries.append(entry)
                except Exception as e:
                    record_id_str = rec.get("fields", {}).get("Id", f"at index {i}")
                    print(f"Warning: Skipping record '{record_id_str}' due to a conversion error: {e}")

        return parsed_entries

    def register_entry(self, entry: JournalEntry) -> Any:
        return self.register_entries([entry])

    def register_entries(self, entries: list[JournalEntry]) -> list[Any]:
        records_to_create = [{"fields": _journal_entry_to_teable_fields(entry)} for entry in entries]
        path = f"/table/{self.journal_table_id}/record"
        response = self._make_request("POST", path, json={"records": records_to_create})
        return response.get("records", [])

    def update_entry(self, entry: JournalEntry) -> Any:
        return self.update_entries([entry])

    def update_entries(self, entries: list[JournalEntry]) -> list[Any]:
        print("Warning: Batch update in Teable is performed individually.")
        updated_records = []
        for entry in entries:
            records = self.get_all_records(query={"where": json.dumps({"field": "Id", "op": "is", "value": entry.id})})
            if not records:
                print(f"Warning: Could not find record with Id '{entry.id}' to update.")
                continue

            teable_record_id = records[0]["id"]
            path = f"/table/{self.journal_table_id}/record/{teable_record_id}"
            payload = {"fields": _journal_entry_to_teable_fields(entry)}
            updated_records.append(self._make_request("PATCH", path, json=payload))
        return updated_records

    def get_all_records(self, query: dict | None = None) -> list[dict]:
        """Gets all records, with an optional query."""
        params = query or {}
        path = f"/table/{self.journal_table_id}/record"
        print(path)
        response = self._make_request("GET", path, params=params)
        return response.get("records", [])

    def get_existing_entry_ids(self) -> list[str]:
        all_records = self.get_all_records()
        return [str(record["fields"]["Id"]) for record in all_records if "Id" in record.get("fields", {})]

    def get_existing_entries_with_modified_at(self) -> dict[str, datetime]:
        all_records = self.get_all_records()
        existing_data = {}
        for record in all_records:
            fields = record.get("fields", {})
            record_id = fields.get("Id")
            modified_at_str = fields.get("ModifiedAt")
            if record_id and modified_at_str:
                try:
                    existing_data[str(record_id)] = datetime.fromisoformat(modified_at_str)
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse ModifiedAt for entry {record_id}: {modified_at_str}")
                    raise
        return existing_data


if __name__ == "__main__":
    from dotenv import dotenv_values

    print("Running TeableJournalClient test...")

    config = dotenv_values()

    token = config.get("TEABLE_API_TOKEN")
    base_id = config.get("TEABLE_BASE_ID")
    url = config.get("TEABLE_API_URL", "https://app.teable.ai")

    if token and base_id and url:
        try:
            client = TeableJournalClient(api_token=token, base_id=base_id, api_url=url)

            journal_entries = client.download_journal_entries()
            print(f"Successfully downloaded and parsed {len(journal_entries)} entries.")

            if not journal_entries:
                print("No entries to process.")
            else:
                journey_cloud_entries = [journal_to_journey(entry) for entry in journal_entries]
                journey_cloud_dicts = [entry.to_dict() for entry in journey_cloud_entries]

                print("\n--- Journey Cloud Formatted JSON (from Teable) ---")
                print(json.dumps(journey_cloud_dicts, indent=2, ensure_ascii=False))
                print("----------------------------------------------------")

            print("\nTest finished successfully.")

        except (ValueError, requests.exceptions.RequestException) as e:
            print(f"An error occurred during the test: {e}")
            raise
    else:
        print("Error: Could not read TEABLE_API_TOKEN, TEABLE_BASE_ID, and TEABLE_API_URL from your .env file.")
        print("Please ensure the .env file exists in the root directory and the variables are set correctly.")

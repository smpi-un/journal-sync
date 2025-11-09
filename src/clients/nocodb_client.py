import json
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

from clients.nocodb_client_config import (
    NOCODB_API_TOKEN,
    NOCODB_FIELD_NAMES,
    NOCODB_JOURNAL_TABLE_COLUMNS,
    NOCODB_JOURNAL_TABLE_NAME,
    NOCODB_PROJECT_ID,
    NOCODB_URL,
)
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry


class NocoDBJournalClient(AbstractJournalClient):
    def __init__(self):
        self.nocodb_url = NOCODB_URL
        self.api_base_url = urljoin(NOCODB_URL, "api/v2/")
        self.api_token = NOCODB_API_TOKEN
        self.project_id = NOCODB_PROJECT_ID
        self.headers = {"xc-token": self.api_token}
        self.journal_table_id = None
        self.journal_table_uuid = None

    def _handle_request_error(self, e, action_description="request"):
        print(f"Error during {action_description}: {e}")
        if e.response:
            print(f"Request URL: {e.request.url}")
            print(f"Response content: {e.response.text}")
        sys.stdout.flush()
        return None

    def _get_journal_table_meta(self):
        if self.journal_table_id and self.journal_table_uuid:
            return {"id": self.journal_table_id, "uuid": self.journal_table_uuid}

        table_meta = self.get_table_meta(NOCODB_JOURNAL_TABLE_NAME)
        if table_meta:
            self.journal_table_id = table_meta["id"]
            # NocoDB v2 API uses UUID for some operations, need to fetch detailed meta
            detailed_meta = self._get_detailed_table_meta(self.journal_table_id)
            if detailed_meta:
                self.journal_table_uuid = detailed_meta.get("uuid")
                if not self.journal_table_uuid:
                    print(
                        "Info: NocoDB table"
                        f" '{NOCODB_JOURNAL_TABLE_NAME}' is missing UUID. "
                        f"Falling back to Table ID '{self.journal_table_id}'."
                    )
                    self.journal_table_uuid = self.journal_table_id
                return {"id": self.journal_table_id, "uuid": self.journal_table_uuid}

        # If table not found, try to create it
        print(
            f"Journal table '{NOCODB_JOURNAL_TABLE_NAME}' not found. "
            "Attempting to create..."
        )
        created_table_meta = self.create_table_if_not_exists(
            NOCODB_JOURNAL_TABLE_NAME, NOCODB_JOURNAL_TABLE_COLUMNS
        )
        if created_table_meta:
            self.journal_table_id = created_table_meta["id"]
            self.journal_table_uuid = created_table_meta.get("uuid")
            if not self.journal_table_uuid:
                print(
                    "Info: NocoDB table"
                    f" '{NOCODB_JOURNAL_TABLE_NAME}' is missing UUID after creation. "
                    f"Falling back to Table ID '{self.journal_table_id}'."
                )
                self.journal_table_uuid = self.journal_table_id
            return {"id": self.journal_table_id, "uuid": self.journal_table_uuid}

        raise ValueError(
            "Could not find or create journal table "
            f"'{NOCODB_JOURNAL_TABLE_NAME}' in NocoDB."
        )

    def _get_detailed_table_meta(self, table_id):
        """Fetches detailed metadata for a table using v2 API."""
        detailed_meta_url = urljoin(self.api_base_url, f"meta/tables/{table_id}")
        try:
            response = requests.get(detailed_meta_url, headers=self.headers)
            response.raise_for_status()
            detailed_meta_data = response.json()
            return detailed_meta_data
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(
                e, f"fetching detailed metadata for table ID {table_id}"
            )

    def get_table_meta(self, table_name):
        """Gets metadata for the specified table using v2 API."""
        list_tables_url = urljoin(
            self.api_base_url, f"meta/bases/{self.project_id}/tables"
        )
        try:
            response = requests.get(list_tables_url, headers=self.headers)
            response.raise_for_status()
            tables = response.json()["list"]
            for table in tables:
                if table["title"] == table_name:
                    return table
            return None
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, f"listing tables for {table_name}")

    def _journal_entry_to_nocodb_record(self, entry: JournalEntry) -> dict[str, Any]:
        record_fields = {}

        # Explicitly map JournalEntry fields to NocoDB column names and types
        if entry.id is not None:
            record_fields[NOCODB_FIELD_NAMES["id"]] = entry.id
        if entry.entry_at is not None:
            record_fields[NOCODB_FIELD_NAMES["entry_at"]] = entry.entry_at.isoformat()
        if entry.timezone is not None:
            record_fields[NOCODB_FIELD_NAMES["timezone"]] = entry.timezone
        if entry.created_at is not None:
            record_fields[NOCODB_FIELD_NAMES["created_at"]] = (
                entry.created_at.isoformat()
            )
        if entry.modified_at is not None:
            record_fields[NOCODB_FIELD_NAMES["modified_at"]] = (
                entry.modified_at.isoformat()
            )
        if entry.text_content is not None:
            record_fields[NOCODB_FIELD_NAMES["text_content"]] = entry.text_content
        if entry.rich_text_content is not None:
            record_fields[NOCODB_FIELD_NAMES["rich_text_content"]] = (
                entry.rich_text_content
            )
        if entry.title is not None:
            record_fields[NOCODB_FIELD_NAMES["title"]] = entry.title
        if entry.tags:
            record_fields[NOCODB_FIELD_NAMES["tags"]] = ", ".join(
                entry.tags
            )  # NocoDB 'varchar' for tags
        if entry.notebook is not None:
            record_fields[NOCODB_FIELD_NAMES["notebook"]] = entry.notebook
        record_fields[NOCODB_FIELD_NAMES["is_favorite"]] = 1 if entry.is_favorite else 0
        record_fields[NOCODB_FIELD_NAMES["is_pinned"]] = 1 if entry.is_pinned else 0
        if entry.mood_label is not None:
            record_fields[NOCODB_FIELD_NAMES["mood_label"]] = entry.mood_label
        if entry.mood_score is not None:
            record_fields[NOCODB_FIELD_NAMES["mood_score"]] = entry.mood_score
        if entry.activities:
            record_fields[NOCODB_FIELD_NAMES["activities"]] = ", ".join(
                entry.activities
            )  # NocoDB 'varchar' for activities
        if entry.location_lat is not None:
            record_fields[NOCODB_FIELD_NAMES["location_lat"]] = entry.location_lat
        if entry.location_lon is not None:
            record_fields[NOCODB_FIELD_NAMES["location_lon"]] = entry.location_lon
        if entry.location_name is not None:
            record_fields[NOCODB_FIELD_NAMES["location_name"]] = entry.location_name
        if entry.location_address is not None:
            record_fields[NOCODB_FIELD_NAMES["location_address"]] = (
                entry.location_address
            )
        if entry.location_altitude is not None:
            record_fields[NOCODB_FIELD_NAMES["location_altitude"]] = (
                entry.location_altitude
            )
        if entry.weather_temperature is not None:
            record_fields[NOCODB_FIELD_NAMES["weather_temperature"]] = (
                entry.weather_temperature
            )
        if entry.weather_condition is not None:
            record_fields[NOCODB_FIELD_NAMES["weather_condition"]] = (
                entry.weather_condition
            )
        if entry.weather_humidity is not None:
            record_fields[NOCODB_FIELD_NAMES["weather_humidity"]] = (
                entry.weather_humidity
            )
        if entry.weather_pressure is not None:
            record_fields[NOCODB_FIELD_NAMES["weather_pressure"]] = (
                entry.weather_pressure
            )
        if entry.device_name is not None:
            record_fields[NOCODB_FIELD_NAMES["device_name"]] = entry.device_name
        if entry.step_count is not None:
            record_fields[NOCODB_FIELD_NAMES["step_count"]] = entry.step_count
        # Media attachments will be stored as JSON string in a longtext field
        if entry.media_attachments:
            record_fields[NOCODB_FIELD_NAMES["media_attachments"]] = json.dumps(
                entry.media_attachments
            )
        if entry.source_app_name is not None:
            record_fields[NOCODB_FIELD_NAMES["source_app_name"]] = entry.source_app_name
        if entry.source_original_id is not None:
            record_fields[NOCODB_FIELD_NAMES["source_original_id"]] = (
                entry.source_original_id
            )
        if entry.source_imported_at is not None:
            record_fields[NOCODB_FIELD_NAMES["source_imported_at"]] = (
                entry.source_imported_at.isoformat()
            )
        if entry.source_raw_data is not None:
            record_fields[NOCODB_FIELD_NAMES["source_raw_data"]] = json.dumps(
                entry.source_raw_data
            )  # Store raw data as JSON string

        return record_fields

    def register_entry(self, entry: JournalEntry) -> Any:
        table_meta = self._get_journal_table_meta()
        table_uuid = table_meta["uuid"]
        nocodb_record = self._journal_entry_to_nocodb_record(entry)
        response = self.create_records(table_uuid, [nocodb_record])
        return response

    def register_entries(self, entries: list[JournalEntry]) -> list[Any]:
        table_meta = self._get_journal_table_meta()
        table_uuid = table_meta["uuid"]
        nocodb_records = [
            self._journal_entry_to_nocodb_record(entry) for entry in entries
        ]
        response = self.create_records(table_uuid, nocodb_records)
        return response

    def get_existing_entry_ids(self) -> list[str]:
        table_meta = self._get_journal_table_meta()
        table_id = table_meta["id"]
        all_records = self.get_all_records(table_id)
        if all_records:
            # Assuming 'Id' is the field name for the unique ID in NocoDB
            return [
                str(record[NOCODB_FIELD_NAMES["id"]])
                for record in all_records
                if NOCODB_FIELD_NAMES["id"] in record
            ]
        return []

    def get_existing_entries_with_modified_at(self) -> dict[str, datetime]:
        table_meta = self._get_journal_table_meta()
        table_id = table_meta["id"]
        all_records = self.get_all_records(table_id)
        existing_data = {}
        if all_records:
            for record in all_records:
                record_id = record.get(NOCODB_FIELD_NAMES["id"])
                modified_at_str = record.get(NOCODB_FIELD_NAMES["modified_at"])
                if record_id and modified_at_str:
                    try:
                        existing_data[str(record_id)] = datetime.fromisoformat(
                            modified_at_str
                        )
                    except ValueError:
                        print(
                            f"Warning: Could not parse modified_at for entry {record_id}: {modified_at_str}"
                        )
        return existing_data

    def update_entry(self, entry: JournalEntry) -> Any:
        table_meta = self._get_journal_table_meta()
        table_uuid = table_meta["uuid"]
        nocodb_record = self._journal_entry_to_nocodb_record(entry)
        # NocoDB update_records expects a list of records
        response = self.update_records(table_uuid, [nocodb_record])
        return response

    def update_entries(self, entries: list[JournalEntry]) -> list[Any]:
        table_meta = self._get_journal_table_meta()
        table_uuid = table_meta["uuid"]
        nocodb_records = [
            self._journal_entry_to_nocodb_record(entry) for entry in entries
        ]
        response = self.update_records(table_uuid, nocodb_records)
        return response

    def create_table(self, table_name, columns_definition):
        """Creates a new table in NocoDB using v2 API."""
        create_table_url = urljoin(
            self.api_base_url, f"meta/bases/{self.project_id}/tables"
        )
        payload = {"title": table_name, "columns": columns_definition}
        print(f"Attempting to create table '{table_name}'...")
        try:
            response = requests.post(
                create_table_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            print(f"Table '{table_name}' created successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, f"creating table {table_name}")

    def create_table_if_not_exists(self, table_name, columns_definition):
        """
        Checks if a table exists, if not, creates it. Returns detailed table metadata.
        """
        table_meta = self.get_table_meta(table_name)
        if table_meta:
            print(f"Table '{table_name}' already exists.")
            # Fetch detailed metadata for existing table
            detailed_meta = self._get_detailed_table_meta(table_meta["id"])
            return detailed_meta
        else:
            # Create table and then fetch its detailed metadata
            created_table_meta = self.create_table(table_name, columns_definition)
            if created_table_meta:
                detailed_meta = self._get_detailed_table_meta(created_table_meta["id"])
                return detailed_meta
            return None

    def add_column_to_table(self, table_id, column_definition):
        """Adds a column to an existing table in NocoDB."""
        add_column_url = urljoin(self.api_base_url, f"meta/tables/{table_id}/columns")
        print(
            f"Attempting to add column '{column_definition.get('title')}' to table ID '{table_id}'..."
        )
        try:
            response = requests.post(
                add_column_url, headers=self.headers, json=column_definition
            )
            print(response.text)
            response.raise_for_status()
            print(f"Column '{column_definition.get('title')}' added successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(
                e, f"adding column {column_definition.get('title')}"
            )

    def upload_file(self, file_path):
        """Uploads a file to NocoDB storage and returns its metadata."""
        upload_url = urljoin(self.api_base_url, "storage/upload")
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(upload_url, headers=self.headers, files=files)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, f"uploading file {file_path}")

    def create_attachment_record(self, attachment_table_id, file_metadata, order):
        """Creates a record in the NocoDB Attachments table without linking."""
        create_url = urljoin(self.api_base_url, f"tables/{attachment_table_id}/records")
        attachment_data = {
            "FileName": file_metadata.get("title"),
            "FilePath": file_metadata.get("path"),
            "Order": order,
            "Attachment": [
                {
                    "url": (
                        "https://some-s3-server.com/nc/uploads/2023/10/16/some-key/"
                        "3niqHLngUKiU2Hupe8.jpeg"
                    ),  # Placeholder
                    "title": file_metadata.get("title"),
                    "mimetype": file_metadata.get(
                        "mimetype", "application/octet-stream"
                    ),
                    "size": file_metadata.get("size", 0),
                    "signedUrl": "",  # Placeholder
                }
            ],
        }
        try:
            response = requests.post(
                create_url, headers=self.headers, json=attachment_data
            )
            print(response.text)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(
                e, f"creating attachment record for {file_metadata.get('title')}"
            )

    def link_attachment_to_journal_entry(
        self,
        attachment_table_id,
        attachment_record_id,
        link_column_id,
        journal_entry_id,
    ):
        """Links an attachment record to a journal entry."""
        link_url = urljoin(
            self.api_base_url,
            f"tables/{attachment_table_id}/links/{link_column_id}/records/{attachment_record_id}",
        )
        payload = [journal_entry_id]
        try:
            response = requests.post(link_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(
                e,
                (
                    f"linking attachment {attachment_record_id} to journal entry "
                    f"{journal_entry_id}"
                ),
            )

    def get_all_records(self, table_id):
        """Gets all records from the specified table using table ID."""
        list_records_url_v2 = urljoin(self.api_base_url, f"tables/{table_id}/records")
        print(f"Attempting to get all existing records from URL: {list_records_url_v2}")
        try:
            response = requests.get(list_records_url_v2, headers=self.headers)
            response.raise_for_status()
            return response.json()["list"]
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(
                e, f"getting existing records from table ID {table_id}"
            )

    def create_records(self, table_id, records):
        """Creates new records in the specified table using table ID."""
        print(records)
        if not records:
            return
        print(f"Creating {len(records)} new records...")
        try:
            create_url_v2 = urljoin(self.api_base_url, f"tables/{table_id}/records")
            response = requests.post(create_url_v2, headers=self.headers, json=records)
            print(response.text)
            response.raise_for_status()
            print("New records created successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "creating new records")

    def update_records(self, table_id, records):
        """Updates existing records in the specified table using table ID."""
        if not records:
            return
        print(f"Updating {len(records)} existing records...")
        try:
            update_url_v2 = urljoin(self.api_base_url, f"tables/{table_id}/records")
            response = requests.patch(update_url_v2, headers=self.headers, json=records)
            response.raise_for_status()
            print("Existing records updated successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "updating existing records")

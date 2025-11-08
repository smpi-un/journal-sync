import requests
import mimetypes
import os
import json
from typing import List, Dict, Any
from datetime import datetime

from clients.teable_client_config import TEABLE_API_TOKEN, TEABLE_API_URL, TEABLE_BASE_ID, TEABLE_FIELD_NAMES, JOURNAL_TABLE_NAME, ATTACHMENT_TABLE_NAME
from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry

class TeableJournalClient(AbstractJournalClient):
    """A wrapper class for the Teable API, using requests directly."""
    def __init__(self):
        self.base_url = TEABLE_API_URL.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {TEABLE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.base_id = TEABLE_BASE_ID
        self.journal_table_id = None
        self.attachment_table_id = None
        self.attachment_field_id = None
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        print("Ensuring Teable tables exist...")
        # Ensure JournalEntries table exists
        journal_table = self.get_table_by_name(JOURNAL_TABLE_NAME)
        if not journal_table:
            print(f"Table '{JOURNAL_TABLE_NAME}' not found, creating it...")
            from clients.teable_client_config import JOURNAL_TABLE_COLUMNS # Import here to avoid circular dependency if config imports client
            journal_table = self.create_table(JOURNAL_TABLE_NAME, JOURNAL_TABLE_COLUMNS)
            if not journal_table:
                raise ValueError(f"Failed to create table '{JOURNAL_TABLE_NAME}'.")
        else:
            print(f"Table '{JOURNAL_TABLE_NAME}' already exists.")
        self.journal_table_id = journal_table['id']
        print(f"Table '{JOURNAL_TABLE_NAME}' ID: {self.journal_table_id}")
        self._verify_primary_key_setting(self.journal_table_id, "Id")

        # Get and store the Attachments field ID
        fields = self.get_table_fields(self.journal_table_id)
        if fields:
            for field in fields:
                if field.get('name') == TEABLE_FIELD_NAMES['media_attachments']:
                    self.attachment_field_id = field.get('id')
                    break
        if not self.attachment_field_id:
            print(f"Warning: Could not find the field ID for '{TEABLE_FIELD_NAMES['media_attachments']}'. File uploads will fail.")
        else:
            print(f"Found Attachment Field '{TEABLE_FIELD_NAMES['media_attachments']}' with ID: {self.attachment_field_id}")

        # Ensure Attachments table exists and is linked
        # attachment_table = self.get_table_by_name(ATTACHMENT_TABLE_NAME)
        # if not attachment_table:
        #     print(f"Table '{ATTACHMENT_TABLE_NAME}' not found, creating it...")
        #     from clients.teable_client_config import ATTACHMENT_TABLE_COLUMNS, ATTACHMENT_LINK_FIELD, ATTACHMENT_LINK_FIELD_DEFINITION
        #     
        #     # Deep copy to avoid modifying the original config list
        #     attachment_cols_to_create = [col.copy() for col in ATTACHMENT_TABLE_COLUMNS]
        #     link_field_def = ATTACHMENT_LINK_FIELD_DEFINITION.copy()
        #     link_field_def["options"]["foreignTableId"] = self.journal_table_id
        #     attachment_cols_to_create.append(link_field_def)

        #     attachment_table = self.create_table(ATTACHMENT_TABLE_NAME, attachment_cols_to_create)
        #     if not attachment_table:
        #         raise ValueError(f"Failed to create table '{ATTACHMENT_TABLE_NAME}'.")
        # else:
        #     print(f"Table '{ATTACHMENT_TABLE_NAME}' already exists.")
        # self.attachment_table_id = attachment_table['id']
        # print(f"Table '{ATTACHMENT_TABLE_NAME}' ID: {self.attachment_table_id}")
        # self._verify_primary_key_setting(self.attachment_table_id, "Id")

    def _verify_primary_key_setting(self, table_id: str, field_name: str):
        """
        Verifies that a specific field in a Teable table is marked as primary.
        """
        fields = self.get_table_fields(table_id)
        if not fields:
            print(f"Warning: Could not retrieve fields for table ID {table_id} to verify primary key.")
            return
        
        is_primary_found = False
        for field in fields:
            if field.get('name') == field_name and field.get('isPrimary') is True:
                is_primary_found = True
                break
        
        if not is_primary_found:
            print(f"Warning: Field '{field_name}' in table ID {table_id} is NOT marked as primary key in Teable.")
            print("This might lead to unexpected behavior regarding unique identification.")

    def _get_journal_table_id(self):
        if not self.journal_table_id:
            self._ensure_tables_exist() # Re-run setup if for some reason ID is not set
        return self.journal_table_id

    def _journal_entry_to_teable_record(self, entry: JournalEntry, include_attachments=False) -> Dict[str, Any]:
        record_fields = {}
        
        # Explicitly map JournalEntry fields to Teable column names and types
        if entry.id is not None: record_fields[TEABLE_FIELD_NAMES["id"]] = entry.id
        # print(entry.id) # Reduce noise
        if entry.entry_at is not None: record_fields[TEABLE_FIELD_NAMES["entry_at"]] = entry.entry_at.isoformat()
        if entry.timezone is not None: record_fields[TEABLE_FIELD_NAMES["timezone"]] = entry.timezone
        if entry.created_at is not None: record_fields[TEABLE_FIELD_NAMES["created_at"]] = entry.created_at.isoformat()
        if entry.modified_at is not None: record_fields[TEABLE_FIELD_NAMES["modified_at"]] = entry.modified_at.isoformat()
        if entry.text_content is not None: record_fields[TEABLE_FIELD_NAMES["text_content"]] = entry.text_content
        if entry.rich_text_content is not None: record_fields[TEABLE_FIELD_NAMES["rich_text_content"]] = entry.rich_text_content
        if entry.title is not None: record_fields[TEABLE_FIELD_NAMES["title"]] = entry.title
        if entry.tags: record_fields[TEABLE_FIELD_NAMES["tags"]] = ", ".join(entry.tags) # Teable 'singleLineText' for tags
        if entry.notebook is not None: record_fields[TEABLE_FIELD_NAMES["notebook"]] = entry.notebook
        record_fields[TEABLE_FIELD_NAMES["is_favorite"]] = entry.is_favorite
        record_fields[TEABLE_FIELD_NAMES["is_pinned"]] = entry.is_pinned
        if entry.mood_label is not None: record_fields[TEABLE_FIELD_NAMES["mood_label"]] = entry.mood_label
        if entry.mood_score is not None: record_fields[TEABLE_FIELD_NAMES["mood_score"]] = entry.mood_score
        if entry.activities: record_fields[TEABLE_FIELD_NAMES["activities"]] = ", ".join(entry.activities) # Teable 'singleLineText' for activities
        if entry.location_lat is not None: record_fields[TEABLE_FIELD_NAMES["location_lat"]] = entry.location_lat
        if entry.location_lon is not None: record_fields[TEABLE_FIELD_NAMES["location_lon"]] = entry.location_lon
        if entry.location_name is not None: record_fields[TEABLE_FIELD_NAMES["location_name"]] = entry.location_name
        if entry.location_address is not None: record_fields[TEABLE_FIELD_NAMES["location_address"]] = entry.location_address
        if entry.location_altitude is not None: record_fields[TEABLE_FIELD_NAMES["location_altitude"]] = entry.location_altitude
        if entry.weather_temperature is not None: record_fields[TEABLE_FIELD_NAMES["weather_temperature"]] = entry.weather_temperature
        if entry.weather_condition is not None: record_fields[TEABLE_FIELD_NAMES["weather_condition"]] = entry.weather_condition
        if entry.weather_humidity is not None: record_fields[TEABLE_FIELD_NAMES["weather_humidity"]] = entry.weather_humidity
        if entry.weather_pressure is not None: record_fields[TEABLE_FIELD_NAMES["weather_pressure"]] = entry.weather_pressure
        if entry.device_name is not None: record_fields[TEABLE_FIELD_NAMES["device_name"]] = entry.device_name
        if entry.step_count is not None: record_fields[TEABLE_FIELD_NAMES["step_count"]] = entry.step_count
        # Attachments are handled in register_entries
        if entry.source_app_name is not None: record_fields[TEABLE_FIELD_NAMES["source_app_name"]] = entry.source_app_name
        if entry.source_original_id is not None: record_fields[TEABLE_FIELD_NAMES["source_original_id"]] = entry.source_original_id
        if entry.source_imported_at is not None: record_fields[TEABLE_FIELD_NAMES["source_imported_at"]] = entry.source_imported_at.isoformat()
        if entry.source_raw_data is not None: record_fields[TEABLE_FIELD_NAMES["source_raw_data"]] = json.dumps(entry.source_raw_data) # Store raw data as JSON string

        return {"fields": record_fields}

    def register_entry(self, entry: JournalEntry) -> Any:
        return self.register_entries([entry])

    def register_entries(self, entries: List[JournalEntry]) -> List[Any]:
        table_id = self._get_journal_table_id()
        if not table_id:
            raise ValueError("Journal table ID is not set.")

        records_to_create_without_attachments = []
        entries_with_attachments = []
        
        for entry in entries:
            if entry.media_attachments:
                entries_with_attachments.append(entry)
            else:
                records_to_create_without_attachments.append(self._journal_entry_to_teable_record(entry))

        all_results = []

        # Batch create records without attachments
        if records_to_create_without_attachments:
            print(f"Registering {len(records_to_create_without_attachments)} entries without attachments...")
            try:
                response = self.create_records(table_id, records_to_create_without_attachments)
                all_results.extend(response.get('records', []))
            except Exception as e:
                print(f"Error batch-creating records: {e}")

        # Handle entries with attachments one by one
        if entries_with_attachments:
            if not self.attachment_field_id:
                print("Error: Attachment field ID is not available. Cannot upload files.")
                # Optionally, create the records without attachments anyway
                for entry in entries_with_attachments:
                    record_payload = self._journal_entry_to_teable_record(entry)
                    try:
                        response = self.create_records(table_id, [record_payload])
                        all_results.extend(response.get('records', []))
                    except Exception as e:
                        print(f"Error creating record for entry {entry.id} (attachments skipped): {e}")
                return all_results

            print(f"Registering {len(entries_with_attachments)} entries with attachments one by one...")
            for entry in entries_with_attachments:
                # 1. Create the record without attachments first
                record_payload = self._journal_entry_to_teable_record(entry)
                try:
                    print(f"Creating record for entry {entry.id}...")
                    response = self.create_records(table_id, [record_payload])
                    created_records = response.get('records')
                    if not created_records:
                        print(f"Failed to create record for entry {entry.id}, skipping attachment upload.")
                        continue
                    
                    record_id = created_records[0]['id']
                    all_results.append(created_records[0])

                    # 2. Upload attachments to the newly created record
                    print(f"Uploading {len(entry.media_attachments)} attachments for record {record_id}...")
                    for attachment in entry.media_attachments:
                        file_path = attachment.get('path')
                        if file_path and os.path.exists(file_path):
                            try:
                                self.upload_file(table_id, record_id, self.attachment_field_id, file_path)
                                print(f"  Successfully uploaded {os.path.basename(file_path)}")
                            except Exception as e:
                                print(f"  Error uploading file {file_path} for record {record_id}: {e}")
                        else:
                            print(f"  Warning: Attachment file not found or path is missing: {file_path}")

                except Exception as e:
                    print(f"Error processing entry {entry.id} with attachments: {e}")
        
        return all_results

    def get_existing_entry_ids(self) -> List[str]:
        table_id = self._get_journal_table_id()
        all_records = self.get_all_records(table_id)
        if all_records and 'records' in all_records:
            # Assuming 'id' is the field name for the unique ID in Teable
            return [str(record['fields']['Id']) for record in all_records['records'] if 'Id' in record['fields']]
        return []

    def get_existing_entries_with_modified_at(self) -> Dict[str, datetime]:
        table_id = self._get_journal_table_id()
        all_records = self.get_all_records(table_id)
        existing_data = {}
        if all_records and 'records' in all_records:
            for record in all_records['records']:
                record_id = record['fields'].get(TEABLE_FIELD_NAMES["id"])
                modified_at_str = record['fields'].get(TEABLE_FIELD_NAMES["modified_at"])
                if record_id and modified_at_str:
                    try:
                        existing_data[str(record_id)] = datetime.fromisoformat(modified_at_str)
                    except ValueError:
                        print(f"Warning: Could not parse modified_at for entry {record_id}: {modified_at_str}")
        return existing_data

    def update_entry(self, entry: JournalEntry) -> Any:
        table_id = self._get_journal_table_id()
        teable_record = self._journal_entry_to_teable_record(entry)
        # Teable update_records expects a list of records, each with 'id' and 'fields'
        response = self.update_records(table_id, [teable_record])
        return response

    def update_entries(self, entries: List[JournalEntry]) -> List[Any]:
        table_id = self._get_journal_table_id()
        teable_records = [self._journal_entry_to_teable_record(entry) for entry in entries]
        response = self.update_records(table_id, teable_records)
        return response


    def _make_request(self, method, path, json_data=None):
        url = f"{self.base_url}{path}"
        # print(f"--- DEBUG: Making {method} request to {url} ---") # Commented out for less verbose output
        response = requests.request(method, url, headers=self.headers, json=json_data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("--- SERVER ERROR RESPONSE ---")
            print(response.text)
            print("---------------------------")
            raise e
        return response.json()

    def get_tables(self):
        # GET /base/{baseId}/table
        return self._make_request("GET", f"/base/{self.base_id}/table")

    def create_table(self, table_name, fields):
        # POST /base/{baseId}/table
        payload = {
            "name": table_name,
            "fields": fields
        }
        return self._make_request("POST", f"/base/{self.base_id}/table", json_data=payload)

    def get_table_fields(self, table_id):
        # GET /table/{tableId}/field
        return self._make_request("GET", f"/table/{table_id}/field")

    def get_table_by_name(self, table_name):
        """Finds a table by its name."""
        tables = self.get_tables()
        if tables:
            for table in tables:
                if table['name'] == table_name:
                    return table
        return None

    def get_all_records(self, table_id):
        # GET /base/{baseId}/table/{tableId}/record
        return self._make_request("GET", f"/table/{table_id}/record")

    def create_records(self, table_id, records):
        # POST /base/{baseId}/table/{tableId}/record
        # print("================") # Commented out for less verbose output
        print(records)
        return self._make_request("POST", f"/table/{table_id}/record", json_data={"records": records})

    def update_records(self, table_id, records):
        # PATCH /table/{tableId}/record/{recordId}
        updated_results = []
        for record in records:
            record_id = record.get("id") # Assuming 'id' is present in the record payload
            if not record_id:
                print(f"Warning: Skipping record update due to missing ID: {record}")
                continue
            
            try:
                response = self._make_request("PATCH", f"/table/{table_id}/record/{record_id}", json_data={"fields": record["fields"]})
                updated_results.append(response)
            except Exception as e:
                print(f"Error updating record {record_id}: {e}")
        return updated_results

    def upload_file(self, table_id, record_id, field_id, file_path):
        # POST /api/table/{tableId}/record/{recordId}/{fieldId}/uploadAttachment
        url = f"{self.base_url}/table/{table_id}/record/{record_id}/{field_id}/uploadAttachment"
        # Remove Content-Type header for multipart/form-data, requests will set it
        headers = {
            "Authorization": f"Bearer {TEABLE_API_TOKEN}"
        }
        
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream' # Default if type cannot be guessed

        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, mime_type)}
            # print(f"--- DEBUG: Making POST request to {url} for file upload ---") # Commented out for less verbose output
            response = requests.post(url, headers=headers, files=files)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print("--- SERVER ERROR RESPONSE ---")
                print(response.text)
                print("---------------------------")
                raise e
            return response.json()


import json
import mimetypes
import os
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from journal_core.interfaces import AbstractJournalClient
from journal_core.models import JournalEntry, MediaAttachment

from .payload_client_config import FILES_COLLECTION_SLUG, JOURNAL_COLLECTION_SLUG


def _journal_entry_to_mutation_dict(entry: JournalEntry, attachment_ids: list[str]) -> dict[str, Any]:
    """Converts a JournalEntry into a dictionary compliant with the GraphQL `mutationJournalInput`."""

    def to_iso_format(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None

    # Handle nested structures
    location_data = {
        "latitude": entry.location_lat,
        "longitude": entry.location_lon,
        "name": entry.location_name,
        "address": entry.location_address,
        "altitude": entry.location_altitude,
    }
    # Filter out None values for a cleaner payload
    location_data = {k: v for k, v in location_data.items() if v is not None}

    weather_data = {
        "temperature": entry.weather_temperature,
        "condition": entry.weather_condition,
        "humidity": entry.weather_humidity,
        "pressure": entry.weather_pressure,
    }
    weather_data = {k: v for k, v in weather_data.items() if v is not None}

    raw_data = None
    if isinstance(entry.source_raw_data, str):
        try:
            raw_data = json.loads(entry.source_raw_data)
        except json.JSONDecodeError:
            raw_data = entry.source_raw_data
    elif entry.source_raw_data is not None:
        raw_data = entry.source_raw_data

    source_data = {
        "appName": entry.source_app_name,
        "originalId": entry.id,
        "importedAt": to_iso_format(entry.source_imported_at),
        "rawData": raw_data,
    }
    source_data = {k: v for k, v in source_data.items() if v is not None}

    # Handle rich text conversion
    rich_text_payload = None
    if entry.rich_text_content:
        # Assuming rich_text_content is already a valid Slate JSON object or can be parsed
        try:
            rich_text_payload = (
                json.loads(entry.rich_text_content)
                if isinstance(entry.rich_text_content, str)
                else entry.rich_text_content
            )
        except json.JSONDecodeError:
            # Fallback for plain text in rich text field
            rich_text_payload = [{"type": "p", "children": [{"text": str(entry.rich_text_content)}]}]

    # Build the final payload, ensuring all fields match the GraphQL mutation input type
    payload = {
        "entryAt": to_iso_format(entry.entry_at),
        "title": entry.title,
        "richTextContent": rich_text_payload,
        "textContent": entry.text_content,
        "attachments": [{"file": att_id} for att_id in attachment_ids],
        "isFavorite": entry.is_favorite,
        "isPinned": entry.is_pinned,
        "notebook": entry.notebook,
        "tags": [{"tag": t} for t in entry.tags if t],
        "moodLabel": entry.mood_label,
        "moodScore": entry.mood_score,
        "activities": [{"activity": a} for a in entry.activities if a],
        "location": location_data if location_data else None,
        "weather": weather_data if weather_data else None,
        "timezone": entry.timezone,
        "deviceName": entry.device_name,
        "stepCount": entry.step_count,
        "source": source_data if source_data else None,
        "createdAt": to_iso_format(entry.created_at),
        "updatedAt": to_iso_format(entry.modified_at),  # Mapping modified_at to updatedAt
    }

    # Clean out any top-level keys that are None or empty lists/dicts for a tidier API call
    return {k: v for k, v in payload.items() if v is not None and v != [] and v != {}}


def _payload_doc_to_journal_entry(doc: dict[str, Any]) -> JournalEntry:
    """Converts a Payload CMS document dictionary (from GraphQL) back to a JournalEntry object."""

    def parse_dt(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            # Handles ISO 8601 format with or without 'Z'
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    source = doc.get("source", {}) or {}
    location = doc.get("location", {}) or {}
    weather = doc.get("weather", {}) or {}

    # A simple conversion from Slate JSON back to plain text for text_content
    text_content = doc.get("textContent")
    if not text_content and doc.get("richTextContent"):
        try:
            # Extract text from Slate's structure
            slate_nodes = doc["richTextContent"]
            text_parts = []
            if slate_nodes:
                for node in slate_nodes:
                    for child in node.get("children", []):
                        if "text" in child:
                            text_parts.append(child["text"])
            text_content = "\n".join(text_parts)
        except (TypeError, KeyError):
            text_content = str(doc.get("richTextContent"))

    entry_at_dt = parse_dt(doc.get("entryAt"))
    if entry_at_dt is None:
        raise ValueError("JournalEntry requires 'entry_at' to be a valid datetime.")

    # In GraphQL schema, `updatedAt` is the modification timestamp.
    modified_at_dt = parse_dt(doc.get("updatedAt"))

    # Parse attachments
    media_attachments: list[MediaAttachment] = []
    if doc.get("attachments"):
        for att_block in doc["attachments"]:
            if not att_block:
                continue
            file_obj = att_block.get("file")
            if file_obj and isinstance(file_obj, dict):
                media_attachments.append(
                    MediaAttachment(
                        id=att_block.get("id"),  # This is the ID of the attachment *block*
                        file_id=file_obj.get("id"),  # This is the ID of the file itself
                        filename=file_obj.get("filename"),
                        url=file_obj.get("url"),
                        mime_type=file_obj.get("mimeType"),
                        filesize=file_obj.get("filesize"),
                    )
                )

    return JournalEntry(
        id=source.get("originalId", ""),
        doc_id=doc.get("id"),
        entry_at=entry_at_dt,
        timezone=doc.get("timezone"),
        created_at=parse_dt(doc.get("createdAt")),
        modified_at=modified_at_dt,
        text_content=text_content,
        rich_text_content=json.dumps(doc.get("richTextContent")) if doc.get("richTextContent") else None,
        title=doc.get("title"),
        tags=[item.get("tag") for item in doc.get("tags", []) if item and item.get("tag")],
        notebook=doc.get("notebook"),
        is_favorite=doc.get("isFavorite", False),
        is_pinned=doc.get("isPinned", False),
        mood_label=doc.get("moodLabel"),
        mood_score=doc.get("moodScore"),
        activities=[item.get("activity") for item in doc.get("activities", []) if item and item.get("activity")],
        location_lat=location.get("latitude"),
        location_lon=location.get("longitude"),
        location_name=location.get("name"),
        location_address=location.get("address"),
        location_altitude=location.get("altitude"),
        weather_temperature=weather.get("temperature"),
        weather_condition=weather.get("condition"),
        weather_humidity=weather.get("humidity"),
        weather_pressure=weather.get("pressure"),
        device_name=doc.get("deviceName"),
        step_count=doc.get("stepCount"),
        media_attachments=media_attachments,
        source_app_name=source.get("appName"),
        source_original_id=source.get("originalId"),
        source_imported_at=parse_dt(source.get("importedAt")),
        source_raw_data=source.get("rawData"),
    )


class PayloadCmsJournalClient(AbstractJournalClient):
    """A client for interacting with a Payload CMS 'journals' collection via GraphQL."""

    def __init__(self, api_url: str, api_key: str, auth_collection_slug: str = "users"):
        if not api_url or not api_key:
            raise ValueError("Payload CMS API URL and API Key must be provided.")

        self.api_url = api_url
        self.graphql_url = urljoin(self.api_url, "api/graphql")
        self.headers = {
            "Authorization": f"{auth_collection_slug} API-Key {api_key}",
        }
        self.collection_slug = JOURNAL_COLLECTION_SLUG
        self.files_slug = FILES_COLLECTION_SLUG

        # Setup GraphQL client
        transport = RequestsHTTPTransport(url=self.graphql_url, headers=self.headers, use_json=True)
        self.graphql_client = Client(transport=transport, fetch_schema_from_transport=False)

    def get_file_details(self, file_id: str) -> dict[str, Any]:
        """Fetches the full document for a specific file."""
        # TODO: To be reimplemented with GraphQL
        raise NotImplementedError

    def download_file_by_url(self, url: str) -> bytes:
        """Downloads the binary content of a file from its full URL."""
        full_url = urljoin(self.api_url, url)
        try:
            response = requests.get(full_url, headers=self.headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file from {full_url}: {e}")
            raise

    def upload_file(self, file_data: bytes, filename: str) -> dict[str, Any]:
        """Uploads a file to the 'files' collection via REST, correctly setting the MIME type."""
        # GraphQL mutations for file uploads are complex. Sticking with REST for this is practical.
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Default MIME type

        files = {"file": (filename, file_data, mime_type)}
        rest_url = urljoin(self.api_url, f"api/{self.files_slug}".lstrip("/"))

        upload_headers = self.headers.copy()
        if "Content-Type" in upload_headers:
            del upload_headers["Content-Type"]

        try:
            response = requests.post(rest_url, headers=upload_headers, files=files)
            response.raise_for_status()
            return response.json()["doc"]
        except requests.exceptions.RequestException as e:
            print(f"Error uploading file to Payload CMS: {e}")
            if e.response:
                print(f"Response body: {e.response.text}")
            raise

    def update_journal_entry_attachments(self, journal_id: str, attachments_payload: list[dict]) -> Any:
        """Updates only the attachments field for a specific journal entry."""
        # TODO: To be reimplemented with GraphQL `updateJournal` mutation
        raise NotImplementedError

    def register_entry(self, entry: JournalEntry) -> dict[str, Any]:
        """Creates a new journal entry in Payload via the `createJournal` GraphQL mutation."""
        # Step 1: Upload any new local files and get their IDs.
        uploaded_file_ids = []
        if entry.media_attachments:
            for att in entry.media_attachments:
                is_new_upload = bool(att.path and att.filename)
                if is_new_upload and att.path and att.filename:
                    if os.path.exists(att.path):
                        print(f"    - Uploading local file: {att.filename}...")
                        with open(att.path, "rb") as f:
                            file_data = f.read()
                        uploaded_file_doc = self.upload_file(file_data, att.filename)
                        uploaded_file_ids.append(uploaded_file_doc["id"])
                    else:
                        print(f"    - WARNING: Path not found for attachment, skipping: {att.path}")
                elif att.file_id:
                    print(f"    - Preserving existing file with ID: {att.file_id}")
                    uploaded_file_ids.append(att.file_id)

        # Step 2: Convert the JournalEntry to a GraphQL mutation-ready dictionary.
        mutation_vars = _journal_entry_to_mutation_dict(entry, uploaded_file_ids)
        if uploaded_file_ids:
            print(f"  -> Prepared {len(uploaded_file_ids)} attachments for entry payload.")

        # Step 3: Define and execute the GraphQL mutation.
        mutation = gql(
            """
            mutation CreateJournal($data: mutationJournalInput!) {
                createJournal(data: $data) {
                    id
                    title
                    entryAt
                }
            }
            """
        )

        try:
            print(f"  -> Sending createJournal mutation for entry: {entry.id}")
            result = self.graphql_client.execute(mutation, variable_values={"data": mutation_vars})
            return result.get("createJournal", {})
        except Exception as e:
            print(f"  ERROR: Failed to register entry {entry.id} via GraphQL. Reason: {e}")
            raise

    def register_entries(self, entries: list[JournalEntry]) -> list[Any]:
        results = []
        for idx, entry in enumerate(entries):
            print(f"Registering entry {idx + 1}/{len(entries)} (ID: {entry.id})...")
            try:
                result = self.register_entry(entry)
                results.append(result)
            except Exception:
                print(f"  Skipping entry {entry.id} due to a registration error.")
        return results

    def update_entry(self, entry: JournalEntry) -> Any:
        raise NotImplementedError("A full `update_entry` with attachment handling is not yet implemented.")

    def update_entries(self, entries: list[JournalEntry]) -> list[Any]:
        return [self.update_entry(entry) for entry in entries]

    def get_existing_entry_ids(self) -> list[str]:
        """Fetches all journal entry 'originalId' values from Payload via GraphQL."""
        query = gql(
            """
            query GetJournals($page: Int) {
                Journals(limit: 100, page: $page) {
                    docs {
                        source {
                            originalId
                        }
                    }
                    hasNextPage
                    nextPage
                }
            }
        """
        )

        all_ids: list[str] = []
        current_page = 1
        has_next_page = True

        print("Fetching existing entry IDs from Payload CMS via GraphQL...")

        while has_next_page:
            try:
                print(f"  - Fetching page {current_page}...")
                result = self.graphql_client.execute(query, variable_values={"page": current_page})

                journals_data = result.get("Journals", {})
                docs = journals_data.get("docs", [])

                for doc in docs:
                    if doc and doc.get("source"):
                        original_id = doc["source"].get("originalId")
                        if original_id:
                            all_ids.append(original_id)

                has_next_page = journals_data.get("hasNextPage", False)
                if has_next_page:
                    current_page = journals_data.get("nextPage", current_page + 1)

            except Exception as e:
                print(f"Error fetching existing entry IDs via GraphQL: {e}")
                break

        print(f"Found {len(all_ids)} existing entry IDs.")
        return all_ids

    def get_existing_entries_with_modified_at(self) -> dict[str, datetime]:
        """Fetches all originalId -> updatedAt mappings from Payload via GraphQL."""
        query = gql(
            """
            query GetJournalsModified($page: Int) {
                Journals(limit: 100, page: $page) {
                    docs {
                        updatedAt
                        source {
                            originalId
                        }
                    }
                    hasNextPage
                    nextPage
                }
            }
        """
        )

        entries_map: dict[str, datetime] = {}
        current_page = 1
        has_next_page = True

        print("Fetching existing entries (ID & modified date) from Payload CMS via GraphQL...")

        while has_next_page:
            try:
                print(f"  - Fetching page {current_page}...")
                result = self.graphql_client.execute(query, variable_values={"page": current_page})

                journals_data = result.get("Journals", {})
                docs = journals_data.get("docs", [])

                for doc in docs:
                    if not doc or not doc.get("source"):
                        continue
                    original_id = doc["source"].get("originalId")
                    modified_str = doc.get("updatedAt")
                    if original_id and modified_str:
                        try:
                            entries_map[original_id] = datetime.fromisoformat(modified_str.replace("Z", "+00:00"))
                        except (ValueError, TypeError):
                            print(f"Warning: Could not parse 'updatedAt' for entry {original_id}: {modified_str}")

                has_next_page = journals_data.get("hasNextPage", False)
                if has_next_page:
                    current_page = journals_data.get("nextPage", current_page + 1)

            except Exception as e:
                print(f"Error fetching entries with modified date via GraphQL: {e}")
                break

        print(f"Found {len(entries_map)} existing entries.")
        return entries_map

    def download_journal_entries(self) -> list[JournalEntry]:
        """Downloads all journal entries from Payload and converts them to JournalEntry objects."""
        query = gql(
            """
            query DownloadJournals($page: Int) {
                Journals(limit: 100, page: $page) {
                    docs {
                        id
                        entryAt
                        title
                        richTextContent
                        textContent
                        isFavorite
                        isPinned
                        notebook
                        tags { tag }
                        moodLabel
                        moodScore
                        activities { activity }
                        location { latitude longitude name address altitude }
                        weather { temperature humidity pressure condition }
                        timezone
                        deviceName
                        stepCount
                        source { appName originalId importedAt rawData }
                        attachments {
                            id
                            file {
                                id
                                filename
                                url
                                mimeType
                                filesize
                            }
                        }
                        createdAt
                        updatedAt
                    }
                    hasNextPage
                    nextPage
                }
            }
        """
        )

        all_entries: list[JournalEntry] = []
        current_page = 1
        has_next_page = True

        print("Downloading and parsing journal entries from Payload CMS via GraphQL...")

        while has_next_page:
            try:
                print(f"  - Fetching page {current_page}...")
                result = self.graphql_client.execute(query, variable_values={"page": current_page})
                journals_data = result.get("Journals", {})
                docs = journals_data.get("docs", [])

                for doc in docs:
                    if not doc:
                        continue
                    try:
                        all_entries.append(_payload_doc_to_journal_entry(doc))
                    except Exception as e:
                        doc_id = doc.get("id", "N/A")
                        original_id = doc.get("source", {}).get("originalId", "N/A")
                        print(
                            f"Warning: Failed to parse document {doc_id} "
                            f"(original ID: {original_id}) from Payload. Error: {e}"
                        )

                has_next_page = journals_data.get("hasNextPage", False)
                if has_next_page:
                    current_page = journals_data.get("nextPage", current_page + 1)

            except Exception as e:
                print(f"Error downloading journal entries via GraphQL: {e}")
                break

        print(f"Successfully downloaded and parsed {len(all_entries)} journal entries.")
        return all_entries

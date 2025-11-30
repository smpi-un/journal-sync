import json
import os
from datetime import datetime
from typing import Any

from journal_core.interfaces import AbstractJournalDataSource
from journal_core.models import JournalEntry, MediaAttachment


class JourneyCloudDataSource(AbstractJournalDataSource):
    """
    A data source for JourneyCloud data, capable of reading from a ZIP archive
    containing exported journal entries.
    """

    def __init__(self, data_path: str):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data path not found: {data_path}")
        self.data_path = data_path

    def _parse_journey_cloud_entry(self, raw_entry: dict[str, Any], entry_dir_path: str) -> JournalEntry:
        """
        Parses a raw JourneyCloud entry dictionary into the new, comprehensive JournalEntry object.
        """

        # Helper for safe datetime parsing
        def parse_dt(dt_str: str | None) -> datetime | None:
            if dt_str:
                try:
                    # JourneyCloud often uses 'Z' for UTC, which fromisoformat handles with '+00:00'
                    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return None

        # --- 基本識別情報 ---
        entry_id = raw_entry.get("id", "")  # Use 'id' from JourneyCloud sample

        # --- 時間情報 ---
        entry_at = (
            parse_dt(raw_entry.get("dateOfJournal")) or parse_dt(raw_entry.get("createdAt")) or datetime.now()
        )  # Fallback to now if no date
        timezone = raw_entry.get("timezone")
        created_at = parse_dt(raw_entry.get("dateOfJournal"))  # Assuming dateOfJournal is creation time
        modified_at = parse_dt(raw_entry.get("updatedAt"))

        # --- コンテンツ ---
        text_content = None
        rich_text_content = None
        if raw_entry.get("type") == "markdown":
            rich_text_content = raw_entry.get("text")
        else:
            text_content = raw_entry.get("text")
        title = None  # JourneyCloud sample does not have a direct title field

        # --- 整理・分類 ---
        tags = []
        if raw_entry.get("tags") and isinstance(raw_entry["tags"], list):
            tags = [tag.strip() for tag in raw_entry["tags"] if tag.strip()]
        notebook = None  # JourneyCloud sample does not have a 'notebook' field
        is_favorite = bool(raw_entry.get("favourite", False))
        is_pinned = False  # JourneyCloud sample does not have a 'pinned' field

        # --- コンテキスト情報 (気分・活動) ---
        mood_label = None  # JourneyCloud sample does not have a 'mood' field
        mood_score = raw_entry.get("sentiment")
        activities = []
        if raw_entry.get("activity") and raw_entry["activity"] != 0:
            activities = [str(raw_entry["activity"])]  # Convert activity number to string for list

        # --- 位置情報 (フラット化) ---
        location_lat = (
            raw_entry.get("location", {}).get("latitude") if isinstance(raw_entry.get("location"), dict) else None
        )
        location_lon = (
            raw_entry.get("location", {}).get("longitude") if isinstance(raw_entry.get("location"), dict) else None
        )
        location_name = (
            raw_entry.get("location", {}).get("name") if isinstance(raw_entry.get("location"), dict) else None
        )
        location_address = raw_entry.get("address")
        location_altitude = (
            raw_entry.get("location", {}).get("altitude") if isinstance(raw_entry.get("location"), dict) else None
        )

        # --- 天気情報 (フラット化) ---
        weather_temperature = (
            raw_entry.get("weather", {}).get("temperature") if isinstance(raw_entry.get("weather"), dict) else None
        )
        weather_condition = (
            raw_entry.get("weather", {}).get("condition") if isinstance(raw_entry.get("weather"), dict) else None
        )
        weather_humidity = (
            raw_entry.get("weather", {}).get("humidity") if isinstance(raw_entry.get("weather"), dict) else None
        )
        weather_pressure = (
            raw_entry.get("weather", {}).get("pressure") if isinstance(raw_entry.get("weather"), dict) else None
        )

        # --- デバイス・その他メタデータ ---
        device_name = None  # JourneyCloud sample does not have a 'device' field
        step_count = None  # JourneyCloud sample does not have a 'stepCount' field

        # --- メディア情報 (準フラット化) ---
        media_attachments: list[MediaAttachment] = []
        attachments_from_json = raw_entry.get("attachments", [])
        if isinstance(attachments_from_json, list):
            for attachment_filename in attachments_from_json:
                # Construct the full path to the attachment
                full_attachment_path = os.path.join(entry_dir_path, attachment_filename)
                if os.path.exists(full_attachment_path):
                    media_attachments.append(
                        MediaAttachment(
                            id=attachment_filename,  # Placeholder ID
                            file_id=attachment_filename,  # Placeholder file_id
                            path=full_attachment_path,
                            filename=attachment_filename,
                        )
                    )
                else:
                    print(f"Warning: Attachment file not found: {full_attachment_path}")

        # --- 出所情報 (フラット化) ---
        source_app_name = "JourneyCloud"
        source_original_id = entry_id
        source_imported_at = datetime.now()
        source_raw_data = raw_entry  # Store the original raw data for debugging/completeness

        return JournalEntry(
            id=entry_id,
            entry_at=entry_at,
            timezone=timezone,
            created_at=created_at,
            modified_at=modified_at,
            text_content=text_content,
            rich_text_content=rich_text_content,
            title=title,
            tags=tags,
            notebook=notebook,
            is_favorite=is_favorite,
            is_pinned=is_pinned,
            mood_label=mood_label,
            mood_score=mood_score,
            activities=activities,
            location_lat=location_lat,
            location_lon=location_lon,
            location_name=location_name,
            location_address=location_address,
            location_altitude=location_altitude,
            weather_temperature=weather_temperature,
            weather_condition=weather_condition,
            weather_humidity=weather_humidity,
            weather_pressure=weather_pressure,
            device_name=device_name,
            step_count=step_count,
            media_attachments=media_attachments,
            source_app_name=source_app_name,
            source_original_id=source_original_id,
            source_imported_at=source_imported_at,
            source_raw_data=source_raw_data,
        )

    def _load_journal_entry_from_json(self, entry_dir_path: str, entry_id: str) -> dict[str, Any] | None:
        """
        Loads a journal entry from its JSON file within its directory.
        """
        json_file_path = os.path.join(entry_dir_path, f"{entry_id}.json")
        if not os.path.exists(json_file_path):
            print(f"Warning: JSON file not found for entry {entry_id} at {json_file_path}")
            return None
        try:
            with open(json_file_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {json_file_path}")
            return None

    def fetch_entries(self, **kwargs) -> list[JournalEntry]:
        """
        Fetches JourneyCloud entries by reading from a directory structure.
        """
        all_journal_entries: list[JournalEntry] = []

        entry_dirs = []
        for d in os.listdir(self.data_path):
            full_path = os.path.join(self.data_path, d)
            if os.path.isdir(full_path):
                entry_dirs.append(d)

        print(f"Found {len(entry_dirs)} potential journal entry directories in {self.data_path}.")

        for entry_dir_name in entry_dirs:
            entry_dir_path = os.path.join(self.data_path, entry_dir_name)
            raw_data = self._load_journal_entry_from_json(entry_dir_path, entry_dir_name)
            if raw_data:
                try:
                    journal_entry = self._parse_journey_cloud_entry(raw_data, entry_dir_path)
                    all_journal_entries.append(journal_entry)
                except Exception as e:
                    print(f"Error parsing entry {entry_dir_name}: {e}")

        return all_journal_entries

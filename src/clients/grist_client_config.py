
import os

# --- Grist API Configuration ---
GRIST_API_URL = None
GRIST_API_KEY = None
GRIST_DOC_ID = None

# --- Table and Field Naming ---
JOURNAL_TABLE_NAME = "JournalEntries"
ATTACHMENT_TABLE_NAME = "Attachments" # Not directly used for Grist attachments in this implementation

# This dictionary maps the JournalEntry model fields to the Grist table field names.
GRIST_FIELD_NAMES = {
    "id": "JournalId", # Reverted to "Id"
    "entry_at": "EntryAt",
    "timezone": "Timezone",
    "created_at": "CreatedAt",
    "modified_at": "ModifiedAt",
    "text_content": "TextContent",
    "rich_text_content": "RichTextContent",
    "title": "Title",
    "tags": "Tags",
    "notebook": "Notebook",
    "is_favorite": "IsFavorite",
    "is_pinned": "IsPinned",
    "mood_label": "Mood",
    "mood_score": "MoodScore",
    "activities": "Activities",
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
    "media_attachments": "MediaAttachments", # Storing as JSON string or URLs
    "source_app_name": "SourceAppName",
    "source_original_id": "SourceOriginalId",
    "source_imported_at": "SourceImportedAt",
    "source_raw_data": "SourceRawData",
}

# Define the columns for the "JournalEntries" table in Grist
GRIST_JOURNAL_TABLE_COLUMNS = [
    {"id": GRIST_FIELD_NAMES["id"], "fields": {"label": GRIST_FIELD_NAMES["id"]}}, # "Text" # Primary key in Grist is usually 'id' or a custom column
    {"id": GRIST_FIELD_NAMES["entry_at"], "fields": {"label": GRIST_FIELD_NAMES["entry_at"]}}, # "type": "DateTime"},
    {"id": GRIST_FIELD_NAMES["timezone"], "fields": {"label": GRIST_FIELD_NAMES["timezone"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["created_at"], "fields": {"label": GRIST_FIELD_NAMES["created_at"]}}, # "type": "DateTime"},
    {"id": GRIST_FIELD_NAMES["modified_at"], "fields": {"label": GRIST_FIELD_NAMES["modified_at"]}}, # "type": "DateTime"},
    {"id": GRIST_FIELD_NAMES["text_content"], "fields": {"label": GRIST_FIELD_NAMES["text_content"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["rich_text_content"], "fields": {"label": GRIST_FIELD_NAMES["rich_text_content"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["title"], "fields": {"label": GRIST_FIELD_NAMES["title"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["tags"], "fields": {"label": GRIST_FIELD_NAMES["tags"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["notebook"], "fields": {"label": GRIST_FIELD_NAMES["notebook"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["is_favorite"], "fields": {"label": GRIST_FIELD_NAMES["is_favorite"]}}, # "type": "Bool"},
    {"id": GRIST_FIELD_NAMES["is_pinned"], "fields": {"label": GRIST_FIELD_NAMES["is_pinned"]}}, # "type": "Bool"},
    {"id": GRIST_FIELD_NAMES["mood_label"], "fields": {"label": GRIST_FIELD_NAMES["mood_label"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["mood_score"], "fields": {"label": GRIST_FIELD_NAMES["mood_score"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["activities"], "fields": {"label": GRIST_FIELD_NAMES["activities"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["location_lat"], "fields": {"label": GRIST_FIELD_NAMES["location_lat"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["location_lon"], "fields": {"label": GRIST_FIELD_NAMES["location_lon"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["location_name"], "fields": {"label": GRIST_FIELD_NAMES["location_name"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["location_address"], "fields": {"label": GRIST_FIELD_NAMES["location_address"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["location_altitude"], "fields": {"label": GRIST_FIELD_NAMES["location_altitude"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["weather_temperature"], "fields": {"label": GRIST_FIELD_NAMES["weather_temperature"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["weather_condition"], "fields": {"label": GRIST_FIELD_NAMES["weather_condition"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["weather_humidity"], "fields": {"label": GRIST_FIELD_NAMES["weather_humidity"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["weather_pressure"], "fields": {"label": GRIST_FIELD_NAMES["weather_pressure"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["device_name"], "fields": {"label": GRIST_FIELD_NAMES["device_name"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["step_count"], "fields": {"label": GRIST_FIELD_NAMES["step_count"]}}, # "type": "Numeric"},
    {"id": GRIST_FIELD_NAMES["media_attachments"], "fields": {"label": GRIST_FIELD_NAMES["media_attachments"]}}, # "type": "Text"}, # Storing as JSON string or URLs
    {"id": GRIST_FIELD_NAMES["source_app_name"], "fields": {"label": GRIST_FIELD_NAMES["source_app_name"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["source_original_id"], "fields": {"label": GRIST_FIELD_NAMES["source_original_id"]}}, # "type": "Text"},
    {"id": GRIST_FIELD_NAMES["source_imported_at"], "fields": {"label": GRIST_FIELD_NAMES["source_imported_at"]}}, # "type": "DateTime"},
    {"id": GRIST_FIELD_NAMES["source_raw_data"], "fields": {"label": GRIST_FIELD_NAMES["source_raw_data"]}}, # "type": "Text"},
]

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Teable API Configuration ---
TEABLE_API_URL = os.getenv("TEABLE_API_URL", "https://app.teable.ai/api")
TEABLE_API_TOKEN = os.getenv("TEABLE_API_TOKEN")
TEABLE_BASE_ID = os.getenv("TEABLE_BASE_ID")

# Validate that required environment variables are set
if not TEABLE_API_TOKEN:
    raise ValueError("TEABLE_API_TOKEN is not set in the environment or .env file.")
if not TEABLE_BASE_ID:
    raise ValueError("TEABLE_BASE_ID is not set in the environment or .env file.")

# --- Table and Field Naming ---
JOURNAL_TABLE_NAME = "JourneyEntries"
ATTACHMENT_TABLE_NAME = "Attachments"

# This dictionary maps the JournalEntry model fields to the Teable table field names.
# This provides a single point of configuration if the field names in Teable change.
TEABLE_FIELD_NAMES = {
    "id": "Id",
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
    "media_attachments": "Attachments",
    "source_app_name": "SourceAppName",
    "source_original_id": "SourceOriginalId",
    "source_imported_at": "SourceImportedAt",
    "source_raw_data": "SourceRawData",
}

# --- Table Schema Definitions ---

# Define the columns for the "JournalEntries" table
# This is used when the client verifies or creates the table.
JOURNAL_TABLE_COLUMNS = [
    {"name": TEABLE_FIELD_NAMES["id"], "type": "singleLineText", "isPrimary": True},
    {"name": TEABLE_FIELD_NAMES["entry_at"], "type": "date", "options": {"dateFormat": "YYYY-MM-DD HH:mm:ss"}},
    {"name": TEABLE_FIELD_NAMES["timezone"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["created_at"], "type": "date", "options": {"dateFormat": "YYYY-MM-DD HH:mm:ss"}},
    {"name": TEABLE_FIELD_NAMES["modified_at"], "type": "date", "options": {"dateFormat": "YYYY-MM-DD HH:mm:ss"}},
    {"name": TEABLE_FIELD_NAMES["text_content"], "type": "longText"},
    {"name": TEABLE_FIELD_NAMES["rich_text_content"], "type": "longText"},
    {"name": TEABLE_FIELD_NAMES["title"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["tags"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["notebook"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["is_favorite"], "type": "checkbox"},
    {"name": TEABLE_FIELD_NAMES["is_pinned"], "type": "checkbox"},
    {"name": TEABLE_FIELD_NAMES["mood_label"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["mood_score"], "type": "number", "options": {"format": "decimal", "precision": 1}},
    {"name": TEABLE_FIELD_NAMES["activities"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["location_lat"], "type": "number", "options": {"format": "decimal", "precision": 8}},
    {"name": TEABLE_FIELD_NAMES["location_lon"], "type": "number", "options": {"format": "decimal", "precision": 8}},
    {"name": TEABLE_FIELD_NAMES["location_name"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["location_address"], "type": "longText"},
    {"name": TEABLE_FIELD_NAMES["location_altitude"], "type": "number", "options": {"format": "decimal", "precision": 2}},
    {"name": TEABLE_FIELD_NAMES["weather_temperature"], "type": "number", "options": {"format": "decimal", "precision": 1}},
    {"name": TEABLE_FIELD_NAMES["weather_condition"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["weather_humidity"], "type": "number", "options": {"format": "decimal", "precision": 2}},
    {"name": TEABLE_FIELD_NAMES["weather_pressure"], "type": "number", "options": {"format": "decimal", "precision": 2}},
    {"name": TEABLE_FIELD_NAMES["device_name"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["step_count"], "type": "number", "options": {"format": "integer"}},
    {"name": TEABLE_FIELD_NAMES["media_attachments"], "type": "attachment"},
    {"name": TEABLE_FIELD_NAMES["source_app_name"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["source_original_id"], "type": "singleLineText"},
    {"name": TEABLE_FIELD_NAMES["source_imported_at"], "type": "date", "options": {"dateFormat": "YYYY-MM-DD HH:mm:ss"}},
    {"name": TEABLE_FIELD_NAMES["source_raw_data"], "type": "longText"},
]

# Define the columns for the "Attachments" table
ATTACHMENT_TABLE_COLUMNS = [
    {"name": "Id", "type": "singleLineText", "isPrimary": True},
    {"name": "Filename", "type": "singleLineText"},
    {"name": "URL", "type": "singleLineText"},
    {"name": "MIMEType", "type": "singleLineText"},
    {"name": "Size", "type": "number", "options": {"format": "integer"}},
]

# Define the link field to connect Attachments back to JournalEntries
ATTACHMENT_LINK_FIELD_NAME = "JournalEntry"
ATTACHMENT_LINK_FIELD_DEFINITION = {
    "name": ATTACHMENT_LINK_FIELD_NAME,
    "type": "link",
    "options": {
        "foreignTableId": "", # This will be filled in dynamically
        "relationship": "many-to-one",
        "foreignTableName": JOURNAL_TABLE_NAME
    }
}

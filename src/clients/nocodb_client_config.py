import os

# NocoDB connection details
NOCODB_URL = "http://localhost:8080" # Default value, will be overridden by env var if set
NOCODB_API_TOKEN = None
NOCODB_PROJECT_ID = None

NOCODB_JOURNAL_TABLE_NAME = "JournalEntries"
NOCODB_ATTACHMENT_TABLE_NAME = "Attachments"
NOCODB_ATTACHMENT_LINK_FIELD = (
    "JournalEntry"  # Field in Attachments table linking to JournalEntries
)
NOCODB_ATTACHMENT_ORDER_FIELD = "Order"  # Field in Attachments table for order
NOCODB_JOURNAL_ATTACHMENT_FIELD = (
    "Attachments"  # Attachment column in JournalEntries table
)

# Define column structures for automatic table creation
NOCODB_JOURNAL_TABLE_COLUMNS = [
    {"title": "EntryAt", "column_name": "EntryAt", "data_type": "varchar"},
    {"title": "Id", "column_name": "Id", "data_type": "varchar", "pk": True},
    {"title": "Timezone", "column_name": "Timezone", "data_type": "varchar"},
    {
        "title": "JournalCreatedAt",
        "column_name": "JournalCreatedAt",
        "data_type": "varchar",
    },
    {
        "title": "JournalModifiedAt",
        "column_name": "JournalModifiedAt",
        "data_type": "varchar",
    },
    {"title": "TextContent", "column_name": "TextContent", "data_type": "longtext"},
    {
        "title": "RichTextContent",
        "column_name": "RichTextContent",
        "data_type": "longtext",
    },
    {"title": "Title", "column_name": "Title", "data_type": "varchar"},
    {"title": "Tags", "column_name": "Tags", "data_type": "varchar"},
    {"title": "Notebook", "column_name": "Notebook", "data_type": "varchar"},
    {"title": "IsFavorite", "column_name": "IsFavorite", "data_type": "tinyint"},
    {"title": "IsPinned", "column_name": "IsPinned", "data_type": "tinyint"},
    {"title": "MoodLabel", "column_name": "MoodLabel", "data_type": "varchar"},
    {"title": "MoodScore", "column_name": "MoodScore", "data_type": "decimal"},
    {"title": "Activities", "column_name": "Activities", "data_type": "varchar"},
    {"title": "LocationLat", "column_name": "LocationLat", "data_type": "decimal"},
    {"title": "LocationLon", "column_name": "LocationLon", "data_type": "decimal"},
    {"title": "LocationName", "column_name": "LocationName", "data_type": "varchar"},
    {
        "title": "LocationAddress",
        "column_name": "LocationAddress",
        "data_type": "longtext",
    },
    {
        "title": "LocationAltitude",
        "column_name": "LocationAltitude",
        "data_type": "decimal",
    },
    {
        "title": "WeatherTemperature",
        "column_name": "WeatherTemperature",
        "data_type": "decimal",
    },
    {
        "title": "WeatherCondition",
        "column_name": "WeatherCondition",
        "data_type": "varchar",
    },
    {
        "title": "WeatherHumidity",
        "column_name": "WeatherHumidity",
        "data_type": "decimal",
    },
    {
        "title": "WeatherPressure",
        "column_name": "WeatherPressure",
        "data_type": "decimal",
    },
    {"title": "DeviceName", "column_name": "DeviceName", "data_type": "varchar"},
    {"title": "StepCount", "column_name": "StepCount", "data_type": "int"},
    {
        "title": "MediaAttachmentsJson",
        "column_name": "MediaAttachmentsJson",
        "data_type": "longtext",
    },
    {"title": "SourceAppName", "column_name": "SourceAppName", "data_type": "varchar"},
    {
        "title": "SourceOriginalId",
        "column_name": "SourceOriginalId",
        "data_type": "varchar",
    },
    {
        "title": "SourceImportedAt",
        "column_name": "SourceImportedAt",
        "data_type": "varchar",
    },
    {"title": "SourceRawData", "column_name": "SourceRawData", "data_type": "longtext"},
]

NOCODB_ATTACHMENT_TABLE_COLUMNS = [
    {
        "title": "Id",
        "column_name": "Id",
        "data_type": "int",
        "pk": True,
        "auto_increment": True,
    },
    {"title": "FileName", "column_name": "FileName", "data_type": "varchar"},
    {"title": "FilePath", "column_name": "FilePath", "data_type": "varchar"},
    {
        "title": NOCODB_ATTACHMENT_ORDER_FIELD,
        "column_name": NOCODB_ATTACHMENT_ORDER_FIELD,
        "data_type": "int",
    },
]

# Link field definition for Attachments to JournalEntries
NOCODB_ATTACHMENT_LINK_FIELD_DEFINITION = {
    "title": NOCODB_ATTACHMENT_LINK_FIELD,
    "column_name": NOCODB_ATTACHMENT_LINK_FIELD,
    "data_type": "link",
    "type": "manyToOne",  # Assuming many attachments to one journal entry
    "fk_table_name": NOCODB_JOURNAL_TABLE_NAME,
    "fk_column_name": "Id",  # Link to the primary key of the JournalEntries table
}

# Field names mapping for NocoDB
NOCODB_FIELD_NAMES = {
    "entry_at": "EntryAt",
    "id": "Id",
    "timezone": "Timezone",
    "created_at": "JournalCreatedAt",
    "modified_at": "JournalModifiedAt",
    "text_content": "TextContent",
    "rich_text_content": "RichTextContent",
    "title": "Title",
    "tags": "Tags",
    "notebook": "Notebook",
    "is_favorite": "IsFavorite",
    "is_pinned": "IsPinned",
    "mood_label": "MoodLabel",
    "mood_score": "MoodScore",
    "activities": "Activities",
    "location_lat": "LocationLat",
    "location_lon": "LocationLon",
    "location_name": "LocationName",
    "location_address": "LocationAddress",
    "location_altitude": "LocationAltitude",
    "weather_temperature": "WeatherTemperature",
    "weather_condition": "WeatherCondition",
    "weather_humidity": "WeatherHumidity",
    "weather_pressure": "WeatherPressure",
    "device_name": "DeviceName",
    "step_count": "StepCount",
    "media_attachments": "MediaAttachmentsJson",
    "source_app_name": "SourceAppName",
    "source_original_id": "SourceOriginalId",
    "source_imported_at": "SourceImportedAt",
    "source_raw_data": "SourceRawData",
}

# Teable connection details
TEABLE_API_TOKEN = "teable_accdNvfnVYLi5spZPWP_Ev+j1y2wxuQZg2pBxftyeX+H0bVep+FZgpPReWAM/4o="
TEABLE_API_URL = "http://localhost:3000/api"
TEABLE_BASE_ID = "bse6U9m5sgpVUCjA45t"

# NocoDB connection details
# NOCODB_URL = "http://localhost:8080"
# API_TOKEN = "1KCGgmxDevRbHSY-W03weuBJaKBnT4m_eQc8xUBi"
# PROJECT_ID = "pjuurfy8ii46bvj"
JOURNAL_TABLE_NAME = "JourneyEntries"
ATTACHMENT_TABLE_NAME = "Attachments"
ATTACHMENT_LINK_FIELD = "JournalEntry" # Field in Attachments table linking to JourneyEntries
ATTACHMENT_ORDER_FIELD = "Order" # Field in Attachments table for order
JOURNAL_ATTACHMENT_FIELD = "Attachments" # Attachment column in JourneyEntries table


# Define column structures for automatic table creation
JOURNAL_TABLE_COLUMNS = [
    {"name": "EntryAt", "type": "singleLineText"},
    {"name": "Id", "type": "singleLineText", "isPrimary": True},
    {"name": "Timezone", "type": "singleLineText"},
    {"name": "CreatedAt", "type": "singleLineText"},
    {"name": "ModifiedAt", "type": "singleLineText"},
    {"name": "TextContent", "type": "longText"},
    {"name": "RichTextContent", "type": "longText"},
    {"name": "Title", "type": "singleLineText"},
    {"name": "Tags", "type": "singleLineText"},
    {"name": "Notebook", "type": "singleLineText"},
    {"name": "IsFavorite", "type": "checkbox"},
    {"name": "IsPinned", "type": "checkbox"},
    {"name": "MoodLabel", "type": "singleLineText"},
    {"name": "MoodScore", "type": "number"},
    {"name": "Activities", "type": "singleLineText"},
    {"name": "LocationLat", "type": "number"},
    {"name": "LocationLon", "type": "number"},
    {"name": "LocationName", "type": "singleLineText"},
    {"name": "LocationAddress", "type": "longText"},
    {"name": "LocationAltitude", "type": "number"},
    {"name": "WeatherTemperature", "type": "number"},
    {"name": "WeatherCondition", "type": "singleLineText"},
    {"name": "WeatherHumidity", "type": "number"},
    {"name": "WeatherPressure", "type": "number"},
    {"name": "DeviceName", "type": "singleLineText"},
    {"name": "StepCount", "type": "number"},
    {"name": JOURNAL_ATTACHMENT_FIELD, "type": "attachment"},
    {"name": "SourceAppName", "type": "singleLineText"},
    {"name": "SourceOriginalId", "type": "singleLineText"},
    {"name": "SourceImportedAt", "type": "singleLineText"},
    {"name": "SourceRawData", "type": "longText"}
]

ATTACHMENT_TABLE_COLUMNS = [
    {"name": "Id", "type": "autoNumber", "isPrimary": True},
    {"name": "FileName", "type": "singleLineText"},
    {"name": "FilePath", "type": "singleLineText"},
    {"name": ATTACHMENT_ORDER_FIELD, "type": "number"}
]

# Link field definition for Attachments to JournalEntries
ATTACHMENT_LINK_FIELD_DEFINITION = {
    "name": ATTACHMENT_LINK_FIELD,
    "type": "link",
    "options": {
        "foreignTableId": None,  # This will be filled dynamically
        "relationship": "oneMany",
        "lookup": False
    }
}

# Field names for Teable
TEABLE_FIELD_NAMES = {
    "entry_at": "EntryAt",
    "id": "Id",
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
    "media_attachments": JOURNAL_ATTACHMENT_FIELD,
    "source_app_name": "SourceAppName",
    "source_original_id": "SourceOriginalId",
    "source_imported_at": "SourceImportedAt",
    "source_raw_data": "SourceRawData"
}
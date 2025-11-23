# --- Teable API Configuration ---
TEABLE_API_URL = "https://app.teable.ai"  # Default value, will be overridden by env var if set
TEABLE_API_TOKEN = None
TEABLE_BASE_ID = None

# --- Table and Field Naming ---
JOURNAL_TABLE_NAME = "JourneyEntries"
ATTACHMENT_TABLE_NAME = "Attachments"

# --- Table Schema Definitions ---

# Define the columns for the "JournalEntries" table
# This is used when the client verifies or creates the table.
JOURNAL_TABLE_COLUMNS = [
    {"name": "Id", "type": "singleLineText"},
    {"name": "EntryAt", "type": "singleLineText"},  # Changed from date to text
    {"name": "CalendarEntryAt", "type": "date"},  # Added for calendar view
    {"name": "Timezone", "type": "singleLineText"},
    {"name": "CreatedAt", "type": "singleLineText"},  # Changed from date to text
    {"name": "ModifiedAt", "type": "singleLineText"},  # Changed from date to text
    {"name": "TextContent", "type": "longText"},
    {"name": "RichTextContent", "type": "longText"},
    {"name": "Title", "type": "singleLineText"},
    {"name": "Tags", "type": "singleLineText"},
    {"name": "Notebook", "type": "singleLineText"},
    {"name": "IsFavorite", "type": "checkbox"},
    {"name": "IsPinned", "type": "checkbox"},
    {"name": "Mood", "type": "singleLineText"},
    {"name": "MoodScore", "type": "number"},
    {"name": "Activities", "type": "singleLineText"},
    {"name": "LocationLat", "type": "number"},
    {"name": "LocationLon", "type": "number"},
    {"name": "LocationName", "type": "singleLineText"},
    {"name": "LocationAddress", "type": "longText"},
    {"name": "LocationAltitude", "type": "number"},
    {"name": "WeatherTemp", "type": "number"},
    {"name": "WeatherCondition", "type": "singleLineText"},
    {"name": "WeatherHumidity", "type": "number"},
    {"name": "WeatherPressure", "type": "number"},
    {"name": "DeviceName", "type": "singleLineText"},
    {"name": "StepCount", "type": "number"},
    {"name": "Attachments", "type": "attachment"},
    {"name": "SourceAppName", "type": "singleLineText"},
    {"name": "SourceOriginalId", "type": "singleLineText"},
    {"name": "SourceImportedAt", "type": "singleLineText"},  # Changed from date to text
    {"name": "SourceRawData", "type": "longText"},
]

# Define the columns for the "Attachments" table
ATTACHMENT_TABLE_COLUMNS = [
    {"name": "Id", "type": "singleLineText"},
    {"name": "Filename", "type": "singleLineText"},
    {"name": "URL", "type": "singleLineText"},
    {"name": "MIMEType", "type": "singleLineText"},
    {"name": "Size", "type": "number"},
]

# Define the link field to connect Attachments back to JournalEntries
ATTACHMENT_LINK_FIELD_NAME = "JournalEntry"
ATTACHMENT_LINK_FIELD_DEFINITION = {
    "name": ATTACHMENT_LINK_FIELD_NAME,
    "type": "link",
    "options": {
        "foreignTableId": "",  # This will be filled in dynamically
        "relationship": "many-to-one",
        "foreignTableName": JOURNAL_TABLE_NAME,
    },
}

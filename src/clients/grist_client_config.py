import os

# --- Grist API Configuration ---
GRIST_API_URL = None
GRIST_API_KEY = None
GRIST_DOC_ID = None

# --- Table and Field Naming ---
JOURNAL_TABLE_NAME = "JournalEntries"
ATTACHMENT_TABLE_NAME = "Attachments"

# Define the columns for the "JournalEntries" table in Grist.
# The 'id' of each column should correspond to the PascalCase version of the JournalEntry fields.
GRIST_JOURNAL_TABLE_COLUMNS = [
    {"id": "JournalId", "fields": {"label": "JournalId"}},
    {"id": "EntryAt", "fields": {"label": "EntryAt", "type": "Text"}},
    {"id": "CalendarEntryAt", "fields": {"label": "CalendarEntryAt", "type": "DateTime"}},
    {"id": "Timezone", "fields": {"label": "Timezone"}},
    {"id": "CreatedAt", "fields": {"label": "CreatedAt", "type": "Text"}},
    {"id": "ModifiedAt", "fields": {"label": "ModifiedAt", "type": "Text"}},
    {"id": "TextContent", "fields": {"label": "TextContent"}},
    {"id": "RichTextContent", "fields": {"label": "RichTextContent"}},
    {"id": "Title", "fields": {"label": "Title"}},
    {"id": "Tags", "fields": {"label": "Tags"}},
    {"id": "Notebook", "fields": {"label": "Notebook"}},
    {"id": "IsFavorite", "fields": {"label": "IsFavorite"}},
    {"id": "IsPinned", "fields": {"label": "IsPinned"}},
    {"id": "Mood", "fields": {"label": "Mood"}},
    {"id": "MoodScore", "fields": {"label": "MoodScore"}},
    {"id": "Activities", "fields": {"label": "Activities"}},
    {"id": "LocationLat", "fields": {"label": "LocationLat"}},
    {"id": "LocationLon", "fields": {"label": "LocationLon"}},
    {"id": "LocationName", "fields": {"label": "LocationName"}},
    {"id": "LocationAddress", "fields": {"label": "LocationAddress"}},
    {"id": "LocationAltitude", "fields": {"label": "LocationAltitude"}},
    {"id": "WeatherTemp", "fields": {"label": "WeatherTemp"}},
    {"id": "WeatherCondition", "fields": {"label": "WeatherCondition"}},
    {"id": "WeatherHumidity", "fields": {"label": "WeatherHumidity"}},
    {"id": "WeatherPressure", "fields": {"label": "WeatherPressure"}},
    {"id": "DeviceName", "fields": {"label": "DeviceName"}},
    {"id": "StepCount", "fields": {"label": "StepCount"}},
    {"id": "MediaAttachments", "fields": {"label": "MediaAttachments"}},
    {"id": "SourceAppName", "fields": {"label": "SourceAppName"}},
    {"id": "SourceOriginalId", "fields": {"label": "SourceOriginalId"}},
    {"id": "SourceImportedAt", "fields": {"label": "SourceImportedAt", "type": "Text"}},
    {"id": "SourceRawData", "fields": {"label": "SourceRawData"}},
]
# NocoDB connection details
NOCODB_URL = "http://localhost:8080"
NOCODB_API_TOKEN = None
NOCODB_PROJECT_ID = None

NOCODB_JOURNAL_TABLE_NAME = "JournalEntries"

# NocoDB v3 API Column Definitions for Table Creation
# Uses 'title' and 'type' as per the v3 documentation.
NOCODB_JOURNAL_TABLE_COLUMNS = [
    {"title": "JournalId", "type": "SingleLineText"},
    {"title": "EntryAt", "type": "SingleLineText"},
    {"title": "CalendarEntryAt", "type": "SingleLineText"},
    {"title": "Timezone", "type": "SingleLineText"},
    {"title": "JournalCreatedAt", "type": "SingleLineText"},
    {"title": "JournalModifiedAt", "type": "SingleLineText"},
    {"title": "TextContent", "type": "LongText"},
    {"title": "RichTextContent", "type": "LongText"},
    {"title": "Title", "type": "SingleLineText"},
    {"title": "Tags", "type": "SingleLineText"},
    {"title": "Notebook", "type": "SingleLineText"},
    {"title": "IsFavorite", "type": "Checkbox"},
    {"title": "IsPinned", "type": "Checkbox"},
    {"title": "Mood", "type": "SingleLineText"},
    {"title": "MoodScore", "type": "Decimal"},
    {"title": "Activities", "type": "SingleLineText"},
    {"title": "LocationLat", "type": "Decimal"},
    {"title": "LocationLon", "type": "Decimal"},
    {"title": "LocationName", "type": "SingleLineText"},
    {"title": "LocationAddress", "type": "LongText"},
    {"title": "LocationAltitude", "type": "Decimal"},
    {"title": "WeatherTemp", "type": "Decimal"},
    {"title": "WeatherCondition", "type": "SingleLineText"},
    {"title": "WeatherHumidity", "type": "Decimal"},
    {"title": "WeatherPressure", "type": "Decimal"},
    {"title": "DeviceName", "type": "SingleLineText"},
    {"title": "StepCount", "type": "Number"},
    {"title": "MediaAttachments", "type": "LongText"},
    {"title": "SourceAppName", "type": "SingleLineText"},
    {"title": "SourceOriginalId", "type": "SingleLineText"},
    {"title": "SourceImportedAt", "type": "SingleLineText"},
    {"title": "SourceRawData", "type": "LongText"},
]

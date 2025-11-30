import json
from datetime import datetime

from data_sources.journey_models import (
    JourneyCloudEntry,
    JourneyLocation,
    JourneyWeather,
)
from journal_core.models import JournalEntry, MediaAttachment


def journey_to_journal(journey_entry: JourneyCloudEntry, raw_data: dict) -> JournalEntry:
    """Converts a JourneyCloudEntry object to the application's internal JournalEntry object."""

    def parse_dt(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    # Flatten location and weather data
    location_lat = journey_entry.location.lat if journey_entry.location else None
    location_lon = journey_entry.location.lng if journey_entry.location else None
    location_name = journey_entry.location.name if journey_entry.location else None
    location_altitude = journey_entry.location.altitude if journey_entry.location else None

    weather_temp = journey_entry.weather.degreeC if journey_entry.weather else None
    weather_cond = journey_entry.weather.description if journey_entry.weather else None

    # Create MediaAttachment objects
    media_attachments = [
        MediaAttachment(id=fname, file_id=fname, filename=fname) for fname in journey_entry.attachments
    ]

    entry_at_dt = parse_dt(journey_entry.dateOfJournal)
    if entry_at_dt is None:
        raise ValueError("JournalEntry requires 'entry_at' to be a valid datetime.")

    return JournalEntry(
        id=journey_entry.id,
        entry_at=entry_at_dt,
        created_at=parse_dt(journey_entry.createdAt or journey_entry.dateOfJournal),
        modified_at=parse_dt(journey_entry.updatedAt),
        timezone=journey_entry.timezone,
        text_content=journey_entry.text,
        rich_text_content=journey_entry.text,
        tags=journey_entry.tags,
        is_favorite=journey_entry.favourite,
        mood_score=journey_entry.sentiment,
        location_lat=location_lat,
        location_lon=location_lon,
        location_name=location_name,
        location_address=journey_entry.address,
        location_altitude=location_altitude,
        weather_temperature=weather_temp,
        weather_condition=weather_cond,
        media_attachments=media_attachments,
        source_app_name="JourneyCloud",
        source_original_id=journey_entry.id,
        source_raw_data=json.dumps(raw_data, ensure_ascii=False),
    )


def journal_to_journey(journal_entry: JournalEntry) -> JourneyCloudEntry:
    """Converts an internal JournalEntry object back to a JourneyCloudEntry object."""

    # If the raw data exists, the most reliable way is to deserialize it.
    if journal_entry.source_raw_data and isinstance(journal_entry.source_raw_data, str):
        try:
            raw_dict = json.loads(journal_entry.source_raw_data)
            return JourneyCloudEntry.from_dict(raw_dict)
        except json.JSONDecodeError:
            # Fallback to manual conversion if raw data is invalid
            pass

    # Manual conversion (fallback or if raw_data is not available)
    location = None
    if journal_entry.location_lat is not None and journal_entry.location_lon is not None:
        location = JourneyLocation(
            lat=journal_entry.location_lat,
            lng=journal_entry.location_lon,
            name=journal_entry.location_name,
            altitude=journal_entry.location_altitude,
        )

    weather = None
    if journal_entry.weather_temperature is not None:
        weather = JourneyWeather(
            degreeC=journal_entry.weather_temperature,
            description=journal_entry.weather_condition,
        )

    def format_dt(dt: datetime | None) -> str | None:
        if dt:
            # Always include milliseconds for consistency with original format
            iso_str = dt.isoformat(timespec="milliseconds")
            return iso_str.replace("+00:00", "Z")
        return None

    return JourneyCloudEntry(
        id=journal_entry.id,
        dateOfJournal=format_dt(journal_entry.entry_at) or "",
        updatedAt=format_dt(journal_entry.modified_at) or "",
        createdAt=format_dt(journal_entry.created_at),
        text=journal_entry.text_content or "",
        timezone=journal_entry.timezone or "",
        favourite=journal_entry.is_favorite,
        sentiment=journal_entry.mood_score or 0.0,
        address=journal_entry.location_address,
        location=location,
        weather=weather,
        tags=journal_entry.tags,
        attachments=[att.filename for att in journal_entry.media_attachments if att.filename],
    )

from datetime import UTC, datetime

from src.journal_core.models import JournalEntry


def test_to_journey_cloud_dict_full():
    """
    Tests the conversion of a comprehensive JournalEntry object to the Journey Cloud dictionary format.
    """
    entry_time = datetime(2023, 10, 27, 10, 30, 0, tzinfo=UTC)
    modified_time = datetime(2023, 10, 27, 11, 0, 0, tzinfo=UTC)

    entry = JournalEntry(
        id="test-id-123",
        entry_at=entry_time,
        modified_at=modified_time,
        timezone="Asia/Tokyo",
        rich_text_content="This is a **great** test.",
        tags=["test", "pytest", "conversion"],
        is_favorite=True,
        mood_score=0.8,
        activities=["8"],  # Corresponds to a Journey activity code
        location_lat=35.681236,
        location_lon=139.767125,
        location_name="Tokyo Station",
        location_address="1 Chome-9 Marunouchi, Chiyoda City, Tokyo 100-0005, Japan",
        location_altitude=3.0,
        weather_temperature=22.5,
        weather_condition="Clear",
        weather_humidity=60.5,
        weather_pressure=1012.5,
        media_attachments=[
            {"type": "photo", "path": "/path/to/image.jpg", "filename": "image.jpg"},
            {"type": "video", "path": "/path/to/video.mp4", "filename": "video.mp4"},
        ],
    )

    journey_dict = entry.to_journey_cloud_dict()

    # --- Assertions ---
    assert journey_dict["id"] == "test-id-123"
    assert journey_dict["dateOfJournal"] == "2023-10-27T10:30:00Z"
    assert journey_dict["createdAt"] == "2023-10-27T10:30:00Z"
    assert journey_dict["updatedAt"] == "2023-10-27T11:00:00Z"
    assert journey_dict["timezone"] == "Asia/Tokyo"

    # Content
    assert journey_dict["text"] == "This is a **great** test."
    assert journey_dict["type"] == "markdown"

    # Metadata
    assert journey_dict["tags"] == ["test", "pytest", "conversion"]
    assert journey_dict["favourite"] is True
    assert journey_dict["sentiment"] == 0.8
    assert journey_dict["activity"] == 8

    # Location
    assert "location" in journey_dict
    location = journey_dict["location"]
    assert location["latitude"] == 35.681236
    assert location["longitude"] == 139.767125
    assert location["name"] == "Tokyo Station"
    assert location["altitude"] == 3.0
    assert (
        journey_dict["address"]
        == "1 Chome-9 Marunouchi, Chiyoda City, Tokyo 100-0005, Japan"
    )

    # Weather
    assert "weather" in journey_dict
    weather = journey_dict["weather"]
    assert weather["temperature"] == 22.5
    assert weather["condition"] == "Clear"
    assert weather["humidity"] == 60.5
    assert weather["pressure"] == 1012.5

    # Attachments
    assert "attachments" in journey_dict
    assert journey_dict["attachments"] == ["image.jpg", "video.mp4"]


def test_to_journey_cloud_dict_minimal():
    """
    Tests the conversion of a minimal JournalEntry object.
    """
    entry_time = datetime(2023, 10, 28, 15, 0, 0, tzinfo=UTC)
    entry = JournalEntry(
        id="minimal-id", entry_at=entry_time, text_content="Just a simple note."
    )

    journey_dict = entry.to_journey_cloud_dict()

    assert journey_dict["id"] == "minimal-id"
    assert journey_dict["dateOfJournal"] == "2023-10-28T15:00:00Z"
    assert journey_dict["text"] == "Just a simple note."
    assert "type" not in journey_dict  # Should not be markdown
    assert journey_dict["favourite"] is False
    assert journey_dict["activity"] == 0
    assert "location" not in journey_dict
    assert "weather" not in journey_dict
    assert (
        "tags" in journey_dict and journey_dict["tags"] == []
    )  # Should be present and empty
    assert "attachments" not in journey_dict
    assert "updatedAt" not in journey_dict  # Since modified_at was None


def test_to_journey_cloud_dict_no_attachments_filename():
    """
    Tests that attachments without a 'filename' key are ignored.
    """
    entry = JournalEntry(
        id="attachment-test",
        entry_at=datetime.now(),
        media_attachments=[
            {"type": "photo", "path": "/path/to/image.jpg"},  # Missing 'filename'
            {"type": "video", "path": "/path/to/video.mp4", "filename": "video.mp4"},
        ],
    )

    journey_dict = entry.to_journey_cloud_dict()

    assert "attachments" in journey_dict
    assert journey_dict["attachments"] == ["video.mp4"]

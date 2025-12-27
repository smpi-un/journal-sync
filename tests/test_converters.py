from dataclasses import asdict

from pytest import approx

from src.data_sources.journey_models import JourneyCloudEntry
from src.journal_core.converters import journal_to_journey, journey_to_journal

# A sample record from a previous run to be used as test data.
# This captures nested objects, lists, and various data types.
SAMPLE_JOURNEY_RECORD = {
    "id": "xH9WUl0f8f4KShUgGZLb",
    "dateOfJournal": "2025-03-22T23:23:07.000Z",
    "text": '<p dir="auto">うまく印刷できてるけど、そもそもの形が異形。</p><p dir="auto">サポーターがね。</p>',
    "timezone": "Asia/Tokyo",
    "updatedAt": "2025-03-23T00:13:09.563Z",
    "favourite": False,
    "sentiment": 0,
    "address": "日本、〒939-8055 富山県富山市下堀３１−９",
    "location": {"lat": 36.66111755371094, "lng": 137.22857666015625},
    "weather": {
        "id": 0,
        "degreeC": 16.3,
        "description": "Clear sky",
        "icon": "01d",
        "place": "Toyama",
    },
    "attachments": ["aKBma1YNyDgmP64y5QdE.jpg", "KZXkb6oLngAWSJNUmRYb.jpg"],
    "tags": [],
    "encrypted": False,
    "version": 1,
    "activity": 0,
    "type": "html",
    "schemaVersion": 2,
    "createdAt": "2025-03-22T23:23:07.000Z",  # Added for completeness
}


def test_conversion_roundtrip():
    """
    Tests that converting a JourneyCloudEntry to a JournalEntry and back
    results in an identical JourneyCloudEntry object.
    """
    # 1. Arrange: Create the initial JourneyCloudEntry object from raw data.
    # The `from_dict` method is tested implicitly here.
    original_journey_entry = JourneyCloudEntry.from_dict(SAMPLE_JOURNEY_RECORD)

    # 2. Act: Perform the forward and backward conversions.
    # Convert to the internal domain model.
    journal_entry = journey_to_journal(original_journey_entry, SAMPLE_JOURNEY_RECORD)

    # Convert back to the source data model.
    # The `journal_to_journey` converter should ideally use the `source_raw_data`
    # for a perfect reconstruction.
    final_journey_entry = journal_to_journey(journal_entry)

    # 3. Assert: The final object should be "close enough" to the original.
    # We must handle nested dicts and floats manually, as pytest.approx
    # does not support nested dictionaries.
    original_dict = asdict(original_journey_entry)
    final_dict = asdict(final_journey_entry)

    # Pop the float-containing parts and compare them with pytest.approx
    assert original_dict.pop("location") == approx(final_dict.pop("location"))
    assert original_dict.pop("weather") == approx(final_dict.pop("weather"))
    assert original_dict.pop("sentiment") == approx(final_dict.pop("sentiment"))

    # Compare the rest of the dictionary for exact equality
    assert original_dict == final_dict


def test_reconstruction_without_raw_data():
    """
    Tests that converting back to JourneyCloudEntry without relying on
    source_raw_data still produces a valid and mostly correct object.
    """
    # 1. Arrange
    original_journey_entry = JourneyCloudEntry.from_dict(SAMPLE_JOURNEY_RECORD)
    journal_entry = journey_to_journal(original_journey_entry, SAMPLE_JOURNEY_RECORD)

    # 2. Act: Simulate a scenario where the raw data is lost.
    journal_entry.source_raw_data = None
    reconstructed_journey_entry = journal_to_journey(journal_entry)

    # 3. Assert: Check key fields to ensure the manual reconstruction logic works.
    assert original_journey_entry.id == reconstructed_journey_entry.id
    assert original_journey_entry.dateOfJournal == reconstructed_journey_entry.dateOfJournal
    assert original_journey_entry.text == reconstructed_journey_entry.text
    if original_journey_entry.location and reconstructed_journey_entry.location:
        assert original_journey_entry.location.lat == reconstructed_journey_entry.location.lat
    assert original_journey_entry.attachments == reconstructed_journey_entry.attachments

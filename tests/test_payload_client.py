import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from clients.payload_client import (
    PayloadCmsJournalClient,
    _journal_entry_to_payload_cms_entry,
    _payload_doc_to_journal_entry,
)
from journal_core.models import JournalEntry


class TestPayloadClient(unittest.TestCase):
    def test_round_trip_conversion(self):
        """
        Tests that a JournalEntry can be converted to a Payload doc
        and back to a nearly identical JournalEntry.
        """
        # 1. Create a complex JournalEntry
        original_entry = JournalEntry(
            id="test-id-123",
            entry_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            title="My Test Entry",
            text_content="<p>This is a test.</p>",
            rich_text_content=None,  # Let's assume it's HTML from Journey
            tags=["testing", "python"],
            is_favorite=True,
            mood_score=0.8,
            location_name="Test Location",
            weather_condition="Sunny",
            source_app_name="TestApp",
            source_raw_data={"key": "value"},
        )

        # 2. Convert to Payload format (as a dictionary)
        payload_entry_obj = _journal_entry_to_payload_cms_entry(original_entry)

        # This step is done inside the client, but we replicate it here
        # to simulate the data that would be sent to and returned from the API.
        payload_doc = {
            "id": "payload-generated-id-abc",  # Payload would generate its own ID
            "entryAt": payload_entry_obj.entryAt.isoformat(),
            "title": payload_entry_obj.title,
            "textContent": payload_entry_obj.textContent,
            "richTextContent": payload_entry_obj.richTextContent,
            "tags": [{"tag": t.tag} for t in payload_entry_obj.tags],
            "isFavorite": payload_entry_obj.isFavorite,
            "moodScore": payload_entry_obj.moodScore,
            "location": {"name": payload_entry_obj.location.name} if payload_entry_obj.location else None,
            "weather": {"condition": payload_entry_obj.weather.condition} if payload_entry_obj.weather else None,
            "source": {
                "appName": payload_entry_obj.source.appName,
                "originalId": payload_entry_obj.source.originalId,
                "rawData": payload_entry_obj.source.rawData,
            }
            if payload_entry_obj.source
            else None,
            "createdAt": "2025-01-01T12:00:00Z",
            "updatedAt": "2025-01-01T12:00:00Z",
        }

        # 3. Convert back to JournalEntry
        reconverted_entry = _payload_doc_to_journal_entry(payload_doc)

        # 4. Assert equality on key fields
        self.assertEqual(original_entry.id, reconverted_entry.id)
        self.assertEqual(original_entry.entry_at, reconverted_entry.entry_at)
        self.assertEqual(original_entry.title, reconverted_entry.title)
        # In our reverse conversion, HTML content from text_content is put back into text_content
        self.assertEqual(original_entry.text_content, reconverted_entry.text_content)
        self.assertEqual(original_entry.tags, reconverted_entry.tags)
        self.assertEqual(original_entry.is_favorite, reconverted_entry.is_favorite)
        self.assertEqual(original_entry.mood_score, reconverted_entry.mood_score)
        self.assertEqual(original_entry.location_name, reconverted_entry.location_name)
        self.assertEqual(original_entry.weather_condition, reconverted_entry.weather_condition)
        self.assertEqual(original_entry.source_app_name, reconverted_entry.source_app_name)
        # Comparing raw data can be tricky if there are nested structures.
        # A simple equality check works for this flat dict.
        self.assertEqual(original_entry.source_raw_data, reconverted_entry.source_raw_data)

    @patch("clients.payload_client.requests.request")
    def test_download_journal_entries(self, mock_request):
        """
        Tests the download_journal_entries method to ensure it correctly
        parses data from a mocked API response.
        """
        # 1. Mock the API response from Payload CMS
        mock_response = MagicMock()
        mock_api_data = {
            "docs": [
                {
                    "id": "payload-id-1",
                    "entryAt": "2025-01-01T12:00:00.000Z",
                    "title": "First Entry",
                    "textContent": "Hello World",
                    "source": {"originalId": "test-id-1"},
                },
                {
                    "id": "payload-id-2",
                    "entryAt": "2025-01-02T15:30:00.000Z",
                    "title": "Second Entry",
                    "textContent": "Another post",
                    "source": {"originalId": "test-id-2"},
                },
            ],
            "totalDocs": 2,
        }
        mock_response.json.return_value = mock_api_data
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 2. Initialize the client and call the download method
        client = PayloadCmsJournalClient(api_url="http://fake-url.com", api_key="fake-key")
        downloaded_entries = client.download_journal_entries()

        # 3. Assert the results
        self.assertEqual(len(downloaded_entries), 2)

        # Check first entry
        self.assertEqual(downloaded_entries[0].id, "test-id-1")
        self.assertEqual(downloaded_entries[0].title, "First Entry")
        self.assertEqual(downloaded_entries[0].entry_at, datetime(2025, 1, 1, 12, 0, tzinfo=UTC))

        # Check second entry
        self.assertEqual(downloaded_entries[1].id, "test-id-2")
        self.assertEqual(downloaded_entries[1].title, "Second Entry")
        self.assertEqual(downloaded_entries[1].entry_at, datetime(2025, 1, 2, 15, 30, tzinfo=UTC))


if __name__ == "__main__":
    unittest.main()

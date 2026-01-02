import unittest
from datetime import UTC, datetime
from unittest.mock import patch

# The client now uses gql, so we adjust the patch target.
# Also, the conversion functions have been refactored.
from clients.payload_client import (
    PayloadCmsJournalClient,
    _journal_entry_to_mutation_dict,
    _payload_doc_to_journal_entry,
)
from journal_core.models import JournalEntry, MediaAttachment


class TestPayloadGraphQLClient(unittest.TestCase):
    def test_round_trip_conversion(self):
        """
        Tests the data pipeline:
        1. JournalEntry -> GraphQL mutation variables (`_journal_entry_to_mutation_dict`)
        2. A mock GraphQL doc -> JournalEntry (`_payload_doc_to_journal_entry`)
        """
        # 1. Create a complex JournalEntry
        original_entry = JournalEntry(
            id="test-id-123",
            entry_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            modified_at=datetime(2025, 1, 1, 13, 0, 0, tzinfo=UTC),
            created_at=datetime(2025, 1, 1, 11, 0, 0, tzinfo=UTC),
            title="My Test Entry",
            rich_text_content='[{"type":"p","children":[{"text":"This is rich text."}]}]',
            tags=["testing", "python"],
            is_favorite=True,
            mood_score=0.8,
            location_name="Test Location",
            weather_condition="Sunny",
            source_app_name="TestApp",
            source_raw_data={"key": "value"},
        )

        # 2. Convert to GraphQL `createJournal` mutation variables
        # The attachment IDs would come from the file upload process.
        attachment_ids = ["fake-file-id-1"]
        mutation_vars = _journal_entry_to_mutation_dict(original_entry, attachment_ids)

        # Assert some key fields in the generated mutation variables
        self.assertEqual(mutation_vars["entryAt"], "2025-01-01T12:00:00+00:00")
        self.assertEqual(mutation_vars["title"], "My Test Entry")
        self.assertEqual(mutation_vars["tags"], [{"tag": "testing"}, {"tag": "python"}])
        self.assertEqual(mutation_vars["attachments"], [{"file": "fake-file-id-1"}])
        self.assertEqual(mutation_vars["source"]["originalId"], "test-id-123")
        self.assertIn("children", mutation_vars["richTextContent"][0])

        # 3. Create a mock GraphQL doc that would be returned from a query
        graphql_doc = {
            "id": "payload-generated-id-abc",
            "entryAt": "2025-01-01T12:00:00+00:00",
            "createdAt": "2025-01-01T11:00:00+00:00",
            "updatedAt": "2025-01-01T13:00:00+00:00",
            "title": "My Test Entry",
            "richTextContent": [{"type": "p", "children": [{"text": "This is rich text."}]}],
            "tags": [{"tag": "testing"}, {"tag": "python"}],
            "isFavorite": True,
            "moodScore": 0.8,
            "location": {"name": "Test Location"},
            "weather": {"condition": "Sunny"},
            "source": {
                "appName": "TestApp",
                "originalId": "test-id-123",
                "rawData": {"key": "value"},
            },
            "attachments": [
                {
                    "id": "attachment-block-id",
                    "file": {
                        "id": "fake-file-id-1",
                        "filename": "test.jpg",
                        "url": "/media/test.jpg",
                    },
                }
            ],
        }

        # 4. Convert mock doc back to JournalEntry
        reconverted_entry = _payload_doc_to_journal_entry(graphql_doc)

        # 5. Assert equality on key fields
        self.assertEqual(original_entry.id, reconverted_entry.id)
        self.assertEqual(original_entry.entry_at, reconverted_entry.entry_at)
        self.assertEqual(original_entry.title, reconverted_entry.title)
        self.assertEqual(reconverted_entry.text_content, "This is rich text.")  # Check Slate->text conversion
        self.assertEqual(original_entry.tags, reconverted_entry.tags)
        self.assertEqual(original_entry.is_favorite, reconverted_entry.is_favorite)
        self.assertEqual(original_entry.mood_score, reconverted_entry.mood_score)
        self.assertEqual(original_entry.location_name, reconverted_entry.location_name)
        self.assertEqual(original_entry.weather_condition, reconverted_entry.weather_condition)
        self.assertEqual(original_entry.source_app_name, reconverted_entry.source_app_name)
        self.assertEqual(original_entry.source_raw_data, reconverted_entry.source_raw_data)
        self.assertEqual(len(reconverted_entry.media_attachments), 1)
        self.assertEqual(reconverted_entry.media_attachments[0].file_id, "fake-file-id-1")

    # We now patch the GQL Client's `execute` method
    @patch("clients.payload_client.Client")
    def test_download_journal_entries(self, MockGQLClient):
        """
        Tests the download_journal_entries method to ensure it correctly
        parses data from a mocked GraphQL API response.
        """
        # 1. Mock the GraphQL API response
        mock_api_data = {
            "Journals": {
                "docs": [
                    {
                        "id": "payload-id-1",
                        "entryAt": "2025-01-01T12:00:00.000Z",
                        "title": "First Entry",
                        "richTextContent": [{"type": "p", "children": [{"text": "Hello World"}]}],
                        "source": {"originalId": "test-id-1"},
                        "updatedAt": "2025-01-01T12:00:00.000Z",
                    },
                    {
                        "id": "payload-id-2",
                        "entryAt": "2025-01-02T15:30:00.000Z",
                        "title": "Second Entry",
                        "richTextContent": [{"type": "p", "children": [{"text": "Another post"}]}],
                        "source": {"originalId": "test-id-2"},
                        "updatedAt": "2025-01-02T15:30:00.000Z",
                    },
                ],
                "hasNextPage": False,
            }
        }
        # The client instance is on the class, so we mock its `execute` method
        mock_gql_instance = MockGQLClient.return_value
        mock_gql_instance.execute.return_value = mock_api_data

        # 2. Initialize the client and call the download method
        # The constructor will use the mocked GQL Client
        client = PayloadCmsJournalClient(api_url="http://fake-url.com", api_key="fake-key")
        downloaded_entries = client.download_journal_entries()

        # 3. Assert the results
        self.assertEqual(len(downloaded_entries), 2)
        mock_gql_instance.execute.assert_called_once()  # Should be called once since hasNextPage is false

        # Check first entry
        self.assertEqual(downloaded_entries[0].id, "test-id-1")
        self.assertEqual(downloaded_entries[0].title, "First Entry")
        self.assertEqual(downloaded_entries[0].entry_at, datetime(2025, 1, 1, 12, 0, tzinfo=UTC))
        self.assertEqual(downloaded_entries[0].text_content, "Hello World")

        # Check second entry
        self.assertEqual(downloaded_entries[1].id, "test-id-2")
        self.assertEqual(downloaded_entries[1].title, "Second Entry")
        self.assertEqual(downloaded_entries[1].entry_at, datetime(2025, 1, 2, 15, 30, tzinfo=UTC))
        self.assertEqual(downloaded_entries[1].text_content, "Another post")

    @patch("clients.payload_client.Client")
    @patch("clients.payload_client.PayloadCmsJournalClient.upload_file")
    def test_register_entry(self, mock_upload_file, MockGQLClient):
        """Tests the `register_entry` mutation call."""
        # 1. Mock GQL client and upload function
        mock_gql_instance = MockGQLClient.return_value
        mock_gql_instance.execute.return_value = {
            "createJournal": {"id": "new-payload-id", "title": "Test Entry", "entryAt": "2025-01-01T12:00:00+00:00"}
        }
        mock_upload_file.return_value = {"id": "uploaded-file-id-123"}

        # 2. Create entry with an attachment to be uploaded
        entry = JournalEntry(
            id="local-id-1",
            entry_at=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
            title="Test Entry",
            media_attachments=[
                # Provide dummy IDs to satisfy the constructor. The register_entry logic
                # correctly prioritizes path/filename for new uploads.
                MediaAttachment(
                    id="dummy-block-id", file_id="dummy-file-id", path="/fake/path/image.jpg", filename="image.jpg"
                )
            ],
        )

        # 3. Call register_entry
        client = PayloadCmsJournalClient(api_url="http://fake-url.com", api_key="fake-key")
        # We need to patch `os.path.exists` because the upload logic checks it.
        with patch("clients.payload_client.os.path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=b"fake-data")):
                result = client.register_entry(entry)

        # 4. Assertions
        # Assert file upload was called
        mock_upload_file.assert_called_once_with(b"fake-data", "image.jpg")

        # Assert GraphQL mutation was called with correct variables
        mock_gql_instance.execute.assert_called_once()
        args, kwargs = mock_gql_instance.execute.call_args

        # kwargs['variable_values']['data'] contains the mutation input
        mutation_vars = kwargs["variable_values"]["data"]
        self.assertEqual(mutation_vars["title"], "Test Entry")
        self.assertEqual(mutation_vars["source"]["originalId"], "local-id-1")
        self.assertEqual(len(mutation_vars["attachments"]), 1)
        self.assertEqual(mutation_vars["attachments"][0]["file"], "uploaded-file-id-123")

        # Assert the result from the method is correct
        self.assertEqual(result["id"], "new-payload-id")


if __name__ == "__main__":
    unittest.main()

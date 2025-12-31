import json
import shutil
import tempfile
from pathlib import Path

import pytest

from src.data_sources.journey_cloud_source import JourneyCloudDataSource


@pytest.fixture
def temp_journey_data_dir():
    """
    Creates a temporary directory structure for Journey Cloud data
    and yields the path to this directory.
    """
    temp_dir = Path(tempfile.mkdtemp())

    # --- Test Case 1: Markdown Entry ---
    md_entry_id = "md001"
    md_entry_dir = temp_dir / md_entry_id
    md_entry_dir.mkdir()
    md_data = {
        "id": md_entry_id,
        "dateOfJournal": "2023-10-27T10:00:00Z",
        "text": "# Hello\n\nThis is a *markdown* entry.",
        "type": "markdown",
    }
    with open(md_entry_dir / f"{md_entry_id}.json", "w", encoding="utf-8") as f:
        json.dump(md_data, f)

    # --- Test Case 2: HTML Entry ---
    html_entry_id = "html001"
    html_entry_dir = temp_dir / html_entry_id
    html_entry_dir.mkdir()
    html_data = {
        "id": html_entry_id,
        "dateOfJournal": "2023-10-27T11:00:00Z",
        "text": "<h1>Hello</h1><p>This is an <b>HTML</b> entry.</p>",
        "type": "html",
    }
    with open(html_entry_dir / f"{html_entry_id}.json", "w", encoding="utf-8") as f:
        json.dump(html_data, f)

    # --- Test Case 3: Plain Text Entry (no type specified) ---
    text_entry_id = "txt001"
    text_entry_dir = temp_dir / text_entry_id
    text_entry_dir.mkdir()
    text_data = {
        "id": text_entry_id,
        "dateOfJournal": "2023-10-27T12:00:00Z",
        "text": "Just some plain text.",
    }
    with open(text_entry_dir / f"{text_entry_id}.json", "w", encoding="utf-8") as f:
        json.dump(text_data, f)

    yield str(temp_dir)

    # Teardown: clean up the temporary directory
    shutil.rmtree(temp_dir)


def test_fetch_entries_markdown_conversion(temp_journey_data_dir):
    """
    Tests that a markdown entry is correctly converted to HTML.
    """
    data_source = JourneyCloudDataSource(data_path=temp_journey_data_dir)
    entries = data_source.fetch_entries()

    md_entry = next((e for e in entries if e.id == "md001"), None)

    assert md_entry is not None
    assert md_entry.text_content == "# Hello\n\nThis is a *markdown* entry."
    # Basic check for rendered HTML
    assert "<h1>Hello</h1>" in md_entry.rich_text_content
    assert "<em>markdown</em>" in md_entry.rich_text_content


def test_fetch_entries_html_conversion(temp_journey_data_dir):
    """
    Tests that an HTML entry is correctly converted to Markdown.
    """
    data_source = JourneyCloudDataSource(data_path=temp_journey_data_dir)
    entries = data_source.fetch_entries()

    html_entry = next((e for e in entries if e.id == "html001"), None)

    assert html_entry is not None
    assert html_entry.rich_text_content == "<h1>Hello</h1><p>This is an <b>HTML</b> entry.</p>"

    # The default heading style for markdownify is SETEXT.
    expected_markdown = "Hello\n=====\n\nThis is an **HTML** entry."
    assert html_entry.text_content.strip() == expected_markdown.strip()


def test_fetch_entries_plain_text(temp_journey_data_dir):
    """
    Tests that a plain text entry (with no type) is handled correctly.
    """
    data_source = JourneyCloudDataSource(data_path=temp_journey_data_dir)
    entries = data_source.fetch_entries()

    text_entry = next((e for e in entries if e.id == "txt001"), None)

    assert text_entry is not None
    assert text_entry.text_content == "Just some plain text."
    assert text_entry.rich_text_content == "Just some plain text."

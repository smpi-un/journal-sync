import json
import zipfile
from pathlib import Path

import pytest
from utils.unzip_journey import unzip_and_update_json


@pytest.fixture
def journey_zip_file(tmp_path: Path) -> Path:
    """
    Creates a dummy Journey zip file for testing.

    Structure:
    /
    └── entry1/
        ├── entry1.json
        ├── photo.jpg
        └── document.pdf
    """
    source_dir = tmp_path / "source"
    entry_dir = source_dir / "entry1"
    entry_dir.mkdir(parents=True)

    # Create dummy JSON
    json_path = entry_dir / "entry1.json"
    json_path.write_text(json.dumps({"id": "entry1", "text": "This is a test entry."}))

    # Create dummy attachments
    (entry_dir / "photo.jpg").write_text("fake image data")
    (entry_dir / "document.pdf").write_text("fake pdf data")

    # Create the zip file
    zip_path = tmp_path / "test_journey.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # The order of writing is important for the test
        zf.write(json_path, "entry1/entry1.json")
        zf.write(entry_dir / "photo.jpg", "entry1/photo.jpg")
        zf.write(entry_dir / "document.pdf", "entry1/document.pdf")

    return zip_path


def test_unzip_and_update_json(journey_zip_file: Path, tmp_path: Path):
    """
    Tests the core functionality of unzipping a Journey archive and updating the JSON.
    """
    output_dir = tmp_path / "output"

    # --- Execute ---
    unzip_and_update_json(str(journey_zip_file), str(output_dir))

    # --- Assertions ---

    # 1. Check if files are extracted correctly
    expected_entry_dir = output_dir / "entry1"
    expected_json_path = expected_entry_dir / "entry1.json"
    expected_photo_path = expected_entry_dir / "photo.jpg"
    expected_pdf_path = expected_entry_dir / "document.pdf"

    assert output_dir.is_dir()
    assert expected_entry_dir.is_dir()
    assert expected_json_path.is_file()
    assert expected_photo_path.is_file()
    assert expected_pdf_path.is_file()

    # 2. Check the content of the updated JSON file
    with open(expected_json_path, encoding="utf-8") as f:
        updated_data = json.load(f)

    assert "attachments" in updated_data

    # 3. Check the order of attachments
    # The order should match the order they were added to the zip in the fixture
    assert updated_data["attachments"] == ["photo.jpg", "document.pdf"]

    # 4. Check that original data is preserved
    assert updated_data["id"] == "entry1"
    assert updated_data["text"] == "This is a test entry."


def test_unzip_non_existent_file(tmp_path: Path):
    """
    Tests that the function handles a non-existent zip file gracefully.
    """
    output_dir = tmp_path / "output"
    non_existent_zip = tmp_path / "no.zip"

    # Should not raise an exception, but print an error
    unzip_and_update_json(str(non_existent_zip), str(output_dir))

    # The output directory should not be created if the zip doesn't exist
    # (Based on the current implementation)
    assert not output_dir.exists()


def test_unzip_bad_zip_file(tmp_path: Path):
    """
    Tests that the function handles a corrupted or non-zip file gracefully.
    """
    output_dir = tmp_path / "output"
    bad_zip_path = tmp_path / "bad.zip"
    bad_zip_path.write_text("this is not a zip file")

    # Should not raise an exception, but print an error
    unzip_and_update_json(str(bad_zip_path), str(output_dir))

    # The output directory might be created, but no files should be extracted
    assert output_dir.is_dir()
    assert len(list(output_dir.iterdir())) == 0

# Current Code Analysis: `src/main.py`

## Overview
The `src/main.py` script is designed to import Journey.Cloud diary entries and their associated attachments into NocoDB. It includes logic for creating tables if they don't exist, handling attachments, and performing conditional updates based on timestamps.

## Current Structure & NocoDB Interaction
- **Configuration:** Uses global variables for NocoDB URL, API token, project ID, and table/field names.
- **Table Metadata:** `get_table_meta` fetches high-level table info (V1 API). `create_table_if_not_exists` now attempts to fetch detailed table metadata (V2 API: `/api/v2/meta/tables/{tableId}`) after initial check/creation.
- **Table Creation:** `create_table` uses `POST /api/v1/db/meta/projects/{PROJECT_ID}/tables` to create tables with initial column definitions.
- **Column Addition:** `add_column_to_table` uses `POST /api/v2/tables/{tableId}/columns` to add columns to an existing table.
- **File Upload:** `upload_file_to_nocodb` uses `POST /api/v2/storage/upload` for attachment files.
- **Attachment Record Creation:** `create_attachment_record` creates records in the `Attachments` table, linking them to `JourneyEntries`.
- **Record Operations:** Uses `GET /api/v2/tables/{tableId}/records` to fetch existing records, `POST` for new records, and `PATCH` for updates.
- **ZIP Handling:** Uses `zipfile` and `tempfile.TemporaryDirectory` to extract and process data from a ZIP archive.

## Identified Issues & Debugging History

### 1. `FileNotFoundError` for `temp_dir`
- **Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmpXXXXXX'` when `os.listdir(temp_dir)` was called.
- **Root Cause:** The `with tempfile.TemporaryDirectory() as temp_dir:` block was not encompassing all the code that needed access to the extracted files. The directory was being cleaned up prematurely as the `with` block was exited too early.
- **Current Status:** Fixed by correcting the indentation to ensure all processing logic remains within the `with` block.

### 2. `TypeError: list indices must be integers or slices, not str` for `file_metadata["id"]`
- **Symptom:** Occurred when trying to access `file_metadata["id"]` after `upload_file_to_nocodb`.
- **Root Cause:** The `file_metadata` returned by NocoDB's `/api/v2/storage/upload` endpoint was a list containing a dictionary, not a dictionary directly.
- **Current Status:** Fixed by adding `isinstance` checks and safely accessing `file_metadata[0].get("id")` or `file_metadata.get("id")`.

### 3. `Error: Could not find 'Id' column uxid in 'JourneyEntries' table metadata.`
- **Symptom:** Script failed to find the `uxid` for the "Id" column in `JourneyEntries` table metadata.
- **Root Cause:** The initial V1 meta API call (`/api/v1/db/meta/projects/{PROJECT_ID}/tables`) did not return detailed column information. My code was also incorrectly looking for `uxid` when the column identifier is simply `id`.
- **Current Status:** Fixed by:
    - Switching to `GET /api/v2/meta/tables/{tableId}` to fetch detailed table metadata (including columns).
    - Using `col.get("id")` instead of `col.get("uxid")` to retrieve the column's unique identifier.

### 4. `Warning: Failed to get ID from created attachment record for ... Created record: {... 'JournalEntry': '[object Object]'}`
- **Symptom:** `create_attachment_record` successfully creates a record in the `Attachments` table, but the returned JSON does not contain an `id` or `Id` key at the top level, and the `JournalEntry` field shows `[object Object]`.
- **Root Cause (Hypothesis):** The `Attachments` table's columns, especially the `JournalEntry` link column, are not being correctly created or recognized by NocoDB. The `create_table` function, when called for `Attachments`, is not correctly processing the `columns_definition` for link types.
- **Current Status:**
    - `create_table_if_not_exists` has been refactored to fetch detailed metadata after creation.
    - The `main` function now attempts to create the `Attachments` table *without* the link column initially, and then *adds* the link column using `add_column_to_table` with the correct `fk_uxid` (which is `journal_id_column_id`).
    - The `JournalEntry: '[object Object]'` indicates the link column is still not correctly established in NocoDB's internal schema, even if the `add_column_to_table` call succeeds. This suggests a deeper issue with NocoDB's API for adding link columns or how `colOptions` are interpreted.

### 5. `Failed to create new records. Error: 400 Client Error: Bad Request for url: http://localhost:8080/api/v2/tables/monn9ihpww8gz0f/records`
- **Symptom:** NocoDB returns a `400 Bad Request` when attempting to create new records in the `JourneyEntries` table.
- **Root Cause (Hypothesis):**
    - **Missing `Response content`:** The most critical missing piece of information is the detailed error message from NocoDB. `e.response.text` is consistently empty, preventing precise diagnosis. This is unusual for NocoDB's API.
    - **Data Type Mismatch:** A field in `record_data` might have a value that doesn't match the NocoDB column type (e.g., `Music` field is `json` type but `null` is sent, or `Tags` is `MultiSelect` but a comma-separated string is sent).
    - **Required Field Missing:** A non-nullable field in NocoDB is not being provided.
    - **`Attachments` field format:** Although `Attachments: []` is now sent, if the `Attachments` column in `JourneyEntries` is not correctly configured as an "Attachment" type in NocoDB, this could cause a `400`.
- **Current Status:** The `record_data` is now printed for debugging. The lack of `e.response.text` is the primary blocker for diagnosing this.

---

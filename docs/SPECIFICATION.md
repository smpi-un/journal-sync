# Project Specification: Journey.Cloud Importer

## Overall Goal
The primary goal of this project is to import diary data exported from Journey.Cloud into various backend services. This imported data will serve as a foundation for future extensions, including editing functionalities and custom user interfaces within the chosen backend.

Currently supported and targeted backends include:
-   **Teable**
-   **NocoDB**
-   **Grist** (under active development)

## Current State (as of latest update)
A Python script (`src/main.py`) exists that attempts to import data. It supports Teable and NocoDB clients. Initial integration for Grist has been attempted but is currently not fully functional and requires further development.

## Desired Features & Specifications

### 1. Data Source: ZIP File Import
-   The script should accept a Journey.Cloud exported ZIP file as its primary input.
-   The ZIP file contains individual diary entries, each typically in its own subdirectory, consisting of a JSON file and associated media (images, videos).

### 2. Attachment Handling
-   **Import Attachments:** Media files (images, videos) associated with diary entries must be imported.
-   **Separate Attachment Table:** Attachments should be stored in a dedicated table within the chosen backend (e.g., "Attachments" in NocoDB/Teable).
-   **Relational Linking:** Each attachment record in the "Attachments" table must be linked to its corresponding diary entry in the "JourneyEntries" table.
-   **Attachment Order:** The order of attachments for a given diary entry must be preserved. This order is determined by the order of files within the ZIP archive for that entry.

### 3. Conditional Update Logic for Journal Entries
-   When importing a diary entry:
    -   **Check Existence:** Determine if a record with the same unique identifier (Journey.Cloud `id` field) already exists in the "JourneyEntries" table in the chosen backend.
    -   **Compare Modification Dates:** If an existing record is found, compare the `updatedAt` timestamp from the incoming Journey.Cloud data with the `UpdatedAt` timestamp of the existing record.
    -   **Overwrite if Newer:** If the incoming data's `updatedAt` is *newer* than the existing record's `UpdatedAt`, the existing record should be updated (overwritten).
    -   **Skip if Older/Same:** If the incoming data's `updatedAt` is *older than or the same as* the existing record's `UpdatedAt`, the existing record should *not* be updated.

### 4. Automatic Table & Column Creation
-   The script should automatically create the necessary tables (e.g., "JourneyEntries" and "Attachments") if they do not already exist in the chosen backend.
-   It should also ensure that all required columns for these tables are present, adding them if they are missing. This includes correctly setting up link columns.

### 5. Client-Specific Implementations

#### Teable Client
-   **Status:** Largely functional.
-   **Table Naming:** "JourneyEntries" for journal entries, "Attachments" for media.
-   **Field Mapping:** Defined in `clients/teable_client_config.py`.
-   **API Interaction:** Uses Teable's REST API.

#### NocoDB Client
-   **Status:** Largely functional, with some known issues (see `NOCODB_CODE_ANALYSIS.md`).
-   **Table Naming:** "JournalEntries" for journal entries, "Attachments" for media.
-   **Field Mapping:** Defined in `clients/nocodb_client_config.py`.
-   **API Interaction:** Uses NocoDB's REST API (mix of v1 and v2 endpoints).

#### Grist Client
-   **Status:** Under development. Initial implementation has been reverted due to API understanding issues.
-   **Table Naming:** Intended to use "JournalEntries".
-   **Field Mapping:** Intended to be defined in `clients/grist_client_config.py`.
-   **API Interaction:** Intended to use Grist's REST API. Requires further investigation into table identification and data population mechanisms.